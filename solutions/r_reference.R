#!/usr/bin/env Rscript

# Implementación independiente en R base de los tres casos sintéticos canónicos.
# No usa reticulate, Pandas ni paquetes de CRAN. Lee los CSV crudos y escribe tablas
# comparables con las soluciones de Pandas, SQL, Excel y Polars.

script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(script_arg) != 1) stop("Ejecute este archivo con Rscript.")
script_path <- sub("^--file=", "", script_arg[1])
root <- normalizePath(file.path(dirname(script_path), ".."), winslash = "/", mustWork = TRUE)

read_input <- function(path) {
  if (!file.exists(path)) stop(sprintf("No existe %s", path))
  read.csv(path, stringsAsFactors = FALSE, na.strings = c("", "NA"),
           check.names = FALSE, fileEncoding = "UTF-8")
}

profile_frame <- function(frame) {
  duplicates <- sum(duplicated(frame))
  data.frame(
    column = names(frame),
    dtype = vapply(frame, function(column) class(column)[1], character(1)),
    nulls = vapply(frame, function(column) sum(is.na(column)), numeric(1)),
    unique = vapply(frame, function(column) length(unique(column[!is.na(column)])), numeric(1)),
    rows = rep(nrow(frame), ncol(frame)),
    exact_duplicates = rep(duplicates, ncol(frame)),
    stringsAsFactors = FALSE
  )
}

analyze_transport <- function(case_number) {
  if (!(case_number %in% c(1, 2, 3))) stop("Caso inválido. Use 1, 2 o 3.")
  folder <- file.path(root, "data", sprintf("case_%d", case_number))
  trips <- read_input(file.path(folder, "viajes.csv"))
  routes <- read_input(file.path(folder, "recorridos.csv"))
  operators <- read_input(file.path(folder, "operadores.csv"))
  schedule <- read_input(file.path(folder, "programacion.csv"))

  original <- nrow(trips)
  t <- trips[!duplicated(trips), , drop = FALSE]
  t$pasajeros <- suppressWarnings(as.numeric(t$pasajeros))
  t$inicio_tipado <- as.POSIXct(t$inicio, format = "%Y-%m-%d %H:%M:%S", tz = "UTC")
  t$fin_tipado <- as.POSIXct(t$fin, format = "%Y-%m-%d %H:%M:%S", tz = "UTC")
  t <- merge(t, routes, by = "recorrido_id", all.x = TRUE, sort = FALSE)
  t <- merge(t, operators, by = "operador_id", all.x = TRUE, sort = FALSE)
  t$duracion_min <- as.numeric(difftime(t$fin_tipado, t$inicio_tipado, units = "mins"))
  t$realizado <- !is.na(t$estado) & t$estado == "REALIZADO"
  t$pasajeros_invalido <- is.na(t$pasajeros) | t$pasajeros < 0
  t$duracion_invalida <- is.na(t$duracion_min) | t$duracion_min < 0
  t$clave_desconocida <- is.na(t$operador_id)

  quality <- data.frame(
    indicador = c("filas_originales", "duplicados_exactos", "claves_desconocidas",
                  "pasajeros_invalidos_realizados", "duracion_invalida_realizados"),
    valor = c(original, original - nrow(t), sum(t$clave_desconocida),
              sum(t$realizado & t$pasajeros_invalido),
              sum(t$realizado & t$duracion_invalida)),
    stringsAsFactors = FALSE
  )

  valid <- t[t$realizado & !t$clave_desconocida, , drop = FALSE]
  valid$dia_octubre <- as.integer(format(valid$inicio_tipado, "%d"))
  valid$hora <- as.integer(format(valid$inicio_tipado, "%H"))
  with_pax <- valid[!valid$pasajeros_invalido, , drop = FALSE]

  demand_sum <- aggregate(pasajeros ~ operador, data = with_pax, FUN = sum)
  demand_count <- aggregate(viaje_id ~ operador, data = with_pax, FUN = length)
  names(demand_count)[2] <- "viajes_con_dato"
  demand <- merge(demand_sum, demand_count, by = "operador", sort = TRUE)
  hour <- aggregate(pasajeros ~ hora, data = with_pax, FUN = sum)
  hour <- hour[order(hour$hora), , drop = FALSE]

  dur <- valid[!valid$duracion_invalida, , drop = FALSE]
  duration_parts <- lapply(split(dur, dur$recorrido_id), function(group) {
    data.frame(
      recorrido_id = group$recorrido_id[1],
      media_min = mean(group$duracion_min),
      mediana_min = as.numeric(quantile(group$duracion_min, 0.5, type = 7)),
      p90_min = as.numeric(quantile(group$duracion_min, 0.9, type = 7)),
      puntualidad_pct = 100 * mean(group$duracion_min <= group$meta_min),
      stringsAsFactors = FALSE
    )
  })
  duration <- do.call(rbind, duration_parts)
  duration <- duration[order(duration$recorrido_id), , drop = FALSE]

  counts <- aggregate(rep(1L, nrow(valid)),
                      by = list(recorrido_id = valid$recorrido_id,
                                dia_octubre = valid$dia_octubre), FUN = sum)
  names(counts)[3] <- "realizados"
  schedule$dia_octubre <- as.integer(schedule$dia_octubre)
  schedule$viajes_programados <- as.integer(schedule$viajes_programados)
  compliance <- merge(schedule, counts, by = c("recorrido_id", "dia_octubre"),
                      all = TRUE, sort = TRUE)
  compliance$realizados[is.na(compliance$realizados)] <- 0L
  compliance$cumplimiento_pct <- ifelse(
    !is.na(compliance$viajes_programados) & compliance$viajes_programados > 0,
    100 * compliance$realizados / compliance$viajes_programados,
    NA_real_
  )

  operator_base <- merge(compliance, routes, by = "recorrido_id", all.x = FALSE, sort = FALSE)
  operator_base <- merge(operator_base, operators, by = "operador_id", all.x = FALSE, sort = FALSE)
  operator_base$programados_suma <- ifelse(is.na(operator_base$viajes_programados),
                                           0L, operator_base$viajes_programados)
  realized_operator <- aggregate(realizados ~ operador, data = operator_base, FUN = sum)
  programmed_operator <- aggregate(programados_suma ~ operador, data = operator_base, FUN = sum)
  names(programmed_operator)[2] <- "viajes_programados"
  by_operator <- merge(realized_operator, programmed_operator, by = "operador", sort = TRUE)
  by_operator$cumplimiento_pct <- 100 * by_operator$realizados / by_operator$viajes_programados

  realized_route <- aggregate(rep(1L, nrow(valid)),
                              by = list(recorrido_id = valid$recorrido_id), FUN = sum)
  names(realized_route)[2] <- "realizados"
  realized_route <- realized_route[order(realized_route$recorrido_id), , drop = FALSE]

  list(calidad = quality, demanda = demand, demanda_hora = hour, duracion = duration,
       cumplimiento = compliance, cumplimiento_operador = by_operator,
       realizados_recorrido = realized_route)
}

analyze_retail <- function() {
  raw <- read_input(file.path(root, "cases", "retail", "input.csv"))
  clean <- raw[!duplicated(raw), , drop = FALSE]
  clean <- clean[clean$quantity > 0 & clean$price >= 0 & clean$cost >= 0 &
                 clean$status %in% c("SALE", "RETURN"), , drop = FALSE]
  clean$units <- ifelse(clean$status == "SALE", clean$quantity, -clean$quantity)
  clean$net_sales <- clean$units * clean$price
  clean$margin <- clean$units * (clean$price - clean$cost)
  metrics <- aggregate(cbind(units, net_sales, margin) ~ product, data = clean, FUN = sum)
  metrics <- metrics[order(metrics$product), , drop = FALSE]
  list(quality = profile_frame(raw), metrics = metrics)
}

analyze_education <- function() {
  raw <- read_input(file.path(root, "cases", "education", "input.csv"))
  clean <- raw[!duplicated(raw), , drop = FALSE]
  clean <- clean[clean$scheduled > 0 & clean$attended >= 0 &
                 clean$attended <= clean$scheduled, , drop = FALSE]
  clean$rate <- 100 * clean$attended / clean$scheduled
  totals <- aggregate(cbind(attended, scheduled) ~ school, data = clean, FUN = sum)
  simple <- aggregate(rate ~ school, data = clean, FUN = mean)
  names(simple)[2] <- "simple_pct"
  metrics <- merge(totals, simple, by = "school", sort = TRUE)
  metrics$weighted_pct <- 100 * metrics$attended / metrics$scheduled
  list(quality = profile_frame(raw), metrics = metrics)
}

write_tables <- function(tables, destination) {
  dir.create(destination, recursive = TRUE, showWarnings = FALSE)
  for (name in names(tables)) {
    write.csv(tables[[name]], file.path(destination, paste0(name, ".csv")),
              row.names = FALSE, na = "", fileEncoding = "UTF-8")
  }
}

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1 || !(args[1] %in% c("transport", "retail", "education"))) {
  stop("Uso: Rscript solutions/r_reference.R <transport|retail|education> [1|2|3] [destino]")
}
case_name <- args[1]
case_number <- if (length(args) >= 2) as.integer(args[2]) else 1L
destination <- if (length(args) >= 3) args[3] else
  file.path(root, "reference_outputs", "r", case_name)

tables <- switch(case_name,
                 transport = analyze_transport(case_number),
                 retail = analyze_retail(),
                 education = analyze_education())
write_tables(tables, destination)
cat(sprintf("%s: %d tablas escritas en %s\n", case_name, length(tables), destination))

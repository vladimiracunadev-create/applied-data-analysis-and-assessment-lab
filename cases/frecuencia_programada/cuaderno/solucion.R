#!/usr/bin/env Rscript
# Contraste R + ggplot2 del caso frecuencia_programada.
script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
script_path <- if (length(script_arg)) sub("^--file=", "", script_arg[1]) else "cuaderno/solucion.R"
root <- normalizePath(file.path(dirname(script_path), "../../.."), mustWork = TRUE)
source_csv <- file.path(root, "cases", "frecuencia_programada", "resultados", "distribucion.csv")

datos <- read.csv(source_csv, check.names = FALSE, fileEncoding = "UTF-8")
resultado <- datos[, c("estadistico", "intervalo_min")]
print(resultado, row.names = FALSE)

args <- commandArgs(trailingOnly = TRUE)
plot_pos <- match("--grafico", args)
if (!is.na(plot_pos)) {
  if (plot_pos == length(args)) stop("--grafico necesita una ruta de salida")
  if (!requireNamespace("ggplot2", quietly = TRUE)) {
    stop("Instale ggplot2 para generar el gráfico: install.packages('ggplot2')")
  }
  destino <- args[plot_pos + 1]
  grafico <- ggplot2::ggplot(
    resultado,
    ggplot2::aes(x = .data[["estadistico"]], y = .data[["intervalo_min"]])
  ) +
    ggplot2::geom_col(fill = "#11253B") +
    ggplot2::labs(
      title = "La distribución revela más que un promedio",
      x = "Estadístico", y = "Intervalo entre salidas (minutos)",
      caption = "Fuente: Resultados reproducibles del caso P12/P13 · Período: publicación GTFS analizada"
    ) +
    ggplot2::theme_minimal(base_size = 11)
  ggplot2::ggsave(destino, grafico, width = 9, height = 5, dpi = 150)
  cat(destino, "\n")
}

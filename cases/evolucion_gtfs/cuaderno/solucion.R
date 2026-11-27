#!/usr/bin/env Rscript
# Contraste R + ggplot2 del caso evolucion_gtfs.
script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
script_path <- if (length(script_arg)) sub("^--file=", "", script_arg[1]) else "cuaderno/solucion.R"
root <- normalizePath(file.path(dirname(script_path), "../../.."), mustWork = TRUE)
source_csv <- file.path(root, "cases", "evolucion_gtfs", "resultados", "oferta_total.csv")

datos <- read.csv(source_csv, check.names = FALSE, fileEncoding = "UTF-8")
resultado <- datos[order(datos$publicacion), c("publicacion", "salidas")]
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
    ggplot2::aes(x = .data[["publicacion"]], y = .data[["salidas"]])
  ) +
    ggplot2::geom_line(ggplot2::aes(group = 1), linewidth = 1, colour = "#11253B") +
    ggplot2::geom_point(size = 2.5, colour = "#55D6BE") +
    ggplot2::labs(
      title = "La oferta programada cae en la publicación más reciente",
      x = "Publicación GTFS", y = "Salidas laborales (recuento)",
      caption = "Fuente: Resultados reproducibles del caso P14/P15 · Período: 2024–2026"
    ) +
    ggplot2::theme_minimal(base_size = 11)
  ggplot2::ggsave(destino, grafico, width = 9, height = 5, dpi = 150)
  cat(destino, "\n")
}

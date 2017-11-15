library("rjson")
library("knitr")
library("rmarkdown")

args = commandArgs(trailingOnly=TRUE)

code_filename <- args[1]
params_filename <- args[2]
output_directory <- args[3]
output_filename <- file.path(output_directory, "REPORT.md")

params_ <- fromJSON(file=params_filename)

setwd(output_directory)
rmarkdown::render(code_filename, output_file=output_filename, params=params_)
pandoc(output_filename)

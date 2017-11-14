library("rjson")
library("knitr")

args = commandArgs(trailingOnly=TRUE)

code_filename <- args[1]
params_filename <- args[2]
output_filename <- args[3]

params <- fromJSON(file=params_filename)

knit(code_filename, output=output_filename)
pandoc(output_filename)
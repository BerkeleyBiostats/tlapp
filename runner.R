sink(stdout(), type = "message")

library(longbowtools)

args = commandArgs(trailingOnly=TRUE)

code_filename <- args[1]
params_filename <- args[2]
output_directory <- args[3]

run_internal(code_filename, params_filename, output_directory=output_directory)
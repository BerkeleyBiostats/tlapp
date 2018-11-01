#!/bin/bash
# Job name:
#SBATCH --job-name=longbow-{{ id }}
#
# Account:
#SBATCH --account=co_biostat
#
# Partition:
#SBATCH --partition=savio2
#
# Wall clock limit:
#SBATCH --time=01:00:00
#

python x.py
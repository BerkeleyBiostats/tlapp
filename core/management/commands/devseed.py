import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core import models

sample_script_inputs = [{
  "name": "sample_size", 
  "type": "int", 
  "default": 10000
}]

# R -e "if (!require('')) install.packages('devtools', repos = 'http://cran.rstudio.com/')"

sample_provision = """
which R
R -e "if (!require('devtools')) install.packages('devtools', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('SuperLearner')) install.packages('SuperLearner', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('glmnet')) install.packages('glmnet', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('speedglm')) install.packages('speedglm', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('future')) install.packages('future', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('origami')) devtools::install_github('jeremyrcoyle/origami')"
R -e "if (!require('igraph')) devtools::install_version('igraph', version='1.0.1', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('uuid')) install.packages('uuid', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('memoise')) install.packages('memoise', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('sl3')) devtools::install_github('jeremyrcoyle/sl3')"
R -e "if (!require('testthat')) install.packages('testthat', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('jsonlite')) install.packages('jsonlite', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('tltools')) devtools::install_github('jeremyrcoyle/tltools')"
R -e "if (!require('rstackdeque')) install.packages('rstackdeque', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('rlang')) install.packages('rlang', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('visNetwork')) install.packages('visNetwork', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('delayed')) devtools::install_github('jeremyrcoyle/delayed@reduce-r-version')"
R -e "if (!require('randomForest')) install.packages('randomForest', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('assertthat')) install.packages('assertthat', repos = 'http://cran.rstudio.com/')"
"""

sample_script = """

---
title: "SuperLearner Benchmarks"
author: "Jeremy Coyle"
date: "10/5/2017"
output: html_document
params:
  sample_size: 10000
---

```{r setup, include=FALSE, results='hide'}
library(knitr)
knitr::opts_chunk$set(echo = TRUE)
library(sl3)
library(delayed)
library(SuperLearner)
library(future)
library(ggplot2)
library(data.table)
```
## Test Setup

### Session Information

```{r sessionInfo, echo=FALSE, results="asis"}
sessionInfo()
```

### Test System

```{r systemInfo, echo=FALSE, results="asis"}
uname <- system("uname -a", intern = TRUE)
os <- sub(" .*", "", uname)
if(os=="Darwin"){
  cpu_model <- system("sysctl -n machdep.cpu.brand_string", intern = TRUE)
  cpus_physical <- as.numeric(system("sysctl -n hw.physicalcpu", intern = TRUE))
  cpus_logical <- as.numeric(system("sysctl -n hw.logicalcpu", intern = TRUE))
  cpu_clock <- system("sysctl -n hw.cpufrequency_max", intern = TRUE)
  memory <- system("sysctl -n hw.memsize", intern = TRUE)
} else if(os=="Linux"){
  cpu_model <- system("lscpu | grep 'Model name'", intern = TRUE)
  cpu_model <- gsub("Model name:[[:blank:]]*","", cpu_model)
  cpus_logical <- system("lscpu | grep '^CPU(s)'", intern = TRUE)
  cpus_logical <- as.numeric(gsub("^.*:[[:blank:]]*","", cpus_logical))
  tpc <- system("lscpu | grep '^Thread(s) per core'", intern = TRUE)
  tpc <- as.numeric(gsub("^.*:[[:blank:]]*","", tpc))
  cpus_physical <- cpus_logical/tpc
  cpu_clock <- as.numeric(gsub("GHz","",gsub("^.*@","",cpu_model)))*10^9
  memory <- system("cat /proc/meminfo | grep '^MemTotal'", intern = TRUE)
  memory <- as.numeric(gsub("kB","",gsub("^.*:","",memory)))*2^10
} else {
  stop("unsupported OS")
}
```

* CPU model: `r cpu_model`
* Physical cores: `r as.numeric(cpus_physical)`
* Logical cores: `r as.numeric(cpus_logical)`
* Clock speed: `r as.numeric(cpu_clock)/10^9`GHz
* Memory: `r round(as.numeric(memory)/2^30, 1)`GB

### Test Data

```{r data_setup, echo=TRUE, results="hide"}

data(cpp)
cpp <- cpp[!is.na(cpp[, "haz"]), ]
covars <- c("apgar1", "apgar5", "parity", "gagebrth", "mage", "meducyrs", "sexn")
cpp[is.na(cpp)] <- 0
# cpp <- cpp[sample(nrow(cpp),10000,replace=T),]
cpp <- cpp[1:150, ]
outcome <- "haz"


task <- sl3_Task$new(cpp, covariates = covars, outcome = outcome)

```

### Test Descriptions

#### `sl3` with Legacy `SuperLearner` Wrappers
```{r sl3_legacy_setup, echo=TRUE}
sl_glmnet <- Lrnr_pkg_SuperLearner$new("SL.glmnet")
sl_random_forest <- Lrnr_pkg_SuperLearner$new("SL.randomForest")
sl_glm <- Lrnr_pkg_SuperLearner$new("SL.glm")
nnls_lrnr <- Lrnr_nnls$new()

sl3_legacy <- Lrnr_sl$new(list(sl_random_forest, sl_glmnet, sl_glm), nnls_lrnr)
```


#### `sl3` with Improved Wrappers
```{r sl3_improved_setup, echo=TRUE}
sl_glmnet <- Lrnr_pkg_SuperLearner$new("SL.glmnet")
random_forest <- Lrnr_randomForest$new()
glm_fast <- Lrnr_glm_fast$new()
nnls_lrnr <- Lrnr_nnls$new()

sl3_improved <- Lrnr_sl$new(list(random_forest, sl_glmnet, glm_fast), nnls_lrnr)
```

#### Legacy `SuperLearner`

```{r legacy_SuperLearner, echo=TRUE, message=FALSE}
time_SuperLearner_sequential <- system.time({
  SuperLearner(task$Y, as.data.frame(task$X), newX = NULL, family = gaussian(), 
               SL.library=c("SL.glmnet","SL.randomForest","SL.glm"),
               method = "method.NNLS", id = NULL, verbose = FALSE,
               control = list(), cvControl = list(), obsWeights = NULL, 
               env = parent.frame())
})

options(mc.cores=cpus_physical)
time_SuperLearner_multicore <- system.time({
  mcSuperLearner(task$Y, as.data.frame(task$X), newX = NULL, family = gaussian(), 
               SL.library=c("SL.glmnet","SL.randomForest","SL.glm"),
               method = "method.NNLS", id = NULL, verbose = FALSE,
               control = list(), cvControl = list(), obsWeights = NULL, 
               env = parent.frame())
})
```
## Results


```{r eval, echo=FALSE, results="hide", message=FALSE}
plan(sequential)
test <- delayed_learner_train(sl3_legacy, task)
time_sl3_legacy_sequential <- system.time({
  sched <- Scheduler$new(test, SequentialJob)
  cv_fit <- sched$compute()
})

test <- delayed_learner_train(sl3_improved, task)
time_sl3_improved_sequential <- system.time({
  sched <- Scheduler$new(test, SequentialJob)
  cv_fit <- sched$compute()
})

plan(multicore, workers=cpus_logical)
test <- delayed_learner_train(sl3_legacy, task)
time_sl3_legacy_multicore_ht <- system.time({
  sched <- Scheduler$new(test, FutureJob, nworkers=cpus_logical, verbose = FALSE)
  cv_fit <- sched$compute()
})

test <- delayed_learner_train(sl3_improved, task)
time_sl3_improved_multicore_ht <- system.time({
  sched <- Scheduler$new(test, FutureJob, nworkers=cpus_logical, verbose = FALSE)
  cv_fit <- sched$compute()
})

test <- delayed_learner_train(sl3_legacy, task)
time_sl3_legacy_multicore <- system.time({
  sched <- Scheduler$new(test, FutureJob, nworkers=cpus_physical, verbose = FALSE)
  cv_fit <- sched$compute()
})

test <- delayed_learner_train(sl3_improved, task)
time_sl3_improved_multicore <- system.time({
  sched <- Scheduler$new(test, FutureJob, nworkers=cpus_physical, verbose = FALSE)
  cv_fit <- sched$compute()
})

plan(multisession, workers=cpus_physical)
test <- delayed_learner_train(sl3_legacy, task)
time_sl3_legacy_multisession <- system.time({
  sched <- Scheduler$new(test, FutureJob, nworkers=cpus_physical, verbose = FALSE)
  cv_fit <- sched$compute()
})

test <- delayed_learner_train(sl3_improved, task)
time_sl3_improved_multisession <- system.time({
  sched <- Scheduler$new(test, FutureJob, nworkers=cpus_physical, verbose = FALSE)
  cv_fit <- sched$compute()
})


```

```{r results, echo=FALSE}
results <- rbind(time_sl3_legacy_sequential, time_sl3_legacy_multicore, 
                 time_sl3_legacy_multicore_ht, time_sl3_legacy_multisession,
                 time_sl3_improved_sequential, time_sl3_improved_multicore, 
                 time_sl3_improved_multicore_ht, time_sl3_improved_multisession,
                 time_SuperLearner_sequential, time_SuperLearner_multicore
                )
test <- rownames(results)
results <- as.data.table(results)

invisible(results[, test := gsub("time_", "", test)])
results <- results[order(results$elapsed)]
invisible(results[, test := factor(test,levels=test)])
ggplot(results, aes(y=test, x=elapsed))+geom_point()+
  xlab("Time (s)")+ylab("Test")+theme_bw()

```


"""

class Command(BaseCommand):
    help = "Initialize the app for development"

    def handle(self, *args, **options):
        user = User.objects.create_superuser(
            'admin', 'admin@example.com', 'admin')
        user.save()

        inputs = sample_script_inputs

        code = sample_script

        mt = models.AnalysisTemplate(
            name='sl3_sample.R',
            fields=inputs,
            code=code,
            provision=sample_provision,
            needs_dataset=False,
        )   
        mt.save()

        inputs = [{
            "name": "Spacing",
            "type": "enum",
            "choices": [
                "tight",
                "loose",
            ],
        },]

        code = """
            print('foo')
        """

        mt2 = models.AnalysisTemplate(
            name='Another sample.R',
            fields=inputs,
            code=code,
            provision=sample_provision,
        )
        mt2.save()

        job = models.ModelRun(
            model_template=mt,
            status=models.ModelRun.status_choices['submitted'],
        )
        job.save()

        job = models.ModelRun(
            model_template=mt2,
            status=models.ModelRun.status_choices['submitted'],
        )
        job.save()

        dataset = models.Dataset(
            title="Subset of growth data from the collaborative perinatal project (CPP)",
            url="https://raw.githubusercontent.com/BerkeleyBiostats/tlapp/30821fe37d9fdb2cb645ad2c42f63f1c1644d7c4/cpp.csv",
            variables={
                "names": [
                    "haz",
                    "parity",
                    "apgar1", 
                    "apgar5", 
                    "gagebrth", 
                    "mage", 
                    "meducyrs", 
                    "sexn"
                ]
            }            
        )
        dataset.save()

        dataset = models.Dataset(
            title="Another sample",
            url="https://raw.githubusercontent.com/BerkeleyBiostats/tlapp/30821fe37d9fdb2cb645ad2c42f63f1c1644d7c4/cpp.csv",
            variables={
                "names": [
                    "foo",
                    "bar",
                ]
            }            
        )
        dataset.save()

        dataset = models.Dataset(
            title="ki1000306-ZincSGA",
            url="https://git.ghap.io/stash/scm/hbgd/ki1000306.git",
            variables={
                "names": "STUDYID,SUBJID,SUBJIDO,SITEID,SEXN,SEX,ARMCD,ARM,GAGEBRTH,PREGOUTN,PREGOUT,DEAD,AGEDTH,CAUSEDTH,FEEDINGN,FEEDING,DURBRST,BRTHYR,BRTHWEEK,BIRTHWT,BIRTHLEN,BIRTHHC,DELIVERY,CRY,IMMBCG,IMMOPV,MULTBRTH,GAGEHX,STLBRTH,LVBRTH,PARITY,DLVLOCN,DLVLOC,CTRYCD,COUNTRY,NPERSON,NCHLDLT5,RADIO,TV,SEWING,FAN,BICYCLE,MCYCLE,TUBEWELL,COOLER,TAXI,INCDAD,OWNHOME,INCMOM,HOMETYPE,SMOKBRTH,COLOFEED,MOMLTRCY,FTRLTRCY,FOODADD,AGEDAYS,WTKG,LENCM,BMI,HCIRCM,WAZ,HAZ,WHZ,BAZ,HCAZ,BSA,RESP__READING_1_,TEMP__READING_1_,RESP__READING_2_,TEMP__PNEUMONIA_READING_1_,RESP__PNEUMONIA_READING_1_,RESP__ILLNESS_READING_1_,RESP__ILLNESS_READING_2_".split(",")
            },
            repository_path="ZINC-SGA/adam/full_ki1000306_ZINC_SGA.csv",
        )
        dataset.save()


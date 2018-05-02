import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core import models

sample_script_inputs = [{
  "name": "sample_size", 
  "type": "int", 
  "default": 2000
}]

# R -e "if (!require('')) install.packages('devtools', repos = 'http://cran.rstudio.com/')"

sample_provision = """
which R
mkdir -p "/data/R/x86_64-redhat-linux-gnu-library/3.2/"
mkdir -p "/data/R/x86_64-redhat-linux-gnu-library/3.4/"

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
R -e "if (!require('stringi')) install.packages('stringi', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('longbowtools')) devtools::install_github('tlverse/longbowtools')"
R -e "if (!require('rstackdeque')) install.packages('rstackdeque', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('rlang')) install.packages('rlang', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('visNetwork')) install.packages('visNetwork', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('delayed')) devtools::install_github('jeremyrcoyle/delayed@reduce-r-version')"
R -e "if (!require('randomForest')) install.packages('randomForest', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('assertthat')) install.packages('assertthat', repos = 'http://cran.rstudio.com/')"
"""

sample_script = """

---
title: "`sl3` and `delayed` benchmarks: A comparison with `SuperLearner`"
output: 
  html_document:
    standalone: true
    self_contained: true
required_packages:  ['knitr', 'igraph@1.0.1', 'github://jeremyrcoyle/sl3@tmle-demo-fixes', 'github://jeremyrcoyle/tmle3@conditional-densities', 'github://jeremyrcoyle/skimr@vector_types', 'Rsolnp', 'glmnet', 'xgboost', 'randomForest', 'future', 'ck37r',
'github://jeremyrcoyle/delayed@reduce-r-version']
params:
  roles:
    value:
      - none
  data: 
    value: 
      type: 'web'
      uri: 'https://raw.githubusercontent.com/BerkeleyBiostats/tlapp/30821fe37d9fdb2cb645ad2c42f63f1c1644d7c4/cpp.csv'
  nodes:
    value:
      none: []
  script_params:
    value:
      sample_size:
        input: 'numeric'
        value: 2000
  output_directory:
    value: ''

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
library(stringr)
library(scales)
library(tltools)
data <- get_tl_data()
nodes <- get_tl_nodes()
library(future)
tl_params <- get_tl_params()

```

## Introduction

This document consists of some simple benchmarks for various choices of SuperLearner implementation, wrapper functions, and parallelization schemes. The purpose of this document is two-fold: 

1. Compare the computational performance of these methods
2. Illustrate the use of these different methods

## Test Setup


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
n=as.numeric(tl_params$sample_size)
data(cpp_imputed)
cpp_big <- cpp_imputed[sample(nrow(cpp_imputed),n,replace=T),]
covars <- c("apgar1", "apgar5", "parity", "gagebrth", "mage", "meducyrs", "sexn")
outcome <- "haz"


task <- sl3_Task$new(cpp_big, covariates = covars, outcome = outcome, outcome_type="continuous")

```

* Number of observations: `r nrow(task$X)`
* Number of covariates: `r ncol(task$X)`

### Test Descriptions


#### Legacy `SuperLearner`

The legacy [SuperLearner](https://github.com/ecpolley/SuperLearner/) package serves as a suitable baseline. We can fit it sequentially (no parallelization):

```{r legacy_SuperLearner_sequential, echo=TRUE, message=FALSE}
time_SuperLearner_sequential <- system.time({
  SuperLearner(task$Y, as.data.frame(task$X), newX = NULL, family = gaussian(), 
               SL.library=c("SL.glmnet","SL.randomForest","SL.glm"),
               method = "method.NNLS", id = NULL, verbose = FALSE,
               control = list(), cvControl = list(), obsWeights = NULL, 
               env = parent.frame())
})
```

We can also fit it using multicore parallelization, using the `mcSuperLearner` function.
```{r legacy_SuperLearner_multicore, echo=TRUE, message=FALSE}
options(mc.cores=cpus_physical)
time_SuperLearner_multicore <- system.time({
  mcSuperLearner(task$Y, as.data.frame(task$X), newX = NULL, family = gaussian(), 
               SL.library=c("SL.glmnet","SL.randomForest","SL.glm"),
               method = "method.NNLS", id = NULL, verbose = FALSE,
               control = list(), cvControl = list(), obsWeights = NULL, 
               env = parent.frame())
})
```

The `SuperLearner` package supports a number of other parallelization schemes, although these weren't tested here.

#### `sl3` with Legacy `SuperLearner` Wrappers

To maximize comparability with the legacy implementation, we can use `sl3` with the `SuperLearner` wrappers, so that the actual computation used to train the learners is identical:
```{r sl3_legacy_setup, echo=TRUE}
sl_glmnet <- Lrnr_pkg_SuperLearner$new("SL.glmnet")
sl_random_forest <- Lrnr_pkg_SuperLearner$new("SL.randomForest")
sl_glm <- Lrnr_pkg_SuperLearner$new("SL.glm")
nnls_lrnr <- Lrnr_nnls$new()

sl3_legacy <- Lrnr_sl$new(list(sl_random_forest, sl_glmnet, sl_glm), nnls_lrnr)
```


#### `sl3` with Native Learners

We can also use native `sl3` learners, which have been rewritten to be performant on large sample sizes:

```{r sl3_native_setup, echo=TRUE}
lrnr_glmnet <- Lrnr_glmnet$new()
random_forest <- Lrnr_randomForest$new()
glm_fast <- Lrnr_glm_fast$new()
nnls_lrnr <- Lrnr_nnls$new()

sl3_native <- Lrnr_sl$new(list(random_forest, lrnr_glmnet, glm_fast), nnls_lrnr)
```

#### `sl3` Parallelization Options

`sl3` uses the [delayed](https://github.com/jeremyrcoyle/delayed) package to parallelize training tasks. Delayed, in turn, uses the [future](https://github.com/HenrikBengtsson/future) package to support a range of parallel back-ends. We test several of these, for both the legacy wrappers and native learners.

First, sequential evaluation (no parallelization):
```{r eval_sequential, echo=TRUE, results="hide", message=FALSE}
plan(sequential)
test <- delayed_learner_train(sl3_legacy, task)
time_sl3_legacy_sequential <- system.time({
  sched <- Scheduler$new(test, SequentialJob)
  cv_fit <- sched$compute()
})

test <- delayed_learner_train(sl3_native, task)
time_sl3_native_sequential <- system.time({
  sched <- Scheduler$new(test, SequentialJob)
  cv_fit <- sched$compute()
})
```

Next, multicore parallelization:
```{r eval_multicore, echo=TRUE, results="hide", message=FALSE}
plan(multicore, workers=cpus_physical)
test <- delayed_learner_train(sl3_legacy, task)
time_sl3_legacy_multicore <- system.time({
  sched <- Scheduler$new(test, FutureJob, nworkers=cpus_physical, verbose = FALSE)
  cv_fit <- sched$compute()
})

test <- delayed_learner_train(sl3_native, task)
time_sl3_native_multicore <- system.time({
  sched <- Scheduler$new(test, FutureJob, nworkers=cpus_physical, verbose = FALSE)
  cv_fit <- sched$compute()
})
```

We also test multicore parallelization with [hyper-threading](https://en.wikipedia.org/wiki/Hyper-threading) -- we use a number of workers equal to the number of logical, not physical, cores:

```{r eval_multicore_ht, echo=TRUE, results="hide", message=FALSE}
plan(multicore, workers=cpus_logical)
test <- delayed_learner_train(sl3_legacy, task)
time_sl3_legacy_multicore_ht <- system.time({
  sched <- Scheduler$new(test, FutureJob, nworkers=cpus_logical, verbose = FALSE)
  cv_fit <- sched$compute()
})

test <- delayed_learner_train(sl3_native, task)
time_sl3_native_multicore_ht <- system.time({
  sched <- Scheduler$new(test, FutureJob, nworkers=cpus_logical, verbose = FALSE)
  cv_fit <- sched$compute()
})
```

Finally, we test parallelization using multisession:
```{r eval_multisession, echo=TRUE, results="hide", message=FALSE}
plan(multisession, workers=cpus_physical)
test <- delayed_learner_train(sl3_legacy, task)
time_sl3_legacy_multisession <- system.time({
  sched <- Scheduler$new(test, FutureJob, nworkers=cpus_physical, verbose = FALSE)
  cv_fit <- sched$compute()
})

test <- delayed_learner_train(sl3_native, task)
time_sl3_native_multisession <- system.time({
  sched <- Scheduler$new(test, FutureJob, nworkers=cpus_physical, verbose = FALSE)
  cv_fit <- sched$compute()
})


```

## Results
```{r results, echo=FALSE}

results <- rbind(time_sl3_legacy_sequential, time_sl3_legacy_multicore, 
                 time_sl3_legacy_multicore_ht, time_sl3_legacy_multisession,
                 time_sl3_native_sequential, time_sl3_native_multicore, 
                 time_sl3_native_multicore_ht, time_sl3_native_multisession,
                 time_SuperLearner_sequential, time_SuperLearner_multicore
                )
test <- rownames(results)

results <- as.data.table(results)

invisible(results[, test := gsub("time_", "", test)])
invisible(results[, native:=str_detect(test, "native")])
invisible(results[, parallel:=!str_detect(test, "sequential")])
results <- results[order(results$elapsed)]
invisible(results[, test := factor(test,levels=test)])
breaks=2^(-20:20)
ggplot(results, aes(y=test, x=elapsed, color=factor(native), shape=factor(parallel)))+geom_point(size=3)+
  xlab("Time (seconds) -- log scale")+ylab("Test")+theme_bw()+
  scale_shape_discrete("Parallel Computation")+scale_color_discrete("Native Learners")+
  scale_x_continuous(trans = log2_trans(), breaks=breaks)+ annotation_logticks(base=2, sides="b")  
save(results, file="benchmark_results.rdata")
```

We can see that using the native learners results in about a 4x speedup relative to the legacy wrappers. This can be at least partially explained by the fact that legacy `SL.randomForest` wrapper uses `randomForest.formula` for continuous data, which resorts to using the `model.matrix` function, known to be slow on large datasets. Improvements to the legacy wrappers would probably reduce or eliminate this difference. 

We can also see that multicore parallelization for the legacy `SuperLearner` function results in another 4x speedup on this system. Relative to that, the `sl3_legacy_multicore` test results in almost an additional 2x speedup. This can be explained by the use of delayed parallelization. While `mcSuperLearner` parallelizes simply across the $V$ cross-validation folds, `delayed` allows `sl3` to parallelize across all training tasks that comprise the SuperLearner, which is a total of $(V+1)*n_{learners}$ training tasks, $n_{learners}$ is the number of learners in the library (here 4), and $(V+1)$ is one more than the number of cross-validation folds, accounting for the re-fit to the full data typically implemented in the `SuperLearner` algorithm. We don't see a substantial difference between the three parallelization schems for sl3. 

These effects appear multiplicative, resulting in the fastest implementation, `sl3_improved_multicore_ht` (`sl3` with native learners and hyper-threaded multicore parallelization), being about 32x faster than the slowest, `SuperLearner_sequential` (Legacy `SuperLearner` without parallelization). This is a dramatic improvement in the time required to run this SuperLearner.

## Session Information

```{r sessionInfo, echo=FALSE, results="asis"}
sessionInfo()
```


"""

class Command(BaseCommand):
    help = "Initialize the app for development"

    def handle(self, *args, **options):
        user = User.objects.create_superuser(
            'admin', 'admin@example.com', 'admin')
        user.save()

        token = models.Token(
          user=user,
          token="admintoken"
        )
        token.save()

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
---
title: "Another Sample"
author: "Jeremy Coyle"
date: "10/5/2017"
output: 
  html_document:
    self_contained: false
params:
  roles:
    value:
      - W
      - A
      - Y
      - exclude
      - id
---

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


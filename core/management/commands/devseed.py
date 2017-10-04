import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core import models

sample_script_inputs = [{
    "name": "Learners",
    "type": "enum",
    "choices": [
        "glmfast",
        "SL.glmnet"
    ]
}]

# R -e "if (!require('')) install.packages('devtools', repos = 'http://cran.rstudio.com/')"

sample_provision = """
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
"""

sample_script = """


---
title: "Sample TL App script"
author: "Jeremy Coyle"
date: "9/1/2017"
output: html_document
---

```{r setup, include=FALSE}
library(knitr)
knitr::opts_chunk$set(echo = TRUE)
```

```{r tltools_setup, include=FALSE}
library(tltools)

if(!exists("tlparams")){
  sample_input_file <- fpath <- system.file("extdata", "sample_input.json", package="tltools")
  tlparams <- ScriptParams$new(sample_input_file)
}
```

## Analysis Parameters
```{r comment='', echo=FALSE}
cat(readLines(tlparams$input_file, warn=FALSE), sep = '\n')
```

## Analysis 

```{r analysis, echo=TRUE, cache=T}
# Note for Marc Pare:
# in some sense we might want to separate the part of the script that runs an analysis 
# (computantionally expensive, unlikely to change) from the part of the script that reports the results 
# (runs fast, might change a lot)
# the former would likely be an R script, the latter an Rmd document
# this chunk is the analysis part, the rest is the report part
# just something to think about
library(sl3)
library(SuperLearner)
#define task from tlparams specification
cpp <- tlparams$data
cpp[is.na(cpp)] <- 0
covars <- c(unlist(tlparams$data_nodes$W), tlparams$data_nodes$A)
outcome <- tlparams$data_nodes$Y
task <- sl3_Task$new(cpp, covariates = covars, outcome = outcome)


# Hardcode this for now.
# Later: build the full learner configuration from the tlparams$params value
tlparams$params = list(
    learners = list(
        glm_learner = list(learner = "Lrnr_glm_fast"),
        sl_glmnet_learner = list(
            learner = "Lrnr_pkg_SuperLearner",
            params = list(
                SL_wrapper = "SL.glmnet"
            )
        )
    ),
    metalearner = list(learner="Lrnr_nnls")
)

#define learners based on tlparams
learner_from_params <- function(learner){
  Lrnr_factory <- get(learner$learner)
  params <- learner$params
  
  if(is.null(params)){
    params <- list()
  }
  learner <- do.call(Lrnr_factory$new, params)
  
  return(learner)
}

learners <- lapply(tlparams$params$learners, learner_from_params)
metalearner <- learner_from_params(tlparams$params$metalearner)
sl_learner <- Lrnr_sl$new(learners = learners, metalearner = metalearner)
sl_fit <- sl_learner$train(task)


```

## Results

Just a sample of some output types


### Coef table
```{r coefs, echo=FALSE}
ml_fit <- sl_fit$fit_object$full_fit$fit_object$learner_fits[[2]]$fit_object
coeftab <- as.matrix(coef(ml_fit))
learner_names <- sapply(learners,`[[`,'name')
rownames(coeftab) <- learner_names
colnames(coeftab) <- "Coef"
kable(coeftab)
```

### Coef plot
```{r coef_plot, echo=FALSE, fig.height=2, fig.width=4}
library(ggplot2)
coefdf <- as.data.frame(coeftab)
coefdf$Learner <- learner_names
ggplot(coefdf,aes(y=Learner, x=Coef))+geom_point()+theme_bw()
```

### Coef text
```{r coef_text, echo=FALSE}
print(coeftab)
```

### We can also write output to a file

Nothing to see here

```{r coef_file, echo=FALSE}
csv_file <- file.path(tlparams$output_dir, "coef.csv")
write.csv(coeftab,csv_file)

rdata_file<- file.path(tlparams$output_dir, "coef.rdata")
save(coeftab,file=rdata_file)
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


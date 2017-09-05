if grep -h ^deb /etc/apt/sources.list | grep -q 'rstudio'; then
  echo "Skipping adding R repository"
else
  sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9
  sudo add-apt-repository 'deb [arch=amd64,i386] https://cran.rstudio.com/bin/linux/ubuntu xenial/'
  sudo apt-get update
fi

sudo apt-get install -y \
  libcurl4-openssl-dev \
  libglu1-mesa-dev \
  libssl-dev \
  libx11-dev \
  pandoc \
  postgresql \
  postgresql-contrib \
  python-dev \
  python-pip \
  r-base \
  xorg


pip install --upgrade pip
pip install virtualenv

# TODO: write function to reduce boilerplate
R -e "if (!require('devtools')) install.packages('devtools', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('SuperLearner')) install.packages('SuperLearner', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('glmnet')) install.packages('glmnet', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('speedglm')) install.packages('speedglm', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('origami')) devtools::install_github('jeremyrcoyle/origami')"
R -e "if (!require('igraph')) devtools::install_version('igraph', version='1.0.1', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('sl3')) devtools::install_github('jeremyrcoyle/sl3')"
R -e "if (!require('testthat')) install.packages('testthat', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('knitr')) install.packages('knitr', repos = 'http://cran.rstudio.com/')"
R -e "if (!require('tltools')) devtools::install_github('jeremyrcoyle/tltools')"
# List of R packages required by haemosphere
# Run this script by source() command from R after fresh installation of haemosphere or R.
if (!require("BiocManager", quietly = TRUE))
  install.packages("BiocManager", repos = "https://cloud.r-project.org")
BiocManager::install("limma",version = "3.10")
# dependency of edgeR old version need download install
install.packages("https://cran.r-project.org/src/contrib/Archive/locfit/locfit_1.5-9.4.tar.gz", repos=NULL, type="source")
BiocManager::install("edgeR",version = "3.10")
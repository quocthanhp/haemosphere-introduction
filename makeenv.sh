#!/bin/bash

eval "$(conda shell.bash hook)"
sudo mkdir /haemosphere-env
sudo chown ubuntu:ubuntu /haemosphere-env/
conda config --append channels bioconda
conda env update --solver libmamba --file /haemosphere/environment.yml -p /haemosphere-env
conda activate /haemosphere-env
pip install -r /haemosphere/requirements_3.x.txt
pip uninstall intel-numpy --y
MAKEFLAGS="-j"
Rscript /haemosphere/r_packages.r
pip install -e /haemosphere 
cp /haemosphere/geneset.py /haemosphere-env/lib/python3.6/site-packages/genedataset/geneset.py 
cp /haemosphere/dataset.py /haemosphere-env/lib/python3.6/site-packages/genedataset/dataset.py 

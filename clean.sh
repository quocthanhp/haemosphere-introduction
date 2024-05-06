#!/bin/bash

eval "$(conda shell.bash hook)"
conda deactivate
sudo rm -rf /haemosphere-env
conda clean --all --y
pip cache purge

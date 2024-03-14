# haemosphere-introduction


# Deploy py3 on Nectar cloud

Clean job

depoly 22.04 jammy

login with ubuntu

sudo apt-get update && apt-get upgrade -y
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
sudo bash Miniconda3-latest-Linux-x86_64.sh -b -p /miniconda3
PATH="/haemosphere-env/bin:/miniconda3/bin:${PATH}"
conda init
re connect ssh
cd /
sudo git clone https://Young_Ryu@bitbucket.org/jarny/haemosphere.git -b py3-haemoshpere-team2to3
for to this you need app password on bitbucket

conda config --append channels bioconda
sudo mkdir /haemosphere-env
sudo chown ubuntu:ubuntu /haemosphere-env/
conda env update --solver libmamba --file /haemosphere/environment.yml -p /haemosphere-env
conda activate /haemosphere-env
pip install -r /haemosphere/requirements_3.x.txt
MAKEFLAGS="-j" Rscript /haemosphere/r_packages.r
pip install -e /haemosphere


  File "/haemosphere-env/lib/python3.6/site-packages/genedataset/geneset.py", line 360
    print 'total data rows: %s (unique rows:%s)' % (df.shape[0], len(set(df.index)))

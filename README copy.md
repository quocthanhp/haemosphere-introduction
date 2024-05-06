haemosphere README (Documentation for haemosphere development and maintenance)
....
Last updated 2018-08-07 by Jarny

This branch is to store files related to investigating why the python3 port of haemosphere crashes with multiple sessions.

Environment setup
-----------------

Clone the environment and switch to this branch: 

```
git clone git clone git@bitbucket.org:jarny/haemosphere.git -b py3-haemosphere-debug
```

To create the environment with most of the prerequisites:

```
conda env create -p ../haemosphere-condaenv -f environment.yml -y
conda activate ../haemosphere-condaenv
pip install .
```

Note that the `environment.yml` uses the a modified version of the `genedataset` package, as none of the available versions on pip work with Python 3.6.
The environment also attempts to use package versions similar to the Python 2 version of haemosphere. 


Reproducing Crashes
-------------------

As-is, haemosphere should crash pretty reliably when using the `development.ini` config file:

```bash
pserve development.ini
```

Start performing differential queries. This should be done in seperate browsers as `beaker` creates sessions for each browser, not each browser tab.
For example, I had a Firefox and Chrome browser open on my PC, and a Firefox tab open on a Milton Open OnDemand desktop.
After running queries concurrently for awhile, a crash should eventually  occur. The browser windows will say something like "An unexpected error occurred" and you'll get some errors from Python and specific errors from rpy2.

Change the number of threads that Waitress will use to 1 by editing `development.ini`

```
...
[server:main]
use: egg:waitress#main
host: 0.0.0.0
port: 6544
threads: 1
...
```

Run the server

```
pserve development.ini
```

Perform the queries and the crashes shouldn't happen anymore. The server performance will also be much slower.

Breadcrumbs
-----------

Multiple threads cannot access R concurrently. The program needs to be modified to run seperate R processes for each user's query e.g., as demonstrated in [this stackoverflow question](https://stackoverflow.com/questions/63785478/multithreaded-flask-application-causes-stack-error-in-rpy2-r-process). 

However, instead of using a multiple process frameowrk, it might be more suitable to use a database server (e.g., MySQL) on the backend to process users' queries (together with SQLALchemy). This is because the pyramids+waitress framewwork is intended to perform IO workloads in parallel. It isn't very suitable for performing the reading AND processing. By using an SQL server, the processing is off-loaded to the SQL server (which can process in parallel). The h5 datasets could be pre-processed with limma and edgeR and the processed data inserted into the data. When the haemosphere web server is running, it would query the SQL database server which would return the organised processed data.

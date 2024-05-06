"""
Script to start pyramid server. Usage:
> python start_pyramid_server.py development.ini

Do not use absolute path for config file here, as this will be prepended using the location of this script.
"""
import os, sys, subprocess, logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M')

PID_FNAME = "pyramid.pid"
currentDir = os.path.dirname(os.path.realpath(__file__))	# directory where this script if found


def getPyramidPid():
	"""
	Gets the latest PID written to `pyramid.pid`, assuming that that
	file is in the same directory as this script.
	"""
	pidfpath = "%s/%s" % (currentDir, PID_FNAME)
	try:
		pid = open(pidfpath).read()
		return pid
	except IOError:
		return None


def serverIsRunning():
	"""
	Check if this app is already being served by pserve.
	"""
	pid = getPyramidPid()
	if pid is None:
		# pserve not running
		return False
	ps = subprocess.Popen(('ps', pid), stdout=subprocess.PIPE)
	output = ps.communicate()[0]
	# if the process is still running, the output will have two lines
	return len(output.strip().split('\n')) > 1


def startPyramidServer(configfile):
	"""Check to see if pyramid server is running and start it if not.
	Assumes that this script is found inside the main pyramid project directory at the same level as the .ini files.
	Note that log file will go to data/access.log.
	"""
	logging.info("Starting pyramid server. (%s)" % configfile)
	subprocess.call(["pserve","--daemon","--log-file=%s/data/access.log" % currentDir, "%s/%s" % (currentDir,configfile)])


if __name__=="__main__":
	if not serverIsRunning():
		startPyramidServer(sys.argv[1])
	else:
		logging.info("Pyramid server already running (PID: %s)" % getPyramidPid())

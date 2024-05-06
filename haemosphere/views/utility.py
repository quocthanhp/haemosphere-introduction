"""
This module contains various functions which may be used by many other functions in the system.
"""
from __future__ import absolute_import
from __future__ import unicode_literals
from haemosphere.models import sharewould
import smtplib
def currentEnv(request):
	"""
	Return the current environment. {dev,private,public}
	"""
	return request.registry.settings['haemosphere.env']

def hosturl(request):
	"""Return host url (without http part)
	"""
	#return request.host	# request.host_url also works
	return request.registry.settings['haemosphere.hosturl']

def forest(request):
	"""
	Return the ShareWould instance attached to this request. It needs the path to the datasets directory,
	which is provided here via config file eg. development.ini. Access the values in the config file
	using request.registry.settings.
	"""
	return sharewould.ShareWould(request.registry.settings['haemosphere.model.datasets.root'])

def params(request, key, default=None):
	"""
	Return parameter value attached to the key of request.params. Just a shortcut to avoid writing the following code
	for methods accepting various ways of parameter submission. 
	Eg: params(request, 'filename', 'myfile.txt') may be equivalent to request.params.get('filename', 'myfile.txt')
	"""	
	value = request.params.get(key)
	if not value: value = request.POST.get(value)
	try:
		if not value and hasattr(request, 'json_body'): value = request.json_body.get(key)
	except Exception as e:
		print('error:', e)

	return value if value else default

def confirmationToken(obj, type):
	"""Return a itsdangerous encrypted token to be used for email confirmations.
	Only 2 current use cases:
		>> confirmationToken('smith', 'password') # to create a token for password reset for username 'smith'
		>> confirmationToken({'username':'smith', 'email':'smith@gmail.com', ...}, 'register') # to create a token for new user registration
	"""
	from itsdangerous import URLSafeTimedSerializer
	serializer = URLSafeTimedSerializer('zq9vaxc2QEOjQTeXOPwKNO8NBFo')
	return serializer.dumps(obj, salt=type)

def objectFromToken(token, type, expiration=3600):
	"""Return the serialized object from token. Will return false if token doesn't match serializer or salt (ie. it's been tampered with).
	Ensure that same string as confirmationToken() is used for serialization and salt.
	"""
	from itsdangerous import URLSafeTimedSerializer
	serializer = URLSafeTimedSerializer('zq9vaxc2QEOjQTeXOPwKNO8NBFo')
	try:
		return serializer.loads(token, salt=type, max_age=expiration)
	except:
		return False
		
		
# Wrapper to send email
def sendEmail(request, subject, recipients, body):
	# The following can't be used if I want to use custom password field
	from pyramid_mailer import get_mailer
	from pyramid_mailer.mailer import Mailer, DummyMailer
	from pyramid_mailer.message import Message
	from email.mime.text import MIMEText

	rs = request.registry.settings
	mailer = get_mailer(request)
	'''
	if type(mailer) is not DummyMailer:
		# we are sending email for real
		# Not using ssl mailserver anymore (2018-06), so leave out these fields
		#import base64
		#mailer = Mailer(host=rs['mail.host'], port=rs['mail.port'], username=rs['mail.username'], password=base64.b64decode(rs['mail.password']), ssl=rs['mail.ssl'])
		mailer = Mailer(host=rs['mail.host'], port=rs['mail.port'])

	message = Message(subject=subject,  sender=rs['mail.sender'], recipients=recipients, body=body)

	mailer.send_immediately(message)
	'''
	print(rs['mail.sender'])
	gmail_user = 'haemosphere@gmail.com'
	gmail_password = 'icrtp123'
	sent_from = gmail_user
	to = recipients

	email_text = """\
	From: %s
	To: %s
	Subject: %s

	%s
	""" % (sent_from, to, subject, body)

	message = """From: %s\nTo: %s\nSubject: %s\n\n%s
	""" % (sent_from, to, subject, body)

	try:
		server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
		server.ehlo()
		server.login(gmail_user, gmail_password)
		server.sendmail(sent_from, to, message)
		server.close()

		print("Email sent!")
	except Exception as e: print(e)


def addGenesetToSession(request, gs):
	"""
	Add a Geneset instance gs to current list of genesets in the session.
	"""
	if gs.size()==0: return	# no point in adding an empty geneset
	if 'genesets' not in request.session: request.session['genesets'] = []
	
	# also check to see if previous geneset is identical in name and number:
	currentGenesets = request.session['genesets']
	if len(currentGenesets)>0 and currentGenesets[0].name==gs.name and currentGenesets[0].size()==gs.size(): return
	
	request.session['genesets'].insert(0,gs)
	if len(request.session['genesets'])>10: request.session['genesets'].pop()			
		
def versionInfo(request):
	"""
	Return version information as a list of dictionaries [{'version':'1.0', 'notes':['First note item, ...]}, ...]
	"""
	import re
	versionInfo = []
	currentItem = {}
	try:
		for line in open('CHANGES.txt').read().split('\n'):
			if re.match('\d.\d',line):
				if currentItem:  # add to info
					versionInfo.append(currentItem)
				# reset currentItem
				currentItem = {'version':line, 'notes':[]}
			elif line.startswith('- '):
				if not line.startswith('- [') or currentEnv(request)=='dev' or line.startswith('- [%s]' % currentEnv(request)):
					currentItem['notes'].append(line.replace('- ','').replace('[%s]' % currentEnv(request), ''))
		if currentItem:  # pick up the last item
			versionInfo.append(currentItem)
		return versionInfo
	except:
		return [{'version':'', 'notes':['There was an error fetching version notes']}]
	
def moveItemInList(l, item, new_index):
    """ Remove item in list and place it at selected index
    """        
    l.pop(l.index(item))
    l.insert(new_index, item)
		
def replaceItemInList(l, old_item, new_item):
    """ Remove old_item from a list then insert new_item at that index
    """
    for index, item in enumerate(l):
        if item == old_item:
            l.pop(index)
            l.insert(index, new_item)	
			
def replaceKeyInDict(d, old_key, new_key):
    """ Replace a key in a dictionary with a new key without altering the date associated
        with the key
    """
    d[new_key] = d[old_key]
    del d[old_key] 					

		
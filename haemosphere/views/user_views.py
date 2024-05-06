from __future__ import absolute_import
from pyramid.view import view_config, forbidden_view_config
from pyramid.security import remember, forget
from pyramid.httpexceptions import HTTPFound

from haemosphere.models import users
from .utility import forest, params, confirmationToken, objectFromToken, hosturl, sendEmail

def currentUser(request):
	"""
	Return the User instance attached to this request. Only works after a successful authentication.
	"""
	try:
		username = request.authenticated_userid
		return users.getUser(request.dbsession, username)
	except:
		return None

# ---------------------------------------------------------
# login and user related
# ---------------------------------------------------------
@view_config(route_name="/login", renderer="haemosphere:templates/login.mako")
@forbidden_view_config(renderer='haemosphere:templates/login.mako')
def login(request):
	"""Used for both showing the login page and authenticating. 
	"""
	login_url = request.route_url('/login')
	referrer = request.url
	if referrer == login_url:
		referrer = '/' # never use the login form itself as came_from
	came_from = request.params.get('came_from', referrer)
	message = request.params.get('message','')
	username = ''
	password = ''

	if 'form.submitted' in request.params:	# assume that we're trying to authenticate
		username = request.params['username'].strip()
		user = users.getUser(request.dbsession, username)	# email would also work for username here
		pw_attempt = request.params['password'] if 'password' in request.params else None

		if user is not None and user.check_password(pw_attempt):
			# Headers will return one or more HTTP headers (SET cookie, I believe)
			# that can later be queried to see if the request is from the same,
			# authenticated user.
			headers = remember(request, user.username)
			##print request.session.keys()

			# We return a "Found" response, which will cause a redirect, 
			# making the application look up what will be a new resource tree.
			if 'last_path' in request.session:
				return HTTPFound(location=request.session['last_path'], headers=headers)
			else:
				return HTTPFound(location=came_from, headers=headers)

		# If we got here, we didn't authenticate.
		message = 'Failed login'

	return {'message':message}

@view_config(route_name='/logout')
def logout(request):
	return HTTPFound(location = '/', headers = forget(request))

@view_config(route_name="/user/checkusername", renderer="json")
def checkUsernameAvailability(request):
	username = params(request, 'username')
	return {'usernameAvailable': username not in [user.username for user in users.allUsers(request.dbsession)]}

@view_config(route_name="/user/emailconfirm", renderer="json")
def sendConfirmationEmail(request):
	"""Send email to confirm registration.
	"""
	# Input params
	userProp = params(request, 'user')
	if not userProp:
		message = "No user information supplied."
		return {'message':message}
			
	# remove duplicate fields
	if 'emailCopy' in userProp: userProp.pop('emailCopy',None)
	if 'passwordCopy' in userProp: userProp.pop('passwordCopy',None)
	
	# validate and send email
	if len([val for val in userProp.values() if val==''])>0:
		message = "You have missing fields in the user registration. All fields must be provided."
	elif userProp['username'] in [user.username for user in users.allUsers(request.dbsession)]:
		message = "This username already exists in the system. Please select another. You can always make it the same as your email."
	elif userProp['email'] in [user.email for user in users.allUsers(request.dbsession)]:
		message = "This email already exists in the system."
	else:
		url = 'https://%s/user/register?token=%s' % (hosturl(request), confirmationToken(userProp, 'register'))
		messageBody = '\n'.join(['Hi %s' % userProp['fullname'],
			'\nTo complete your registration to Haemosphere, click on the following link: %s' % url,
			"\nIf you didn't request registration, let us know.",
			"\n\nHaemosphere Team\nhaemosphere.org"])
		sendEmail(request, 'User registration for Haemosphere', [userProp['email']], messageBody)
		message = 'Confirmation email has been sent.'
	return {'message':message}

@view_config(route_name="/user/register")
def registerUser(request):
	"""Register a new user given the correct token.
	"""
	# Input params
	token = params(request, 'token')
	
	message = "Error with registration."	# default message
	up = objectFromToken(token, 'register')	# user properties recovered from token
	if up:
		# create a new user
		user = users.createUser(request.dbsession,
                                up['username'],
                                up['fullname'],
                                up['email'],
                                up['password'])
		if user:
			forest(request).add(user.username)		
			message = "Registration complete"
			return HTTPFound(location='/', headers=remember(request, up['username']))
		
	return HTTPFound(location='/login?message=%s' % message)

@view_config(route_name="/user/account", permission="view", renderer="haemosphere:templates/user.mako")
def userAccount(request):
	"""Show user account details page, which can be used to update details as well as logout.
	"""
	from .group_views import groupPages
	username = request.authenticated_userid
	user = users.getUser(request.dbsession, username)
	return {'user':user, 'groupPages':groupPages(user.groupnames())}

@view_config(route_name="/user/update", permission="view", renderer="json")
def updateUserAccount(request):
	"""Update user details such as fullname, email and password here.
	"""
	attr = params(request, 'attr')
	value = params(request, 'value')
	
	username = request.authenticated_userid
	user = users.getUser(request.dbsession, username)
	if user is None:
		return {'error': 'No user "{0}" found.'.format(username)}
	
	if attr=='fullname': users.editUser(request.dbsession,
                                        username, username, value, user.email)
	elif attr=='email': users.editUser(request.dbsession,
                                       username, username, user.fullname, value)
	elif attr=='password': users.resetUserPassword(request.dbsession,
                                                   username, password=value)
	else: return {'error': 'No matching attribute to update'}

	return user.to_json()
	
@view_config(route_name="/user/retrieve", renderer="json")
def retrieveUserDetails(request):
	"""Send email to user with the token for resetting the password.
	"""
	# Input params
	email = params(request, 'email')
	
	user = users.getUser(request.dbsession, email)

	if user is None:
		message = 'No user in the system matching this email'
	else:
		# create an encrypted token with username embedded and attach it to the email
		url = 'http://%s/user/reset?url=%s' % (hosturl(request), confirmationToken(user.username, 'password'))
		messageBody = '\n'.join(['Hi %s,' % user.fullname,
			'\nYour username in Haemosphere is %s.\nClick on this link if you wish to reset your password: %s' % (user.username, url),
			"\nIf you didn't request a password reset, let us know.",
			"\n\nHaemosphere Team\nhaemosphere.org"])
		sendEmail(request, 'User detail retrieval for Haemosphere', [user.email], messageBody)
		message = 'Email has been sent.'
		
	return {'message':message}

@view_config(route_name="/user/reset", renderer="haemosphere:templates/passreset.mako")
def showResetUserPassword(request):
	"""Show the user password reset page.
	"""
	# Input params - token has username encoded inside, which won't get decoded if it was tempered with
	token = request.params.get('url')
	
	username = objectFromToken(token, 'password')	# will return False if username can't be recovered from token
	return {'token':token} if username else {'error':"The link for resetting password expired. Please go through the process again."}
	
@view_config(route_name="/user/passreset", renderer="json")
def resetUserPassword(request):
	"""Perform the actual password reset.
	"""
	# Input params
	token = params(request, 'token')
	password = params(request, 'password')
	
	username = objectFromToken(token, 'password')
	passwordChanged = False
	if username and username in [user.username for user in users.allUsers(request.dbsession)]:
		users.resetUserPassword(request.dbsession, username, password=password)
		passwordChanged = True
	return {'passwordChanged':passwordChanged}

@view_config(route_name="/user/users", permission="view", renderer="haemosphere:templates/users.mako")
def showUsers(request):
	# Check that user is admin, otherwise redirect to a different view
	if currentUser(request).isAdmin():
		return {'users': users.allUsers(request.dbsession), 'groups': [g.name for g in users.allGroups(request.dbsession)]}
	else:
		return HTTPFound(request.route_path('/user/account'))


@view_config(route_name="/user/manage", permission="view", renderer="json")
def manageUserAccount(request):
	"""Manage user accounts. Only admin is allowed to perform these functions.
	"""
	if not currentUser(request).isAdmin():
		return {'error':'only users in Admin group are allowed to manage users.'}

	try:
		return doManageUserAction(request)
	except:
		exc = sys.exc_info()[1]
		return {'error': repr(exc)}


def doManageUserAction(request):
	"""
	Actually perform a user management action.

	Several of the functions/methods called here may raise exceptions;
	it is left to the caller to handle them.
	"""
	action = params(request, 'action')

	if action=='create_group':
		users.createGroup(request.dbsession, params(request, 'name'))
	elif action=='delete_group':
		users.deleteGroup(request.dbsession, params(request, 'name'))
	elif action=='add_group_to_user':
		users.getUser(request.dbsession, params(request,'username')).addGroup(params(request,'groupname'))
		request.dbsession.flush()
	elif action=='remove_group_from_user':
		users.getUser(request.dbsession, params(request,'username')).removeGroup(params(request,'groupname'))
		request.dbsession.flush()
	elif action=='create_user':
		user = users.createUser(request.dbsession,
                                params(request,'username'),
                                params(request,'fullname'),
                                params(request,'email'),
                                params(request,'password'))
		if user: forest(request).add(user.username)
	elif action=='delete_user':
		username = params(request,'username')
		users.deleteUser(request.dbsession, username)
		if forest(request).exists(username):
			forest(request).remove(username)
	elif action=='edit_user':
		users.editUser(request.dbsession,
                       params(request, 'currentUsername'),
                       params(request, 'newUsername'),
                       params(request, 'fullname'),
                       params(request, 'email'))
		if params(request, 'currentUsername') != params(request, 'newUsername'):
			forest(request).add(params(request, 'newUsername'))
			forest(request).remove(params(request, 'currentUsername'), new_parent=params(request, 'newUsername'))
	elif action=='reset_password':
		return {'password': users.resetUserPassword(request.dbsession, params(request, 'username'))}
	return {}


@view_config(route_name="/user/sendemail", renderer="json")
def sendEmailToUsers(request):
	"""
	Send an email to multiple users.
	"""
	if not currentUser(request) or not currentUser(request).isAdmin():
		return {'message': "Only Admin users are allowed to email other users."}
	# Input params
	formData = params(request, 'data')
	if not formData:
		return {'message': "Email not sent: no form data supplied."}
	if 'recipients' not in formData:
		return {'message': "Email not sent: no recipients specified."}
	elif 'subject' not in formData:
		return {'message': "Email not sent: no subject line specified."}
	elif 'body' not in formData:
		return {'message': "Email not sent: no email content specified."}

	usernames = formData['recipients'].split(',')
	if not usernames or ''.join(usernames)=='':
		return {'message': "Email not sent: no recipients specified."}

	sent = []
	for username in usernames:
		if not users.getUser(request.dbsession, username.strip()):
			return {'message': "Email not sent: username '{}' is invalid".format(username)}

	for username in usernames:
		u = users.getUser(request.dbsession, username.strip())
		messageBody = "Dear {},\n\n{}\n\nRegards,\nHaemosphere Team\nhaemosphere.org".format(u.fullname, formData['body'])
		sendEmail(request, formData['subject'], [u.email], messageBody)
		sent.append(username)

	message = "Email sent to users: {}".format(', '.join(sent))
	return {'message': message}


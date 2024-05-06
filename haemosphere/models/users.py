from __future__ import absolute_import
import hashlib

from sqlalchemy import (
    Table,
    Column, Integer, Text, Sequence,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.hybrid import hybrid_property

from .meta import Base

	
# create associative entity (aka secondary entity) for the
# many-to-many relationship between Users and Groups
user_groups = Table('user_groups', Base.metadata,
    Column('user_id', ForeignKey('users.id'), primary_key=True),
    Column('group_id', ForeignKey('groups.id'), primary_key=True)
)
# ----------------------------------------------------------
# Main User class, where one instance corresponds to one user
# ----------------------------------------------------------
class User(Base):
	__tablename__ = 'users'

	id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
	username = Column(Text, nullable=False, unique=True)
	fullname = Column(Text, nullable=False)
	email = Column(Text, nullable=False, unique=True)
	_password = Column('password', Text, nullable=False)

	groups = relationship('Group',
                          secondary=user_groups,
                          back_populates='users')

	@hybrid_property
	def password(self):
		return self._password

	@password.setter
	def password(self, pw):
		self._password = User.hash(pw)

	def __init__(self, username, fullname, email, password):
		self.username = username
		self.fullname = fullname
		self.email = email
		self.password = password

	def __repr__(self):
		return "<User username='{0.username}' fullname='{0.fullname}'>".format(self)

	def check_password(self, pw):
		return self.password == User.hash(pw)

	def addGroup(self, groupname):
		sess = self.get_session()
		try:
			group = sess.query(Group).filter_by(name=groupname).one()
			if group not in self.groups:
				self.groups.append(group)
		except NoResultFound:
			raise ValueError("group '{}' does not exist".format(groupname))

	def removeGroup(self, groupname):
		sess = self.get_session()
		try:
			group = sess.query(Group).filter_by(name=groupname).one()
			if group in self.groups:
				self.groups.remove(group)
		except NoResultFound:
			raise ValueError("group '{}' does not exist".format(groupname))

	def groupnames(self):
		return [g.name for g in self.groups]

	def to_json(self):
		return {'username': self.username,
                'fullname': self.fullname,
                'email': self.email,
                'password': self.password,
                'groups': self.groupnames()}

	def isAdmin(self):
		return 'Admin' in self.groupnames()

	def get_session(self):
		return Session.object_session(self)

	@staticmethod
	def hash(passwordString, *args):
		if passwordString is None: return None
		return hashlib.md5(passwordString.encode('utf-8')).hexdigest()

	@staticmethod
	def group_finder(username, request):
		user = getUser(request.dbsession, username)
		if user:
			groups = [ 'group:{}'.format(name) for name in user.groupnames() ]
			return groups


class Group(Base):
	__tablename__ = 'groups'

	id = Column(Integer, Sequence('group_id_seq'), primary_key=True)
	name = Column(Text, nullable=False, unique=True)

	users = relationship('User',
                         secondary=user_groups,
                         back_populates='groups')

	def __repr__(self):
		return "<Group '{}'>".format(self.name)


# ----------------------------------------------------------
# module methods for manipulating User instances
# ----------------------------------------------------------
def getUser(dbsess, username, tryEmail=True):
	'''Fetch the User instance matching username. If tryEmail==True, it will also try to match email which should be unique.
	'''
	try:
		user = dbsess.query(User).filter_by(username=username).one()
	except NoResultFound:
		if tryEmail:
			try:
				user = dbsess.query(User).filter_by(email=username).one()
			except NoResultFound:
				return None
		else:
			return None
	return user


def allUsers(dbsess):
	'''Fetch a list of all User instances.
	'''
	return dbsess.query(User).all()


def allGroups(dbsess):
	'''Fetch a list of all groups.
	'''
	return dbsess.query(Group).all()


def createUser(dbsess, username, fullname, email, password):
	"""Create a new user and return the User instance if successful.
	If username or email already exist, returns None.
	"""
	u = User(username=username, fullname=fullname,
             email=email, password=password)
	try:
		dbsess.add(u)
		dbsess.flush()
		return u
	except IntegrityError as exc:
		if 'UNIQUE constraint failed' in exc.__class__.__name__:
			# username or email address already taken
			dbsess.rollback()
			return None
		else:
			raise
		

def deleteUser(dbsess, username):
	'''Delete user matching username.
	'''
	user = getUser(dbsess, username)
	if not user:
		return
	dbsess.delete(user)
	dbsess.flush()


def editUser(dbsess, currentUsername, newUsername, fullname, email):
	'''Edit user matching currentUsername.

    Username can be changed by specifying a different newUsername,
	which will be checked against existing usernames to ensure uniqueness.
	'''
	user = getUser(dbsess, currentUsername)
	if not user:
		return
	if currentUsername != newUsername:
		try:
			user.username = newUsername
			dbsess.flush()
		except IntegrityError as exc:
			if 'UNIQUE constraint failed' in exc.__class__.__name__:
				# username already taken
				dbsess.rollback()
				raise ValueError("username '{}' is already taken".format(newUsername))
			else:
				raise

	# change attributes and save
	user.fullname = fullname
	user.email = email
	dbsess.flush()
	

def resetUserPassword(dbsess, username, password=None):
	'''Reset user password. If password is None, use email.
	'''
	user = getUser(dbsess, username)
	try:
		if password:
			user.password = password
		else:
			user.password = user.email
		dbsess.flush()
	except:
		dbsess.rollback()
		raise

	return user.password
		

def createGroup(dbsess, groupname):
	"""
	Create a new group and return the Group instance if successful.
	If groupname already exists, returns None.
	"""
	try:
		group = Group(name=groupname)
		dbsess.add(group)
		dbsess.flush()
		return group
	except IntegrityError as exc:
		if 'UNIQUE constraint failed' in exc.__class__.__name__:
			# groupname already taken
			dbsess.rollback()
			raise ValueError("group name '{}' is already taken".format(groupname))
		else:
			raise


def deleteGroup(dbsess, groupname):
	try:
		g = dbsess.query(Group).filter_by(name=groupname).one()
		dbsess.delete(g)
		dbsess.flush()
	except NoResultFound:
		# delete never ran, so no need to rollback
		raise ValueError("group '{}' does not exist".format(groupname))
		return
	except:
		dbsess.rollback()
		raise

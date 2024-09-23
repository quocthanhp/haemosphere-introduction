from __future__ import absolute_import
from pyramid.config import Configurator

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid_beaker import session_factory_from_settings
from . import models
from .models import users, sharewould
from .views.views import RootFactory
from .utils import preload_datasets
from .models.object_enums import ObjectTypeEnum
import rpy2.robjects as ro

DATASET_PATH = "/haemosphere/data/datasets/F0r3sT/PUBLIC"

def main(global_config, **settings):
	""" This function returns a Pyramid WSGI application.
	"""
	session_factory = session_factory_from_settings(settings)

	config = Configurator(settings=settings, root_factory=RootFactory)
	config.set_session_factory(session_factory)

	config.include('pyramid_mako')
	config.include('.models')
	config.include('.routes')

	config.set_authentication_policy(AuthTktAuthenticationPolicy(secret="nascondo", 
																 callback=users.User.group_finder,
																 debug=False))
	config.set_authorization_policy(ACLAuthorizationPolicy())

	# Set up the area for datasets.
	sharewould.init_model(settings['haemosphere.model.datasets.root'])

	# Pre-load dataset to memory
	preload_datasets(DATASET_PATH, ObjectTypeEnum.HSDATASET)

	# Pre-load R
	# Load R libraries here when the Pyramid app starts
	# r = ro.r
	# r('library(limma)')
	# r('library(edgeR)')
	# r('library(BiocParallel)')
	
	config.scan()
	return config.make_wsgi_app()

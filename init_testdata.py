"""
This script initialises some data for the test suite.

It is assumed that the database has already been initialised
by running `initdb test.ini`, and that some public datasets are
stored in the dataset root directory specified in the ini file
located at <config_uri>.
"""
import os
import shutil
import sys
import transaction

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from pyramid.scripts.common import parse_vars

from haemosphere.models import (
    get_engine,
    get_session_factory,
    get_tm_session,
    )
from haemosphere.models.users import User, Group


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")\n'
          'Sharewould data is copied from the data dir specified in <config_uri>.' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2 or argv[1] in ['-h', '--help']:
        usage(argv)
    options = parse_vars(argv[2:])
    setup_logging('test.ini')
    settings = get_appsettings('test.ini', options=options)

    # connect to DB
    engine = get_engine(settings)
    session_factory = get_session_factory(engine)

    # add test data to SQL db
    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)
        add_data(dbsession)

    # copy sharewould datasets
    existing_datasets_dir = get_appsettings(argv[1])['haemosphere.model.datasets.root']
    copy_sharewould_data(settings, existing_datasets_dir)


def add_data(dbsess):
    from haemosphere.models.users import createUser, createGroup, getUser
    createGroup(dbsess, 'Admin')
    u = createUser(dbsess, 'tester1', 'A Tester', 'tester@test.com', 'password')
    u.addGroup('Admin')


def copy_sharewould_data(settings, existing_datasets_dir):
    subpath = "/F0r3sT/PUBLIC"
    dataset_root = settings['haemosphere.model.datasets.root']
    if os.path.exists(dataset_root):
        shutil.rmtree(dataset_root)
    shutil.copytree(existing_datasets_dir + subpath, dataset_root + subpath)


if __name__ == '__main__':
    main()

"""
This script migrates user and group data from a HDF5 file
to the SQL database (connection details are defined in
haemosphere/models/__init__.py).

It is assumed that the database has already been initialised
via the `initdb.py` script, and that the data being migrated
is not already in the database. (Though it should abort if you
try to import the same data twice, as uniqueness constraints
will be violated.)
"""
import os
import sys
import transaction
import pandas as pd

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
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, options=options)

    # get data from HDF5 store
    datafilepath = settings['haemosphere.model.users.datafile']
    users = pd.read_hdf(datafilepath, 'users')
    groups = pd.read_hdf(datafilepath, 'groups')

    # connect to DB
    engine = get_engine(settings)
    session_factory = get_session_factory(engine)

    # migrate
    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)
        add_groups(groups, dbsession)
        add_users(users, dbsession)
        create_user_group_links(groups, dbsession)


def add_groups(groups, dbsess):
    for group in groups.index:
        dbsess.add(Group(name=group))


def add_users(users, dbsess):
    # note need to manually update the password since passwords
    # in HDF file are already hashed
    for username, userdata in users.iterrows():
        u = User(username=username,
                 fullname=userdata['fullname'],
                 email=userdata['email'],
                 password=userdata['password'])
        u._password = userdata['password']
        dbsess.add(u)


def create_user_group_links(groups, dbsess):
    for groupname, usernames in groups.iteritems():
        group = dbsess.query(Group).filter_by(name=groupname).one()
        for username in usernames:
            user = dbsess.query(User).filter_by(username=username).one()
            user.groups.append(group)


if __name__ == '__main__':
    main()

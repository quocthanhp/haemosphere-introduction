"""
This script initialises the SQL database for storing
user and group data.
"""
import os
import sys

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from pyramid.scripts.common import parse_vars

from haemosphere.models.meta import Base
from haemosphere.models.labsamples import Base as LabSamplesBase


from haemosphere.models import (
    get_engine,
    get_engine2
    )


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

    engine = get_engine(settings)
    Base.metadata.create_all(engine)

    engine2 = get_engine2(settings)
    LabSamplesBase.metadata.create_all(engine2)


if __name__ == '__main__':
    main()
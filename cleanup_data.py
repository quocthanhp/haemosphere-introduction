"""
This script will convert all entries in the labsamples database matching a given pattern
to a new pattern.
This script will take five command line arguments:
    1) configuration file (e.g. development.ini)
    2) The table to be updated ["Sample", "Celltype", "Batch"]
    3) The column in the given table to be updated
    4) A string used to find all matching entries
    5) A string that all previously matched data will be updated to
"""
import os
import sys
import transaction
import pandas as pd
import haemosphere.models.labsamples as labsamples


from zope.sqlalchemy import mark_changed

from pyramid.paster import (
	get_appsettings,
	setup_logging,
	)

from pyramid.scripts.common import parse_vars

from haemosphere.models import (
	get_engine2,
	get_session_factory,
	get_tm_session,
	)
	
from haemosphere.models.labsamples import Sample, Batch, Celltype

def usage(argv):
	cmd = os.path.basename(argv[0])
	print('usage: %s <config_uri> [var=value]\n'
			'(example: "%s development.ini sample cell_num 386k 386L")' % (cmd, cmd))
	sys.exit(1)


def main(argv=sys.argv):
	if len(argv) < 6:
		usage(argv)
	config_uri = argv[1]
	table = argv[2]
	column = argv[3]
	old_data = argv[4]
	new_data = argv[5]	
	
	setup_logging(config_uri)
	settings = get_appsettings(config_uri)

	# connect to DB
	engine = get_engine2(settings)
	session_factory = get_session_factory(engine)

	# update matching data selected table column
	with transaction.manager:
		dbsession = get_tm_session(session_factory, transaction.manager)
        if table == "Sample":
            update_samples(column, old_data, new_data, dbsession)        
        elif table == "Celltype":
            update_celltypes(column, old_data, new_data, dbsession)         
        elif table == "Batch":
            update_batches(column, old_data, new_data, dbsession) 
        else:
            print("Invalid Table Name")
            
                        
def update_samples(column, old_data, new_data, dbsession):
    data = labsamples.getAllSamples(dbsession, column, old_data)
    
    if not data:
        print("No matching data found for %s" % old_data)
        return

    for entry in data:
        labsamples.editSample(dbsession, entry.id, column, new_data)

    transaction.commit()
    print("Finished updating %s to %s" % (old_data, new_data))

def update_celltypes(column, old_data, new_data, dbsession):
    data = labsamples.getAllCelltypes(dbsession, column, old_data)
    
    if not data:
        print("No matching data found for %s" % old_data)
        return

    for entry in data:
        labsamples.editCelltype(dbsession, entry.id, column, new_data)

    transaction.commit()
    print("Finished updating %s to %s" % (old_data, new_data))
    
def update_batches(column, old_data, new_data, dbsession):
    data = labsamples.getAllBatches(dbsession, column, old_data)
    
    if not data:
        print("No matching data found for %s" % old_data)
        return

    for entry in data:
        labsamples.editBatch(dbsession, entry.id, column, new_data)

    transaction.commit()
    print("Finished updating %s to %s" % (old_data, new_data))
    
    
    



if __name__ == '__main__':
    main()

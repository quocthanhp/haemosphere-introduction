
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


def main(argv=sys.argv):	
    dev = "development.ini"
    script = "cleanup_data.py"
        
    updates = {
        "Sample" : {
            "cell_num" : {
                "old_data" : ["1100k", "14097k", "14500k", "145k", "1490k", "233k", "246k+605k", "262k", "267k", "287k", "1590k", "1874k", "196k", "207k", "2100k+2217k", "3000k", "325k", "3400k", "456k+333k"],
                "new_data" : ["1100K", "14097K", "14500K", "145K", "1490K", "233K", "246K+605K", "262K", "267K", "287K", "1590K", "1874K", "196K", "207K", "2100K+2217K", "3000K", "325K", "3400K", "456K+333K"],
            },
            "elution_volume" : {
                "old_data" : ["16+31"],
                "new_data" : ["31+16"],
            },
            "rna_prep" : {
                "old_data" : ["Qiagen\ Mini+DNase", "Qiagen\ Mini\ +\ Dnase", "Qiagen\ Mini+DNase/Qiagen\ Micro", "Qiagen\ Mini+Dnase", "Qiagen\ Mini+Dnase/Qiagen\ Micro"],
                "new_data" : ["Qiagen\ Mini\ +\ DNase", "Qiagen\ Mini\ +\ DNase", "Qiagen\ Mini\ +\ DNase/Qiagen\ Micro", "Qiagen\ Mini\ +\ DNase", "Qiagen\ Mini\ +\ DNase"],
            },              
            "sort_date" : {
                "old_data" : ["No\ Sort"],
                "new_data" : ["Not\ Sorted"],
            },
        },
        "Celltype" : {
            "notes" : {
                "old_data" : ["Akashi\ et\ al.,\ 2000", "Wu\ 2006", "Nutt\ and\ Kee,\ 2007", "Ng\ et\ al\ 2011"],
                "new_data" : ["\(Akashi\ et\ al.,\ 2000\)", "\(Wu\ 2006\)", "\(Nutt\ and\ Kee,\ 2007\)", "Ng\ et\ al,\ 2011"],
            },
            "species" : {
                "old_data" : ["Mus\ musculus"],
                "new_data" : ["MusMusculus"],
            },
            "surface_markers" : {
                "old_data" : ["No\ Sort", "Not\ sorted"],
                "new_data" : ["Not\ Sorted", "Not\ Sorted"],
            },               
            "tissue" : {
                "old_data" : ["Cell\ line", "BM\ Crush"],
                "new_data" : ["Cell\ Line", "BM\ \(Crush\)"],
            },
        },        
    }
    
    
    for table, cols in updates.iteritems():
        for column, data in cols.iteritems():
            for old_data, new_data in zip(data["old_data"], data["new_data"]):    
                os.system("python %s %s %s %s %s %s" % (script, dev, table, column, old_data, new_data))


if __name__ == '__main__':
    main()

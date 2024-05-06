"""
This script migrates the labsample data from the samples, 
batches, and celltypes txt files to the SQL database 
(connection details are defined in haemosphere/models/__init__.py).
"""
import os
import sys
import transaction
import pandas as pd

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
			'(example: "%s development.ini")' % (cmd, cmd))
	sys.exit(1)


def main(argv=sys.argv):
	if len(argv) < 2:
		usage(argv)
	config_uri = argv[1]
	options = parse_vars(argv[2:])
	setup_logging(config_uri)
	settings = get_appsettings(config_uri, options=options)

	# get data from txt files store
	directorypath = settings['haemosphere.model.grouppages']
	samplepath = directorypath + '/HiltonLab/HematlasSamples_samples.txt'
	batchpath = directorypath + '/HiltonLab/HematlasSamples_batches.txt'
	celltypepath = directorypath + '/HiltonLab/HematlasSamples_celltypes.txt'

	samples = pd.read_csv(samplepath, sep='\t').fillna('')
	batches = pd.read_csv(batchpath, sep='\t').fillna('')
	celltypes = pd.read_csv(celltypepath, sep='\t').fillna('')

	# connect to DB
	engine = get_engine2(settings)
	session_factory = get_session_factory(engine)

	# migrate
	with transaction.manager:
		dbsession = get_tm_session(session_factory, transaction.manager)
		add_celltypes(celltypes, dbsession)
		add_batches(batches, dbsession)
		add_samples(samples, dbsession)
        link_samples_batches(samples, dbsession)


def add_samples(samples, dbsess):
	for sample_id, cell_num, elution_date, elution_volume, rin, rna, rna_prep, sort_date, total_rna, amplified_rna_bio, batch_id, celltype, description, notes, original_sample_id, previous_sample_id, genotype, treatment, group in samples.get_values():
# 		try:
# 			ctype = dbsess.query(Celltype).filter_by(celltype=celltype).one()
# 		except:
# 			ctype = None
		s = dbsess.query(Sample).filter_by(sample_id=sample_id).first()
		if not s:
			new_sample = Sample(sample_id = sample_id,
								cell_num = cell_num,
								elution_date = elution_date,
								elution_volume = elution_volume,
								rin = rin,
								rna = rna,
								rna_prep = rna_prep,
								sort_date = sort_date,
								total_rna = total_rna,
								amplified_rna_bio = amplified_rna_bio,
# 								batch_id = batch_id,
# 								celltype = celltype,
								description = description,
								notes = notes,
								original_sample_id = original_sample_id,
								previous_sample_id = previous_sample_id,
								genotype = genotype,
								treatment = treatment,
								group = group)
			dbsess.add(new_sample)
				
# 		b = dbsess.query(Batch).filter_by(batch_id=batch_id).one()
# 		new_sample.batch.append(b)

# 		c = dbsess.query(Celltype).filter_by(celltype=celltype).one()
# 		new_sample.celltype = c

	transaction.commit()

		
def add_celltypes(celltypes, dbsess):
	for celltype, cell_lineage, colour, description, include_haemopedia, maturity, notes, order, species, strain, surface_markers, previous_names, tissue in celltypes.get_values():
		c = dbsess.query(Celltype).filter_by(celltype=celltype).first()
		if not c:
		
			new_celltype = Celltype(celltype=celltype,
								cell_lineage=cell_lineage,
								colour=colour,
								description=description,
								include_haemopedia=include_haemopedia,
								maturity=maturity,
								notes=notes,
								order=order,
								species=species,
								strain=strain,
								surface_markers=surface_markers,
								previous_names=previous_names,
								tissue=tissue)					
			dbsess.add(new_celltype)
	transaction.commit()


def add_batches(batches, dbsess):
	for batch_id, description, date_data_received in batches.get_values():
		b = dbsess.query(Batch).filter_by(batch_id=batch_id).first()
		if not b:
			new_batch = Batch(batch_id=batch_id,
								description=description,
								date_data_received=date_data_received)
			dbsess.add(new_batch)
	transaction.commit()


def link_samples_batches(samples, dbsess):
	for sample_id, cell_num, elution_date, elution_volume, rin, rna, rna_prep, sort_date, total_rna, amplified_rna_bio, batch_id, celltype, description, notes, original_sample_id, previous_sample_id, genotype, treatment, group in samples.get_values():
		
		s = dbsess.query(Sample).filter_by(sample_id=sample_id).one()
		try:
			b = dbsess.query(Batch).filter_by(batch_id=batch_id).one()
			s.batch = b
		except Exception:
			pass			

		try:
			c = dbsess.query(Celltype).filter_by(celltype=celltype).one()
			s.celltype = c   
		except:
			pass

 	transaction.commit()


if __name__ == '__main__':
    main()

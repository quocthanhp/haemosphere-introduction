from __future__ import absolute_import
from pyramid.view import view_config
from pyramid.response import Response, FileResponse

from haemosphere.models import hsgeneset

from .hsdataset_views import datasetFromName
from .utility import params


@view_config(route_name='/downloadfile')
def downloadFile(request):
	"""Return a request.response object corresponding to a file download.
	Note that for static files, simply returning a response object from: 
	response = FileResponse('haemosphere/models/data/Genes.txt') works.
	"""
	import tempfile
	
	# Parse input - a lot of input params depend on filetype, so look under each 'if' block for more
	filetype = params(request, 'filetype')
	filename = 'HaemosphereFile.txt'	# just some default - should be overwritten within each 'if' block
	# Each 'if' block should also define a response object to be returned

	if filetype=='AllGenes':
		f = tempfile.NamedTemporaryFile(prefix=filetype, suffix='.txt')
		hsgeneset.HSGeneset().dataframe().to_csv(f.name, sep="\t")
		f.seek(0,0)
		response = FileResponse(f.name)
		filename = 'AllGenes.txt'
		
	elif filetype=='AllMouseGeneSymbols' or filetype=='AllHumanGeneSymbols':
		f = tempfile.NamedTemporaryFile(prefix=filetype, suffix='.txt')
		df = hsgeneset.HSGeneset().dataframe()
		species = 'MusMusculus' if filetype=='AllMouseGeneSymbols' else 'HomoSapiens'
		temp_str = '\n'.join(sorted(df[df['Species']==species]['GeneSymbol']))		
		f.write(temp_str.encode('utf-8'))
		f.seek(0,0)
		response = FileResponse(f.name)
		filename = '%s.txt' % filetype
		
	elif filetype=='dataset':	# download a dataset file
		# Inputs
		datasetName = params(request, 'datasetName')
		datasetFile = params(request, 'datasetFile')
		if not datasetName or not datasetFile:
			return Response("No dataset name")
			
		ds = datasetFromName(request, datasetName)
		f = tempfile.NamedTemporaryFile(prefix=filetype, suffix='.txt')

		if datasetFile=='raw':	# requesting raw counts
			ds.expressionMatrix(datatype='counts').to_csv(f.name, sep="\t")
		elif datasetFile=='cpm':
			ds.expressionMatrix(datatype='cpm').to_csv(f.name, sep="\t")
		elif datasetFile=='tpm':
			ds.expressionMatrix(datatype='tpm').to_csv(f.name, sep="\t")
		elif datasetFile=='expression':	# microarray dataset expression matrix
			ds.expressionMatrix().to_csv(f.name, sep="\t")
		elif datasetFile=='probes':
			probeIds = ds.expressionMatrix().index
			gpid = ds.geneIdsFromProbeIds(probeIds=probeIds, returnType='dict')
			temp_str1 = '\n'.join(['%s\t%s' % (probeId, ','.join(gpid[probeId])) for probeId in probeIds if probeId in gpid])
			f.write(temp_str1.encode('utf-8'))
		elif datasetFile=='samples':
			ds.sampleTable().to_csv(f.name, sep="\t")
			
		f.seek(0,0)
		response = FileResponse(f.name)
		filename = '%s_%s.txt' % (datasetName, datasetFile)
			
	elif filetype=='pdf':	# assume we're downloading a pdf of an image using rsvg-convert
		# Inputs
		filedata = params(request, 'filedata')
		filename = params(request, 'filename', 'svg.pdf')  # optional

		if filedata:
			import subprocess
			
			# write filedata, which is a stringified version of the svg, to tempfile
			svgfile = tempfile.NamedTemporaryFile(prefix='svg', suffix='.txt')
			svgfile.write(filedata.encode('utf-8'))
			svgfile.seek(0,0)	# not sure why, but it won't work without this
			
			# create another tempfile for output of conversion to pdf
			pdffile = tempfile.NamedTemporaryFile(prefix='svg', suffix='.pdf')
			
			# call rsvg-convert with input and output files, then serve it as FileResponse
			subprocess.call(["rsvg-convert", svgfile.name, "-o", pdffile.name, "-f", "pdf"])
			response = FileResponse(pdffile.name)
		else:
			return request.response	# should really return error response once I work it out

	elif filetype=="RFile":	# downloading R file - this file should already exist at the path specified in request.session
		filepath = request.session.get('r_object_filepath')
		import os
		if os.path.isfile(filepath):
			response = FileResponse(filepath)
			filename = "haemosphere.topTable.rData"
		else:
			return request.response
		
	else:
		return request.response
		
	response.headers['Content-Disposition'] = ("attachment; filename=%s" % str(filename))	# str() needed to avoid 'u' attached to some filename strings

	return response


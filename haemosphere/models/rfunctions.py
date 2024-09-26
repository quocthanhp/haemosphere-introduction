'''
Note that convert_to_r_dataframe() method of rpy2 will prepend 'X' to dataset column names if any of these
start with a 'number': eg. '6hrFXII' column will turn into 'X6hrFXII'.
'''
# On vcpubhl01, import rpy2.robjects fails with an error on readline library, but only through pserve, and not through ipython.
# After much work, found this page https://github.com/ContinuumIO/anaconda-issues/issues/152 
# which suggested this statement before rpy2 import and it works!
from __future__ import absolute_import
import readline

import pandas, sys
import os

import rpy2.robjects as ro
from rpy2.robjects import pandas2ri, r, globalenv
pandas2ri.activate()

import logging
log = logging.getLogger(__name__)


topTableString = """\
# Return a matrix resembling limma's topTable function.
#
# Example: Suppose x is the data frame of expression values, with columns ('BCell(1)','TCell(1)','TCell(2)','BCell(2)','HSC(1)','HSC(2)').
# haemosphere.topTable(x, c('B','T','T','B','HSC','HSC'), c('B','T','T','B','HSC','HSC'), 'B', 'T') 
# will return topTable of DE genes between 'B' and 'T'. 
# Use microarray=False if x is rna-seq data (filterMinCPM, filterMinExpressedSamples and normalizationMethod are ignored for microarray).
#
# Now we can also do haemosphere.topTable(x, c('B','T','T','B','HSC','HSC'), c('Committed','Committed','Committed','Committed','Prog','Prog'), 'Committed', 'Prog') 
# to find DE genes between progenitor cell types and committed cell types. In this case, the design matrix is
# constructed the same way as before (hence we need replicateGroups), but contrast matrix is constructed with correct
# mixtures of each replicates.
#
# minRows is used to return the minimum number of rows for the returned table, regardless of adjPCutoff. 
# This is useful when there are 0 or hardly any DE genes - at least the user can see that there hasn't been an error.
#
# Parameters
# ----------
# x (data.frame): expression data frame with features as rows, sample ids as columns
# replicateGroups (string vector): sample group values deemed "replicates" designated to each sample id, in the same order and length as columns of x
# groups (string vector): sample group values of interest for analysis, in the same order and length as columns of x
# group1 (string): a member of groups
# group2 (string): another member of groups, different to group1
# microarray (boolean): True if x is microarray expression data, False otherwise
# filterMinCPM (float), filterMinExpressedSamples (integer): 
#		keep only rows where filterMinExpressedSamples or more samples out of group1 and group2 must be greater than filterMinCPM 
# normalizationMethod (string): same as used in the 'method' argument of edgeR's calcNormFactors fuction.
# adjPCutoff (float): consider rows with adj.P.Val (from limma's topTable) less than this value as significant.
# minRows (integer): minimum number of rows to return regardless of significant rows.
#
# Returns
# -------
# data.frame with columns ("features","logFC","adjPVal","AveExpr").
# 		matrix(0,0,0) if something went wrong.
#
haemosphere.topTable = function(file, replicateGroups, groups, group1, group2, microarray=T, 
	filterMinCPM=0.5, filterMinExpressedSamples=2, normalizationMethod='TMM', adjPCutoff=0.05, minRows=50)
{	
	if (microarray) library(limma)
	else library(edgeR)
	options(digits=4)

	x <- readRDS(file)

	# find indices of group1 and group2 from groups vector
	group1Indices = which(groups==group1)
	group2Indices = which(groups==group2)
	
	# Design matrix is created using replicate groups; it can't have certain characters, so use make.names first.
	# (So do not try to match the elements of these vectors before and after make.names.)
	# make.names doesn't recognise special characters like '+' or '-' properly, so both 'CD8+' and 'CD8-' will become 'CD8.'
	# To avoid this, create new names to both groups and replicateGroups based on their position in unique
	# Note also that if an element of a char vector starts with a 'number', such as '6hrFXII', make.names will prepend 'X' (same for numeric vectors)
	replicateGroups = make.names(match(replicateGroups, unique(replicateGroups)))  # we'll end up with c('X1','X2','X1',...)
	groups = make.names(match(groups, unique(groups)))
	design = model.matrix(~0+as.factor(replicateGroups))
	colnames(design) = levels(as.factor(replicateGroups))

	# Since we need to supply the arguments to makeContrasts dynamically, we can't just use the normal form of makeContrasts,
	# because it expects variable names rather than strings. Using parse() after constructing a string works in a normal R session,
	# but it doesn't work through rpy2. Instead, found the trick using do.call from 
	# https://stat.ethz.ch/pipermail/bioconductor/2009-June/027913.html, which works wonders.
	if (identical(replicateGroups, groups)) {  # makeContrasts the normal way
		cont.matrix = do.call(makeContrasts, list(paste(replicateGroups[group1Indices][1], replicateGroups[group2Indices][1], sep="-"), levels=design))
	}
	else {
		# construct strings to be used for makeContrasts; they should look like "(B+T)/4"
		group1String = paste("(", paste(unique(replicateGroups[group1Indices]),collapse="+"), ")/", length(replicateGroups[group1Indices]), sep="")
		group2String = paste("(", paste(unique(replicateGroups[group2Indices]),collapse="+"), ")/", length(replicateGroups[group2Indices]), sep="")
		cont.matrix = do.call(makeContrasts, list(paste(group1String, group2String, sep="-"), levels=design))
	}
	
	# perfrom lmFit
	if (microarray)
		fit = lmFit(x, design)
	else {
		# create a DGEList object and normalize if specified
		x = DGEList(x)
		if (!is.null(normalizationMethod)) x = calcNormFactors(x, method=normalizationMethod)
		
		# keep only rows where filterMinExpressedSamples or more samples out of group1 and group2 must be greater than filterMinCPM
		x.cpm = cpm(x)
		x = x[rowSums(x.cpm[,c(group1Indices, group2Indices)]>filterMinCPM)>=filterMinExpressedSamples,]
		
		fit = lmFit(voom(x, design=design, normalize.method='none'), design)
	}

	eb = eBayes(contrasts.fit(fit, cont.matrix))

	# fetch topTable
	m = topTable(eb, adjust='fdr', sort.by='P', number=Inf)   # this should fetch every gene/probe sorted by adj p
	
	sigRows = which(m[,"adj.P.Val"]<adjPCutoff)
	
	if (nrow(m)<minRows)
		minRows = nrow(m)
		
	if (length(sigRows)<minRows) # too few rows, so return at least minRows
		m = m[1:minRows,]
	else	# return all significant rows
		m = m[sigRows,]
	
	# 2015-09-25: After a recent update of rpy2, it seems row index is not preserved after converting from R to pandas.
	# so add the rownames into m
	m['features'] = rownames(m)

	# select column subset and remove dots in adj.P.Val colname
	m = m[c("features","logFC","adj.P.Val","AveExpr")]
	colnames(m)[3] = "adjPValue"

	if (nrow(m)==0)  # something went wrong
		return(matrix(0,0,0))
	else
		return(data.frame(m))
}

# Wrapper for the main function. This is done to enable object saving. Note that wrapper has one extra argument of 'saveToFile'. 
# If this points to a filename or filepath, all the input objects as well as the main function will be saved to this file. 
# This enables replication of the function in a different environment by using load().
haemosphere.topTableWrapper = function(x, replicateGroups, groups, group1, group2, microarray=T, 
	filterMinCPM=0.5, filterMinExpressedSamples=2, normalizationMethod='TMM', adjPCutoff=0.05, minRows=50, saveToFile='')
{
	if (saveToFile!='') {
		save(haemosphere.topTable, x, replicateGroups, groups, group1, group2, microarray, filterMinCPM, 
			filterMinExpressedSamples, normalizationMethod, adjPCutoff, minRows, file=saveToFile)
	}
	return(haemosphere.topTable(x, replicateGroups, groups, group1, group2, microarray=microarray, filterMinCPM=filterMinCPM, 
								filterMinExpressedSamples=filterMinExpressedSamples, normalizationMethod=normalizationMethod, 
								adjPCutoff=adjPCutoff, minRows=minRows))
}
"""

RDS_PATH = "/haemosphere/haemosphere/models/rds"

def topTable(selectedDatasetName, dataframe, replicateGroups, groups, group1, group2, isMicroarray, filterMinCpm=0.5, 
			 filterMinExpressedSamples=2, normalizationMethod='TMM', saveToFile=''):
	"""
	Given a pandas dataframe of microarray or rna-seq expression matrix (counts) as dataframe, run DE analysis on limma in R 
	and return the topTable	results as another pandas dataframe. groups is the list of groups values each column of dataframe 
	belongs to, in the same order. 
	group1 and group2 are specific values from groups.
	normalizationMethod may be one of ("TMM","RLE","upperquartile","none")
	replicateGroups is the sample group items corresponding to (usually) biological replicates.
	
	Example:
		>> expMatrix = pandas.read_csv('./ExpressionMatrix_MatureMegs.txt', sep='\t', index_col=0)
		>> celltypes = ['Meg8N', 'Meg16N', 'WFL', 'Meg16N', 'Meg8N', 'Meg32N', 'Meg8N', 'Meg32N', 'WFL', 'Meg16N', 'Meg32N', 'WFL']
		>> print topTable(expMatrix, celltypes, celltypes, 'Meg8N', 'Meg16N', True).iloc[:10,:]
	  
	"""
	# log.debug(dataframe.columns)
	# log.debug(dataframe.index)
	rds_path = f"{RDS_PATH}/{selectedDatasetName}.rds"
	if os.path.exists(rds_path):
		print(f"RDS file {rds_path} found. Reading from it.")
	else:
		# Save to .rds file
		r_df = pandas2ri.py2rpy(dataframe)
		ro.r('saveRDS')(r_df, file=rds_path)

	globalenv["rds_path"] = rds_path

	r(topTableString)
	result = r("haemosphere.topTableWrapper(rds_path, c('{0}'), c('{1}'), '{2}', '{3}', {4}, filterMinCPM={5}, filterMinExpressedSamples={6}, normalizationMethod='{7}', saveToFile='{8}'); "\
		.format("','".join(replicateGroups), "','".join(groups), group1, group2, \
		'T' if isMicroarray else 'F', filterMinCpm, filterMinExpressedSamples, normalizationMethod, saveToFile))
	result = result.set_index("features")
	
	# If dataframe has index which look like integers, result will have index which are integers! Check this.
	if len(result)>0 and isinstance(result.index[0], int) and isinstance(dataframe.index[0], str):
		result.index = result.index.astype(str)
	if result is None:
		log.debug("None Result\n")
	return result


def distances(dataframe, isMicroarray, top=500):
	"""
	Return pandas DataFrame of all pairwise columns of dataframe.
	"""
	globalenv["dataframe"] = dataframe
	
	r("""\
	haemosphere.distances = function(x, microarray=T, top=500)
	{		
		if (!microarray) {
			library(edgeR)
			x = voom(DGEList(x), normalization='none')
			x = x$E
		}
		
		# use all rows if the number of rows is less than top
		if (top>=nrow(x)) top = nrow(x)-1
		
		x <- as.matrix(x)
		nsamples <- ncol(x)
		cn <- colnames(x)
		bad <- rowSums(is.finite(x)) < nsamples
		if (any(bad)) 
			x <- x[!bad, , drop = FALSE]
		nprobes <- nrow(x)
		top <- min(top, nprobes)
		labels <- as.character(colnames(x))
		dd <- matrix(0, nrow = nsamples, ncol = nsamples, dimnames = list(cn, cn))
		topindex <- nprobes - top + 1
	
		s <- rowMeans((x - rowMeans(x))^2)
		q <- quantile(s, p = (topindex - 1.5)/(nprobes - 1))
		x <- x[s >= q, ]
		for (i in 2:(nsamples)) dd[i, 1:(i - 1)] = sqrt(colMeans((x[,i] - x[, 1:(i - 1), drop = FALSE])^2))
		
		return(as.matrix(as.dist(dd)))
    }""")
	
	result = pandas.DataFrame(r("haemosphere.distances(dataframe, {0}, {1}); ".format('T' if isMicroarray else 'F', top)))
	
	# R will convert column strings from AB-CD to AB.CD, for example, so preserve these
	result.index = dataframe.columns
	result.columns = dataframe.columns
	return result

def cpm(dataframe):
	globalenv['dataframe'] = dataframe
	df = pandas.DataFrame(r('library(edgeR); output = cpm(calcNormFactors(DGEList(dataframe), method="TMM"));'))
	df.index = dataframe.index
	df.columns = dataframe.columns
	return df

# ------------------------------------------------------------
# Tests - eg. nosetests hsgeneset.py
# ------------------------------------------------------------
def test_topTable():
	df = pandas.DataFrame([[40,21,5,2],[22,46,1,5],[51,62,4,6]], columns=['a','b','c','d'], index=['x','y','z'])
	assert topTable(df, ['A','A','B','B'], ['A','A','B','B'], 'A', 'B', True).at['z','logFC']>51.4

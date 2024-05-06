from __future__ import absolute_import
from __future__ import print_function
import pandas
from . import hsgeneset

def createDatafile(**kwargs):
	"""Create the text files associated with ScoreGenes class.
	"""
	commentsFile = kwargs.get('drug_target_comments')
	targetsFile = kwargs.get('drug_targets')
	outfileScores = kwargs.get('outfileScores')
	outfileComments = kwargs.get('outfileComments')
	
	comments = pandas.read_csv(commentsFile, sep='\t')
	targets = pandas.read_csv(targetsFile, sep='\t')
	print(comments.columns.tolist(), '\n')
	print(targets.columns.tolist(), '\n')
	
	# targets table contains score for each gene
	scores = targets[['gene_id', 'associated_gene_name', 'eg_pubmed_count', 'username', 'user_comment', 'drug_target_score']]
	scores.columns = ['geneId', 'previousGeneSymbol', 'pubmedCount', 'user', 'shortComment', 'drugTargetScore']
	scores = scores.set_index('geneId').fillna('')
	
	# comments table contains extended comments for each gene
	comments = comments[['gene_id', 'username', 'dtg', 'comment', 'content_type']]
	comments.columns = ['geneId', 'user', 'date', 'comment', 'contentType']
	comments = comments[pandas.notnull(comments['comment'])]
	
	# write to outfile
	scores.to_csv(outfileScores, sep='\t')
	comments.to_csv(outfileComments, sep='\t', index=False)

	
# ----------------------------------------------------------
# ScoreGenes class
# ----------------------------------------------------------
class ScoreGenes(object):

	def __repr__(self):
		return "<ScoreGenes filepath='{0.filepath}'>".format(self)
	
	def __init__(self, scoresFile, commentsFile):
		self.scoresFile = scoresFile
		self.commentsFile = commentsFile
		self._scores = pandas.read_csv(scoresFile, sep='\t', index_col=0)
		self._comments = pandas.read_csv(commentsFile, sep='\t')
	
	def scoresTable(self):
		return self._scores

	def commentsTable(self):
		return self._comments

	def saveChanges(self, **kwargs):
		"""save changes to file.
		Example: saveChanges(**{'shortComment': 'Insufficient expression', 'score': 'no', 'comment': '', 'user': 'Jarny Choi', 'geneId': 'ENSMUSG00000063234'})

		Parameters
		----------
		user (str): compulsory key, eg. 'John Smith' - use full name since this is the only user info kept
		geneId (str): compulsory key, eg. 'ENSMUSG00000063234'
		score (str): optional, {'yes','no','more research required'}
		shortComment (str): optional
		comment (str): optional, more extended comment
		
		Returns
		-------
		Returns current date and time as string in '2015-10-23 14:30' format, None if there was an error.
		
		"""
		import time
		
		# parse input
		user = kwargs.get('user')
		geneId = kwargs.get('geneId')
		score = kwargs.get('score')
		shortComment = kwargs.get('shortComment')
		comment = kwargs.get('comment')
		
		if not user or not geneId or (score and score not in ['yes','no','more research required']):
			return None
		
		comments = [comment] if comment else []	# may need to add comments if score is changed
		
		if score or shortComment:  # change matching row in score table
			df = self.scoresTable()
			if score: 
				comments.append("Drug target score changed from '%s' to '%s'" % (df.at[geneId,'drugTargetScore'], score))
				df.set_value(geneId, 'drugTargetScore', score)
			if shortComment:
				comments.append("Short comment changed from '%s' to '%s'" % (df.at[geneId,'shortComment'], shortComment))
				df.set_value(geneId, 'shortComment', shortComment)
			df.set_value(geneId, 'user', user)
			df.to_csv(self.scoresFile, sep='\t')
			
		date = time.strftime('%Y-%m-%d %H:%M')

		if comments:	# add new comments
			df = self.commentsTable()
			for comment in comments:
				df.loc[len(df)+1] = [geneId, user, date, comment, 'plain']
			df.to_csv(self.commentsFile, sep='\t', index=False)
			
		return date
		
# ------------------------------------------------------------
# Tests - eg. nosetests labsamples.py
# ------------------------------------------------------------
def test_scoreTable():
	sg = ScoreGenes('data/grouppages/CSL/scoregenes_scores.txt', 'data/grouppages/CSL/scoregenes_comments.txt')
	print(sg.scoreTable().iloc[:3,:])


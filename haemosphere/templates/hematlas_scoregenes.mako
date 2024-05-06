<%
'''
Inputs required
scoreTable: [{'geneId':'ENSMUSG00000111','pubmedCount':5, ...}, ...]
commentsTable: [{"date": "2012-07-10 14:54:36.055068", ...}, ...]
lineages: ['Multi Potential Progenitor',...]
lineageColours: {'Erythrocyte Linage':'#ccc',...}
or
error: string indicating error
'''
import json

%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<head>
<title>Haemosphere - Hematlas ScoreGenes</title>

<%namespace name="common_elements" file="common.mako"/>
${common_elements.header_elements()}

<link type="text/css" href="/css/d3.slider.css" rel="stylesheet" />
<script type="text/javascript" src="/js/d3.slider.js"></script>

<style type="text/css">
table.barcode tbody {
	height:initial;
}
.d3-slider {
	height: 0.6em;
}
.d3-slider-handle {
	height: 1.0em;
}

table.dataTable {
	margin-top:0;
}

table.dataTableHeader tbody {
	height: initial;
}
table.dataTableHeader tbody tr {
	background-color:white;
}
table.dataTableHeader tbody td {
	border:0;
	white-space: nowrap;
}
table.dataTableHeader tbody td:last-child {
	border:0;
}
</style>

<script type="text/javascript">
app.controller('ScoreGenesController', ['$scope', '$http', 'CommonService', function ($scope, $http, CommonService) 
{
	// Inputs
	% if error:
	$scope.error = ${json.dumps(error) | n};
	
	% else:
	scoreTable = ${json.dumps(scoreTable) | n};
	commentsTable = ${json.dumps(commentsTable) |n};
	$scope.lineages = ${json.dumps(lineages) |n};
	$scope.lineageColours = ${json.dumps(lineageColours) |n};

	// used by dialog when a gene id selected
	$scope.selectedScoreTableRow = null;
	$scope.selectedComments = [];	// subset of commentsTable corresponding to a gene
	$scope.selectedScore = null;
	
	// allowed scores and shortComments
	$scope.scoreFilters = [{'name':'yes', 'value':true}, {'name':'no', 'value':false}, {'name':'more research required', 'value':true}];
	$scope.shortComments = ['Insufficient expression',
							'Cell surface predicted, no known function',
							'Cell surface confirmed, no known function',
							'Cell surface predicted, known function',
							'Cell surface confirmed, known function',
							'FTO',
							'Intracellular',
							'No Human Expression',
							'probe differences',
							'Ubiquitous'];
	$scope.selectedShortComment = null;
	
	// copy scoreTable to use for filtering
	$scope.filteredRows = scoreTable;
	$scope.shownRows = [].concat($scope.filteredRows);	// subset of filteredRows to show on paginated page. Note this copies references (see http://lorenzofox3.github.io/smart-table-website/, stSafeSrc)

	$scope.commonService = CommonService;
	$scope.rowsPerPage = 100;
	$scope.showDialog = false;

	// define initial slider value and set up slider
	$scope.sliderMin = 4;
	$scope.sliderMax = 10;		
	$scope.sliderValue = 5.5;
	
	var slider = d3.slider().min($scope.sliderMin).max($scope.sliderMax);	// floats don't render as ticks for some reason, so leave ticks out altogether
	slider.value($scope.sliderValue);
	d3.select('#slider').call(slider);
		
	slider.on("slide", function(evt, value) {
		$scope.sliderValue = value;
		if (!$scope.$$phase) $scope.$apply();
	});
	
	$scope.scaledOpacity = function(value) { 
		return value>$scope.sliderValue? 0.8*(1 + (value-$scope.sliderValue)/($scope.sliderMax-$scope.sliderValue)) : 
			0.3*(1 + (value-$scope.sliderValue)/($scope.sliderValue-$scope.sliderMin));
	}

	// filter rows based on scoreFilters
	$scope.filterRows = function()
	{
		// work out which scores to keep
		var scoresToKeep = $scope.scoreFilters.filter(function(d) { return d.value; }).map(function(d) { return d.name; });
		
		$scope.filteredRows = [];
		for (var i=0; i<scoreTable.length; i++) {
			if (scoresToKeep.indexOf(scoreTable[i].drugTargetScore)!=-1)
				$scope.filteredRows.push(scoreTable[i]);
		}
	}
	
	// Return the number of genes given score (eg. 'yes')
	$scope.numberOfGenes = function(score)
	{
		return scoreTable.filter(function(d) { return d.drugTargetScore==score; }).length;
	}
	
	// Should run when user clicks on either drug target score or comment - brings up dialog with details of score and comment for selected gene
	$scope.showScoreDialog = function(scoreTableRow)
	{
		$scope.selectedScoreTableRow = scoreTableRow;
		$scope.selectedScore = {'current':scoreTableRow.drugTargetScore, 'new':scoreTableRow.drugTargetScore};
		$scope.selectedShortComment = {'current':scoreTableRow.shortComment, 'new':scoreTableRow.shortComment};
		$scope.newComment = {'new':''};	// remember we have to use this trick to pass variable content from dialog back to controller

		// Find all comments matching scoreTableRow.geneId
		$scope.selectedComments = commentsTable.filter(function(d) { return d.geneId==scoreTableRow.geneId; });
		$scope.showDialog = true;
	}
	
	$scope.closeDialog = function() { $scope.showDialog = false; }

	// Save changes on the modal dialog
	$scope.saveChanges = function()
	{
		// gather changes
		var changes = {};
		if ($scope.selectedScore.new!=$scope.selectedScore.current) changes['score'] = $scope.selectedScore.new;
		if ($scope.selectedShortComment.new!=$scope.selectedShortComment.current) changes['short comment'] = $scope.selectedShortComment.new;
		if ($scope.newComment.new!='') changes['extended comment'] = $scope.newComment.new;
					   
		// show summary of changes
		var summary = ["You're about to make the following changes:\n"];
		for (var key in changes) 
			summary.push(key + ': ' + changes[key]);

		if (confirm(summary.join('\n'))) {
			changes['geneId'] = $scope.selectedScoreTableRow.geneId;
			CommonService.showLoadingImage();
			$http.post("/grouppages/CSL/scoregenes_save", changes).
				then(function(response) {	// get user from server
					CommonService.hideLoadingImage();
					$scope.closeDialog();
					
					// update matching row of scoreTable
					var scoreTableRow = scoreTable.filter(function(d) { return d.geneId==changes.geneId; })[0];
					scoreTableRow.drugTargetScore = $scope.selectedScore.new;
					scoreTableRow.shortComment = $scope.selectedShortComment.new;
					
					if ($scope.newComment.new!='') {	// append a new row into commentsTable
						commentsTable.push({'geneId':changes.geneId, 'user':response.user, 'date':response.date, 'comment':$scope.newComment.new, 'type':'plain'});
					}
				}, function(response) {
					CommonService.hideLoadingImage();
					alert("There was an unexpected error with save. Currently the save can't cope with unusual characters like accents in non-English names, so check if you have any of these characters in the comments.");
				});
		}
	}
	
	// Run on page load
	$scope.filterRows();
	
	% endif
		
}]);

</script>

</head>

<body>
<div id="wrap">
${common_elements.banner()}

	<div id="content">
		<div id="shadow"></div>
		<div style="margin-left:40px; margin-right:40px; overflow:auto;" ng-controller="ScoreGenesController">
			<h1 class="marquee">Hematlas ScoreGenes</h1>
			% if error:
			<p>{{error}}</p>
			% else:
			<table></table>
			
			<table st-table="shownRows" st-safe-src="filteredRows" class="dataTable" style="border-top:0px;">
				<thead>
				<tr style="background:white">
					<th colspan="7" style="border-left:0px; border-right:0px;">
						<table class="dataTableHeader"><tbody><tr>
							<td ng-repeat="score in scoreFilters">
								<input type="checkbox" ng-model="score.value" ng-click="filterRows()"/> {{score.name}} ({{numberOfGenes(score.name)}})
							</td>
							<td style="padding-left:50px;">lineage score colour cutoff ({{sliderValue.toFixed(2)}})</td>
							<td style="padding-left:10px;">{{sliderMin}}</td>
							<td><div id="slider" style="width:120px;"></div></td>
							<td>{{sliderMax}}</td>
							<td style="padding-left:50px;"><input st-search="" placeholder="search this table..." type="text"/></td>
						</tr></tbody></table>
					</th>
				</tr>
				<tr>
					<th st-sort="GeneSymbol">Gene Symbol</th>
					<th st-sort="previousGeneSymbol">Previous Symbol</th>
					<th st-sort="pubmedCount">Pubmed Count</th>
					<th st-sort="drugTargetScore">Drug Target Score</th>
					<th st-sort="shortComment">Comments</th>
					<th>External</th>
					<th>Lineage Score</th>
				</tr>
				</thead>
				<tbody>
				<tr ng-repeat="row in shownRows">
					<td><a href='/expression/show?geneId={{row["geneId"]}}' target="_blank">{{row['GeneSymbol']}}</a></td>
					<td>{{row['previousGeneSymbol']}}</td>
					<td>{{row['pubmedCount']}}</td>
					<td><a href ng-click="showScoreDialog(row)">{{row['drugTargetScore']}}</a></td>
					<td><a href ng-click="showScoreDialog(row)">{{row['shortComment']}}</a></td>
					<td>
						&nbsp;<a href='http://www.ncbi.nlm.nih.gov/sites/entrez?db=gene&term={{row.EntrezId}}' target="_blank" ng-mouseover="commonService.showTooltip('Go to Entrez site using gene id: '+row.EntrezId,$event)" ng-mouseout="commonService.hideTooltip()"><img src="/images/ncbi.ico" border="0"/></a>
						&nbsp;<a href='http://www.ensembl.org/Gene/Summary?g={{row.geneId}}' target="_blank" ng-mouseover="commonService.showTooltip('Go to Ensembl site using gene id: '+row.geneId,$event)" ng-mouseout="commonService.hideTooltip()"><img src="/images/ensembl.gif" border="0"/></a>
					</td>
					<td>
						<table class="barcode" style="border-collapse:collapse; border-spacing:0;"><tr>
							<td ng-repeat="lineage in lineages" style="width:15px; height:10px; border-top:1px solid #e6e6e6; background-color:{{lineageColours[lineage]}}; opacity:{{scaledOpacity(row.lineageValues[lineage])}};"></td>
						</tr></table>
					</td>
				</tr>
				</tbody>
				<tfoot>
					<td colspan="3" style="text-align:right; padding-top:20px;"><input type="text" ng-model="rowsPerPage" size="4"> rows per page</td>
					<td colspan="3" style="padding-left:50px;"><div st-pagination="" st-items-by-page="rowsPerPage" st-displayed-pages="7"></div></td>
				</tfoot>
			</table>
			
			<modal-dialog show='showDialog'>
				<div style="padding:10px; height:600px; overflow:auto;">
					<h3>Score editing for gene: <span style="color:#0000d8">{{selectedScoreTableRow.GeneSymbol}}</span></h3>
					<table>
						<tr><td style="padding-bottom:10px;">
							Change the score:
							<label ng-repeat="filter in scoreFilters">
								<input type="radio" ng-model="selectedScore.new" value="{{filter.name}}"/> {{filter.name}}
							</label>
						</td></tr>
						<tr><td style="padding-bottom:10px;">
							Change short comment: <input type="text" ng-show="shortComments.indexOf(selectedShortComment.current)==-1" ng-model="selectedShortComment.new"/> 
							<select ng-model="selectedShortComment.new" ng-options="item for item in shortComments">
						</td></tr>
						<tr><td style="overflow:auto;">
						<span ng-repeat="item in selectedComments">
							<b>{{item.user}}</b>, {{item.date | limitTo:16}}
							<p style="margin-top:5px; margin-bottom:20px;">{{item.comment}}</p>
						</span>
						</td></tr>
						<tr><td>
							Add Comments<br/>
							<textarea style="width:620px; height:150px; max-height:250px;" ng-model="newComment.new"></textarea>
						</td></tr>
					</table>
					<button ng-click="saveChanges()">save</button> <button ng-click="closeDialog()">close</button>
				</div>
			</model-dialog>
			% endif
		</div>
		<br style="clear:both;" />
	
	${common_elements.footer()}
	</div> <!-- content -->

</div> <!-- wrap -->  
</body>
</html>

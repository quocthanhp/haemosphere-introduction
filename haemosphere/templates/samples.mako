<%
'''
Inputs required
datasets: [{'name':'haemopedia', 'species':'MusMusculus'}, ...]
selectedDatasetName: 'haemopedia'
sampleTable: [{'sampleId':'sample1', 'celltype':'B', ...}, ...]
columns: ['sampleId','celltype',...]
sampleGroupsDisplayed: ['celltype','cell_lineage',...]   # subset of columns used for actual calculations and displays in haemosphere 
userIsAdmin: boolean
'''
import json
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<head>
<title>Haemosphere - Samples</title>

<%namespace name="common_elements" file="common.mako"/>
${common_elements.header_elements()}

<style type="text/css">
table.dataTable td {
	vertical-align:top;
}
ul.tabs {
	list-style: none;
	padding:0;
	margin:0;
}
ul.tabs li {
	display: inline;
	border: solid;
	border-width: 1px 1px 0 1px;
	margin: 0 0.5em 0 0;
}
ul.tabs li a {
	padding: 0 1em;
}
</style>

<script type="text/javascript">
app.controller('SamplesController', ['$scope', '$http', 'CommonService', function ($scope, $http, CommonService) 
{
	// Inputs
	$scope.datasets = ${json.dumps(datasets) | n};
	$scope.selectedDataset = $scope.datasets.filter(function(d) { return d.name=='${selectedDatasetName}'; })[0];
	$scope.sampleTable = ${json.dumps(sampleTable) | n};
	$scope.columns = ${json.dumps(columns) |n};
	$scope.sampleGroupsDisplayed = ${json.dumps(sampleGroupsDisplayed) |n};
	var guestUser = ${json.dumps(guestUser)};
	
	$scope.commonService = CommonService;
	$scope.helptext = "<div style='width:400px;'><b>Tips on using this page</b>" +
		"<ul style='padding-left:15px'><li>Some datasets have many columns here, so you can choose to hide some if you're not interested in all of them.</li>" + 
		'<li>If you are logged in, you can also select a subset of the samples here and create a dataset subset, which will be saved under your username for easier access later.</li></ul></div>';

	// dialog data needs an object for it to be two way binding (eg. array won't change the variable when selection made in dialog)
	$scope.dialogData = {'selectedColumns':{},
						 'sampleGroupsDisplayed':[],
						 'otherSampleGroups':[]};
						 
	$scope.closeDialog = function() { $scope.showDialog = false; }
	
	// For selecting dataset -------------------------------------------------------------
	$scope.changeDataset = function()
	{
		CommonService.showLoadingImage();
		window.location.assign('/datasets/samples?datasetName=' + $scope.selectedDataset.name);
		CommonService.hideLoadingImage();
	}	
	
	// For selecting rows ----------------------------------------------------------------
	$scope.selectedRows = {}; // {'CAGRF7126-1217': false, ...}
	for (var i=0; i<$scope.sampleTable.length; i++)
		$scope.selectedRows[$scope.sampleTable[i].sampleId] = false;
	
	// Set checkbox state for all shown rows. state should be true or false.
	$scope.setSelectedState = function(state)
	{
		for (var rowId in $scope.selectedRows)
			$scope.selectedRows[rowId] = state;
	}

	// For selecting columns -------------------------------------------------------------
	$scope.columnsToShow = $scope.columns;
	
	$scope.showSelectColumnsDialog = function()
	{
		for (var i=0; i<$scope.columns.length; i++)
			$scope.dialogData.selectedColumns[$scope.columns[i]] = $scope.columnsToShow.indexOf($scope.columns[i])!=-1;
		
		$scope.showDialog = true;
		$scope.selectColumnsDialog = true;
		$scope.subsetDialog = false;
	}

	$scope.selectColumns = function()
	{
		var selectedColumns = $scope.columns.filter(function(col) { return $scope.dialogData.selectedColumns[col]; });
		if (selectedColumns.length<2)
			alert("You have to show at least one column other than sampleId which is always shown.");
		else {
			$scope.columnsToShow = selectedColumns;
			$scope.closeDialog();
		}
	}
	
	// For creating a dataset subset -----------------------------------------------------
	$scope.showSubsetDialog = function()
	{
		// Disable this for now due to a bug
		alert("This function is currently disabled due to a bug. We will release a fix soon.");
		return;
		if (guestUser) {	// currently only for registered users
			alert("This function is only available to registered users since it stores the info under the user preferences.");
			return;
		}
		$scope.selectedSampleIds = Object.keys($scope.selectedRows).filter(function(key) { return $scope.selectedRows[key]; });
		if ($scope.selectedSampleIds.length>1) 
		{
			// create a list of "otherSampleGroups": these are sample groups which aren't originally a part of sampleGroupsDisplayed but
			// can be chosen by the user, but must not have any missing values for the samples selected
			$scope.dialogData['sampleGroupsDisplayed'] = $scope.sampleGroupsDisplayed;
			$scope.dialogData['otherSampleGroups'] = [];
			var selectedRows = $scope.sampleTable.filter(function(row) { return $scope.selectedRows[row.sampleId]; });
			
			for (var i=0; i<$scope.columns.length; i++) {
				if ($scope.columns[i]=='sampleId' || $scope.sampleGroupsDisplayed.indexOf($scope.columns[i])!=-1) continue;
				if (selectedRows.length == selectedRows.filter(function(row) { return row[$scope.columns[i]]!=''; }).length)
					$scope.dialogData['otherSampleGroups'].push($scope.columns[i]);
			}
			$scope.dialogData['subsetName'] = '';
			$scope.dialogData['subsetDescription'] = "[subset of " + $scope.selectedDataset.name + "]";
			
			$scope.showDialog = true;
			$scope.selectColumnsDialog = false;
			$scope.subsetDialog = true;
		}
		else 
			alert("You have to choose two or more samples to create a subset of this dataset.");
	}
	
	// Move column from one side to the other in the sample groups displayed definition within the dialog
	$scope.moveColumnToSampleGroupsDisplayed = function(column)
	{
		$scope.dialogData.sampleGroupsDisplayed.push(column);
		$scope.dialogData.otherSampleGroups.splice($scope.dialogData.otherSampleGroups.indexOf(column), 1);
	}
	$scope.moveColumnToOtherSampleGroups = function(column)
	{
		$scope.dialogData.otherSampleGroups.push(column);
		$scope.dialogData.sampleGroupsDisplayed.splice($scope.dialogData.sampleGroupsDisplayed.indexOf(column), 1);
	}
	
	$scope.createSubset = function()
	{
		if ($scope.dialogData['subsetName']=='') {
			alert("Name of the dataset subset can't be blank.");
		}
		else if ($scope.datasets.map(function(ds) { return ds.name; }).indexOf($scope.dialogData['subsetName'])!=-1) {
			alert("Dataset name already exists.");
		}
		else {
			CommonService.showLoadingImage();
			$http.post("/datasets/createsubset", { "datasetName": $scope.selectedDataset.name,
												   "subsetName": $scope.dialogData['subsetName'], 
												   "subsetDescription": $scope.dialogData['subsetDescription'], 
												   "sampleIds": $scope.selectedSampleIds,
												   "sampleGroupsDisplayed": $scope.dialogData['sampleGroupsDisplayed']}).
				then(function(response) {	
					CommonService.hideLoadingImage();
					$scope.showDialog = false;
					alert("Successfully saved this dataset subset.");
				}, function(response) {
					CommonService.hideLoadingImage();
					$scope.showDialog = false;
					alert('There was an unexpected error while saving this dataset subset.');
				});
		}
	}
	
	// Because we have dynamic columns when a dataset is selected, st-sort doesn't work. So we do our own sorting here.
	$scope.sortedColumn = null;	// currently sorted column
	$scope.sortDirection = 1;	// +1 for ascending, -1 for descending
	$scope.sortColumn = function(column)
	{
		// any rows with missing columns will cause weird behaviour when sorting, since the sort algorithm seems to 
		// use the first element of sorted row to determine the columns to show
		
		if ($scope.sortedColumn==column) {	// clicked on currently sorted column, so change sort direction
			$scope.sortDirection *= -1;	// so 1 will become -1, vice versa
		}
		else {	// clicked on a column not currently sorted, so set currently sorted column to this one
			$scope.sortedColumn = column;
			$scope.sortDirection = 1;
		}
				
		$scope.sampleTable.sort(function(a,b) { 
			if (a[column]<b[column]) return -1*$scope.sortDirection;
			else if (a[column]>b[column]) return 1*$scope.sortDirection;
			else return 0;
		});
	}
		
}]);

</script>

</head>

<body>
<div id="wrap">
${common_elements.banner()}

	<div id="content">
		<div id="shadow"></div>

		<div style="margin-left:40px; margin-right:40px;" ng-controller="SamplesController">
		
			<h1 class="marquee">Table of samples</h1>
			<div>
				<select ng-model="selectedDataset" ng-options="ds.name group by ds.species for ds in datasets" ng-change="changeDataset()"></select>
				<a href="#" ng-click="showSelectColumnsDialog()" style="margin-left:50px;">{{columnsToShow.length}} out of {{columns.length}} columns shown</a>
				&nbsp; &#47; &nbsp;
				<a href="#" ng-click="showSubsetDialog()">create subset</a>
				<img src="/images/question_mark.png" ng-mouseover="commonService.showTooltip(helptext,$event)" ng-mouseout="commonService.hideTooltip()" width="20px" height="20px" style="margin-bottom:-5px; margin-left:10px;">
			</div>
			<div style="overflow:auto;">
			<table st-table="sampleTable" class="dataTable">
				<thead>
				</thead>
				<tbody style="overflow:inherit;">
				<tr style="background-color:#d0ddf5;">
					<td><a href ng-click="setSelectedState(true)">all</a> &#47; <a href ng-click="setSelectedState(false)">none</a></td>
					<td ng-repeat="column in columnsToShow" 
						ng-click="sortColumn(column)" 
						ng-class="sortedColumn==column? (sortDirection>0? 'st-sort-ascent' : 'st-sort-descent') : ''">{{column}}
					</td>
				</tr>
				<tr ng-repeat="row in sampleTable">
					<td><input type="checkbox" ng-model="selectedRows[row.sampleId]"></td>
					<td ng-repeat="column in columnsToShow" ng-dblclick="updateField($parent.$index,column)">
						<a href="http://www.ncbi.nlm.nih.gov/pubmed/?term={{row[column].split(';')[1]}}" target="_blank" ng-if="column=='firstPublished'">{{row[column].split(';')[0]}}</a>
						<span ng-if="column!='firstPublished'">{{row[column]}}</span>
					</td>
				</tr>
				</tbody>
				<tfoot>
				</tfoot>
			</table>
			</div>
	
		<modal-dialog show='showDialog'>
			<div ng-show="selectColumnsDialog" style="padding:10px;">
				<h3>Select columns to show</h3>
				<p>Some datasets have many columns and it may be convenient to show/hide some columns.</p>
				<div style="height:320px; overflow:auto;">
					<table class="smallTable" cellspacing="0">
					<thead>
						<tr>
							<th>select</th>
							<th>column</th>
						</tr>
					</thead>
					<tbody>
						<tr ng-repeat="column in columns">
							<td><input type="checkbox" ng-model="dialogData.selectedColumns[column]" ng-disabled="column=='sampleId'"></td>
							<td>{{column}}</td>
						</tr>
					</tbody>
					</table>
				</div>
				<button ng-click="selectColumns()" style="margin-top:20px;">select</button>			
			</div>
			<div ng-show="subsetDialog" style="padding:10px;">
				<h3>Create a dataset subset</h3>
				<p>You can create a subset of this dataset using only the samples you've selected. Review your choices here and proceed.</p>
				<p>Number of samples selected: <strong>{{selectedSampleIds.length}}</strong></p>
				<p>You can choose to define "displayed sample groups" here for this subset. These are special sample groups used by haemosphere for various
				functions, such as grouping values for the expression profile plot or using them in differential expression analysis.
				The default ones are those inherited from the current dataset, but you may choose to edit these. Note that you can't have missing values for 
				any of the samples in these sample groups, so only the allowed sample groups are shown here. Click on each item to move it from one side to the other.</p>
				<div style="height:200px; overflow:auto;">
				<table class="smallTable" cellspacing="0">
					<thead><tr><th>other sample groups</th><th>displayed sample groups</th></tr></thead>
					<tbody><tr>
					<td style="padding:10px; vertical-align:top;"><p ng-repeat="column in dialogData.otherSampleGroups">
						<a href="#" ng-click="moveColumnToSampleGroupsDisplayed(column)">{{column}}</a>
					</p></td>
					<td style="padding:10px; vertical-align:top"><p ng-repeat="column in dialogData.sampleGroupsDisplayed">
						<a href="#" ng-click="moveColumnToOtherSampleGroups(column)">{{column}}</a>
					</p></td>
					</tr></tbody>
				</table>
				</div>
				<p>Name of the dataset (must be unique): <input type="text" ng-model="dialogData.subsetName"></p>
				<p>Description (helps you later to identify what you did): <input type="text" ng-model="dialogData.subsetDescription" size="60"></p>
				<button ng-click="createSubset()" style="margin-top:20px;">continue</button>
			</div>
			<p style="padding:10px;"><button ng-click="closeDialog()" style="float:right;">close</button>
		</modal-dialog>
		
		</div> <!-- SamplesController -->
		<br style="clear:both;" />
		
		${common_elements.footer()}
	</div> <!-- content -->

</div> <!-- wrap -->  
</body>
</html>

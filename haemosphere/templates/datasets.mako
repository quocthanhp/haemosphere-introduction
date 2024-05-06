<%
'''
Inputs required
datasets: [{'name':'haemopedia', 'species':'MusMusculus', ...}, ...]	# subset of allDatasets user has selected
allDatasets: [{'name':'haemopedia', 'species':'MusMusculus', ...}, ...]	# all datasets user has access to
guestUser: boolean
'''
import json
env = request.registry.settings['haemosphere.env']   # {'dev','private','public'}
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<head>
<title>Haemosphere - Datasets</title>

<%namespace name="common_elements" file="common.mako"/>
${common_elements.header_elements()}

<style type="text/css">
</style>

<script type="text/javascript">
app.controller('DatasetsController', ['$scope', '$http', 'CommonService', function ($scope, $http, CommonService) 
{
	// Inputs
	$scope.datasets = ${json.dumps(datasets) | n};
	$scope.allDatasets = ${json.dumps(allDatasets) | n};
	$scope.selectedDataset = $scope.datasets[0];	// for dialog selection
	var guestUser = ${json.dumps(guestUser)};
	
	$scope.commonService = CommonService;
	$scope.actions = ["select datasets...", "order datasets..."];
	$scope.selectionAction = null;
	
	// Set up dialog variables
	$scope.dialogData = {'selectedDatasets':{}, 'datasetOrdering':[]};
	$scope.showDownloadDatasetDialog = false;
	$scope.closeDialog = function() { 
		$scope.showDownloadDatasetDialog = false;
		$scope.showSelectDatasetsDialog = false;
		$scope.showOrderDatasetsDialog = false;
	}
	
	// Run this function when an action is selected
	$scope.setAction = function()
	{
		if (guestUser) {	// currently all functions in the actions only useful for registered users
			alert("These functions are only available to registered users since these work as user preferences.");
		}
		else if ($scope.selectedAction=="select datasets...") 
		{
			for (var i=0; i<$scope.allDatasets.length; i++)
				$scope.dialogData.selectedDatasets[$scope.allDatasets[i].name] = $scope.datasets.map(function(ds) { return ds.name; }).indexOf($scope.allDatasets[i].name)!=-1;
			$scope.showSelectDatasetsDialog = true;
		}
		else if ($scope.selectedAction=="order datasets...") 
		{
			$scope.dialogData.datasetOrdering = $scope.datasets.map(function(ds) { return ds.name; });
			$scope.showOrderDatasetsDialog = true;
		}
		$scope.selectedAction = null;
	}

	$scope.helptext = "<b>Tips on using this page</b>" +
		"<p>[click on me for a quick tour of this page]</p>" +
		"<ul style='padding-left:15px'><li>You can sort columns by clicking on column header.</li>" + 
		"<li>Click on the dataset name to perform sample distance analysis.</li>" +
		"<li>Click on the link in the Samples column to show sample table for the dataset. If you are a registered user, you can create custom data subsets here.</li>" +
		"<li>Click on the Download link in the Tools column to download the expression data and sample table.</li>" +
		'<li>Version here refers to the internal dataset version number used by Haemosphere.</li></ul>';

	// For downloading datasets ------------------------------------------------------------
	$scope.showDownloadDialog = function(dataset)
	{
		$scope.selectedDataset = dataset;
		$scope.showDownloadDatasetDialog = true;
	}
	
	$scope.downloadFile = function(datasetFile)
	{
		CommonService.showLoadingImage();
		window.location.assign("/downloadfile?&filetype=dataset&datasetName=" + $scope.selectedDataset.name + "&datasetFile=" + datasetFile);
		CommonService.hideLoadingImage();
	}

	// For selecting datasets ------------------------------------------------------------
	// Set checkbox state for all rows in showSelectDatasetDialog. state should be true or false.
	$scope.setSelectedState = function(state)
	{
		for (var dsname in $scope.dialogData.selectedDatasets)
			$scope.dialogData.selectedDatasets[dsname] = state;
	}

	$scope.applySelections = function()
	{
		var selectedDatasets = $scope.allDatasets.filter(function(ds) { return $scope.dialogData.selectedDatasets[ds.name]; });
		if (selectedDatasets.length==0) {
			alert("You have to select at least one dataset.");
		}
		else {   
			CommonService.showLoadingImage();
			$http.post("/datasets/select", { "datasetNames": selectedDatasets.map(function(ds) { return ds.name; }) }).
				then(function(response) {	
					// reload page
					window.location.assign("/datasets/show");
				}, function(response) {
					CommonService.hideLoadingImage();
					alert('There was an unexpected error while trying to select these datasets.');
				});
		}
	}
		
	// For dataset ordering --------------------------------------------------------------
	// These functions move items up/down for ordering of datasets in the dialog - the ordering isn't committed until apply button is pressed
	$scope.moveItemUp = function(index)
	{
		if (index==0) return;
		$scope.dialogData.datasetOrdering[index] = $scope.dialogData.datasetOrdering.splice(index-1, 1, $scope.dialogData.datasetOrdering[index])[0];
	}
	$scope.moveItemDown = function(index)
	{
		if (index==$scope.dialogData.datasetOrdering.length-1) return;
		$scope.dialogData.datasetOrdering[index] = $scope.dialogData.datasetOrdering.splice(index+1, 1, $scope.dialogData.datasetOrdering[index])[0];
	}
	
	// Function to actually apply ordering
	$scope.applyOrdering = function()
	{
		CommonService.showLoadingImage();
		$http.post("/datasets/order", { "datasetOrdering": $scope.dialogData.datasetOrdering }).
			then(function(response) {
				// reload page
				window.location.assign("/datasets/show");
			}, function(response) {
				CommonService.hideLoadingImage();
				alert('There was an unexpected error while trying to order these datasets.');
			});
	}
	
}]);

</script>

</head>

<body>
<div id="wrap">  
${common_elements.banner()}

	<div id="content">
		${common_elements.flashMessage('accesserror')}
		<div id="shadow"></div>
		<div style="margin-left:40px; margin-right:40px;" ng-controller="DatasetsController">
			<h1 class="marquee" style="display:inline">Datasets</h1>
			<img src="/images/question_mark.png" ng-mouseover="commonService.showTooltip(helptext,$event)" ng-mouseout="commonService.hideTooltip()" 
				onclick="javascript:introJs('#content').start();" width="20px" height="20px" style="margin-left:10px; margin-right:10px;">
			<select ng-model="selectedAction" ng-options="action for action in actions" ng-change="setAction()">
				<option value="" disabled="disabled">action...</option>
			</select>
			<table st-table="datasets" class="dataTable">
				<thead>
				<tr>
					<th st-sort="name" style="width:150px;">Name</th>
					<th st-sort="description" style="width:500px">Description</th>
					<th st-sort="platform_type" style="width:80px;">Platform</th>
					<th st-sort="platform_details" style="width:300px;">Platform Details</th>
					<th st-sort="species" style="width:80px;">Species</th>
					<th st-sort="pubmed_id" style="width:80px;">Published</th>
					<th st-sort="sampleNumber" style="width:50px;" data-step="4" data-intro="Click on a column header to sort the table.">Samples</th>
					<th st-sort="version" style="width:50px;">Version</th>
					<th style="width:50px;">Tools</th>
				</tr>
				</thead>
				<tbody>
				<tr ng-repeat="row in datasets" style="background-color:{{row.species=='MusMusculus'? '#fdf6f5' : '#fff'}}">
					<td style="width:148px;" ng-attr-data-step="{{$index==0? 1 : undefined}}" ng-attr-data-intro="{{$index==0? 'Click here to plot sample relationships.': undefined}}">
						<a href="/datasets/analyse?datasetName={{row.name}}" 
							ng-mouseover="commonService.showTooltip('View Multidimensional scaling (MDS) plot for this dataset.',$event)" 
							ng-mouseout="commonService.hideTooltip()">{{row.name}}
						</a>
						<span ng-show="row.parent!=null">
							<a href="#" ng-mouseover="commonService.showTooltip('subset of ' + row.parent,$event)" ng-mouseout="commonService.hideTooltip()">&#42;</a>
						</span>
					</td>
					<td style="width:498px">{{row.description}}</td>
					<td style="width:78px;">{{row.platform_type}}</td>
					<td style="width:298px;">{{row.platform_details}}</td>
					<td style="width:78px;">{{row.species}}</td>
					<td style="width:78px;">
						<span ng-show="row.pubmed_id!=''">
							<a href='http://www.ncbi.nlm.nih.gov/pubmed/?term={{row.pubmed_id}}' target="_blank" 
								ng-mouseover="commonService.showTooltip('Go to pubmed website for this dataset.',$event)" 
								ng-mouseout="commonService.hideTooltip()">pubmed
							</a>
						</span>
						<span ng-show="row.pubmed_id==''">no</span>
					</td>
					<td style="width:48px;">
						<a href="/datasets/samples?datasetName={{row.name}}"
 							ng-attr-data-step="{{$index==0? 2 : undefined}}" ng-attr-data-intro="{{$index==0? 'Click here to show sample table.': undefined}}"
 							ng-mouseover="commonService.showTooltip('Show table of samples for this dataset.',$event)" 
							ng-mouseout="commonService.hideTooltip()">{{row.sampleNumber}}</a></td>
					<td style="width:50px;">{{row.version}}</td>
					<td style="width:48px;">
						<a href="#" ng-click="showDownloadDialog(row)" 
 							ng-attr-data-step="{{$index==0? 3 : undefined}}" ng-attr-data-intro="{{$index==0? 'Click here to show download data dialog.': undefined}}"
							ng-mouseover="commonService.showTooltip('Download expression matrix and sample data as text files.',$event)" 
							ng-mouseout="commonService.hideTooltip()">download...
						</a>
					</td>
				</tr>
				</tbody>
			</table>
			<modal-dialog show='showDownloadDatasetDialog'>
				<div style="padding:10px;">
					<h3>Download data for: {{selectedDataset.name}}</h3>
					<p>You can download expression matrix and sample data here as text files.</p>
					<ul>
						<li ng-show="selectedDataset.isRnaSeqData"><a href='#' ng-click="downloadFile('raw')">raw counts summarised at genes</a></li>
						<li ng-show="selectedDataset.isRnaSeqData"><a href='#' ng-click="downloadFile('cpm')">cpm values</a></li>
						<li ng-show="selectedDataset.isRnaSeqData"><a href='#' ng-click="downloadFile('tpm')">tpm values</a></li>
						<li ng-show="!selectedDataset.isRnaSeqData"><a href='#' ng-click="downloadFile('expression')">expression matrix</a></li>
						<li ng-show="!selectedDataset.isRnaSeqData"><a href='#' ng-click="downloadFile('probes')">probe id to gene id mapping</a></li>
						<li><a href='#' ng-click="downloadFile('samples')">sample table</a></li>
					</ul>
					<p><button ng-click="closeDialog()">close</button></p>
				</div>
			</modal-dialog>
			<modal-dialog show='showSelectDatasetsDialog'>
				<div style="padding:10px; height:600px; overflow:auto;">
					<h3>Select datasets</h3>
					<p>You can select datasets to show here, which will also be used in all other pages where datasets are displayed.</p>
					<table st-table="allDatasets" class="dataTable">
						<thead><tr>
							<th><a href ng-click="setSelectedState(true)">all</a> &#47; <a href ng-click="setSelectedState(false)">none</a></th>
							<th st-sort="name">name</th>
							<th st-sort="species">species</th>
							<th st-sort="platform_type">platform</th>
						</tr></thead>
						<tbody style="height:350px;"><tr ng-repeat="ds in allDatasets">
							<td><input type="checkbox" ng-model="dialogData.selectedDatasets[ds.name]"></td>
							<td>{{ds.name}}</td>
							<td>{{ds.species}}</td>
							<td>{{ds.platform_type}}</td>
						</tr></tbody>
					</table>
					<p><button ng-click="applySelections()">apply</button><button ng-click="closeDialog()">close</button></p>
				</div>
			</modal-dialog>
			<modal-dialog show='showOrderDatasetsDialog'>
				<div style="padding:10px;">
					<h3>Order datasets</h3>
					<p>You can set ordering of datasets here, which will be used in all other pages where datasets are displayed.</p>
					<div style="height:350px; overflow:auto;">
						<table class="smallTable">
							<thead><tr><th>dataset</th><th>order</th></tr></thead>
							<tbody><tr ng-repeat="name in dialogData.datasetOrdering">
								<td>{{name}}</td>
								<td><a href="#" ng-click="moveItemUp($index)" style="font-size:16px; font-weight:bold">&uarr;</a> &nbsp; &nbsp;
									<a href="#" ng-click="moveItemDown($index)" style="font-size:16px; font-weight:bold">&darr;</a></td>
							</tr></tbody>
						</table>
					</div>
					<p><button ng-click="applyOrdering()">apply</button><button ng-click="closeDialog()">close</button></p>
				</div>
			</modal-dialog>
		</div> <!-- DatasetsController -->
		<br style="clear:both;" />
	
	${common_elements.footer()}
	</div> <!-- content -->

</div> <!-- wrap -->  
</body>
</html>

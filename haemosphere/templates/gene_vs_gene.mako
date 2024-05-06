<%
import json
'''
list of all variables used by this mako template:
error (str)
datasets (list of dict)
selectedDatasetName (str)
geneIds (list of str)
genes (list of dict)
allGenes (list of dict)
lineages (list of str)
lineageColours (dict)
celltypesFromLineage (dict)
valuesFromLineage (dict)
correlationsFromLineage (dict)
'''
def decode_b(t):
    return t.decode('utf-8')
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<head>
<title>Haemosphere - Gene vs Gene Expression Profile</title>

<%namespace name="common_elements" file="common.mako"/>
${common_elements.header_elements()}

<script type="text/javascript" src="/js/plotly.min.js"></script>

<style type="text/css">
h1 {
	display: inline;
}

.axis text, .legend text {
  font: 10px sans-serif;
}
.axis path,
.axis line {
  fill: none;
  stroke: #000;
  shape-rendering: crispEdges;
}


</style>

<script type="text/javascript">
app.controller('GeneVsGeneController', ['$scope', '$http', '$httpParamSerializerJQLike', 'CommonService', function($scope, $http, $httpParamSerializerJQLike, CommonService) 
{	
	$scope.commonService = CommonService;

	// Inputs from python
	$scope.error = ${json.dumps(error) | n};
	$scope.datasets = ${json.dumps(datasets) | n};
	var selectedDatasetName = ${json.dumps(selectedDatasetName) | n};
	var geneIds = ${json.dumps(geneIds) | n};
	var genes = ${json.dumps(genes) | n};
	var allGenes = ${json.dumps(allGenes) | n};
	var lineages = ${json.dumps(lineages) | n};
	var lineageColours = ${json.dumps(lineageColours, default=decode_b, indent=4) | n};
	var celltypesFromLineage = ${json.dumps(celltypesFromLineage) | n};
	var valuesFromLineage = ${json.dumps(valuesFromLineage) | n};
	$scope.correlationsFromLineage = ${json.dumps(correlationsFromLineage) | n};

	// Derived variables
	$scope.selectedDataset = $scope.datasets.find(function(x) { return x.name==selectedDatasetName});
	$scope.genes = [];
	for (var i=0; i<geneIds.length; i++) {
		$scope.genes.push(genes.find(function(x) { return x.EnsemblId==geneIds[i] }));
	}
	$scope.filteredGenes = [];
	$scope.selectedGene = $scope.genes[0];
	$scope.selectedGeneIndex = 0;
	$scope.setSameScale = true;
	$scope.helptext = "<div style='width:400px;'><h3>Tips on using this page</h3>"
			+ "<ul style='margin-top:0px;'>"
			+ "<li>Click on the gene symbol to bring up a dialog where you can change the gene.</li>"
			+ "<li>Changing the dataset will reload the page and plot the same genes in the selected dataset.</li>"
			+ "<li>A gene which is not contained in a selected dataset is not shown. Instead another abitrary gene will be chosen.</li>"
			+ "<li>The numbers in the brackets of the legend show the number of points and the pearson correlation for those which belong to that lineage only. "
			+ "This value is only calculated for lineages with 3 or more cell types, and gives a better estimate the more number of cell types a lineage has.</li>"
			+ "<li>The plot is interactive, with selectable legends, zoom, hover and more. To remove a lineage click on its name in the legend, to show only that lineage, double click on it. Hovering over the plot also provides a number of options for saving and editing the plot. </li>"
			+ "</ul></div>";

	$scope.drawPlot = function()
	{	
		if ($scope.error!="") return;

		// One trace per lineage
		var traces = [];
		for (var i=0; i<lineages.length; i++) {
			var corr = $scope.correlationsFromLineage[lineages[i]];
			corrString = corr==null? '' : corr.toFixed(2);
			traces.push({x: valuesFromLineage[geneIds[0]][lineages[i]], 
						 y: valuesFromLineage[geneIds[1]][lineages[i]], 
						 type: "scatter", mode: "markers", text: celltypesFromLineage[lineages[i]],
						 marker: {color: lineageColours[lineages[i]]},
						 name: lineages[i] + "<span style='color:#ccc'> (" + celltypesFromLineage[lineages[i]].length + ", " + corrString + ")</span>",
						 hoverinfo: "text"});
		}
		
		corr = $scope.correlationsFromLineage["all"];
		corrString = corr==null? 'NA' : corr.toFixed(2);
		var layout = {xaxis: {title: $scope.genes[0].GeneSymbol},
					  yaxis: {title: $scope.genes[1].GeneSymbol},
					  title: "overall pearson correlation: " + corrString};

		var plotDiv = document.getElementById("gvgPlotDiv");
		var plot = Plotly.newPlot(plotDiv, traces, layout);

		// If setSameScale is true, we want to use the same range for x and y axis. However, we can't get the current
		// values of these ranges after the plot has been completed, so use an event here.
		plotDiv.on('plotly_afterplot', function() {
			var update = {};
			if ($scope.setSameScale) {
				var min = Math.min(...[layout.xaxis.range[0], layout.yaxis.range[0]]);
				var max = Math.max(...[layout.xaxis.range[1], layout.yaxis.range[1]]);
				update = {'xaxis.range': [min,max], 'yaxis.range': [min,max]};
			}
			Plotly.relayout(plotDiv, update);
		});
	}

	$scope.showGeneDialog = function(gene)
	{
		$scope.selectedGene = gene;
		d3.selectAll("div#geneDialogDiv")
			.style({"opacity":0.9, "padding":"20px", "width":"450px", "left":"50%", "top":"50%", "transform":"translate(-50%, -50%)", "-webkit-transform":"translate(-50%, -50%)", "-moz-transform":"translate(-50%, -50%)"});
	}

	$scope.hideGeneDialog = function()
	{
		d3.selectAll("div#geneDialogDiv").style({"opacity":0, "padding":null, "left":null, "top":null});	
	}

	$scope.filterGeneListTable = function()
	{
		var filter = $scope.geneFilterValue.toUpperCase();
		$scope.filteredGenes = [];
		if (filter.length<2) return;
		for (var i=0; i<allGenes.length; i++)
			if (allGenes[i].GeneSymbol.toUpperCase().indexOf(filter)>-1)
				$scope.filteredGenes.push(allGenes[i]);
	}

	$scope.reloadPage = function(geneId)
	{
		var newGeneIds = [];
		if (geneId!=null) {	// find which of geneIds should be replaced by looking at index
			newGeneIds = geneIds.map(function(x,i) { return i==$scope.selectedGeneIndex? geneId : x});
		} else {
			newGeneIds = geneIds;
		}

		if ($scope.selectedDataset.species!=$scope.selectedGene.Species) {
			var response = confirm("You have selected a dataset with different species to the selected genes. "
								+ "Click OK to load the dataset with some default genes.");
			if (response)
				newGeneIds = [];
			else {  // put selectedDataset back to original
				$scope.selectedDataset = $scope.datasets.find(function(x) { return x.name==selectedDatasetName});
				return;
			}
		}

		$scope.commonService.showLoadingImage();
		if (newGeneIds.length>0)
			window.location.assign("/expression/genevsgene?gene1=" + newGeneIds[0] + "&gene2=" + newGeneIds[1] + "&datasetName=" + $scope.selectedDataset.name);
		else
			window.location.assign("/expression/genevsgene?datasetName=" + $scope.selectedDataset.name);
	}

	$scope.drawPlot();
}]);
	
</script>

</head>

<body>
<div id="wrap">  
${common_elements.banner()}

<div id="content" ng-controller="GeneVsGeneController">
<div id="shadow"></div>
		
<div style="text-align:center;">
	<h1 class="marquee">
		<a href ng-click="selectedGeneIndex=0; showGeneDialog(genes[0])">{{genes[0].GeneSymbol}}</a>
	</h1> &nbsp; 
	<span style="font-size:14px;">vs</span> &nbsp; 
	<h1 class="marquee">
		<a href ng-click="selectedGeneIndex=1; showGeneDialog(genes[1])">{{genes[1].GeneSymbol}}</a>
	</h1>
	<img src="/images/question_mark.png" ng-mouseover="commonService.showTooltip(helptext,$event)" ng-mouseout="commonService.hideTooltip()" 
		width="20px" height="20px" style="margin-left:10px; margin-top:4px; opacity:0.7">
	<p style="margin-top:30px;">dataset: 
		<select ng-model="selectedDataset" ng-options="ds.name group by ds.species for ds in datasets" ng-change="reloadPage()"></select>
		<input type="checkbox" ng-model="setSameScale" style="margin-left:30px;" ng-change="drawPlot()">use same x-y scales
	</p>
	<div ng-show="error!=''" style="margin-top:50px;"><p>{{error}}</p></div>
	<div id="gvgPlotDiv" style="width:850px; height:550px; margin-left:auto; margin-right:auto; margin-top:30px; overflow:auto;"></div>
	<div id="geneDialogDiv" style="opacity:0; background:#fff; z-index:10000; position:fixed; box-shadow:4px 4px 40px #000;">
		<div style="float:right"><a href="#" style="text-decoration:none; color:#ccc" ng-click="hideGeneDialog();">&#10006;</a></div>
		<h2>Select another gene here</h2>
		<table style="text-align:left; margin-top:30px;">
			<tr>
				<td style="padding-right:10px; vertical-align:top;">
					Currently selected: <a style="font-size:16px;" href="/expression/show?geneId={{selectedGene.EnsemblId}}">{{selectedGene.GeneSymbol}}</a>
					<p><b>description:</b> {{selectedGene.Description}}</p>
					<p><b>Ensembl id:</b> <a href='http://www.ensembl.org/Gene/Summary?g={{selectedGene.EnsemblId}}' target='_blank'>{{selectedGene.EnsemblId}}</a></p>
					<p>Start searching for genes in this dataset. The table on the right will autofill with matching genes once there are
					2 or more characters in the search field. Clicking on one of the fetched genes will reload this page, 
					after replacing this gene with the selection.</p>
				</td>
				<td>
					<input type="text" ng-model="geneFilterValue" ng-keyup="filterGeneListTable()" placeholder="search.." style="width:140px;"><br/>
					<table style="display:block; width:150px; height:400px; overflow-y:scroll; border:1px solid grey; margin-top:10px;">
						<tr ng-repeat="gene in filteredGenes">
							<td><a href="#" ng-click="reloadPage(gene.EnsemblId)">{{gene.GeneSymbol}}</a></td>
						</tr>
					</table>
				<td>
			</tr>
		</table>
	</div>
</div>

<div style="clear:both;"></div>

	
${common_elements.footer()}
</div> <!-- content -->

<div></div>  <!-- dialogs -->

</div> <!-- wrap -->  
</body>
</html>

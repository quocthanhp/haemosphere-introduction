<%
import json
'''
list of all variables used by this mako template:
error
ePref
geneset
datasets
selectedDatasetName
expressionValues
valueRange
featureGroups
groupByItems
sampleGroupItems
selectedGroupByItem
selectedColourByItem
sampleIdsFromSampleGroups
sampleGroupColours
sampleGroupOrderedItems
valueAxisLabel
groupAxisLabel
allGenes (list of dict)
'''
def decode_b(t):
    return t.decode('utf-8')
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<head>
<title>Haemosphere - Expression Profile Page</title>

<%namespace name="common_elements" file="common.mako"/>
${common_elements.header_elements()}
<script type="text/javascript" src="/js/expbarplot.js"></script>

<script type="text/javascript" src="/js/canvg/rgbcolor.js"></script> 
<script type="text/javascript" src="/js/canvg/StackBlur.js"></script>
<script type="text/javascript" src="/js/canvg/canvg.min.js"></script> 

<style type="text/css">
.geneSymbol{
	border:solid 1px #ccc;
	color:#688;
	height:1em;
	padding: 5px;
	background:#fff;
	text-align:center;
	text-decoration:none;
}
.geneSymbol:hover{
	background:#e6e6e6;
}

.geneSymbol a {
	color:#688;
	text-decoration:none;
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
#controlPanelDiv a {
	color: #688;
}
#controlPanelDiv a:hover {
	color: #ffcc66;
}
</style>

<script type="text/javascript">
app.controller('ExpressionController', ['$scope', '$http', '$httpParamSerializerJQLike', 'CommonService', function($scope, $http, $httpParamSerializerJQLike, CommonService) 
{	
	$scope.commonService = CommonService;
	
	// Inputs from python
	$scope.error = "${error if error else ''}";	
	$scope.genes = ${geneset | n};
	$scope.datasets = ${json.dumps(datasets) | n};
	$scope.selectedDataset = $scope.datasets.filter(function(d) { return d.name=='${selectedDatasetName}'; })[0];
	$scope.groupByItems = ${json.dumps(groupByItems) | n};	// ['celltype','cell_lineage',...]
	$scope.colourByItems = [];	// will be populated below
	var sampleGroupItems = ${json.dumps(sampleGroupItems, default=decode_b, indent=4) | n};	// {'cell_lineage': {}, 'celltype': {'cell_lineage': {'Cell Line':['FD',...], ... }, ... }, ... }
	var sampleIdsFromSampleGroups = ${json.dumps(sampleIdsFromSampleGroups) | n};
	var sampleGroupColours = ${json.dumps(sampleGroupColours, default=decode_b, indent=4) | n};
	var sampleGroupOrderedItems = ${json.dumps(sampleGroupOrderedItems) | n};
	$scope.selectedGroupByItem = $scope.groupByItems.filter(function(d) { return d=='${selectedGroupByItem}'; })[0];
	$scope.selectedColourByItem = null;
	var allGenes = ${json.dumps(allGenes) | n};
	
	var expressionValues = ${json.dumps(expressionValues) | n};
	var valueRange = ${json.dumps(valueRange) | n};
	var featureGroups = ${json.dumps(featureGroups) | n};
	var valueAxisLabel = '${valueAxisLabel}';
	var groupAxisLabel = '${groupAxisLabel}';
	
	$scope.persistentGeneInfoDiv = false;	// Used to persistently show geneInfoDiv 
	$scope.showExportDialog = false;
	$scope.exportText = '';
	$scope.helptext = "<div style='width:700px;'><h3>Tips on using this page</h3>"
			+ "<p>[click on me for a quick tour of this page]</p>"
			+ "<ul style='margin-top:0px;'>"
			+ "<li>Hover over the gene symbol to get details about the gene. Clicking on the symbol will make the popup stay open.</li>"
			+ "<li>You can change to a different gene in the current dataset by using the same popup.</li>"
			+ "<li>The plot is automatically a bar plot if only one feature is present. For a line plot, click on a line or a label to see bar plot.</li>"
			+ "<li>On the bar plot, multiple bars under the same colour by item can be grouped into one bar by clicking on the corresponding label in the legend area.</li>"
			+ "<li>Find similar will return a new geneset with 200 most correlated genes (100 positive and 100 negative correlations) for selected dataset.</li>"
			+ "</ul>";
	if ($scope.error=='' && !$scope.selectedDataset.rnaseq)  // for microarray data, talk about min value
		$scope.helptext += "<b>Minimum value for all probes in this dataset (" + $scope.selectedDataset.name + "):</b> " 
				+ valueRange[0] + "<br>(This is used to set the minimum value for each microarray dataset)";
		$scope.helptext += "</div>";
	$scope.actions = ["Functions...", "multi species plot", "find similar genes", "gene vs gene plot", "export data", "save figure"];
	$scope.selectedAction = $scope.actions[0];
	$scope.filteredGenes = [];
	
	// ExpressionPlot instance
	var expressionPlot = new expbarplot.ExpressionBarplot({'targetDiv':"#expression-div", 'legendDiv':"#legend-div", 'controlPanelDiv':"#controlPanelDiv",
		'showTooltipFunction':CommonService.showTooltip, 'hideTooltipFunction':CommonService.hideTooltip, 'minTickInterval':1});

	// Should trigger when group by items changes to update colour by items appropriately
	$scope.setColourByItems = function()
	{
		var sampleGroups = Object.keys(sampleGroupItems[$scope.selectedGroupByItem]);
		if (sampleGroups.length>0) {
			$scope.colourByItems = sampleGroups;
			$scope.selectedColourByItem = $scope.colourByItems[0];
		} else {
			$scope.colourByItems = []
			$scope.selectedColourByItem = null;
		}
	}
	
	// Main function to draw the expression profile plot
	$scope.drawPlot = function()
	{		
		// Create groupBy array from sampleIdsFromSampleGroups and selectedGroupByItem. 
		// This array is used by expressionPlot and determines which sample ids should be aggregated together into
		// one bar for a bar plot, for example.
		var groupBy = [];
		for (var sampleGroupItem in sampleIdsFromSampleGroups[$scope.selectedGroupByItem]) {
			groupBy.push({'name':sampleGroupItem, 'samples':sampleIdsFromSampleGroups[$scope.selectedGroupByItem][sampleGroupItem]});
		}
				
		// Create colourBy array used by expressionPlot. This array is used to group multiple bars together and 
		// give them the same colour. So pass on which of the items currently being shown as bars should be grouped together. 
		var colourBy = [];
		var groupedItems = sampleGroupItems[$scope.selectedGroupByItem][$scope.selectedColourByItem];
		if ($scope.selectedColourByItem==null || groupedItems==null) {	// assume no colourByItem is available for this groupBy selection
			colourBy = [{'name':'all', 'groups':groupBy.map(function(d) { return d.name; })}];
		} else {
			var orderedItems = sampleGroupOrderedItems[$scope.selectedColourByItem];	// ['Multi Potential Progenitor',...]
			for (var i=0; i<orderedItems.length; i++) {
				var colourByItem = {'name':orderedItems[i], 'groups':groupedItems[orderedItems[i]]};
				if ($scope.selectedColourByItem in sampleGroupColours && orderedItems[i] in sampleGroupColours[$scope.selectedColourByItem])
					colourByItem['colour'] = sampleGroupColours[$scope.selectedColourByItem][orderedItems[i]];
				colourBy.push(colourByItem);
			}
		}
		
		// also need gene symbols from gene ids
		var featureGroupNames = {};
		for (var i=0; i<$scope.genes.length; i++)
			featureGroupNames[$scope.genes[i].EnsemblId] = $scope.genes[i].GeneSymbol;
			
		expressionPlot.draw({'values':expressionValues, 'groupBy':groupBy, 'colourBy':colourBy, 
					'valueRange':valueRange, 'value-axis-label':valueAxisLabel, 'group-axis-label':groupAxisLabel, 
					'featureGroups':featureGroups, 'featureGroupNames':featureGroupNames});
	}

	// functions for gene info display ---------------------------------------------------
	$scope.showGeneInfo = function(gene)
	{
		if (!gene) return;
	
		d3.selectAll("div#geneInfoDiv")
			.style({"opacity":0.9, "padding":"20px", "width":"50%", "left":"50%", "top":"50%", "transform":"translate(-50%, -50%)", "-webkit-transform":"translate(-50%, -50%)", "-moz-transform":"translate(-50%, -50%)"});
		
		// work out what to show for orthologue info
		var orthInfo = [];
		if (gene.Orthologue=="") orthInfo = "[no orthologue]";
		else {
			for (var i=0; i<gene.Orthologue.split(",").length; i++) { // multiple orthologue matches possible
				var orth = gene.Orthologue.split(",")[i].split(":");	
				orthInfo.push("<a href='/expression/show?geneId=" + orth[0] + "'>" + orth[1] + "</a>");
			}
			orthInfo = orthInfo.join(", ");
		}
			
		d3.selectAll("div#geneInfoDiv div p")
			.html("<h1 class='marquee'><span class='genesym'>" + gene.GeneSymbol + "</span></h1>"
				  + "<p><b>description:</b> " + gene.Description + "</p>"
				  + "<p><b>synonyms:</b> " + gene.Synonyms + "</p>"
				  + "<p><b>species:</b> " + gene.Species + "</p>"
				  + "<p><b>Ensembl id:</b> <a href='http://www.ensembl.org/Gene/Summary?g=" + gene.EnsemblId + "' target='_blank' style='color:#688'>" + gene.EnsemblId + "</a></p>"
				  + "<p><b>orthologue:</b> " + orthInfo + "</p>"
				  );
	}
	
	$scope.hideGeneInfo = function()
	{
		if (!$scope.persistentGeneInfoDiv) {
			d3.selectAll("div#geneInfoDiv").style({"opacity":0, "padding":null, "left":null, "top":null});	
			d3.selectAll("div#geneInfoDiv div p").html("");
		}
	}
	
	$scope.respondToGeneClick = function(gene)
	{
		if ($scope.persistentGeneInfoDiv) {	// already showing, so hide it
			$scope.persistentGeneInfoDiv = false;
			$scope.hideGeneInfo();
		} else {
			$scope.persistentGeneInfoDiv = true;
			$scope.showGeneInfo(gene);
		}
	}

	$scope.applyAction = function()	
	{
		CommonService.showLoadingImage();
		if ($scope.selectedAction.indexOf("multi species")!=-1)
			window.location.assign('/expression/multispecies?geneId=' + $scope.genes[0].EnsemblId);
		else if ($scope.selectedAction.indexOf("find similar")!=-1)
			findSimilar();
		else if ($scope.selectedAction.indexOf("gene vs gene")!=-1)
			window.location.assign('/expression/genevsgene?gene1=' + $scope.genes[0].EnsemblId);
		else if ($scope.selectedAction.indexOf("export")!=-1)
			exportData();
		else if ($scope.selectedAction.indexOf("save figure")!=-1)
			$scope.showSaveFigureDialog = true;

		CommonService.hideLoadingImage();
		$scope.selectedAction = $scope.actions[0];
	}

	// Run correlation analysis on selected gene/probe ----------------------------------- 
	var findSimilar = function()
	{
		if (expressionPlot.selectedFeatureId) {
			CommonService.showLoadingImage();
			$http.get("/geneset/corr", {
				params: {'featureId':expressionPlot.selectedFeatureId, 'datasetName': $scope.selectedDataset.name}
			}).
			success(function (response) {	
				CommonService.hideLoadingImage();
				// search/keyword places new geneset in session, so return current geneset page if geneset is not null
				if (response['genesetSize']>0)
					window.location.assign("/geneset/current");
				else if (response['error']!='')
					alert(response['error']);
			}).
			error(function(response) {
				CommonService.hideLoadingImage();
				alert('There was an unexpected error with correlation calculation.');
			});
		}
		else
			alert("First select a single feature before using this function.");
	}
	
	// Run this when dataset changes or new gene is selected -----------------------------------------------------
	$scope.reloadPage = function(geneId)
	{
		if (geneId!=null) {	// new gene selected - will assume it's a valid geneId from current dataset
			window.location.assign("/expression/show?geneId=" + geneId + "&datasetName=" + $scope.selectedDataset.name);
		} else {
			// construct the url - automatically fetch orthologue genes if selected dataset is from a different species
			var geneIds = [];
			var useOrthologues = $scope.genes[0].Species!=$scope.selectedDataset.species;
			
			for (var i=0; i<$scope.genes.length; i++) {
				if (useOrthologues) {
					if ($scope.genes[i].Orthologue=="") continue;
					var orths = $scope.genes[i].Orthologue.split(",");
					for (var j=0; j<orths.length; j++)
						geneIds.push("geneId=" + orths[j].split(":")[0]);
				}
				else
					geneIds.push("geneId=" + $scope.genes[i].EnsemblId);
			}

			if (useOrthologues && geneIds.length==0)	// no orthologues found
				alert("There is no orthologue for these genes to be able to show any expression profile for the selected dataset");
			else
				window.location.assign("/expression/show?" + geneIds.join("&") + "&datasetName=" + $scope.selectedDataset.name);
		}
	}
	
	// Function to export the expression data --------------------------------------------
	var exportData = function()
	{
		// Construct column headers, with sample ids as the first row of headers,
		// followed by other rows corresponding to other sample groups
		var sampleIds = Object.keys(expressionValues[Object.keys(expressionValues)[0]]);
		$scope.exportText = '\t' + sampleIds.join('\t');	// leave first column blank for featureId
		for (var i=0; i<$scope.groupByItems.length; i++) {
			var items = [];
			var idsFromItems = sampleIdsFromSampleGroups[$scope.groupByItems[i]]	// {'PreB':['sample1',...], ... }
			for (var item in idsFromItems) {	// work out matching sample group item for each sample id
				for (var j=0; j<idsFromItems[item].length; j++)
					items[sampleIds.indexOf(idsFromItems[item][j])] = item;
			}
			$scope.exportText += '\n\t' + items.join('\t');
		}

		// Add expression value rows
		for (var featureId in expressionValues) {
			if (!expressionPlot.selectedFeatureId || expressionPlot.selectedFeatureId==featureId)
				$scope.exportText += '\n' + featureId + '\t' + sampleIds.map(function(sampleId) { return expressionValues[featureId][sampleId]; }).join('\t');
		}
		$scope.showExportDialog = true;
	}
	
	$scope.closeShowExportDialog = function() { $scope.showExportDialog = false; }

	// Function to save figure to file ---------------------------------------------------
	// figureIndex is used to denote either the main figure or the legend: {0,1}
	$scope.saveFigure = function(figureIndex)
	{
		var html = expressionPlot.svgsAsHtml();		
		CommonService.showLoadingImage();

		// Since the svg doesn't include control div area, construct a useful file name using information there
		var filename = [$scope.genes[0].GeneSymbol, $scope.selectedDataset.name, $scope.selectedGroupByItem, $scope.selectedColourByItem].join('_')
			+ '.' + ['figure','legend'][figureIndex] + '.png';

        // convert svg to canvas
		var params = figureIndex==1? {scaleWidth: 300} : {}
		canvg('canvas', html[figureIndex], params);		

        // output as png
        var canvas = document.getElementById("canvas");
        var img = canvas.toDataURL("image/png");

		var link = document.createElement("a");
        link.setAttribute("href", img);
        link.setAttribute("download", filename);
        link.style.display = 'none';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        CommonService.hideLoadingImage();
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

	$scope.closeSaveFigureDialog = function() { $scope.showSaveFigureDialog = false; }
	
	// code to run on page load ----------------------------------------------------------
	if ($scope.error=='') {
		$scope.setColourByItems();
		$scope.drawPlot();
	}
	
}]);
	
</script>

</head>

<body>
<div id="wrap">  
${common_elements.banner()}

<div id="content" ng-controller="ExpressionController">
<div id="shadow"></div>
		
<div style="margin-left:30px;">	  
	<table>
	<tr>
		<td>
			<table><tr>
			<td>
				<h1 class="marquee" style="display:inline; margin-left:20px; margin-right:10px;" data-step="1" data-intro="Hover over the gene symbol to get details about the gene. Clicking on it will make the popup stay open.">
					<a href ng-mouseover="showGeneInfo(genes[0])" ng-mouseout="hideGeneInfo()" ng-click="respondToGeneClick(gene)">{{genes[0].GeneSymbol}}</a>
				</h1>
			</td>
			<!--
			<td ng-repeat="gene in genes" class="geneSymbol">
				<div style="float:left; width:70px;" ng-mouseover="showGeneInfo(gene)" ng-mouseout="hideGeneInfo()" ng-click="respondToGeneClick(gene)">{{gene.GeneSymbol}}</div>
				<div style="float:right; margin-left:6px; font-size:8px;"><a href='#' ng-click="removeGene(gene)">&#10006;</a></div>
			</td>
			-->
			</tr></table>
		</td>
		<td><!--<input id="geneSearchInput" type="text" style="height:2em;" placeholder="[not working yet]">--><input id="geneSearchInputGeneId" type="hidden"></td>
		<td valign="middle" id="helpTd">
			<img src="/images/question_mark.png" ng-mouseover="commonService.showTooltip(helptext,$event)" ng-mouseout="commonService.hideTooltip()" 
				onclick="javascript:introJs('#content').start();" width="20px" height="20px" style="margin-top:3px; opacity:0.7">
		</td>
	</tr>
	</table cellpadding="10">
	<table align="center">
	<tr><td>
		Dataset
		<select ng-options="ds.name group by ds.platform_type for ds in datasets" ng-model="selectedDataset" ng-change="updatePreferences(); reloadPage()"
				data-step="2" data-intro="Show expression in a different dataset. Only the datasets with matching species are shown."> </select>&nbsp; &nbsp; 
		Group by
		<select ng-options="item for item in groupByItems" ng-model="selectedGroupByItem" ng-change="setColourByItems(); updatePreferences(); drawPlot()"
				data-step="3" data-intro="Select sample group here. Each bar in the bar plot shows the mean value of all samples in that sample group item."></select>&nbsp; &nbsp; 
		Colour By
		<select ng-options="item for item in colourByItems" ng-model="selectedColourByItem" ng-change="updatePreferences(); drawPlot()"
				data-step="4" data-intro="Select another sample group for colouring where bars in the same sample group items will get the same colour."></select>
	</td>
	<td><select style="margin-left:100px;" ng-options="action for action in actions" ng-model="selectedAction" ng-change="applyAction()"
				data-step="5" data-intro="Various functions you can perform on the plot, including finding other genes with similar expression profile or saving the plot as a figure."></select></td>
	</tr>
	</table>
</div>

<div>
	<p ng-show="error!=''" style="font-size:16px; padding-left:200px; padding-top:50px;">{{error}}</p>
	<div id="controlPanelDiv" style="width:1000px; text-align:center; margin-top:20px;"></div>
	<div id="expression-div" style="margin-left:20px; width:85%; height:550px; float:left;overflow: auto;"></div>
	<div id="legend-div" style="width:13%; height:550px; overflow:auto;"></div>
	<div id="geneInfoDiv" style="opacity:0; background:#fff; z-index:10000; position:fixed; box-shadow:4px 4px 40px #000;">
		<div style="float:right"><a href="#" style="text-decoration:none; color:#aaa" ng-click="persistentGeneInfoDiv=false; hideGeneInfo();">&#10006;</a></div>
		<table style="text-align:left; margin-top:30px;">
			<tr>
				<td style="padding-right:10px; vertical-align:top;">
					<div style="float:left;"><p></p></div>
				</td>
				<td style="width:50%; border-left:solid 1px #ccc; padding:20px;	">
					<h2>Select another gene here</h2>
					<p>Start searching for genes in this dataset. The table below will autofill with matching genes once there are
					2 or more characters in the search field. Clicking on one of the fetched genes will reload this page, 
					after replacing this gene with the selection.</p>
					<input type="text" ng-model="geneFilterValue" ng-keyup="filterGeneListTable()" placeholder="search.." style="width:140px;"><br/>
					<table style="display:block; height:200px; overflow-y:scroll; border:1px solid grey; margin-top:10px;">
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

<modal-dialog show='showExportDialog'>
	<div style="overflow:auto;">
		<h3>Export Values</h3>
		<p>Use copy and paste from the text area below. Fields are tab separated.</p>
		<textarea wrap="off" style="width:650px; height:350px; max-height:400px;" ng-model="exportText"></textarea>
		<p><button ng-click="closeShowExportDialog()">close</button></p>
	</div>
</modal-dialog>
	
<modal-dialog show='showSaveFigureDialog'>
	<div style="overflow:auto;">
		<h3>Save Figure</h3>
		<p>You can save this figure as a png file (large size suitable for printing). The legend is provided as a separate figure for full flexibility.</p>
		<p><a href="#" ng-click="saveFigure(0)">main figure</a> &#47; <a href="#" ng-click="saveFigure(1)">legend</a></p>
		<p><button ng-click="closeSaveFigureDialog()">close</button></p>
	</div>
</modal-dialog>
	
${common_elements.footer()}
</div> <!-- content -->

<div></div>  <!-- dialogs -->

</div> <!-- wrap -->  
<canvas ng-show=false id="canvas"></canvas>
</body>
</html>

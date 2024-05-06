<%
import json
'''
list of all variables used by this mako template:
error
gene
orthGene
lineageGroups
expressionValues
valueRanges
columnNames
colours
datasetNames
datasetsToUse
'''
def decode_b(t):
    return t.decode('utf-8')
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<head>
<title>Haemosphere - Multi-species Expression Profile</title>

<%namespace name="common_elements" file="common.mako"/>
${common_elements.header_elements()}

<script type="text/javascript" src="/js/canvg/rgbcolor.js"></script> 
<script type="text/javascript" src="/js/canvg/StackBlur.js"></script>
<script type="text/javascript" src="/js/canvg/canvg.min.js"></script> 
<script type="text/javascript" src="/js/plotly.min.js"></script>

<style type="text/css">
div.geneSymbol {
	text-align: center;
	margin: 10px;
}

div.geneSymbol a {
	font-size: 18px;
}

table.selectDatasetDialog {
	margin: 0;
	padding: 0;
	border-left: solid 1px #ccc;
	border-top: solid 1px #ccc;
}

table.selectDatasetDialog th, table.selectDatasetDialog td {
	vertical-align:top; 
	padding: 10px;
	border-bottom: solid 1px #ccc;
	border-right: solid 1px #ccc;
}

table.main {
	margin-left: auto;
	margin-right: auto;
}

table.main td {
	vertical-align:top; 
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

.vertical{
    writing-mode:tb-rl;
    -webkit-transform:rotate(90deg);
    -moz-transform:rotate(90deg);
    -o-transform: rotate(90deg);
    -ms-transform:rotate(90deg);
    transform: rotate(90deg);
    white-space:nowrap;
    display:block;
    bottom:0;
    width:20px;
    height:20px;
}

</style>

<script type="text/javascript">
app.controller('MultispeciesController', ['$scope', '$http', '$httpParamSerializerJQLike', 'CommonService', function($scope, $http, $httpParamSerializerJQLike, CommonService) 
{	
	$scope.commonService = CommonService;
	
	// Inputs from python
	$scope.error = "${error if error else ''}";	
	$scope.gene = ${json.dumps(gene) | n};
	$scope.orthGene = ${json.dumps(orthGene) | n};
	var lineageGroups = ${json.dumps(lineageGroups) | n};
	var expressionValues = ${json.dumps(expressionValues) | n};
	var valueRanges = ${json.dumps(valueRanges) | n};
	var columnNames = ${json.dumps(columnNames) | n};
	var colours = ${json.dumps(colours, default=decode_b, indent=4) | n};
	var datasetNames = ${json.dumps(datasetNames) | n};
	$scope.datasetsToUse = ${json.dumps(datasetsToUse) | n};

	// Note that we will always show mouse datasets first, even if gene chosen was human.
	$scope.persistentGeneInfoDiv = false;	// Used to persistently show geneInfoDiv 
	$scope.showLegend = false;
	$scope.helptext = "<div style='width:500px;'><h3>About this page</h3>"
			+ "<ul style='margin-top:0px;'>"
			+ "<li>This page shows the expression of a gene and its orthologue summarised across lineages in both mouse and human datasets.</li>"
			+ "<li>Hover over the gene symbol to get details about the gene. Clicking on the symbol will make the popup stay open.</li>"
			+ "<li>Click on the dataset label in the plot title to show expression profile of the gene in that dataset alone.</li>"
			+ "<li>Save graph button will show a dialog where you can select a graph to download. To save the legend, right click on it and choose 'Save Image'.</li>"
			+ "</ul>";
	// This is used just after gene symbol
	$scope.speciesText = {'mouse': ($scope.gene.Species=='HomoSapiens' && Object.keys($scope.orthGene).length==0)? '(no mouse orthologue)' : '(mouse)',
						  'human': ($scope.gene.Species=='MusMusculus' && Object.keys($scope.orthGene).length==0)? '(no human orthologue)' : '(human)'};

	// For selecting datasets -----------------------------------------------------
	$scope.showSelectDatasetsDialog = false;

	$scope.setSelectedDatasets = function() {
		var datasetsShown = datasetNames.map(function(item) { return item.split(", ")[1] });
		$scope.selectedDatasets = {};
		for (var species in $scope.datasetsToUse) {
			$scope.selectedDatasets[species] = $scope.datasetsToUse[species].map(function(item) { 
				return datasetsShown.indexOf(item.name)!=-1 
			});
		}
	}

	$scope.closeShowSelectDatasetsDialog = function() { $scope.showSelectDatasetsDialog = false; }

	$scope.applyDatasetSelection = function()
	{
		// Construct the url. If no dataset has been specified for a given species, add special parameter value in this case
		var datasets = {};
		var atLeastOneDatasetSpecified = false;
		for (var species in $scope.datasetsToUse) {
			datasets[species] = [];
			for (var i=0; i<$scope.datasetsToUse[species].length; i++) {
				if ($scope.selectedDatasets[species][i])
					datasets[species].push("selectedDataset=" + $scope.datasetsToUse[species][i].name);
			}
			if (datasets[species].length==0) 
				datasets[species] = ["selectedDataset=" + species + "_none"];
			else
				atLeastOneDatasetSpecified = true;
		}

		if (!atLeastOneDatasetSpecified) {
			alert("No dataset chosen.");
			return;
		}

		CommonService.showLoadingImage();
		window.location.assign("/expression/multispecies?geneId=" + $scope.gene.EnsemblId + "&" + 
								datasets["MusMusculus"].join("&") + "&" + datasets["HomoSapiens"].join("&"));
	}

	// For saving graphs -----------------------------------------------------
	$scope.showSaveGraphDialog = false;
	$scope.saveGraphDialog = {datasets: datasetNames.map(function(item) { return item.split(", ")[1] })};
	$scope.saveGraphDialog.datasetForDownload = $scope.saveGraphDialog.datasets[1];

	$scope.showDownloadGraph = function() {
		$scope.showSaveGraphDialog = true;
		var tal = tracesAndLayout($scope.saveGraphDialog.datasets.indexOf($scope.saveGraphDialog.datasetForDownload));
		var layout = tal.layout;
		for (var j=0; j<lineageGroups.length; j++) {
			layout['xaxis'+(j+1).toString()]['title'] = lineageGroups[j];
			layout['xaxis'+(j+1).toString()]['titlefont'] = 16;
		}
		layout['yaxis1']['titlefont'] = 16;
		layout['plot_bgcolor'] = "white";
		layout['paper_bgcolor'] = "white";
		layout['margin']['padding'] = 20;
		Plotly.newPlot("saveGraphDiv", tal.traces, layout, {displayModeBar: false});
	}
	// This method will invoke the download dialog.
	$scope.downloadGraph = function() {
		// Find gene symbol based on selected dataset's species and use it in file title.
		for (var species in $scope.datasetsToUse) {
			var selectedDs = $scope.datasetsToUse[species].find(function(item) { return item.name==$scope.saveGraphDialog.datasetForDownload; });
			if (selectedDs!=undefined) break;
		}
		var geneSymbol = $scope.gene.Species==selectedDs.species? $scope.gene.GeneSymbol : $scope.orthGene.GeneSymbol;
		var filename = "Haemosphere_LineageExpression_" + geneSymbol + "_" + $scope.saveGraphDialog.datasetForDownload;
		Plotly.downloadImage(document.getElementById("saveGraphDiv"), {format: 'png', width: 1200, height: 300, filename: filename});
	}
	$scope.closeDownloadGraphDialog = function() {
		$scope.showSaveGraphDialog=false;
	}

	// Main function to draw the plot using plotly. ------------------------------
	// There are some peculiarities with plotly's subplots, which aren't well documented:
	// 1. value of xaxis and yaxis assigned within a trace has to look like the key used within the layout.
	//    This means { xaxis: 'x2', ...} within a trace should match { xaxis2: { domain:...},...} within layout
	//    (ie. '2' suffix after x must match, so if xaxis: 'x5' in trace, we need xaxis5 in layout.
	// 2. This value can't be 0. So xaxis:'x0' and xaxis0 doesn't work.
	// 3. anchor property within layout attaches a particular axis with another specified axis. Simplest is to 
	//    specify the matching y axis as anchor value of x on the same plot, and vice versa.
	// 4. domain (not specific to subplots), specifies the fractional length within which an element occupies.
	//    So xaxis with domain [0,0.45] will take up 0 to 45% of the whole horizontal length starting from x=0.
	//
	// Divided out the function to create the traces and layout from the function that does the div creation and
	// plotting, so that tracesAndLayout can be called from elsewhere also (save graph dialog).
	// 
	// Work out the index where there is a boundary between species - this is just size of mouse datasets - 1.
	function boundaryIndex() {
		return datasetNames.filter(function(item) { return item.split(", ")[2]=="mouse" }).length - 1;
	}
	function plotBackgroundColour(i) {
		return datasetNames[i].split(", ")[2]=="mouse"? "#fdf6f5": "#fff";
	}
	function tracesAndLayout(i) 
	{
		var xsize = 1/lineageGroups.length;  // unit size of each subplot
		var ysize = 1/expressionValues.length;
		var xgap = xsize*0.05;   // how much gap to put

		var titles = datasetNames[i].split(", ");
		var platformType = titles[3];  // either microarray or rna-seq

		// gene id to be used for getting back to expression profile; this must match species of dataset
		var geneId = $scope.gene.EnsemblId;
		if (titles[2]=="mouse" && $scope.gene.Species=="HomoSapiens" || titles[2]=="human" && $scope.gene.Species=="MusMusculus")
			geneId = $scope.orthGene.EnsemblId;
		
		var layout = {title: "<a href='/expression/show?geneId="+geneId+"&datasetName="+titles[1]+"'>" + titles[1] + "</a> (" + titles[3] + ")",
						showlegend:false, margin:{t:35, b:20, pad:0}, titlefont:{size:14}, autosize:true, 
						plot_bgcolor:plotBackgroundColour(i), paper_bgcolor:plotBackgroundColour(i)};
								
		var min = valueRanges[i][0];
		var max = valueRanges[i][1];
						
		// Each trace is a subplot (column-wise)
		var traces = [];
		for (var j=0; j<lineageGroups.length; j++) {
			var n = j+1; // index of subplot, used as suffix for axis
			var trace = {x:columnNames[i][j], y:expressionValues[i][j], type:'bar',
							xaxis:'x'+n.toString(), yaxis:'y'+n.toString(), name:datasetNames[i] + ' - ' + lineageGroups[j],
							text:columnNames[i][j].map(function(item,index) { return expressionValues[i][j][index].toFixed(2) + " " + item }), 
							hoverinfo:"text"};
			if (colours[i][j].length>0)
				trace.marker = {color: colours[i][j]};
			traces.push(trace);
			
			// show y-axis zeroline only if there are zero values
			var zeroline = expressionValues[i][j].length>0 && Math.max.apply(Math, expressionValues[i][j])==0;

			layout['xaxis'+n] = {domain: [j*xsize + xgap, (j+1)*xsize - xgap], anchor:'y'+n.toString(), 
									showticklabels:false, 
									titlefont:{size:10}};
			layout['yaxis'+n] = {anchor:'x'+n.toString(),
									showticklabels:j==0, 
									range:platformType=="microarray"? [min,max] : [min-1, max+1], 
									zeroline:zeroline,
									tickfont:{size: 10}};
			//layout['yaxis'+n] = {domain: [i*ysize + ygap, (i+1)*ysize - ygap], anchor:'x'+n.toString(), showticklabels:false, range:[min-1, max+1]};
			
			if (i==boundaryIndex() || i==expressionValues.length-1) {
				layout['xaxis'+n].title = lineageGroups[j];
			}

			if (j==0) {  // y axis label only on the left most axis
				layout['yaxis'+n].title = "log2";
				layout['yaxis'+n].titlefont = {size: 12};
			}
		}
		return {'traces':traces, 'layout':layout};
	}
	$scope.drawPlot = function()
	{			
		// After experimenting with one plot with a grid of subplots, decided to use one plot per dataset, where each plot is only
		// a one row grid. To do this dynamically, we create a div and insert it into #expression-mouse-div or #expresson-human-div 
		// for each dataset. Note that ng-repeat does not work in this case.
		for (var i=0; i<expressionValues.length; i++) {
			
			// Create the div which will contain the plot
			var div = document.createElement('div');
			div.style["height"] = "130px";
			div.style["width"] = "1000px";
			div.style["background"] = plotBackgroundColour(i);
			div.style["padding-bottom"] = "10px";
			div.style["margin"] = "auto";
			div.style["border"] = "1px solid #f5e8d0";
			var graphId = 'graph-' + i;
			div.id = graphId;
			if (i>boundaryIndex())
				document.getElementById("expression-human-div").appendChild(div);
			else
				document.getElementById("expression-mouse-div").appendChild(div);

			var tal = tracesAndLayout(i);
			Plotly.plot(graphId, tal.traces, tal.layout);
		}  		
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
	
	// code to run on page load ----------------------------------------------------------
	if ($scope.error=='') {
		$scope.drawPlot();
	}
	
}]);
	
</script>

</head>

<body>
<div id="wrap">  
${common_elements.banner()}

<div id="content" ng-controller="MultispeciesController">
<div id="shadow"></div>
		
<div style="background:#fff; text-align:center;">
	<table style="margin-bottom:20px; margin-left:auto; margin-right:auto"><tr>
		<td><h1 class="marquee" style="margin:inherit">Multi-species Plot</h1></td>
		<td><img src="/images/question_mark.png" ng-mouseover="commonService.showTooltip(helptext,$event)" ng-mouseout="commonService.hideTooltip()" 
			width="20px" height="20px" style="margin-left:20px; opacity:0.7"></td>
		<td><button ng-click="setSelectedDatasets(); showSelectDatasetsDialog=true" style="margin-left:30px;">select datasets</button>
			<button ng-click="showDownloadGraph()">save graph</button>
		</td>
		<td><input type="checkbox" ng-model="showLegend" style="margin-left:20px;">show legend</td>
	</tr></table>
	<p ng-show="error!=''" style="font-size:16px; padding-top:50px;">{{error}}</p>

	<table class="main"><tr>
		<td><div class="geneSymbol">
			<a href ng-mouseover="showGeneInfo(gene.Species=='MusMusculus'? gene: orthGene)" ng-mouseout="hideGeneInfo()" ng-click="respondToGeneClick(gene.Species=='MusMusculus'? gene: orthGene)">
				{{gene.Species=='MusMusculus'? gene.GeneSymbol : orthGene.GeneSymbol}}
			</a>
			{{speciesText.mouse}}
		</div>
		<div id="expression-mouse-div" style="margin:auto;"></div>
		<div class="geneSymbol" style="margin-top:20px;">
			<a href ng-mouseover="showGeneInfo(gene.Species=='HomoSapiens'? gene: orthGene)" ng-mouseout="hideGeneInfo()" ng-click="respondToGeneClick(gene.Species=='HomoSapiens'? gene: orthGene)">
				{{gene.Species=='HomoSapiens'? gene.GeneSymbol : orthGene.GeneSymbol}}
			</a>
			{{speciesText.human}}
		</div>
		<div id="expression-human-div" style="margin:auto; background:#fff;"></div></td>
		<td><div ng-show="showLegend" style="float:right; margin-top:40px;"><img src="/images/Lineages.png" style="width:200px"></div></td></tr>
	</table>

	<div id="geneInfoDiv" style="background:#fff; opacity:0; z-index:10000; position:fixed; box-shadow:4px 4px 40px #000;">
		<div style="text-align:left;"><p></p></div><div style="float:right"><a href="#" style="text-decoration:none; color:#ccc" ng-click="persistentGeneInfoDiv=false; hideGeneInfo();">&#10006;</a></div>
	</div>
	<div id="plotDiv"></div>
</div>

<div style="clear:both;"></div>

<modal-dialog show='showSelectDatasetsDialog' style="width:700px;">
	<div style="margin:20px; overflow:auto;">
		<h3>Select Datasets</h3>
		<p>Select datasets to view and click apply to reload the page. Note that a selected dataset may not be returned if no expression value exists for the gene in that dataset.</p>
		<table class="selectDatasetDialog">
		<tr><th>mouse datasets</th><th>human datasets</th></tr>
		<tr>
			<td><ul style="list-style-type:none; padding-left:0"><li ng-repeat="ds in datasetsToUse.MusMusculus">
				<input type="checkbox" ng-model="selectedDatasets.MusMusculus[$index]">{{ds.name}} <span style="color:#ccc;">({{ds.platform_type}})</span></li>
			</ul></td>
			<td><ul style="list-style-type:none; padding-left:0"><li ng-repeat="ds in datasetsToUse.HomoSapiens">
				<input type="checkbox" ng-model="selectedDatasets.HomoSapiens[$index]">{{ds.name}} <span style="color:#ccc;">({{ds.platform_type}})</span></li>
			</ul></td>
		</tr></table>
		<p><button ng-click="applyDatasetSelection()">apply</button> &nbsp; <button ng-click="closeShowSelectDatasetsDialog()">close</button></p>
	</div>
</modal-dialog>
	
<modal-dialog show='showSaveGraphDialog'>
	<div style="padding:10px;">
		<h3>Save Graph</h3>
		<p>You can save a selected graph as a png file (large size suitable for printing). First, select the graph you want to 
		download and click on the download button.</p>
		<select ng-options="item for item in saveGraphDialog.datasets" ng-model="saveGraphDialog.datasetForDownload" ng-change="showDownloadGraph()"></select>
		<div style="overflow:auto;"><div id="saveGraphDiv" style="width:900px; height:200px; margin-top:10px; padding:10px;"></div></div>
		<p><button ng-click="downloadGraph()">download</button>
		<button ng-click="closeDownloadGraphDialog()">close</button></p>
	</div>
</modal-dialog>
	
${common_elements.footer()}
</div> <!-- content -->

<div></div>  <!-- dialogs -->

</div> <!-- wrap -->  
<canvas ng-show=false id="canvas"></canvas>
</body>
</html>

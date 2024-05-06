<%
import json
"""
Required input for this mako file and example entries:
error (str): empty or None if there was no error
datasets: [{'name':'dmap', 'species':'HomoSapiens', 'isRnaSeqData':False, ...}, ...] # a list of dataset properties
geneIds: ['ENSG00024242',...] # Keep track of original geneIds specified, so these are always used no matter what 
selectedDatasetName: 'dmap'
sampleGroups: {'haemopedia':['celltype','tissue',...], ...} # all sample group names for all available datasets
selectedSampleGroup: 'celltype'
genesetName: 'My Geneset'
genesetDescription: 'Description of my geneset'
data: {'columnLabels':['B1','T Cell',...], 
	   'rowLabels':[{'featureId':'geneId1','displayString':'gene1','geneIds':['ENSG00000333',...]},...], 
	   'matrix':[{'x':1,'y':0,'value':2.53,'name':'gene2-T Cell'},...]}
valueRange: [2.5,3.8]
"""
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<head>
<title>Haemosphere - Datasets</title>

<%namespace name="common_elements" file="common.mako"/>
${common_elements.header_elements()}
<script type="text/javascript" src="/js/heatmapplot.js"></script>

<link type="text/css" href="/css/d3.slider.css" rel="stylesheet" />
<script type="text/javascript" src="/js/d3.slider.js"></script>

<script type="text/javascript" src="/js/canvg/rgbcolor.js"></script> 
<script type="text/javascript" src="/js/canvg/StackBlur.js"></script>
<script type="text/javascript" src="/js/canvg/canvg.min.js"></script> 

<style type="text/css">
table.dataTable td {
	vertical-align:top;
}
.d3-slider {
	height: 0.6em;
}
.d3-slider-handle {
	height: 1.0em;
}
</style>

<script type="text/javascript">

app.controller('HeatmapController', ['$scope', '$http', 'CommonService', function ($scope, $http, CommonService) 
{
	// Parse input data
	$scope.error = ${json.dumps(error) |n};
	$scope.datasets = ${json.dumps(datasets) | n};
	for (var i=0; i<$scope.datasets.length; i++)
		if ($scope.datasets[i].name=='${selectedDatasetName}') $scope.selectedDataset = $scope.datasets[i];
	var data = ${json.dumps(data) | n};
	var geneIds = ${json.dumps(geneIds) | n};
	$scope.valueRange = ${json.dumps(valueRange) | n};
	$scope.sampleGroups = ${json.dumps(sampleGroups) | n};
	$scope.selectedSampleGroup = ${json.dumps(selectedSampleGroup) | n};
	$scope.geneset = {'name':'${genesetName}', 'description':'${genesetDescription}'};
	$scope.numberOfRows = data.rowLabels.length;
	
	$scope.showSaveFigureDialog = false;
	
	$scope.commonService = CommonService;
	$scope.helptext = "<div style='width:350px;'><b>How the heatmap is rendered</b>"
			+ "<p>For practical reasons (speed and usability), there is an upper limit of 300 features shown. If there are more than this number of features to show, "
			+ "those with low variance are filtered out.</p>"
			+ "<p>The values shown when you hover over each square are based on mean of the selected sample group"
			+ (true? ".</p>" : ", and for RNA-Seq data, log2(tpm+1) is the formula used for each value (before the mean was calculated).</p>")
			+ "<p>After any row filtering, hierarchical clustering is applied to the rows so that similar features group together. "
			+ "Columns of the heatmap are not clustered but should be ordered according to how the sample group items are ordered within the dataset.</p>" 
			+ "<p>Colour of each square is determined by z score of each row, which is also used by the clustering algorithm. "
			+ "This means genes with similarly shaped expression profiles will be closer together regardless of their actual values.</p>"
			+ "<b>Tips on using this page</b>"
			+ "<p>Hover over each cell to see values assigned to the cell. Hover over a feature name (gene symbol) to see a preview of its expression profile as a barplot.</p>"
			+ "<p>Clicking on a feature name will pop up a new page showing its full expression profile.</p>" 
			+ "<p>Adjust the slider to create more contrast. The slider sets the value corresponding to white colour, "
			+ "which is in between red (high z score) and blue (low).</p></div>";
			
	// Function to bring up expression profile page if clicked on rowId
	var showExpressionProfile = function(rowLabel)
	{
		if (rowLabel.geneIds.length==0) // no matching gene id for some reason
			alert("No matching gene id for this feature id in the dataset to be able to show its expression profile.");
		else {
			if (rowLabel.geneIds.length>1)	// multiple gene ids
				alert("Multiple gene ids match this feature id. Showing the expression profile for the first match.")
			window.open('/expression/show?geneId=' + rowLabel.geneIds[0] + '&datasetName=' + $scope.selectedDataset.name + '&groupByItem=' + $scope.selectedSampleGroup, '_blank');
		}
	}
	
	// Define heatmap and slider
	var heatmapPlot = new heatmapplot.HeatmapPlot({'div':d3.select("#heatmapDiv"), 'mouseover':CommonService.showTooltip, 'mouseout':CommonService.hideTooltip, 
		'rowLabelClickFunction':showExpressionProfile});	
	var slider = d3.slider().min($scope.valueRange[0]).max($scope.valueRange[1]);	// floats don't render as ticks for some reason, so leave ticks out altogether
	//$scope.sliderValue = $scope.valueRange[0] + ($scope.valueRange[1]-$scope.valueRange[0])/2;
	$scope.sliderValue = -0.04;
		
	slider.on("slide", function(evt, value) {
		$scope.sliderValue = value;
		if (!$scope.$$phase) $scope.$apply();
		var domain = heatmapPlot.colourScale.domain();
		heatmapPlot.colourScale.domain([domain[0],value,domain[2]]);
		heatmapPlot.square.transition()
			.duration(800)
			.style('fill', function(d) { return heatmapPlot.colourScale(d.value); });
	})
	
	$scope.setDefaultSelectedSampleGroup = function()
	{
		$scope.selectedSampleGroup = $scope.sampleGroups[$scope.selectedDataset.name][0];
	}

	$scope.drawHeatmap = function()
	{
		data['valueRange'] = $scope.valueRange;
		heatmapPlot.draw(data);
		slider.value($scope.sliderValue);
		d3.select('#slider').call(slider);
	}
		
	$scope.submitForm = function($event)
	{
		$scope.heatmapGeneIds = geneIds.join('&');
		$event.target.submit();
	}
	
	// run on page load
	$scope.drawHeatmap();
	
	$scope.saveFigure = function()
	{
		var data = heatmapPlot.svgAsHtml();
		CommonService.showLoadingImage();
		
		var headerHtml = data[0];
		var bodyHtml = data[1];
		var headerHeight = data[2];
		var bodyHeight = data[3];
		var width = data[4];

		// Since the svg doesn't include control div area, construct a useful file name using information there
		var filename = ["Heatmap", $scope.geneset['name'], $scope.selectedDataset['name'], $scope.selectedSampleGroup].join('_') + '.png';

		var canvas = document.getElementById("canvas");
		canvas.height = (headerHeight+bodyHeight+20)*2;
		canvas.width = width*2;		
		
        // convert svg to canvas		
		canvg('canvas', headerHtml, { ignoreDimensions : true, ignoreClear : true } );		
		canvg('canvas', bodyHtml, { ignoreDimensions : true, ignoreClear : true, offsetY : headerHeight*2 } );
		
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
	
	
}]);

</script>

</head>

<body>
<div id="wrap">  
${common_elements.banner()}

	<div id="content">
		<div id="shadow"></div>
		<div style="margin-left:40px; margin-right:40px;" ng-controller="HeatmapController">
			<div style="margin-bottom:20px;">
			<h1 class="marquee" style="margin-left:50px; display:inline;">
				Heatmap of current geneset: <a href='/geneset/current' ng-mouseover="commonService.showTooltip(geneset.description,$event)" ng-mouseout="commonService.hideTooltip()">
				{{geneset.name | limitTo:50}}{{geneset.name.length>50? '..' : ''}}</a>
			</h1>
			({{numberOfRows}} rows shown)
			</div>
			<table style="margin-left:50px;"><tr>
			<td>
				<form name="mainForm" ng-submit="submitForm($event)" action="/geneset/heatmap" method="POST">
					<select ng-model="selectedDataset" ng-options="dataset.name for dataset in datasets" ng-change="setDefaultSelectedSampleGroup()"></select>
					<select ng-model="selectedSampleGroup" ng-options="name for name in sampleGroups[selectedDataset.name]"></select>
					<input type="submit" value="Reload"/>
					<input type="hidden" name="datasetName" ng-value="selectedDataset.name"/>
					<input type="hidden" name="sampleGroup" ng-value="selectedSampleGroup"/>
					<input type="hidden" name="geneId" ng-value="heatmapGeneIds"/>
				</form>
			</td>
			<td style="padding-left:50px;">
				colour scale ({{sliderValue.toFixed(2)}}):
			</td>
			<td style="color:blue">{{valueRange[0].toFixed(2)}}</td>
			<td><div id="slider" style="width:150px;"></div></td>
			<td style="color:red">{{valueRange[1].toFixed(2)}}</td>
			<td style="padding-left:30px;"><a href='#' ng-click="saveFigure()">save figure</a></td>
			<td style="padding-left:30px;">
				<img src="/images/question_mark.png" ng-mouseover="commonService.showTooltip(helptext,$event,{leftOffset:'-200px'})" ng-mouseout="commonService.hideTooltip()" width="20px" height="20px" style="margin-top:3px; opacity:0.7">
			</td>
			</tr></table>
			<p ng-show="error!=''" style="margin-left:100px;">{{error}}</p>
			<div id="heatmapDiv" style="height:600px; width:1000px;"></div>
		</div>
		<br style="clear:both;" />

<modal-dialog show='showSaveFigureDialog'>
	<div style="overflow:auto;">
		<h3>Save Heatmap Figure</h3>
		<p>You can save this figure as a png file (large size suitable for printing).</p>
		<p><a href="#" ng-click="saveFigure()">Save heatmap</a></p>
		<p><button ng-click="showSaveFigureDialog=false">close</button></p>
	</div>
</modal-dialog>

	
	${common_elements.footer()}
	</div> <!-- content -->
<canvas ng-show=false id="canvas"></canvas>
</div> <!-- wrap -->  
</body>
</html>

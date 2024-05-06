<%
'''This page has visualisation tools such as mds plot for a selected dataset.

Required input variables are (should all be in json form already):

datasets: a list of datasets availble to choose from. eg: [{'name':'haemopedia', 'species':'MusMusculus', 'platform':'microarray'},...]
selectedDatasetIndex: integer indicating the index which can be used to specify the currently selected dataset from datasets.
distances: stringified list of lists specifying sample distances for selected dataset. eg: [[0,0.8145, ...],...]
		   actual example: dist = [[0,0.81457289422126,4.9528661197331,5.03709793432687,4.53215425598026,4.44104057626138,4.60286217477778,4.68424021587279,4.53364881745377,4.55453872527175,4.80602788173352,4.6864825615807,4.54523913562312,4.53504500528936,5.97235774213166,6.0863261003663,6.22052621568304,6.20711562644035,5.18704696335015,5.35525846248339],[0,0,4.84329373463968,4.95248941442584,4.44399234922834,4.35943234836831,4.52020565903809,4.60454386448864,4.40961329370275,4.4446596720109,4.68552825196903,4.57222936869969,4.45250462099704,4.44295723589593,5.94737777512073,6.06565330364339,6.20101735201572,6.17821221713855,5.09608492864866,5.27856793079335],[0,0,0,1.15352867324571,4.33743876037461,4.2343106404703,3.8616847877578,4.15695662714924,3.3414308312458,3.4175953827216,3.08936796125033,3.15098905107587,4.32826172960924,4.37625118109096,6.31837154653001,6.30759166401884,6.86189973695332,6.84316704457812,6.23050449000721,6.2889188578006],[0,0,0,0,4.13448349857633,4.09410007205491,3.74335873247542,4.00541218852692,3.44323609414167,3.62715704098954,3.21197303849207,3.29069962166102,4.46275681613955,4.47468850312511,6.67634182767779,6.6817798078057,7.18639982188578,7.16436849973534,6.37669041117726,6.47208498090067],[0,0,0,0,0,0.913569701774309,1.59822726794408,1.43002104879614,2.81383400363277,3.27657528526356,3.13004214029141,3.24378991304924,4.12904364229781,4.06543087507339,7.15064444648173,7.22035121029441,7.49688451291602,7.44348994759851,5.93936225532674,6.24309264707805],[0,0,0,0,0,0,1.47588630998461,1.21853313455154,2.68169435245704,3.10369508811674,3.00356225172711,3.11089244429955,4.10184117196168,4.05364643253454,7.00934342146253,7.07789968846691,7.36849722806489,7.32476362758553,5.9170925968756,6.18838449031732],[0,0,0,0,0,0,0,1.11321309729988,2.47512831990586,2.88632707779281,2.37497027349818,2.57518150816598,4.10130601150414,4.06769175331662,7.06644334867265,7.11386702152915,7.39909736386811,7.37718375804751,6.00765425103676,6.26420090673982],[0,0,0,0,0,0,0,0,2.89533459206358,3.27443396635205,2.83869878641606,3.01201812743549,4.3696001647748,4.33245066907864,7.19184767636245,7.27662868366938,7.54807178026282,7.5162002102126,6.13523070470867,6.40620836376713],[0,0,0,0,0,0,0,0,0,1.58131559152498,1.61936160260764,1.73185311155421,3.52660380536289,3.55221924999007,6.41472052391996,6.39346877680653,6.8111938747917,6.78957789556906,5.83023370029024,5.97157238924557],[0,0,0,0,0,0,0,0,0,0,2.08006850848716,1.70120998116047,3.53607468812524,3.6328662237963,6.03054820061991,6.03216767008345,6.37213111917826,6.36500128829524,5.6390614467303,5.7141123720137],[0,0,0,0,0,0,0,0,0,0,0,1.19263640729268,3.79292773461346,3.83090981360825,6.68185730167893,6.67891558563215,7.0571142544244,7.06220611423937,6.07552155785822,6.21146655790724],[0,0,0,0,0,0,0,0,0,0,0,0,3.63361302287406,3.69777954994616,6.51297236290774,6.51420560007128,6.85365452878973,6.85482104799243,5.95990639188234,6.07682808708622],[0,0,0,0,0,0,0,0,0,0,0,0,0,0.624595549135599,6.16347640540629,6.08619360520186,6.33916748477274,6.36352028361661,5.3202909882825,5.43749883678148],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,6.27425433019733,6.18850002827826,6.45219218560638,6.4814406731837,5.37972930545766,5.51662563529555],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.25442050365896,3.03657283792107,2.62406444280624,6.15282803270171,5.76844635928948],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2.9633345069364,2.63535838170067,6.29353433294838,5.86924245537701],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.23727765679333,5.27242803649324,4.66297475867069],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5.63917807840824,5.09722398958492],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.23751113126307],[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]
sampleGroups: a list of available sample groups to chooose from. eg: ['sampleId','celltype','tissue',...]. Note 'sampleId' should always be first.
samples: a list of dict containing sample info. eg: [{'sampleId':'sample1', 'celltype':'B', 'tissue':'PB',...}, ...].
		 Should be in the same order as distances.
sampleGroupColours: a nested dictionaryof colours keyed on sampleGroup, then on sampleGroupItems
sampleGroupOrdering: a dictionary of lists, keyed on sampleGroup, where values are ordered list of sample group items
'''
import json
def decode_b(t):
    return t.decode('utf-8')
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<head>
<title>Haemosphere - Dataset Analysis</title>

<%namespace name="common_elements" file="common.mako"/>
${common_elements.header_elements()}

<script type="text/javascript" src="/js/numeric-1.2.6.min.js"></script>
<script type="text/javascript" src="/js/scatterplot.js"></script>
<script type="text/javascript" src="/js/distlineplot.js"></script>
<script type="text/javascript" src="/js/mstplot.js"></script>

<script type="text/javascript" src="/js/canvg/rgbcolor.js"></script> 
<script type="text/javascript" src="/js/canvg/StackBlur.js"></script>
<script type="text/javascript" src="/js/canvg/canvg.min.js"></script> 

<script type="text/javascript">
// From http://www.benfrederickson.com/multidimensional-scaling/
/// given a matrix of distances between some points, returns the
/// point coordinates that best approximate the distances
function mdsClassic(distances, dimensions) 
{
    dimensions = dimensions || 2;

    // square distances
    var M = numeric.mul(-.5, numeric.pow(distances, 2));

    // double centre the rows/columns
    function mean(A) { return numeric.div(numeric.add.apply(null, A), A.length); }
    var rowMeans = mean(M),
        colMeans = mean(numeric.transpose(M)),
        totalMean = mean(rowMeans);

    for (var i = 0; i < M.length; ++i) {
        for (var j =0; j < M[0].length; ++j) {
            M[i][j] += totalMean - rowMeans[i] - colMeans[j];
        }
    }

    // take the SVD of the double centred matrix, and return the
    // points from it
    var ret = numeric.svd(M),
        eigenValues = numeric.sqrt(ret.S);
    return ret.U.map(function(row) {
        return numeric.mul(row, eigenValues).splice(0, dimensions);
    });
};

// sampleGroupColours may come as 'rgb(0,0,255)'. So we may need to convert to hex
// From http://stackoverflow.com/questions/5623838/rgb-to-hex-and-hex-to-rgb
function rgbToHex(r, g, b) {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

</script>

<style type="text/css">
table.dataTable td {
	vertical-align:top;
}
table.dataTable tbody tr:hover, .highlightBackground {
	background-color:#ffff99;
}
</style>

<script type="text/javascript">
app.controller('DatasetController', ['$scope', 'CommonService', function ($scope, CommonService) 
{
	// Input data
	$scope.datasets = ${json.dumps(datasets) | n};
	$scope.selectedDataset = $scope.datasets[${selectedDatasetIndex}];
	$scope.sampleGroups = ${json.dumps(sampleGroups) | n};
	var samples = ${json.dumps(samples) | n};	// array of dictionaries - doesn't have to be a scope variable
	var distances = ${distances};	// array of arrays
	var sampleGroupColours = ${json.dumps(sampleGroupColours, default=decode_b, indent=4) | n};
	var sampleGroupOrdering = ${json.dumps(sampleGroupOrdering) | n};
	
	// used for subset of sample group items when the user selects them
	var samplesSubset = samples;
	var distancesSubset = distances;

	// Initialise or declare all scope variables
	// Try to select "cell_lineage" as default selectedSampleGroup if it exists
	$scope.selectedSampleGroup = ($scope.sampleGroups.indexOf("cell_lineage")!=-1)? "cell_lineage" : $scope.sampleGroups[0];
	$scope.rows;	// used for table rows
	$scope.selectedRows = [];   // used for selecting table rows
	//$scope.plots = ["multidimensional scaling plot", "minimum spanning tree"];
	$scope.plots = ["multidimensional scaling plot"];
	$scope.selectedPlot = $scope.plots[0];
	$scope.plotname = '';	// just title of the graph - set this after plot
	$scope.showLabels = false;
	$scope.commonService = CommonService;
	
	// mds parameters
	$scope.mdsDimensions = ['1,2','1,3','1,4','2,3','2,4','3,4'];
	$scope.selectedMdsDimensions = $scope.mdsDimensions[0];
	
	//scaled to shrink down to fit on the page better 
	$scope.helptext = "<div style='width:500px;'><p>This page is used to explore the relationship between cell types in each dataset. " + 
		"<b>Multidimensional scaling plot (MDS)</b> is a form of principle components analysis. " + 
		"It projects distances in higher dimensions onto 2 dimensions, " +
		"hence changing dimensions to show gives you different projections.</p>" +
		//"<b>Multidimensional scaling plot (MDS)</b> is a form of principle components analysis, and <b>minimum spanning tree</b> connects nearest neighbours without looping.</p>" +
		"<p>Tips on using this page</p>" +
		"<ul style='padding-left:15px'>" +
		//"<li>Click on run button to run the selected method on the dataset.</li>" + 
		"<li>Toggle labels for each point using 'show labels' checkbox.</li>" +
		'<li>Select a sample group to change the labels assigned to each point.</li>' +
		'<li>Use the checkboxes in the table to re-draw the plot using only selected subsets.</li>' +
		"<li>Plot has the option to select dimensions other than the first two.</li>" +
		"<li>Plot can be zoomed and moved around - useful for crowded areas.</li>" +
		'<li>Clicking on a point will show a line plot showing the scaled distance of the selected point to all other points.</li></ul></div>';

	// Work out colour dictionary for all sample groups
	var colourFromSampleGroup = {};	// {'celltype':{'B':'#fff',...},...}
	for (var j=0; j<$scope.sampleGroups.length; j++) 
	{	
		var sampleGroup = $scope.sampleGroups[j];
		
		// Work out a list of unique sample group values for this sample group
		uniqueSampleGroupItems = [];
		for (var i=0; i<samples.length; i++)
			if (uniqueSampleGroupItems.indexOf(samples[i][sampleGroup])==-1) uniqueSampleGroupItems.push(samples[i][sampleGroup]);
		
		// This array is used to select from distinctColours
		var colours = {};
		for (var i=0; i<uniqueSampleGroupItems.length; i++)
			if (sampleGroup in sampleGroupColours && uniqueSampleGroupItems[i] in sampleGroupColours[sampleGroup]) {
				var colour = sampleGroupColours[sampleGroup][uniqueSampleGroupItems[i]];
				if (colour.indexOf('rgb')!=-1) {  // colour has been specified using rgb, so convert to hex
					colour = colour.replace("rgb","").replace("(","").replace(")","").split(",").map(function(x) { return parseInt(x);} );
					colour = rgbToHex(colour[0], colour[1], colour[2]);
				}
				colours[uniqueSampleGroupItems[i]] = colour;
			}
			else
				colours[uniqueSampleGroupItems[i]] = i<CommonService.distinctColours.length? CommonService.distinctColours[i] : '#ccc';
		
		// Assign this dictionary to colourFromSamplGroup
		colourFromSampleGroup[sampleGroup] = colours;
	}	
	
	// Main plot function
	$scope.plot = function()
	{
		// fetch a subset of distances based on selected rows ----------------------------
		var sampleIds = [];	// sampleIds to include based on selectedRows
		for (var i=0; i<$scope.rows.length; i++) {
			if ($scope.selectedRows[i])
 				for (var j=0; j<$scope.rows[i].sampleIds.length; j++)
 					sampleIds.push($scope.rows[i].sampleIds[j]);
		}
		var distanceIndices = [];	// used for subset of distances
		samplesSubset = [];
		for (var i=0; i<samples.length; i++) {
			if (sampleIds.indexOf(samples[i].sampleId)!=-1) {	// keep this sampleId
				samplesSubset.push(samples[i]);
				distanceIndices.push(i);
			}
		}
		distancesSubset = [];
		for (var i=0; i<distances.length; i++) {
			var row = [];
			if (distanceIndices.indexOf(i)!=-1) {	// keep this row
				for (var j=0; j<distances[i].length; j++)	// keep this column
					if (distanceIndices.indexOf(j)!=-1) row.push(distances[i][j]);
				distancesSubset.push(row);
			}
		}
		
		if (distancesSubset.length==0) return;
		
		// plot based on selectedPlot ----------------------------------------------------	
		if ($scope.selectedPlot.indexOf("multidimensional")!=-1) // mds plot
		{
			$scope.plotname = 'mds plot';
			var mdsCoordinates = mdsClassic(distancesSubset,4);	// no need to recalculate if done earlier
			var coordinates = [];	// should look like [{'name':'sample1', 'x':2.3, 'y':-1.4, 'z':4.2}, ...]
			var coordinateIndex = $scope.selectedMdsDimensions.split(',')
			for (var i=0; i<samplesSubset.length; i++)
				coordinates.push({'x':mdsCoordinates[i][parseInt(coordinateIndex[0])-1], 
								  'y':mdsCoordinates[i][parseInt(coordinateIndex[1])-1], 
								  'name':samplesSubset[i][$scope.selectedSampleGroup], 
								  'colour':colourFromSampleGroup[$scope.selectedSampleGroup][samplesSubset[i][$scope.selectedSampleGroup]]});
			scatterPlot.draw(coordinates);
			scatterPlot.xAxisLabel.text('dimension ' + coordinateIndex[0]);
			scatterPlot.yAxisLabel.text('dimension ' + coordinateIndex[1]);
		}
		else if ($scope.selectedPlot.indexOf("minimum")!=-1) // mst plot
		{
			$scope.plotname = 'mst plot';
			var labels = [];	// [{'name':'LSK', 'colour':'#ccc'},...]
			for (var i=0; i<samplesSubset.length; i++)
				labels.push({'name':samplesSubset[i].sampleId,
							 'display':samplesSubset[i][$scope.selectedSampleGroup], 
							 'colour':colourFromSampleGroup[$scope.selectedSampleGroup][samplesSubset[i][$scope.selectedSampleGroup]]});
			mstPlot.draw({'data': distancesSubset, 'labels':labels});
		}

	}

	// Update the labels in the plot - should trigger when selected sample group changes
	$scope.updateLabels = function()
	{
		if ($scope.selectedPlot.indexOf('multidimensional')!=-1)
		{
			if (scatterPlot.data==null) return; // we haven't plotted yet
			// Update scatterPlot - name and colours of circles, and labels
			for (var i=0; i<samplesSubset.length; i++) {
				var sg = $scope.selectedSampleGroup;
				scatterPlot.data[i].colour = colourFromSampleGroup[sg][samplesSubset[i][sg]];
				scatterPlot.data[i].name = samplesSubset[i][sg];
			}
			scatterPlot.draw();
		}
		else if ($scope.selectedPlot.indexOf('minimum')!=-1)
		{
			if (mstPlot.data==null) return; // haven't plotted yet
			
		}
	}
	
	// show or hide labels
	$scope.toggleLabels = function()
	{
		scatterPlot.showLabels = $scope.showLabels;
		if ($scope.showLabels) {
			scatterPlot.label.style('opacity',1);
			scatterPlot.setOverlappingLabelText();
		}
		else
			scatterPlot.label.style('opacity',0);
	}
	
	// Runs when checkbox state changes in the table. Only run the plot if mds, as t-sne should 
	// only run when button is pressed.
	$scope.updatePlot = function()
	{
		if ($scope.selectedRows.length==0 || 
			($scope.selectedPlot.indexOf('multidimensional')!=-1 && scatterPlot.data==null)	|| 
			($scope.selectedPlot.indexOf('minimum')!=-1 && mstPlot.data==null)) return;	// haven't plotted yet
		$scope.plot();
	}
	
	// Set the table of sample data - should trigger when selected sample group changes
	$scope.setTable = function()
	{
		$scope.rows = [];	// clear previous entries
		
		// work out a list of sample ids for each sample group item
		var sampleIdsFromSampleGroupItem = {};
		for (var i=0; i<samples.length; i++) {
			var sampleGroupItem = samples[i][$scope.selectedSampleGroup];
			if (!(sampleGroupItem in sampleIdsFromSampleGroupItem)) sampleIdsFromSampleGroupItem[sampleGroupItem] = [];
			sampleIdsFromSampleGroupItem[sampleGroupItem].push(samples[i]['sampleId']);
		}
		
		// populate table rows
		for (var sampleGroupItem in sampleIdsFromSampleGroupItem) {
			$scope.rows.push({'sampleGroupItem':sampleGroupItem, 
							  'sampleIds':sampleIdsFromSampleGroupItem[sampleGroupItem],
							  'colour':colourFromSampleGroup[$scope.selectedSampleGroup][sampleGroupItem]});
			$scope.selectedRows.push(true);
		}
		
		if ($scope.selectedSampleGroup in sampleGroupOrdering) { // order $scope.rows according to these
			// From http://stackoverflow.com/questions/13304543/javascript-sort-array-based-on-another-array
			var sorting = sampleGroupOrdering[$scope.selectedSampleGroup];
			$scope.rows = $scope.rows.map(function(row) {
				var n = sorting.indexOf(row.sampleGroupItem);
				sorting[n] = '';
				return [n, row];
			}).sort().map(function(j) { return j[1] })
		}
	}
	
	// Use this to select either all rows or none on the table quickly
	$scope.selectRows = function(allOrNone)
	{
		for (var i=0; i<$scope.selectedRows.length; i++)
			$scope.selectedRows[i] = allOrNone=='all';
		if (allOrNone=='all') $scope.updatePlot();
	}
		
	// define mouseover functions - pass these into plots that accept mouseover functions
	function circleMouseover(d,j)
	{
		CommonService.showTooltip('<p>' + d.name + '</p>');
		for (var i=0; i<$scope.rows.length; i++)
			$scope.rows[i].highlight = d.name==$scope.rows[i].sampleGroupItem;
		$scope.$apply();
	}
	function circleMouseout(d,j)
	{
		CommonService.hideTooltip();
		for (var i=0; i<$scope.rows.length; i++)
			$scope.rows[i].highlight = false;
		$scope.$apply();
	}
	
	function drawDistLinePlot(d,i)
	{
		// Create data array needed for distlinePlot. Mainly need distances from d to all other items
		// first gather distances for selected item together with their properties
		var data = [];
		for (var j=0; j<distancesSubset[i].length; j++) {
			data.push({'name':samplesSubset[j][$scope.selectedSampleGroup], 'distance':distancesSubset[i][j], 'colour':colourFromSampleGroup[$scope.selectedSampleGroup][samplesSubset[j][$scope.selectedSampleGroup]]});
		}
		data.sort(function(x,y) {
			if (x.distance<y.distance) return -1;
			else if (x.distance>y.distance) return 1;
			else return 0;
		});
		distlinePlot.draw(data);
	}
	
	$scope.rowMouseover = function(rowIndex,evt)
	{
		var sampleGroupItem = $scope.rows[rowIndex].sampleGroupItem;		
		CommonService.showTooltip('<b>' + sampleGroupItem + '</b><br/>' + $scope.rows[rowIndex].sampleIds.join(', '),evt);

		if (scatterPlot.data!=null) {	// highlight matching item on the plot
			scatterPlot.highlightLabel(sampleGroupItem);
			scatterPlot.highlightCircle(sampleGroupItem);
		}
	}
	$scope.rowMouseout = function(rowIndex)
	{
		var sampleGroupItem = $scope.rows[rowIndex].sampleGroupItem;
		CommonService.hideTooltip();

		if (scatterPlot.data!=null) {	// put matching item's state back to how it was
			scatterPlot.removeHighlightLabel(sampleGroupItem);
			scatterPlot.removeHighlightCircle(sampleGroupItem);
		}		
	}
	
	// Reload the page with selected dataset if this is changed
	$scope.changeDataset = function()
	{
		window.location.assign("/datasets/analyse?datasetName=" + $scope.selectedDataset.name);
	}
	
	// Function to save figures to file ---------------------------------------------------
	// figureIndex is used to denote either the main figure or the dist line plot: {0,1}
	$scope.saveFigure = function(figureIndex)
	{
		var html = figureIndex==0? scatterPlot.svgAsHtml() : distlinePlot.svgAsHtml();
		CommonService.showLoadingImage();

		// Since the svg doesn't include control div area, construct a useful file name using information there
		var filename = [$scope.selectedDataset.name, $scope.selectedPlot, $scope.selectedSampleGroup].join('_') + '.png';

        // convert svg to canvas		
		canvg('canvas', html);		

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
	
	
	
	$scope.closeSaveFigureDialog = function() { $scope.showSaveFigureDialog = false; }
	
	// plotting objects
	var scatterPlot = new scatterplot.ScatterPlot({'svg':d3.select("#mainSvg"), 'showLabels':$scope.showLabels, 'hideOverlappingLabels':true,
									   'mouseover':circleMouseover, 'mouseout':circleMouseout, 'click':drawDistLinePlot});
	var distlinePlot = new distlineplot.DistLinePlot({'svg':d3.select("#distlineSvg"), 'mouseover':circleMouseover, 'mouseout':circleMouseout});
	var mstPlot = new mstplot.MstPlot({'svg':d3.select("#mainSvg"), 'mouseover':circleMouseover, 'mouseout':circleMouseout, 'click':drawDistLinePlot});
	
	$scope.setTable();
	$scope.plot();
}]);

</script>

</head>

<body>
<div id="wrap">  
${common_elements.banner()}

	<div id="content">
		<div id="shadow"></div>
		<div style="margin-left:40px; margin-right:40px;" ng-controller="DatasetController">
			<h1 class="marquee" style="display:inline;">Dataset: {{selectedDataset.name}}</h1>
			<img src="/images/question_mark.png" ng-mouseover="commonService.showTooltip(helptext,$event)" ng-mouseout="commonService.hideTooltip()" width="20px" height="20px" style="margin-left:10px; opacity:0.7">
			<table width="100%" style="margin-top:20px;">
			<tr>
				<td style="width:20px;">
					<select ng-model="selectedDataset" ng-options="ds.name group by ds.species for ds in datasets" ng-change="changeDataset()"></select>
				</td>
				<td>
					<!--<select ng-model="selectedPlot" ng-options="plot for plot in plots" ng-change="plot()"></select>&nbsp;-->
					<!-- <button ng-click="plot()">run</button> -->
					<span ng-show="selectedPlot=='multidimensional scaling plot'" style="margin-left:50px;">
						dimensions to show: <select ng-model="selectedMdsDimensions" ng-options="dim for dim in mdsDimensions" ng-change="plot()"></select>
						&nbsp; <input type="checkbox" ng-model="showLabels" ng-change="toggleLabels()"/>show labels &nbsp;
					</span>
				</td>
				<td style="padding-left:20px;">
					<a href="#" ng-click="showSaveFigureDialog=true">save figure</a>
				</td>
				<td>
					<select ng-model="selectedSampleGroup" ng-options="sampleGroup for sampleGroup in sampleGroups" ng-change="setTable(); updateLabels();"></select>
					&nbsp; <a href="#" ng-click="selectRows('all')">select all</a> &#47; <a href="#" ng-click="selectRows('none')">none</a>
				</td>
			</tr>
			<tr>
				<td></td>
				<td></td>
				<td></td>
				<td style="height:500px; vertical-align:top;" rowspan="2" >
					<table st-table="rows" class="dataTable" style="margin-top:10px">
						<thead>
						<tr>
							<th st-sort="sampleGroupItem">
								{{selectedSampleGroup}} ({{rows.length}}) 
							</th>
						</tr>
						</thead>
						<tbody style="display: block">
						<tr ng-repeat="row in rows" ng-class="{highlightBackground: row.highlight}" ng-mouseenter="rowMouseover($index,$event)" ng-mouseout="rowMouseout($index)">
							<td><input type="checkbox" ng-model="selectedRows[$index]" ng-change="updatePlot()">
							<span style="margin-left:10px; color:{{row.colour}}; font-size:24px; line-height:15px; vertical-align:middle;">&bull;</span>
							{{row.sampleGroupItem}} ({{row.sampleIds.length}})</td>
						</tr>
						</tbody>
					</table>
				</td>
			</tr>
			<tr>
				<td colspan="2"><p style="text-align:center">{{plotname}}</p><svg id="mainSvg" width="800" height="500" style="vertical-align:top;"></svg></td>
				<td><div style="width:125px; height:500px; overflow:auto;"><svg id="distlineSvg" width="120" height="450" style="vertical-align:top;"></svg></div></td>
			</tr>
			</table>
			
			<modal-dialog show='showSaveFigureDialog'>
				<div style="overflow:auto; padding:10px;">
					<h3>Save Figure</h3>
					<p>You can save the figures on this page as png files for print quality. You should manipulate the figure appropriately using the filters
					and zooms provided before saving, as you won't be able to interact with the figure once it is in the png format.</p>
					<p>Multiple figures are provided separately for full flexibility.</p>
					<p><a href="#" ng-click="saveFigure(0)">MDS plot</a> &#47; <a href="#" ng-click="saveFigure(1)">Line distance plot</a></p>
					<p><button ng-click="closeSaveFigureDialog()">close</button></p>
				</div>
			</modal-dialog>

		</div><!-- DatasetController -->
		<br style="clear:both;" />
	
	${common_elements.footer()}
	</div> <!-- content -->

</div> <!-- wrap -->  
<canvas ng-show=false id="canvas"></canvas>
</body>
</html>

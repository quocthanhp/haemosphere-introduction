<%
'''
This template is mainly used to show a list of genesets as a table. Several features exist, including exporting
table data and filtering.

Input vars
----------
historyGenesets: a list of Geneset instances corresponding to current sessions history of genesets.
	The first geneset is assumed to be the latest geneset, and will be displayed as a table.
savedGenesets: a list of Geneset instances corresponding to saved genesets. Always an empty list for guest users.
datasets: [{'name':'haemopedia', 'species':'MusMusculus'}, ...]
guestUser: boolean to denote if current user is guest, in which case there is no option to save genesets.
downloadfile: bloolean to denote if R file download should happen when the page is first loaded.

Note that some preliminary testing indicates that client side pagination is enough to speed up loading of 
this page for large genesets. (No pagination => ~6 seconds for ~5000 genes, pagination => ~3 seconds. 
As the number of items shown on one page increases, the load time will also increase regardless of pagination.)
'''
import json
selectedDatasetName = request.session.get("selectedDatasetName")
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<head>
<title>Haemosphere - Geneset Page</title>

<%namespace name="common_elements" file="common.mako"/>
${common_elements.header_elements()}
	
<style type="text/css">
ul {
	padding-left: 0px;
}
ul a:link {
	color:#666666;
}
ul h3, ul h3 a:link {
	color:coral;
	margin-bottom: 0px;
}
ul a:hover, ul h3 a:hover {
	color:#6699ff;
}
ul li {
	margin-top:5px;
}

</style>

<script type="text/javascript">
app.controller('GenesetController', ['$scope', '$location', '$http', 'CommonService', function($scope, $location, $http, CommonService) 
{
	// Set variables from server
	// genes should look like {'ENSMUSG00000043435': {'GeneSymbol':'TNF', ... }, ...}.
	var genes = ${historyGenesets[0].to_json()  if len(historyGenesets)>0 else "[]" | n};  // must use quotes for "{}" when using | n.
	var datasets = ${json.dumps(datasets) | n};
	var guestUser = ${json.dumps(guestUser) |n};
	var selectedDatasetName = ${json.dumps(selectedDatasetName) |n};
	var downloadfile = ${json.dumps(downloadfile) | n};

	$scope.commonService = CommonService;
	$scope.helptext = "<b>Tips on using this page</b>" +
		"<p>[click on me for a quick tour of this page]</p>" +
		"<ul style='padding-left:15px'><li>You can sort columns by clicking on column header.</li>" + 
		"<li>Click on a filter to quickly filter the list.</li>" +
		"<li>Click on gene symbol to see its expression profile, or compare its expression to other genes or across species and dataset by choosing from the expression column.</li>" +
		"<li>Hover over synonyms to see the full text if not visible.</li>" +
		"<li>Select orthologues, show a heatmap or upload a dataset by choosing from the symbols next to this help icon. </li>"+
		'<li>Come back to this page at any time by clicking on "Genes" link in the top banner of every page.</li>' +
		"<li>You can edit, save or export this geneset by choosing items from the Action list above the table.</li>" +
		'<li>Click on any gene set in history to view and make it the current gene set.</li>' +
		'<li>Click on "History" to manage gene sets in history.</li></ul>';

	// Tour text and ordering are defined here. It looks like hidden elements can't be used with default settings, so not using these on any hidden elements for now.
	$scope.tourtext = {	'geneSymbol': {'step':1, 'text':"Click here to plot expression profile of this gene."},
						'geneFunction': {'step':2, 'text':"You can also plot expression profile of the gene by using this selection. Other plots types are also available here."},
						'sortByColumn': {'step':3, 'text':"Click on a column header to sort by that column."},
						'logoFunctions': {'step':4, 'text':"Here are some functions which take you to a different page, such as heatmap or show the orthologue gene set. Come back anytime by using Genes menu at the top."},
						'pageFunctions': {'step':5, 'text':"These functions keep you on this page, and helps you to manipulate the members of this gene set or export/save."},
						'filters': {'step':6, 'text':"Use this to quickly filter the gene set. Note that many functions are sensitive to the filtered list, so remove the filters if you want to run the function on the full gene set."},
						'history': {'step':7, 'text':"This holds the history of gene sets. Click on any to see that gene set. Click on History to manage the list."},
						'savedGenesets': {'step':8, 'text':"These gene sets have been saved on the server under your username. Manage these by clicking on Saved Genesets."},
						//'correlation': {'step':9, 'text':"This column shows the Pearson correlation between this gene and the selected gene"},
						//'highExpression': {'step':10, 'text':"This column has the difference between the average expression of the selected group and the average expression of the highest expressing of all other groups"},
						//'pvalue': {'step':11, 'text':"This column contains the false discovery rate (corrected p value) for the difference in expression"},
						//'aveExp': {'step':12, 'text':"This column gives the average log2 expression of the gene across all cell types in the dataset" }
	};

	// For functions per gene. Note that model variable has to take multiple genes into account
	$scope.geneFunctions = ["select...", "expression profile", "multi species", "gene vs gene"];

	// main table of current geneset -----------------------------------------------------
	// genes are used in the table as rows - convert EnsemblId key to GeneId
	$scope.allRows = [];
	for (var i=0; i<genes.length; i++) {
		var dict = genes[i];
		dict['GeneId'] = dict['EnsemblId'];
		delete dict['EnsemblId'];
		if ('Synonyms' in dict && dict['Synonyms']!=null)
			dict['Synonyms'] = dict['Synonyms'].replace(/[|]/g, ', ');	// replace vertical bars with commas in synonyms
		dict['selected'] = false;	// used to make individual row selections
		dict['selectedGeneFunction'] = $scope.geneFunctions[0];
		$scope.allRows.push(dict);
	}

	$scope.filteredRows = $scope.allRows;	// subset of allRows after all filters have been applied
	$scope.shownRows = [].concat($scope.filteredRows);	// subset of filteredRows to show on paginated page. Note this copies references (see http://lorenzofox3.github.io/smart-table-website/, stSafeSrc)
	$scope.rowsPerPage = 100;	// default value of rows for pagination - larger values will slow down the table
	$scope.showTopTableScoreColumns = $scope.allRows.length>0 && 'logFC' in $scope.allRows[0];	// boolean to determine if score columns should be shown
	$scope.showCorrScoreColumns = $scope.allRows.length>0 && 'correlation' in $scope.allRows[0];	// correlation score column
	$scope.showGeneralScoreColumns = $scope.allRows.length>0 && 'score' in $scope.allRows[0];	// general score column

	// selecting individual rows -----------------------------------------------
	// Set checkbox state for all shown rows. state should be true or false.
	$scope.setSelectedState = function(state)
	{
		for (var i=0; i<$scope.shownRows.length; i++)
			$scope.shownRows[i].selected = state;
	}
	
	// saved and history genesets -----------------------------------------------
	$scope.historyGenesets = ${json.dumps([{'name':gs.name, 'description':gs.description, 'size':gs.size()} for gs in historyGenesets]) | n};
	$scope.savedGenesets = ${json.dumps(savedGenesets) | n};
	$scope.selectedGeneset = $scope.historyGenesets.length>0? $scope.historyGenesets[0] : {'name':'No Geneset', 'description':'', 'size':0};
	$scope.showGenesets = function()
	{
		$scope.showDialog = true;
		$scope.dialogSelection = "genesets";
	}

	// show geneset at index from history
	$scope.showGenesetFromHistory = function(index)
	{
		window.location.assign('/geneset/current?index=' + index);
	}
	
	// load a saved geneset
	$scope.showGenesetFromSaved = function(name)
	{
		window.location.assign('/geneset/current?savedGeneset=' + name);
	}

	// Save current geneset to server.
	$scope.saveGeneset = function()
	{	
		// Name of geneset has to be unique
		if ($scope.savedGenesets.indexOf($scope.selectedGeneset.name)!=-1) {
			alert("This geneset name already exists in saved genesets. Each name must be unique in saved genesets.");
			return;
		}
		
		CommonService.showLoadingImage();

		// Since we're saving the filtered geneset, pass on relevant geneIds if filtered list is different to full
		var geneIds = [];
		if ($scope.allRows.length!=$scope.filteredRows.length) {
			for (var i=0; i<$scope.filteredRows.length; i++)
				geneIds.push($scope.filteredRows[i]['GeneId']);
		}
		
		$http.post("/geneset/save", { "name": $scope.selectedGeneset.name, "description": $scope.selectedGeneset.description, "geneIds": geneIds}).
			then(function(response) {	
				CommonService.hideLoadingImage();
				// update saved genesets
				$scope.savedGenesets.push($scope.selectedGeneset.name);
				$scope.showDialog = false;
			}, function(response) {
				CommonService.hideLoadingImage();
				$scope.showDialog = false;
				alert('There was an unexpected error with saving this gene set.');
			});
	}
	
	// Edit the name of the selected geneset, where type="saved" or "history".
	// For saved genesets, id should be geneset name, while for history genesets it should be the index.
	$scope.renameGeneset = function(type, id, currentName)
	{
		CommonService.showLoadingImage();
		var newName = prompt("New name of the geneset", currentName);
		if (newName==null) return;
		$http.get("/geneset/rename", {
			params: { type:type, id:id, newName:newName }
		}).
		success(function(response) {	
			CommonService.hideLoadingImage();
			if (type=='saved') {
				$scope.savedGenesets[response['success']] = newName;
			}
			else if (type=='history') {
				$scope.historyGenesets[id].name = newName;
			}
			$scope.showDialog = false;
		}).
		error(function(response) {
			CommonService.hideLoadingImage();
			$scope.showDialog = false;
			alert('There was an unexpected error while renaming this geneset.');
		});
	}

	// Delete selected or all genesets, where type="saved" or "history".
	// For saved genesets, id should be geneset name, while for history genesets it should be the index.
	// Omitting id implies deleting all genesets of that type.
	$scope.deleteGeneset = function(type, id)
	{
		var message = (id==null)? "Are you sure you want to delete all " + type + " genesets? This can't be undone."
			: "Are you sure you want to delete this geneset?";
		if (confirm(message)) {
			CommonService.showLoadingImage();
			$http.get("/geneset/delete", {
				params: {'type':type, 'id':id}
			}).
			success(function (response) {	
				CommonService.hideLoadingImage();
				if (type=='saved') {
					if (id==null) $scope.savedGenesets = [];
					else $scope.savedGenesets.splice($scope.savedGenesets.indexOf(id),1);
				}
				else if (type=='history') {
					if (id==null) $scope.historyGenesets.splice(1,$scope.historyGenesets.length-1);
					else $scope.historyGenesets.splice(id,1);
				}
				$scope.showDialog = false;
			}).
			error(function(response) {
				CommonService.hideLoadingImage();
				$scope.showDialog = false;
				console.log('error with /geneset/delete');
			});
		}
	}

	// filtering data -----------------------------------------------
	$scope.scoreFilter = function(scoreKey, comparatorString) 
	{
		return function(item) {
			return comparatorString=='>='? item[scoreKey]>=0 : item[scoreKey]<0;
		};
	};
	$scope.filters = {};	// keep track of filtered attributes, should look like {'Species':'MusMusculus', ...}
	$scope.setFilteredRows = function()	// set $scope.filteredRows based on $scope.filters
	{
		$scope.commonService.showLoadingImage();
		var newrows = [];
		for (var i=0; i<$scope.allRows.length; i++) {
			var keepRow = true;	// keep this row unless it fails any filter condition
			for (var key in $scope.filters) {	// key is the name of the filter, eg. 'Species'
				if ($scope.filters[key]!=null &&	// ignore null value for this filter
					(key=='Species' && $scope.filters[key]!=$scope.allRows[i][key]) ||	// if key is not species, assume filter is for score column
					($scope.filters[key]=='>=0' && $scope.allRows[i][key]<0 || $scope.filters[key]=='<0' && $scope.allRows[i][key]>=0))
				{
					keepRow = false;
					break;
				}
			}
			if (keepRow) newrows.push($scope.allRows[i]);
		}
		$scope.filteredRows = newrows;
		CommonService.hideLoadingImage();
	}
	$scope.setFilter = function(attribute, value)
	{
		if ($scope.filters[attribute]==value) return;	// already filtered
		$scope.filters[attribute] = value;
		$scope.setFilteredRows();
	}
	
	// function on each gene -----------------------------------------------
	$scope.applyGeneFunction = function(row)
	{
		if (row.selectedGeneFunction.indexOf("expression")!=-1)
			$scope.showExpression(row.GeneId);
		else if (row.selectedGeneFunction.indexOf("multi species")!=-1)
			window.location.assign('/expression/multispecies?geneId=' + row.GeneId);
		else if (row.selectedGeneFunction.indexOf("gene vs gene")!=-1)
			window.location.assign('/expression/genevsgene?gene1=' + row.GeneId);
	}
	
	// geneset functions --------------------------------------
	$scope.showHeatmapDialog = function()
	{
		// check if there is mixed species in filtered list of genes
		var species = $scope.filteredRows[0]['Species'];
		for (var i=1; i<$scope.filteredRows.length; i++) {
			if ($scope.filteredRows[i]['Species']!=species) {
				alert("You have mixed species in your filtered list of genes. Apply the species filter first, as heatmap works on a single dataset and each dataset is species specific.");
				return;
			}
		}
		// check that selected species for geneset is accessible by user and set $scope.datasets which is shown on the dialog
		$scope.datasets = datasets.filter(function(d) { return d.species==species; });
		if ($scope.datasets.length==0) {
			alert("You don't have access to any datasets with the same species as your filtered list of genes.");
				return;
		}
		$scope.showDialog = true;
		$scope.dialogSelection = "heatmap";
		$scope.datasetNames = $scope.datasets.map(function(d) { return d.name; });
		$scope.selectedDataset = {'name':$scope.datasetNames.indexOf(selectedDatasetName)==-1? $scope.datasets[0].name : selectedDatasetName};	// must use this trick to propagate selection within dynamic model back to controller
	}
	
	$scope.showHeatmap = function($event)
	{
		var geneIds = [];
		if ($scope.filteredRows.length<$scope.allRows.length) {	// send selected gene ids with the request
			$scope.heatmapGeneIds = $scope.filteredRows.map(function(d) { return d.GeneId; }).join('&');
		}
		$event.target.submit();
	}
	
	$scope.showExpression = function(geneId)
	{
		window.location.assign('/expression/show?geneId=' + geneId);
	}
	
	$scope.getOrthologueGeneset = function()
	{
		// check that there is at least one orthologue
		var noOrth = true;
		for (var i=0; i<$scope.allRows.length; i++) {
			if ($scope.allRows[i].Orthologue!='') {
				noOrth = false;
				break;
			}
		}
		if (noOrth) {
			alert('No gene has orthologue in this geneset');
		}
		else {
			CommonService.showLoadingImage();
			// If filter has been applied find orthologues only on the filtered genes
			var geneIds = [];
			if ($scope.filteredRows.length<$scope.allRows.length) {	// send selected gene ids with the request
				for (var i=0; i<$scope.filteredRows.length; i++)
					geneIds.push($scope.filteredRows[i]['GeneId']);
			}
			$http.post("/geneset/orthologue", {"geneIds": geneIds}).
				then(function(response) {	
					CommonService.hideLoadingImage();
					if (response.data.success>0)
						window.location.assign('/geneset/current')
					else 
						alert(response.data.error);
				}, function(response) {
					CommonService.hideLoadingImage();
					alert('There was an unexpected error fetching orthologues.');
				});
		}
	}
	
	// table actions ------------------------------------------------
	$scope.actions = ['keep selected','remove selected','export...','save...'];	// available actions
	
	// Should trigger when an action is selected. Control what is shown on the dialog.
	$scope.setAction = function()
	{
		if ($scope.actions.indexOf($scope.selectedAction)==-1) return;
		
		if ($scope.selectedAction.indexOf('keep')>-1 || $scope.selectedAction.indexOf('remove')>-1) {	// modify rows based on selection
			// Obtain a list of selected gene ids
			var geneIds = [];
			for (var i=0; i<$scope.shownRows.length; i++)
				if ($scope.shownRows[i].selected) geneIds.push($scope.shownRows[i].GeneId);
			
			if (geneIds.length==0) {
				alert("First select at least one row and use this feature to manually modify the genes in this gene set.");
				$scope.selectedAction = null;	// reset the selector
				return;
			}
			
			CommonService.showLoadingImage();
			$http.post("/geneset/modify", { "action": $scope.selectedAction.split(' ')[0], "geneIds": geneIds}).
				then(function(response) {	
					CommonService.hideLoadingImage();
					if (response.data.success>0)
						window.location.assign('/geneset/current')
					else 
						alert(response.data.error);
				}, function(response) {
					CommonService.hideLoadingImage();
					alert('There was an unexpected error with this operation.');
				});
		}
		else if ($scope.selectedAction.indexOf('venn diagram')>-1) {
			$scope.showDialog = true;
			$scope.dialogSelection = "venn";
		}
		else if ($scope.selectedAction.indexOf('export')>-1) {
			$scope.showDialog = true;
			$scope.dialogSelection = "export";
			$scope.setExportText();
		}
		else if ($scope.selectedAction.indexOf('save')>-1) {
			// Must be logged in
			if (guestUser) {
				alert("This function is only available for registered users who have logged in. Click on the login link in the top right hand corner to login or register.");
			} else {					
				$scope.showDialog = true;
				$scope.dialogSelection = "save";
			}
		}
		else if ($scope.selectedAction.indexOf('orthologue')>-1) {

		}
		else if ($scope.selectedAction.indexOf('GO')>-1) {
			showLoadingImage();
			$.ajax({
				url: "/geneset/goanalysis",
				data: {},
				type: "GET",
				cache: false,
				success: function (jd, st, xd) {	
					hideLoadingImage();
					if (jd['url'])
						window.location.assign(jd['url'])
					else 
						alert('There was an error with /geneset/goanalysis:\n' + jd['error']);
				},
				error: function(xq, st, er) {
					hideLoadingImage();
					console.log('error with /geneset/goanalysis');
				} 
			});
		}
		$scope.selectedAction = null;	// reset the selector
	}
	
	// This sets export text which goes into the text area.
	$scope.setExportText = function(listType)
	{
		var columns = "GeneId\tGeneSymbol\tEntrzId";
		if ($scope.showTopTableScoreColumns) columns += '\tlogFC\tadjPValue\tAveExpr';
		if ($scope.showCorrScoreColumns) columns += '\tcorrelation';
		if ($scope.showGeneralScoreColumns) columns += '\tscore';
		
		var textArray = [columns];
		var rowsToUse = listType=="all"? $scope.allRows : $scope.filteredRows;
		for (var i=0; i<rowsToUse.length; i++) {
			var gene = rowsToUse[i];
			var geneAttr = [gene.GeneId, gene.GeneSymbol, gene.EntrezId].join('\t');
			if ($scope.showTopTableScoreColumns) geneAttr += '\t' + [gene.logFC, gene.adjPValue, gene.AveExpr].join('\t');
			if ($scope.showCorrScoreColumns) geneAttr += '\t' + gene.correlation;
			if ($scope.showGeneralScoreColumns) geneAttr += '\t' + gene.score;
			textArray.push(geneAttr);
		}
		$scope.exportText = textArray.join('\n');
	}

	$scope.closeDialog = function() { $scope.showDialog = false; }

	if (downloadfile) {
		window.location.assign("/downloadfile?&filetype=RFile");
	}
}]);
</script>

</head>

<body>
<div id="wrap"> 
		
 
${common_elements.banner()}

	<div id="content">
		${common_elements.flashMessage('dataerror')}
		<div id="shadow"></div>
		<div style="margin-left:40px; padding-right:220px; overflow:hidden;" ng-controller="GenesetController">
		
			<div style="float:left; width:180px;"> <!---------- side panel -------------->
			<ul data-step="{{tourtext.filters.step}}" data-intro={{tourtext.filters.text}}>
				<h3 style="margin-bottom:10px">Filters</h3>
				<b>Species</b>
				<li style="padding-left:5px" ng-show="!filters['Species'] || filters['Species']=='MusMusculus'">
					<a href="#" ng-click="setFilter('Species','MusMusculus')">mouse ({{(filteredRows | filter: {Species:'MusMusculus'}).length}})</a>
					<span ng-show="filters['Species']!=null"><a href="#" ng-click="setFilter('Species',null)">(x)</a></span>
				</li>
				<li style="padding-left:5px" ng-show="!filters['Species'] || filters['Species']=='HomoSapiens'">
					<a href="#" ng-click="setFilter('Species','HomoSapiens')">human ({{(filteredRows | filter: {Species:'HomoSapiens'}).length}})</a>
					<span ng-show="filters['Species']!=null"><a href="#" ng-click="setFilter('Species',null)">(x)</a></span>
				</li>
				<div ng-show="showTopTableScoreColumns" style="margin-top:10px">
					<b>Scores</b>
					<li style="padding-left:5px" ng-show="!filters['logFC'] || filters['logFC']=='>=0'">
						<a href="#" ng-click="setFilter('logFC','>=0')">logFC>=0 ({{(filteredRows | filter: scoreFilter('logFC','>=')).length}})</a>
						<span ng-show="filters['logFC']!=null"><a href="#" ng-click="setFilter('logFC',null)">(x)</a></span>
					</li>
					<li style="padding-left:5px" ng-show="!filters['logFC'] || filters['logFC']=='<0'">
						<a href="#" ng-click="setFilter('logFC','<0')">logFC<0 ({{(filteredRows | filter: scoreFilter('logFC','<')).length}})</a>
						<span ng-show="filters['logFC']!=null"><a href="#" ng-click="setFilter('logFC',null)">(x)</a></span>
					</li>
				</div>
				<div ng-show="showCorrScoreColumns" style="margin-top:10px">
					<b>Correlation</b>
					<li style="padding-left:5px" ng-show="!filters['correlation'] || filters['correlation']=='>=0'">
						<a href="#" ng-click="setFilter('correlation','>=0')">correlation>=0 ({{(filteredRows | filter: scoreFilter('correlation','>=')).length}})</a>
						<span ng-show="filters['correlation']!=null"><a href="#" ng-click="setFilter('correlation',null)">(x)</a></span>
					</li>
					<li style="padding-left:5px" ng-show="!filters['correlation'] || filters['correlation']=='<0'">
						<a href="#" ng-click="setFilter('correlation','<0')">correlation<0 ({{(filteredRows | filter: scoreFilter('correlation','<')).length}})</a>
						<span ng-show="filters['correlation']!=null"><a href="#" ng-click="setFilter('correlation',null)">(x)</a></span>
					</li>
				</div>
				<div ng-show="showGeneralScoreColumns" style="margin-top:10px">
					<b>Score</b>
					<li style="padding-left:5px" ng-show="!filters['score'] || filters['score']=='>=0'">
						<a href="#" ng-click="setFilter('score','>=0')">score>=0 ({{(filteredRows | filter: scoreFilter('score','>=')).length}})</a>
						<span ng-show="filters['score']!=null"><a href="#" ng-click="setFilter('score',null)">(x)</a></span>
					</li>
					<li style="padding-left:5px" ng-show="!filters['score'] || filters['score']=='<0'">
						<a href="#" ng-click="setFilter('score','<0')">score<0 ({{(filteredRows | filter: scoreFilter('score','<')).length}})</a>
						<span ng-show="filters['score']!=null"><a href="#" ng-click="setFilter('score',null)">(x)</a></span>
					</li>
				</div>
			</ul>
			<ul data-step="{{tourtext.history.step}}" data-intro={{tourtext.history.text}}>
				<h3><a href='#' ng-click="showGenesets()">History</a></h3>
				<li ng-repeat="gs in historyGenesets track by $index|limitTo:5">
					<a href='#' ng-click='showGenesetFromHistory($index)' ng-mouseover='commonService.showTooltip(gs.name,$event)' ng-mouseout='commonService.hideTooltip()'>{{gs.name|limitTo:25}}</a>
				</li>
			</ul>
			% if not guestUser:
			<ul data-step="{{tourtext.savedGenesets.step}}" data-intro={{tourtext.savedGenesets.text}}>
				<h3><a href='#' ng-click="showGenesets()">Saved Genesets</a></h3>
				<li ng-repeat="name in savedGenesets track by $index|limitTo:5">
					<a href='#' ng-click='showGenesetFromSaved(name)' ng-mouseover='commonService.showTooltip(name,$event)' ng-mousout='commonService.hideTooltip()'>{{name|limitTo:25}}</a>
				</li>
				<li ng-show="savedGenesets.length>5"><a href='#' ng-click='showSavedGenesets()'>...</a></li>
			</ul>
			% endif
			
			</div> <!---------- side panel -------------->


			<div style="margin-right:-220px; margin-left:auto; width:100%; float:right; padding-right:40px;">
				<table width="100%"><tr>
					<td>
						<table><tr><td>
						<h1 class="marquee" style="display:inline;">
							<a href="#" style="color:inherit" ng-mouseover="commonService.showTooltip(selectedGeneset.description,$event)" ng-mouseout="commonService.hideTooltip()">
								{{selectedGeneset.name | limitTo:50}}{{selectedGeneset.name.length>50? '..' : ''}}</a>
						</h1> 
						<span style="font-size:16px; margin-left:20px;">({{selectedGeneset.size}} genes)</span>
						</td><td>
						<img src="/images/question_mark.png" ng-mouseover="commonService.showTooltip(helptext,$event)" 
							ng-mouseout="commonService.hideTooltip()" onclick="javascript:introJs('#content').setOption('showStepNumbers',true).start();" 
							width="20px" height="20px" style="margin-top:10px; margin-left:20px;">
						<span style="padding-top:10px;" data-step="{{tourtext.logoFunctions.step}}" data-intro={{tourtext.logoFunctions.text}}>
						<a href="/searches?selectedSearch=0"><img src="/images/upload_genes.png" ng-mouseover="commonService.showTooltip('Upload a list of genes to create a new gene set',$event)" ng-mouseout="commonService.hideTooltip()" style="margin-top:10px; margin-left:5px;"></a>
						<a href ng-click="showHeatmapDialog()"><img src="/images/heatmap.png" ng-mouseover="commonService.showTooltip('Show heatmap for this gene set',$event)" ng-mouseout="commonService.hideTooltip()" style="margin-top:10px; margin-left:5px;"></a>
						<a href ng-click="getOrthologueGeneset()"><img src="/images/orthologue.png" ng-mouseover="commonService.showTooltip('Fetch a geneset of orthologues',$event)" ng-mouseout="commonService.hideTooltip()" style="margin-top:10px; margin-left:5px;"></a>
						</span></td></tr></table>
					</td>
					<td style="text-align:right;"></td>
				</tr></table>
				<table st-persist="genesetTable" st-table="shownRows" st-safe-src="filteredRows" class="dataTable" style="border-top:0px; margin-top:0px;">
					<thead>
					<tr style="background:white"><th colspan="8" style="border:0px; width:850px; text-align:right;">
						<input st-search="" placeholder="search this table..." type="text"/>&nbsp;
						<select ng-model="selectedAction" ng-options="action for action in actions" ng-change="setAction()" data-step="{{tourtext.pageFunctions.step}}" data-intro={{tourtext.pageFunctions.text}}>
							<option value="" disabled="disabled">Action...</option>
						</select>
					</th></tr>
					<tr>
						<th style="width:50px;" ><a href ng-click="setSelectedState(true)">all</a> &#47; <a href ng-click="setSelectedState(false)">none</a></th>


                        <th style="width:150px;" st-sort="GeneSymbol" data-step="{{tourtext.sortByColumn.step}}" data-intro={{tourtext.sortByColumn.text}}>Symbol</th>
						<th style="width:300px;" st-sort="Synonyms">Synonyms</th>
						<th style="width:400px;" st-sort="Description">Description</th>
						<th>Expression</th>
						<th style="width:80px;">Links</th>
						<th style="width:100px;" st-sort="Orthologue">Orthologue</th>
						<th style="width:50px;" st-sort="Species" ng-style="{'width':'15%', 'border-right': showTopTableScoreColumns || showCorrScoreColumns || showGeneralScoreColumns? 'None' : '1px solid #cccccc'}">Species</th>
						<th style="width:50px;" st-sort="logFC" ng-show="showTopTableScoreColumns">logFC</th>
						<th style="width:50px;" st-sort="adjPValue" ng-show="showTopTableScoreColumns" ng-mouseover='commonService.showTooltip("p value that has been corrected for multiple testing to false discovery rate", $event)' ng-mouseout="commonService.hideTooltip()">adj P</th>
						<th style="width:50px;" st-sort="AveExpr" ng-show="showTopTableScoreColumns" ng-mouseover='commonService.showTooltip("Log2 average expression across entire dataset (not just groups of interest)", $event)' ng-mouseout="commonService.hideTooltip()">AveExpr</th>
						<th style="width:50px;" st-sort="correlation" ng-show="showCorrScoreColumns" ng-mouseover='commonService.showTooltip("Pearson correlation of this gene with search gene",$event)' ng-mouseout="commonService.hideTooltip()">correlation</th>
						
						<th style="width:50px;" st-sort="score" ng-show="showGeneralScoreColumns">score</th>
					</tr>
					</thead>
					<tbody>
					<tr ng-repeat="row in shownRows" style="background-color:{{row.Species=='MusMusculus'? '#fdf6f5' : '#fff'}}">
						<td style="width:50px;" ><input type="checkbox" ng-model="row.selected"></td>

                        <td style="width:150px;" ng-attr-data-step="{{$index==0? tourtext.geneSymbol.step : undefined}}" ng-attr-data-intro="{{$index==0? tourtext.geneSymbol.text: undefined}}">
							<a href='#' ng-click="showExpression(row.GeneId)" ng-mouseover="commonService.showTooltip('show expression profile for this gene',$event)" ng-mouseout="commonService.hideTooltip()">{{row.GeneSymbol}}</a>
						</td>
						<td style="width:300px;"><span ng-mouseover="commonService.showTooltip(row.Synonyms,$event)" ng-mouseout="commonService.hideTooltip()">{{row.Synonyms | limitTo:20}}{{row.Synonyms.length > 20 ? '...' : ''}}</span></td>
						<td style="width:400px;">{{row.Description}}</td>
						<td ng-attr-data-step="{{$index==0? tourtext.geneFunction.step : undefined}}" ng-attr-data-intro="{{$index==0? tourtext.geneFunction.text: undefined}}">
							<select ng-options="item for item in geneFunctions" ng-model="row.selectedGeneFunction" ng-change="applyGeneFunction(row)"></select>
						</td>
						<td style="width:80px;">
							&nbsp;<a href='http://www.ncbi.nlm.nih.gov/sites/entrez?db=gene&term={{row.EntrezId}}' target="_blank" ng-mouseover="commonService.showTooltip('Go to Entrez site using gene id: '+row.EntrezId,$event)" ng-mouseout="commonService.hideTooltip()"><img src="/images/ncbi.ico" border="0"/></a>
							&nbsp;<a href='http://www.ensembl.org/Gene/Summary?g={{row.GeneId}}' target="_blank" ng-mouseover="commonService.showTooltip('Go to Ensembl site using gene id: '+row.GeneId,$event)" ng-mouseout="commonService.hideTooltip()"><img src="/images/ensembl.gif" border="0"/></a>
						</td>
						<td style="width:100px;"><a ng-repeat='item in row.Orthologue.split(",")' 
							ng-href='/expression/show?geneId={{row.Orthologue.split(",")[$index].split(":")[0]}}' 
							ng-mouseover="commonService.showTooltip('show expression profile for this gene',$event)" 
							ng-mouseout="commonService.hideTooltip()">
							   {{row.Orthologue.split(",")[$index].split(":")[1]}}{{$index<(row.Orthologue.split(",").length-1)? ", " : ""}}
						</a></td>
						<td style="width:50px;" ng-style="{'width':'15%', 'border-right': showTopTableScoreColumns || showCorrScoreColumns || showGeneralScoreColumns? 'None' : '1px solid #cccccc'}">{{row.Species}}</td>
						<td style="width:50px;" ng-show="showTopTableScoreColumns">{{row.logFC | number:2}}</td>
						<td style="width:50px;" ng-show="showTopTableScoreColumns">{{row.adjPValue | number:4}}</td>
						<td style="width:50px;" ng-show="showTopTableScoreColumns">{{row.AveExpr | number:2}}</td>
						<td style="width:50px;" ng-show="showCorrScoreColumns">{{row.correlation | number:2}}</td>
						<td style="width:50px;" ng-show="showGeneralScoreColumns">{{row.score | number:2}}</td>
					</tr>
					</tbody>
					<tfoot ng-show="shownRows.length>=rowsPerPage">
					<tr>
						<td colspan="3" style="text-align:right; padding-top:20px;"><input type="text" ng-model="rowsPerPage" size="4"> rows per page</td>
 						<td colspan="3" style="padding-left:50px;"><div st-pagination="" st-items-by-page="rowsPerPage" st-displayed-pages="7"></div></td>
					</tr>
					</tfoot>
				</table>
			</div>
			
			<modal-dialog show='showDialog'>
				<div style="padding:10px;" ng-show="dialogSelection=='export'">
					<h3>Export Geneset</h3>
					<p>Use copy and paste in the text area below.</p>
					<input type="radio" name="exportText" ng-click="setExportText('all')">all genes &nbsp;
					<input type="radio" name="exportText" checked="checked" ng-click="setExportText('filtered')">filtered genes
					<textarea wrap="off" style="width:650px; height:350px; max-height:400px;" ng-model="exportText"></textarea>
					<p><button ng-click="closeDialog()">close</button>
				</div>
				<div style="padding:10px;" ng-show="dialogSelection=='save'">
					<h3>Save Geneset</h3>
					<p>You can save this geneset to the server, which enables later retrieval as well as some other functions.
					Note that filtered list is saved, so remove all filters first if you wish to save the full list of genes.</p>
					<p>Geneset Name: <input type="text" ng-model="selectedGeneset.name"><p>
					<p>Description: <textarea style="width:650px; height:200px; max-height:200px;" ng-model="selectedGeneset.description"></textarea></p>
					<p><button ng-click="saveGeneset()">save</button> <button ng-click="closeDialog()">cancel</button></p>
				</div>
				<div style="padding:10px;" ng-show="dialogSelection=='heatmap'">
					<h3>Show Heatmap</h3>
					<p>You can see a heatmap of this geneset by selecting a dataset below. It uses the filtered list of genes, so remove all
					filters if you want a heatmap on all genes.</p>
					<p>Number of genes (in filtered list): {{filteredRows.length}}</p>
					<p>Species: {{filteredRows[0].Species}}</p>
					<form ng-submit="showHeatmap($event)" action="/geneset/heatmap" method="POST">
						<p>Select Dataset: <select ng-model="selectedDataset.name" ng-options="name for name in datasetNames"></select><p>
						<p><input type="submit" value="Show"/> <button ng-click="closeDialog()">cancel</button></p>
						<input type="hidden" name="geneId" ng-value="heatmapGeneIds"/>
						<input type="hidden" name="datasetName" ng-value="selectedDataset.name"/>
					</form>
				</div>
				<div style="padding:10px;" ng-show="dialogSelection=='genesets'">
					<h3>Manage Genesets</h3>
					<p>You can remove a saved geneset here or clear genesets from history.</p>
					<table width="100%"><tr>
						% if not guestUser:
						<td><b>Saved Genesets</b> (<a href='#' ng-click="deleteGeneset('saved')">delete all</a>)
							<div style="height:320px; overflow:auto;">
								<table st-table="savedGenesets" class="smallTable" cellspacing="0">
								<thead>
									<tr>
										<th style="width:70%">name</th>
										<th>action</th>
									</tr>
								</thead>
								<tbody>
									<tr ng-repeat="name in savedGenesets">
										<td style="width:70%">{{name | limitTo:20}}</td>
										<td><a href='#' ng-click="renameGeneset('saved',name,name)">rename</a> | <a href='#' ng-click="deleteGeneset('saved',name)">delete</a></td>
									</tr>
								</tbody>
								</table>
							</div>
						</td>
						% endif
						<td width="50%"><b>Genesets in History</b> (<a href='#' ng-click="deleteGeneset('history')">delete all</a>)
							<div style="height:320px; overflow:auto;">
								<table st-table="genesets" class="smallTable" cellspacing="0">
								<thead>
									<tr>
										<th style="width:70%">name</th>
										<th>action</th>
									</tr>
								</thead>
								<tbody>
									<tr ng-repeat="geneset in historyGenesets">
										<td style="width:70%">{{geneset.name | limitTo:20}}</td>
										<td><a href='#' ng-click="renameGeneset('history',$index,geneset.name)">rename</a> | <a href='#' ng-click="deleteGeneset('history',$index)">delete</a></td>
									</tr>
								</tbody>
								</table>
							</div>
						</td>
					</tr></table>
				</div> <!-- dialogSelection=='genesets' -->
			</modal-dialog>
						
		</div> <!-- GenesetController -->
		<div style="clear:both;"></div>

		${common_elements.footer()}
	</div> <!-- content -->

</div> <!-- wrap -->  
</body>
</html>



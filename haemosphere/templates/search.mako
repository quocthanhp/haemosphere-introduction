<%
'''
Required inputs
	datasets: a list of dictionaries: [{'name':'haemopedia', 'species':'MusMusculus', 'isRnaSeqData':True}, ...]
	sampleGroups: a dictionary of list keyed on dataset name: {'haemopedia': [{'name':'celltype','items':['B1','B2',..]},...],...}
				  This is a list of sample groups for each dataset.
	selectedSearch: an index number to select a particular search type. This can be left out but will override the saved option if specified.
	topTableString: string, R function string used by expression search, passed here to show the users
'''
import json
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<head>
<title>Haemosphere - Search Page</title>

<%namespace name="common_elements" file="common.mako"/>
${common_elements.header_elements()}

<style type="text/css">
ul {
  list-style-type: none;
  padding: 0px;
}
  
li.search-mode {
  padding: 5px;
  margin-bottom: 5px;
}

li.search-mode a {
  color: #666;
}

.current-search {
  background-color: #feb;
}
  
li.search-mode a:hover {
  color: orange;
  text-decoration: none;
}

table.keywordSearch td {
	padding-top: 15px;
}
</style>

<script type="text/javascript">
app.controller('SearchController', ['$scope', '$http', 'CommonService', function ($scope, $http, CommonService) 
{
	$scope.commonService = CommonService;
	$scope.showDialog = false;
	$scope.diffExpDialog = {downloadRObjects: false};
	
	// There are 5 different modes of "searches".
	$scope.searchModes = ['Keyword Search', 'Differential Expression Search', 'High Expression Search', 'Gene vs Gene Plot', 'Correlated Gene Search'];
	
	// Function to set search mode - also saves this selection to local storage for recall later
	$scope.setSearchMode = function(searchMode)
	{
		if (searchMode==null || $scope.selectedSearchMode==searchMode) return;
		$scope.selectedSearchMode = searchMode;
		//if (!$scope.$$phase) $scope.$apply();
		localStorage.setItem('SearchController:selectedSearchMode',searchMode);	// remember this selection for next time
	}

	// Set selected search based on request
	var selectedSearch = ${json.dumps(selectedSearch) | n};
	if (selectedSearch!=null && selectedSearch>=0 && selectedSearch<$scope.searchModes.length)	// select specified search
		$scope.setSearchMode($scope.searchModes[selectedSearch]);
	else if (localStorage['SearchController:selectedSearchMode'])	// Select previous mode if available from localStorage
		$scope.setSearchMode(localStorage['SearchController:selectedSearchMode']);
	else	// apply default
		$scope.setSearchMode($scope.searchModes[0]);
	
	// Keyword Search div --------------------------------------------
	$scope.searchString = "";
	$scope.searchScopes = [{'display':'gene symbol, synonyms, Ensembl gene id, description', 'value':'general'},
						   {'display':'gene symbol', 'value':'GeneSymbol'},
						   {'display':'Ensembl gene id', 'value':'EnsemblId'},
						   {'display':'Entrez gene id', 'value':'EntrezId'}];
	$scope.selectedSearchScope = $scope.searchScopes[0];
	$scope.species = ['MusMusculus', 'HomoSapiens'];
	$scope.selectedSpecies = null;
	$scope.exactMatch = false;
	
	$scope.keywordSearch = function()
	{
		CommonService.keywordSearch($scope.searchString.trim(), $scope.selectedSearchScope.value, $scope.selectedSpecies, $scope.exactMatch);	// this function defined within common.mako
	}
		
	// Differential Expression Search div ----------------------------
	$scope.datasets = ${json.dumps(datasets) | n};
	$scope.selectedDataset =  $scope.datasets[0];
	if (localStorage['SearchController:selectedDatasetName']) { // try to replace selectedDataset with what's on local storage
		for (var i=0; i<$scope.datasets.length; i++) 
			if ($scope.datasets[i].name==localStorage['SearchController:selectedDatasetName']) {
				$scope.selectedDataset = $scope.datasets[i];
				break;
			}
	}
	$scope.sampleGroups = ${json.dumps(sampleGroups) | n};
	$scope.normalisations = [{"value":"TMM", "display":"TMM normalisation"}, 
							 {"value":"RLE", "display":"RLE normalisation"}, 
							 {"value":"upperquartile", "display":"upperquartile normalisation"}, 
							 {"value":"none", "display":"no normalisation"}];
	$scope.selectedNormalisation = $scope.normalisations[0];
	$scope.applyMinSampleFilter = true;
	$scope.selectedFilterCpm = 0.5;
	$scope.selectedMinSample = 2;
						  
	// High Expression Search variables ----------------------------
	$scope.highExp = {'selectedSampleGroupItem':null};
	
	// Should run whenever dataset changes so that default sample group can be chosen
	$scope.setDefaultSelectedSampleGroup = function()
	{
		$scope.selectedSampleGroup = $scope.sampleGroups[$scope.selectedDataset.name][0];
		localStorage.setItem('SearchController:selectedDatasetName',$scope.selectedDataset.name);	// not working - why?
	}
	
	// Should run whenever sample group changes so that default sample group items can be chosen
	$scope.setDefaultSelectedSampleGroupItems = function()
	{
		$scope.selectedSampleGroupItem1 = $scope.selectedSampleGroup.items[0];
		$scope.selectedSampleGroupItem2 = $scope.selectedSampleGroup.items[1];
		$scope.highExp.selectedSampleGroupItem = $scope.selectedSampleGroup.items[0];
	}
	
	$scope.expressionSearch = function()
	{
		if ($scope.selectedSampleGroupItem1==$scope.selectedSampleGroupItem2) {
			alert("The two selected sample groups are the same.");
			return;
		}

		CommonService.showLoadingImage();
		$http.get("/search/expression", {
			params: {'dataset':$scope.selectedDataset.name, 'sampleGroup':$scope.selectedSampleGroup.name, 
					'sampleGroupItem1':$scope.selectedSampleGroupItem1, 'sampleGroupItem2':$scope.selectedSampleGroupItem2,
					'normalisation':$scope.selectedNormalisation.value, 'filterCpm':$scope.selectedFilterCpm, 
					'minFilterSample':$scope.selectedMinSample, 'downloadRObjects':$scope.diffExpDialog.downloadRObjects}
		}).
		success(function (response) {	
			CommonService.hideLoadingImage();
			// search/keyword places new geneset in session, so return current geneset page if geneset is not null
			if (response['genesetSize']>0)
				window.location.assign("/geneset/current" + (response["downloadRObjects"]=='true'? "?downloadRObjects=true" : ""));
			else if (response['error']!='')
				alert(response['error']);
		}).
		error(function(response) {
			CommonService.hideLoadingImage();
			alert('There was an unexpected error with differential expression calculation.');
		});
	}
	
	$scope.highExpSearch = function()
	{		
		CommonService.showLoadingImage();
		$http.get("/search/highexp", {
			params: { 'dataset':$scope.selectedDataset.name, 
					  'sampleGroup':$scope.selectedSampleGroup.name, 
					  'sampleGroupItem':$scope.highExp.selectedSampleGroupItem }
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
			alert('There was an unexpected error with high expression calculation.');
		});
	}

	$scope.geneVsGenePlot = function()
	{
		window.location.assign("/expression/genevsgene?datasetName=" + $scope.selectedDataset.name);
	}

	$scope.closeDialog = function() { $scope.showDialog = false; }

	$scope.setDefaultSelectedSampleGroup();
	$scope.setDefaultSelectedSampleGroupItems();
}]);

</script>

</head>

<body>
<div id="wrap">  
${common_elements.banner()}

	<div id="content" ng-controller="SearchController">
		<div id="shadow"></div>
		
		<table style="margin-left:30px;">
		<tr>
			<td></td>
			<td><h1 class="marquee" style="margin-left:20px;">{{selectedSearchMode}}{{selectedSearchMode=='Keyword Search'? ' / Upload Gene List' : ''}}</h1></td>
			<td></td>
		</tr>
		<tr>
			<td style="vertical-align:top; width:200px;">
				<ul><li class="search-mode {{mode==selectedSearchMode && 'current-search' || ''}}" ng-repeat="mode in searchModes"><a href="#" ng-click="setSearchMode(mode)">{{mode}}</a></li></ul>
			</td>
				
			<td style="vertical-align:top; padding-left:20px; padding-right:20px;">
				<div ng-show="selectedSearchMode=='Keyword Search'">	
					<p><table class="keywordSearch">
					<tr>
						<td style="vertical-align:top; width:100px; padding-top:0px;">List of keywords:</td>
						<td><textarea id="searchString" ng-model="searchString" rows="10" style="width:350px"></textarea></td>
					</tr>
					<tr>
						<td>Search Scope:</td>
						<td><select ng-model="selectedSearchScope" ng-options="searchScope.display for searchScope in searchScopes"></select></td>			
					</tr>
					<tr>
						<td>Species:</td>
						<td><select ng-model="selectedSpecies" ng-options="s for s in species"><option value="">[all]</option></select></td>			
					</tr>
					<tr>
						<td></td>
						<td><input type="checkbox" ng-model="exactMatch"> use exact match</td>			
					</tr>
					<tr>
						<td colspan="2" style="padding-top:20px; border-bottom:1px solid #ccc;"></td>
					</tr>
					<tr>
						<td colspan="2" style="padding-top:10px;"><button ng-click="searchString=''">Clear</button>&nbsp; <button id="submitKeywordSearch" ng-click="keywordSearch()">Search</button></td>
					</tr>
					</table></p>
				</div>

				<div ng-show="selectedSearchMode=='Differential Expression Search' || selectedSearchMode=='High Expression Search'">
					<p><table width="100%">
					<tr>
						<td>Dataset:</td>
						<td><select ng-model="selectedDataset" 
									ng-options="dataset.name group by dataset.species for dataset in datasets" 
									ng-change="setDefaultSelectedSampleGroup(); setDefaultSelectedSampleGroupItems();">
							</select>
						</td>
						<td></td>
					</tr>
					<tr>
						<td style="padding-top:15px;">Sample group: </td>
						<td style="padding-top:15px;">
							<select ng-model="selectedSampleGroup" 
									ng-options="group.name for group in sampleGroups[selectedDataset.name]" 
									ng-change="setDefaultSelectedSampleGroupItems()">
							</select>
						</td>
						<td style="padding-top:15px;">
							<div ng-show="selectedSearchMode=='Differential Expression Search'">
								<select ng-model="selectedSampleGroupItem1" ng-options="item for item in selectedSampleGroup.items"></select>
								&nbsp; vs &nbsp;
								<select ng-model="selectedSampleGroupItem2" ng-options="item for item in selectedSampleGroup.items"></select>
							</div>
							<div ng-show="selectedSearchMode=='High Expression Search'">
								<select ng-model="highExp.selectedSampleGroupItem" ng-options="item for item in selectedSampleGroup.items"></select>
							</div>
						</td>
					</tr>
					<tr>
						<td></td>
						<td colspan="2" style="padding-top:20px;">
							<div ng-show="selectedDataset.isRnaseq">
								<a href='#' ng-show="!showOptions" ng-click="showOptions=true"> more options...</a>
								<a href='#' ng-show="showOptions" ng-click="showOptions=false"> hide options</a>
								<p><div ng-show="showOptions">
									<select ng-model="selectedNormalisation" ng-options="item.display for item in normalisations"></select><br/>
									<p><input type="checkbox" ng-model="applyMinSampleFilter"/>
									Filter out genes with counts &lt; <input type="text" ng-model="selectedFilterCpm" size="1">
									per million in at least <input type="text" ng-model="selectedMinSample" size="1"> samples</p>
								</div></p>
							</div>
						</td>
					</tr>
					<tr>
						<td></td>
						<td style="padding-top:20px;">
							<button ng-show="selectedSearchMode=='Differential Expression Search'" ng-click="expressionSearch()">Begin Search</button>
							<button ng-show="selectedSearchMode=='High Expression Search'" ng-click="highExpSearch()">Begin Search</button>
						</td>
						<td></td>
					</tr>
					</table></p>
				</div>

				<div ng-show="selectedSearchMode=='Gene vs Gene Plot'">	
					<p><table width="100%">
					<tr>
						<td>Dataset:</td>
						<td><select ng-model="selectedDataset" 
									ng-options="dataset.name group by dataset.species for dataset in datasets" 
									ng-change="setDefaultSelectedSampleGroup(); setDefaultSelectedSampleGroupItems();">
						</select></td>
					</tr>
					<tr><td></td><td style="width:200px; padding-top:20px;"><button ng-click="geneVsGenePlot()">Show Plot</button></td></tr>
					</table></p>
				</div>

				<div ng-show="selectedSearchMode=='Correlated Gene Search'" style="width:600px;">
					<p>For a selected gene within a dataset, you can find other genes with correlated or anti-correlated expression 
					(pearson correlation is used). This function is available from the <a href="/expression/show">gene expression profile</a> page.
					Expression profile page is usually accessed from the gene set page, which shows the result of a search, such as keyword
					or differential expression search.
					</p>
				</div>
			</td>
			<td style="vertical-align:top; width:300px;">
				<div ng-show="selectedSearchMode=='Keyword Search'">
					<p>Search the full list of genes in the system for terms of interest. Use commas or spaces or new lines to search for multiple matches
					Eg. myb, suz12, ENSMUSG00000005672 will search for myb [or] suz12 [or] ENSMUSG00000005672.</p>
					<p>You can also upload a list of genes here by entering a list of gene symbols or ids. 
					Use search scope to ensure matches are made only within selected fields.</p>
				</div>
				<div ng-show="selectedSearchMode=='Differential Expression Search'">
					<p>You can perform differential expression analysis here. Select dataset of interest, then sample group,
					followed by sample group items. Haemosphere will use R package 
					<a href='http://www.bioconductor.org/packages/release/bioc/html/limma.html' target="_blank">limma</a> to perform the analysis for microarrays and voom from limma and the package
					<a href='http://www.bioconductor.org/packages/release/bioc/html/edgeR.html' target="_blank">edgeR</a> to perform the analysis for RNA-seq data.
					You can also <a href ng-click="showDialog=true">view the R script</a> and download the R objects used here.</p>
				</div>
				<div ng-show="selectedSearchMode=='High Expression Search'">
					<p>Find genes with high expression in the selected sample group. Each gene is scored for the difference between the selected
					sample group and the highest value of the rest, and only genes with positive scores are returned. Also, genes with variance &lt 1
					(on log2 scale) are filtered out, as well as those with max &lt (min of dataset +1). Note that for microarray
					datasets, the calculations are done on probes, then collated back to the gene level.</p>
				</div>
				<div ng-show="selectedSearchMode=='Gene vs Gene Plot'">
					<p>Plot gene vs gene. Selecting a dataset here will take you to the plot page with two arbitrarily chosen genes,
					where you can select genes from the dataset.</p>
				</div>
			</td>
		</tr>
		</table>		

		<modal-dialog show='showDialog'>
			<div style="padding:10px;">
				<h3>R function for differential expression analysis</h3>
				<p>The following is the R script used by haemosphere to run differential expression analysis. Note that this is read-only, and 
				is provided for advanced users who would like to understand the underlying method used or to customise the analysis within 
				R themselves (use the download feature under 'Datasets' to obtain the data). 
				There is also an option to download all relevant R objects as an R binary file which can be loaded into R session using
				load() function. Just select the checkbox here first before running the analysis.</p>
				<p><input type="checkbox" ng-model="diffExpDialog.downloadRObjects">download R objects 
					(your download will start after gene set page loads)</p>
				<textarea wrap="off" style="width:100%; height:350px; max-height:400px;">${topTableString}</textarea>
				<p><button ng-click="closeDialog()">close</button></p>
			</div>
		</modal-dialog>
		<br style="clear:both;" />
	
	${common_elements.footer()}
	</div> <!-- content -->

</div> <!-- wrap -->  
</body>
</html>

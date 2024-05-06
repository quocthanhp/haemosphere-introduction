<%
'''
Inputs required
samples: { 'columns':['id','sampleId','celltype',...], 'data':[['0','sample1','B1',...],...]}
celltypes: { 'columns':['id','celltype','synonyms',...], 'data':[['0','B1','',...],...]}
batches: { 'columns':['id','batchId','description',...], 'data':[['0','iltp1234','Nmt1 mutant cells',...],...]}
or
error: string indicating error
'''
import json

%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<head>
<title>Haemosphere - Hematlas Samples</title>

<%namespace name="labsamples_data" file="labsample_modal.mako"/>

<%namespace name="common_elements" file="common.mako"/>
${common_elements.header_elements()}

<link type="text/css" href="/css/modal.css" rel="stylesheet" />

<style type="text/css">
table.dataTable thead {
	display: table-header-group;
}

table.dataTable td {
	vertical-align:top;
}
table.dataTable thead th {
    padding: 5px;
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

.st-selected {
	background-color: #ccc;
}
.updatedCell {
	background-color: #f5ff89;
}
.createdCell {
    background-color: #a7ff66;
}
.deletedCell {
    background-color: #ff7267;
}

#scroll-table {
    table-layout: fixed;
    width: 200px;
}

td, th { 
    width: 200px;
    height: 30px;
}

.scroll-body, .scroll-head {
    width: 1000px;
    margin-left: 200px;
}

.scroll-body {
    overflow: auto;
}

.scroll-head {
    overflow: hidden;
}

#sticky {
    position: relative;
    z-index: 1;
    background-color: white;
    padding-top: 10px;
    top: 0;
}

table.dataTable tbody tr td:first-child, table.dataTable thead th:first-child {
    position: absolute; 
    left: 0;
    top: auto;
    width: 188px;
    border-right: 1px solid #e6e6e6;
}

table.dataTable	thead tr th:first-child {
	background-color: #d0ddf5;
	border-top: 1px solid #e6e6e6;
    margin-top: -1px;
}

.currently-selected {
    background-color: lightblue;

}

</style>

<script type="text/javascript" src="/js/jquery-3.1.1.min.js"></script>

<script type="text/javascript">
app.controller('SamplesController', ['$scope', '$http', 'CommonService', function ($scope, $http, CommonService) 
{
	// Inputs
	% if error:
	$scope.error = ${json.dumps(error) | n};
	% else:
	$scope.table = {'samples': ${json.dumps(samples) | n}, 'celltypes': ${json.dumps(celltypes) | n}, 'batches': ${json.dumps(batches) | n}};
	% endif
	
	$scope.listOnlyCols = {'samples':['celltype','batchId'], 'celltypes':['tissue'], 'batches':[]};
	
	// Maintain record of data in columns
    $scope.tableLists = {'samples': {}, 'celltypes': {}, 'batches':{}};

    
        for (var key in $scope.tableLists) {
            for (var j = 2; j < $scope.table[key].columns.length; j++) {
                var temp = [];
                for (var i=0; i < $scope.table[key].data.length; i++) {
                    var tempData = $scope.table[key].data[i][j];
                    if(tempData) {
    	                temp.push($scope.table[key].data[i][j]);
                    }
                }        
                // Only get unique values
                temp = temp.filter((value, index, currentVal) => currentVal.indexOf(value) === index);
                $scope.tableLists[key][$scope.table[key].columns[j]] = temp.sort();
            }	    
        }    

        // Keep track of all celltypes
        var temp = [];
		for (var i=0; i<$scope.table['celltypes'].data.length; i++) {
			temp.push($scope.table['celltypes']['data'][i][1]);
		}
		$scope.tableLists['samples']['celltype'] = temp.sort();		

        // Keep track of all batches
		var temp = [];
		for (var i=0; i<$scope.table['batches'].data.length; i++) {
			temp.push($scope.table['batches']['data'][i][1]);
		}
		$scope.tableLists['samples']['batch'] = temp.sort();

	var temp = [];
	for (var i=0; i<$scope.table['samples'].data.length; i++) {
		temp.push($scope.table['samples']['data'][i][1]);
	}    
    $scope.allIds = { 'samples': temp.sort(), 'celltypes': $scope.tableLists['samples']['celltype'], 'batches': $scope.tableLists['samples']['batch']} ;
	
	
	$scope.commonService = CommonService;
	$scope.tableTypes = ['samples','celltypes','batches'];
	$scope.selectedTableType = $scope.tableTypes[0];
	
	$scope.selectedRowIndex = null;
	
	$scope.changesToSave = {'samples':[], 'celltypes':[], 'batches':[]};	// keep track of changes to save [{'rowId':'BEMP', 'column':'cell_lineage', 'value':'Megakaryocyte Lineage'},...]
	$scope.changesToCreate = {'samples':[], 'celltypes':[], 'batches':[]};  // Keep track of entirely new entries to create
	$scope.changesToDelete = {'samples':[], 'celltypes':[], 'batches':[]};  // Keep track of entries to be deleted
	$scope.showConfirmSaveDialog = false;
	$scope.saveDialogVariables = {'makeBackup':false}; // Currently not required
	
	// Because we have dynamic columns when a dataset is selected, st-sort doesn't work. So we do our own sorting here.
	$scope.sortedColumn = {'samples':null, 'celltypes':null, 'batches':null};	// currently sorted column
	$scope.sortDirection = {'samples':1, 'celltypes':1, 'batches':1};	// +1 for ascending, -1 for descending
	$scope.sortColumn = function(tableType, column)
	{		
		// any rows with missing columns will cause weird behaviour when sorting, since the sort algorithm seems to 
		// use the first element of sorted row to determine the columns to show
		
		if ($scope.sortedColumn[tableType]==column) {	// clicked on currently sorted column, so change sort direction
			$scope.sortDirection[tableType] *= -1;	// so 1 will become -1, vice versa
		}
		else {	// clicked on a column not currently sorted, so set currently sorted column to this one
			$scope.sortedColumn[tableType] = column;
			$scope.sortDirection[tableType] = 1;
		}
		
		doColumnSort(tableType);
			
	}
	
	doColumnSort = function(tableType) {
		var table = $scope.table[tableType];
		var columnIndex = table.columns.indexOf($scope.sortedColumn[tableType]);
		table.data.sort(function(a,b) { 
			if (a[columnIndex]<b[columnIndex]) return -1*$scope.sortDirection[tableType];
			else if (a[columnIndex]>b[columnIndex]) return 1*$scope.sortDirection[tableType];
			else return 0;
		});			
	}
	
	$scope.setSelectedRowIndex = function(index) { $scope.selectedRowIndex = index; }
	
		
	// Update a value of the table. Should be invoked by double clicking on a table cell.
	$scope.updateEntry = function(tableType, id, rowId, colIndex, currentValue)
	{
		$scope.updateData = { 'id' : id, 'colIndex' : colIndex, 'tableType' : tableType, 
			'column' : $scope.table[tableType].columns[colIndex], 'rowId' : rowId, 
			'currentValue' : currentValue, 'newValue' : currentValue };

		$scope.updateEntryModal = true;
	}
	
	$scope.doUpdateEntry = function()
	{
		if ($scope.updateData['colIndex']==1 && $scope.allIds[$scope.selectedTableType].data.indexOf($scope.updateData['newValue'])!=-1) {
			alert("Can't change this value because it already exists (first column of each table should have unique fields).");
			return;
		}
		
		$scope.table[$scope.updateData['tableType']].data[$scope.selectedRowIndex][$scope.updateData['colIndex']] = $scope.updateData['newValue'];

		$scope.changesToSave[$scope.updateData['tableType']].push({'id':$scope.updateData['id']? $scope.updateData['id'] : null, 'rowId': $scope.updateData['colIndex']==1? $scope.updateData['currentValue'] : $scope.updateData['rowId'], 'column':$scope.updateData['column'], 'currentValue':$scope.updateData['currentValue'], 'newValue':$scope.updateData['newValue'] });
		$scope.updateEntryModal = false;

	}
	
	
	$scope.easyRead = function(str) 
	{
		if(typeof str === 'undefined' || str === null) {
			return;
		} else {
			return str.replace(/_/g," ").replace(/\w\S*/g, function(word){return word.charAt(0).toUpperCase() + word.substr(1).toLowerCase();});
		}
	}
	
	
	$scope.getCellClass = function(tableType, rowId, column, rowIndex)
	{
	    var cellClass = '';
	    if($scope.selectedRowIndex == rowIndex) {
	        cellClass = 'currently-selected';
	    }
	    
		var matching = $scope.changesToCreate[tableType].filter(function(d) { return d.sample_id==rowId || d.celltype==rowId || d.batchId==rowId; });
		if (matching.length>0) {
		    cellClass = 'createdCell';
		}

		var matching = $scope.changesToSave[tableType].filter(function(d) { return (d.rowId==rowId || d.newValue==rowId) && d.column==column; });
		if (matching.length>0) {
		    cellClass = 'updatedCell';
		}

		var matching = $scope.changesToDelete[tableType].filter(function(d) { return d.rowId==rowId; });
		if (matching.length>0) {
		    cellClass = 'deletedCell';
		}
		
		return cellClass;
	}
	
	$scope.closeConfirmSaveDialog = function()	{ $scope.showConfirmSaveDialog = false;	}
	

	$scope.saveChanges = function()
	{
		CommonService.showLoadingImage();
		$http.post("/grouppages/HiltonLab/samples_save", {'update':$scope.changesToSave, 'create':$scope.changesToCreate, 'delete':$scope.changesToDelete, 'makeBackup':$scope.saveDialogVariables.makeBackup}).
			then(function(response) {	// get user from server
				CommonService.hideLoadingImage();
				$scope.closeConfirmSaveDialog();
				updateRelationships();
				// clear changesToSave and changesToCreate
				$scope.changesToSave = {'samples':[], 'celltypes':[], 'batches':[]};
				$scope.changesToCreate = {'samples':[], 'celltypes':[], 'batches':[]};
				$scope.changesToDelete = {'samples':[], 'celltypes':[], 'batches':[]};
			}, function(response) {
				CommonService.hideLoadingImage();
				alert('There was an unexpected error with save.');
			});
	}
	
	updateRelationships = function() {
		for(var i = 0; i < $scope.changesToSave['batches'].length; i++) {
			if($scope.changesToSave['batches'][i]['column'] === $scope.table['batches']['columns'][1]) {
				// Update sample relationship
				for(var j = 0; j < $scope.table['samples']['data'].length; j++) {
					if($scope.table['samples']['data'][j][11] === $scope.changesToSave['batches'][i]['currentValue']) {
						$scope.table['samples']['data'][j][11] = $scope.changesToSave['batches'][i]['newValue'];
					}
				}
			}
		}
		for(var i = 0; i < $scope.changesToSave['celltypes'].length; i++) {
			if($scope.changesToSave['celltypes'][i]['column'] === $scope.table['celltypes']['columns'][1]) {
				// Update sample relationship
				for(var j = 0; j < $scope.table['samples']['data'].length; j++) {
					if($scope.table['samples']['data'][j][12] === $scope.changesToSave['celltypes'][i]['currentValue']) {
						$scope.table['samples']['data'][j][12] = $scope.changesToSave['celltypes'][i]['newValue'];
					}
				}
			}
		}		
	}
	
	 	
}]);

</script>

</head>

<body ng-cloak>
<div id="wrap">
${common_elements.banner()}

	<div id="content" ng-controller="SamplesController">
		<div id="shadow"></div>
		<div style="margin-left:40px; margin-right:40px;">
			<h1 class="marquee">Hiltonlab Samples</h1>
			% if error:
			<p>{{error}}</p>
			% else:
			<p>This page contains all sample data generated by Hilton Lab, and is intended to serve as the master database of all samples, regardless
			whether they end up in Haemosphere or not.<br/> If you are a user in the HiltonLab group, you are able to edit this table, by double clicking 
			on a cell or using one of the options. </p>
            <div id="sticky-anchor">
            <div id="sticky">			
			    <div style='overflow:hidden'>
				    <div style='float:left; margin-left:20px; margin-right:20px;'>
				    <a href ng-click="selectedTableType='samples'" ng-style="{'font-weight':selectedTableType=='samples'? 'bold' : 'normal'}">samples</a> &#47; 
				    <a href ng-click="selectedTableType='celltypes'" ng-style="{'font-weight':selectedTableType=='celltypes'? 'bold' : 'normal'}">celltypes</a> &#47;
				    <a href ng-click="selectedTableType='batches'" ng-style="{'font-weight':selectedTableType=='batches'? 'bold' : 'normal'}">batches</a>
		    		</div>
			
			    	<div style='float:left'>${labsamples_data.newLabsample()}</div>

				    <div style='float:left'>${labsamples_data.deleteLabsample()}</div>
		        		
				    <div style='float:left; margin-left:20px; margin-right:20px;'>
				    Number of changes made: {{changesToSave['samples'].length + changesToSave['celltypes'].length + changesToSave['batches'].length + changesToCreate['samples'].length + changesToCreate['celltypes'].length + changesToCreate['batches'].length + changesToDelete['samples'].length + changesToDelete['celltypes'].length + changesToDelete['batches'].length}}&nbsp;
				    <button ng-click="showConfirmSaveDialog=true">Save</button>
				    </div>
			    </div>
			

                <div style="position: relative">
                    <div class="scroll-head" id="scroll-column-headers">
                    <table id="scroll-table" class="dataTable" style="margin-bottom:0px; border-bottom:0px;" >
                        
                        <thead>
                             <th ng-repeat="column in table[selectedTableType].columns" ng-if="$index>0"
		    		            ng-click="sortColumn(selectedTableType,column)" 
			    	            ng-class="sortedColumn[selectedTableType]==column? (sortDirection[selectedTableType]>0? 'st-sort-ascent' : 'st-sort-descent') : ''">{{column}}</th>
		                </thead>
                    </table>
                    </div>
                </div>
            </div>
            </div>

            <div style="position: relative">
                <div class="scroll-body" id="scroll-content">
                    <table id="scroll-table" class="dataTable" style="margin-right:0px; border-right:0px; margin-top:0px; border-top:0px;">
                        <tbody>
                            <tr ng-repeat="row in table[selectedTableType].data" ng-click="setSelectedRowIndex($index)" ng-init="rowIndex = $index">
	                            <td ng-repeat="column in table[selectedTableType].columns" 
	                                ng-if="$index>0"
	                                ng-dblclick="updateEntry(selectedTableType, row[0],row[1], $index, row[$index])"
		                  	        ng-class="getCellClass(selectedTableType,row[1],column, rowIndex)">{{row[$index]}}</td>
			                </tr>		
                        </tbody>
                    </table>
                </div>
            </div>

		
			% endif
		</div>
		<br style="clear:both;" />

		${labsamples_data.updateLabsample()}

		${labsamples_data.saveAllChanges()}		

	${common_elements.footer()}
	</div> <!-- content -->

</div> <!-- wrap -->  
</body>
</html>


<script type="text/javascript">
$("#scroll-content").scroll(function() {
    $("#scroll-column-headers").scrollLeft($("#scroll-content").scrollLeft());
});

$(document).scroll(function() {
    var window_top = $(this).scrollTop();
    var div_top = $('#sticky-anchor').offset().top;
    if (window_top > div_top) {
        $("#sticky").css({
            "position": "fixed",
        });
        $("#scroll-content").css({
            "margin-top": "105px",
        });
    } else {
        $("#sticky").css({
            "position": "relative",
        });
        $("#scroll-content").css({
            "margin-top": "0",
        });
    }
});

</script>
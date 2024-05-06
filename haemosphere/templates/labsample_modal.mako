<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<%def name="newLabsample()">
<script type="text/javascript">

app.controller('NewSampleController', ['$scope', '$http', 'CommonService', function ($scope, $http, CommonService) 
{
	$scope.tableFields = {
        'samples' : 
        	{
        	title: 'New Sample', 
        	id: "sample_id",
			},
		'celltypes' :
			{
			title: 'New Celltype', 
        	id: "celltype",
			 },
		'batches' :
			{
			title: 'New Batch', 
        	id: "batch_id",
			} 
	};
	
	$scope.saveMessage = '';

    $scope.newEntry = function(startingValues)
    {
		$scope.entryValues = startingValues;

		$scope.entryName = $scope.tableFields[$scope.selectedTableType]['id'];
		$scope.title = $scope.tableFields[$scope.selectedTableType]['title'];    

		$scope.isEmptyEntry = true;
		$scope.pasteEntireEntry = false;
		$scope.newEntryModal = true;
		document.getElementById('required').style.borderColor = "inherit";
    }
	
	$scope.duplicateEntry = function() 
	{
        // Get current entry data	
	    var data = $scope.table[$scope.selectedTableType].data[$scope.selectedRowIndex];
	    var cols = $scope.table[$scope.selectedTableType].columns;
	    
	    // Merge data and column names into dictionary
	    var entry = {};
	    for (var i = 2; i < cols.length; i++) {
	        entry[cols[i]] = data[i];
	    } 	  
	    
        $scope.newEntry(entry);
        $scope.isEmptyEntry = false;
	}
	
	$scope.splitFields = function() 
	{
		var entireEntry = document.getElementById('newEntireEntry').value;
		var separator = document.getElementById('splitcriteria').value;
	
		var values = [];
		if(separator == "comma") {
			values = entireEntry.split(',');
		} else {
			values = entireEntry.split('\t');
		}

		for (var i = 0; i < values.length; i++) {
			values[i] = values[i].trim();
		}

	    // Get current entry data	
	    var cols = $scope.table[$scope.selectedTableType].columns;
	    
	    // Merge values and column names into dictionary
	    var entry = {};
	    numFields = values.length;

	    for (var i = 1; i < cols.length; i++) {
			if (i <= numFields) {
		        entry[cols[i]] = values[i-1];			
			} else {
				entry[cols[i]] = null;
			}
	    } 	 
	    
		$scope.newEntry(entry);
	}
	
	
	$scope.saveNewEntry = function() 
	{	
		if($scope.entryValues[$scope.entryName] == null ||  $scope.allIds[$scope.selectedTableType].indexOf($scope.entryValues[$scope.entryName])!=-1) {
			document.getElementById('required').style.borderColor = "red";
			return;
		}	
		
		// loop through each column in table and add new entry data to each
		var temp = [];
		var cols = $scope.table[$scope.selectedTableType].columns;
		for (var i = 1; i < cols.length; i++) {
			var col = cols[i];
			if (col in $scope.entryValues) {
				temp[i] = $scope.entryValues[col];
			
			} else {
				temp[i] = "";			
			}
		}
		$scope.changesToCreate[$scope.selectedTableType].push($scope.entryValues);		
		$scope.table[$scope.selectedTableType].data.push(temp);
		$scope.newEntryModal = false;
	}

	$scope.easyRead = function(str) 
	{
		if(typeof str === 'undefined' || str === null) {
			return;
		} else {
			return str.replace(/_/g," ").replace(/\w\S*/g, function(word){return word.charAt(0).toUpperCase() + word.substr(1).toLowerCase();});
		}
	}
	
	
	
	
}]);

</script>

<div ng-controller="NewSampleController">

<button ng-click='newEntry({})' style="margin-left:20px; margin-right:20px;">Add New Entry</button>
<button ng-click='duplicateEntry()' ng-disabled="selectedRowIndex === null" style="margin-left:20px; margin-right:20px;">Copy Selected Row</button>


<b ng-show="saveMessage !== ''">{{saveMessage}}</b>

<modal-dialog show='newEntryModal'>
	<div class="modal-dialog">	

		<div class="modal-header">
			<h2>{{title}}</h2>
		</div>

		<div class="modal-body">
			<div>
				<div style="margin: 8px; white-space: nowrap; width: 100%">
					<div style="overflow: hidden">
						<label class="field">{{easyRead(entryName)}}</label>
						<input id="required" class="textbox" type="text" ng-model="entryValues[entryName]" ng-model-options="{ updateOn: 'blur' }" auto-focus="newEntryModal">
					</div>
				</div>
			</div>					
			<div ng-repeat="(col, values) in tableLists[selectedTableType]">								
				<div style="margin: 8px; white-space: nowrap; width: 100%">					
					<label class="field">{{easyRead(col)}}</label>
					<div style="overflow: hidden;">
						<select ng-show="!newValue" class="selectbox" style="margin-left: 15px; margin-right: 5px; margin-top: 0px; margin-bottom: 0px" ng-model="entryValues[col]">
							<option ng-repeat="subval in values" ng-value="subval">{{subval}}</option>
							<option value="">None</option>
						</select>
						<input ng-show="newValue" class="textbox" type="text" style="margin-left: 15px; margin-right: 5px; margin-top: 0px; margin-bottom: 0px" ng-model="entryValues[col]" ng-model-options="{ updateOn: 'blur' }">
						<button ng-show="col != 'batch' && col != 'celltype'" ng-click="newValue = !newValue">+</button>		
					</div>
				</div>
			</div>
								
		</div>
			
		<div class="modal-footer">
			<div ng-show="isEmptyEntry">	
				<div>
					<a ng-show="!pasteEntireEntry" ng-click="pasteEntireEntry = true" style="color: blue; text-decoration: underline; float: right;">Paste entry</a>
				</div>
				<div ng-show="pasteEntireEntry" style="float: right;">
			
					<textarea id="newEntireEntry" rows="4" cols="100" style="width: 100%"></textarea>
					<div style="margin: 8px; white-space: nowrap; width: 100%; float: right">

						<div style="overflow: hidden; float: right">
							<select id="splitcriteria">
								<option value='comma'>Comma</option>
								<option value='tab'>Tab</option>
							</select>
						</div>
						<label class="field" style="width: 120px; float: right">Split fields by: </label>

					</div>

					<div style="margin-top:4px">
						<button ng-click="splitFields()" style="float: right; margin-right: 8px">Set Fields</button>
					</div>
				</div>
			</div>
						
			<button ng-click="saveNewEntry()" style="float: right; margin: 8px;">Save</button>
		</div>
		
		

		
	</div>

</modal-dialog>
</div>

</%def>


<%def name="deleteLabsample()"> 

<script type="text/javascript">

app.controller('DeleteSampleController', ['$scope', '$http', 'CommonService', function ($scope, $http, CommonService) 
{	
	$scope.deleteMessage = '';
	$scope.deleteEntryModal = false;
	
	$scope.doDeleteEntry = function()
	{
		var entryId = $scope.table[$scope.selectedTableType].data[$scope.selectedRowIndex][0]
		$scope.changesToDelete[$scope.selectedTableType].push(
			{ 	'rowId':$scope.table[$scope.selectedTableType].data[$scope.selectedRowIndex][1],
				'id':entryId ? entryId : null} );		

		$scope.deleteEntryModal = false;
		
		/*
		CommonService.showLoadingImage();
		$http.post("/grouppages/HiltonLab/delete_samples", $scope.entryValues).
			then(function(response) {
				CommonService.hideLoadingImage();
				$scope.deleteEntryModal = false;
				$scope.deleteMessage = response.data['message'];
				if($scope.deleteMessage === null) {
					$scope.$emit('deleteData', { 'table' : $scope.entryValues['tableType'], 'old_entry' : $scope.entryValues['data']['rowId'] } );
					$scope.entryValues = {'tableType': tableType, 'data': {}};
				}			
			}, function(response) {
				CommonService.hideLoadingImage();
				alert('There was an unexpected error with deleting.');
			});		
			*/	
	}
	
	$scope.easyRead = function(str) 
	{
		if(typeof str === 'undefined' || str === null) {
			return;
		} else {
			return str.replace(/_/g," ").replace(/\w\S*/g, function(word){return word.charAt(0).toUpperCase() + word.substr(1).toLowerCase();});
		}
	}

}]);

</script>

<div ng-controller="DeleteSampleController">

<button ng-click='deleteEntryModal=!deleteEntryModal' ng-disabled="selectedRowIndex === null" style="margin-left:20px; margin-right:20px;">Delete Selected Row</button>
<b ng-show="deleteMessage !== ''">{{deleteMessage}}</b>

<modal-dialog show='deleteEntryModal'>
	<div class="modal-dialog">	

			<h2>Delete from {{easyRead(selectedTableType)}}</h2>
 			
 			<div>
 				<p>Are you sure you want to delete entry <b>{{table[selectedTableType].data[selectedRowIndex][1]}}</b>?</p>
			</div>
			
		<div class="modal-footer">
			<button ng-click="doDeleteEntry()">Yes</button>
		</div>
	</div>

</modal-dialog>
</div>

</%def>






<%def name="updateLabsample()">

<modal-dialog show='updateEntryModal'>
	<div class="modal-dialog">	
		<div class="modal-header">
			<h2>Change the value at {{updateData['rowId']}}, {{updateData['column']}}</h2>
		</div>
		
		<div class="modal-body" style="height: 60px">

			<div style="margin: 8px" ng-if="(updateData.column !== 'batch' && updateData.column !== 'celltype') || selectedTableType !== 'samples'">
				<label class="field">{{easyRead(updateData['column'])}}</label>
				<input class="textbox" type="text" ng-model="updateData['newValue']" ng-model-options="{ updateOn: 'blur' }" auto-focus="updateEntryModal">
			</div>

			<div style="margin: 8px" ng-if="updateData.column === 'celltype' && selectedTableType === 'samples'">
				<label class="field">{{easyRead(updateData['column'])}}</label>
				<select class="selectbox" ng-model="updateData['newValue']" ng-model-options="{ updateOn: 'blur' }">
					<option ng-repeat="celltype in tableLists['samples']['celltype']" ng-value="celltype">{{celltype}}</option>
					<option value="">None</option>
				</select>
			</div>
			<div style="margin: 8px" ng-if="updateData.column === 'batch' && selectedTableType === 'samples'">
				<label class="field">{{easyRead(updateData['column'])}}</label>
				<select class="selectbox" ng-model="updateData['newValue']" ng-model-options="{ updateOn: 'blur' }">
					<option ng-repeat="batch in tableLists['samples']['batch']" ng-value="batch">{{batch}}</option>
					<option value="">None</option>
				</select>
			</div>
		</div>
			
		<div class="modal-footer">
			<button ng-click="doUpdateEntry()">Save</button>
		</div>
	</div>
</modal-dialog>	
		
</%def>


<%def name="saveAllChanges()">

		<modal-dialog show='showConfirmSaveDialog'>
			<div class="modal-header">
				<h2>Confirm Changes to be Saved</h2>
			</div>
			<div class="modal-body">				
				<h3>Update</h3>
				<div ng-repeat="tableType in tableTypes">
					<b>{{tableType}}</b>
					<ul>
						<li ng-repeat="item in changesToSave[tableType]">
							<div ng-if="item.column==null">
								Remove row
							</div>
							<div ng-if="item.column!=null">
								({{item.rowId}}, {{item.column}}): {{item.currentValue}} &rarr; {{item.newValue}}
							</div>
						</li>
					</ul>
				</div>
				<h3>Create</h3>
				<div ng-repeat="tableType in tableTypes">
					<b>{{tableType}}</b>
					<ul>
						<div ng-repeat="item in changesToCreate[tableType]">
							<li> 
								{{item.sample_id || item.celltype || item.batchId}}: 							
							</li>
							<ul>
								<li ng-repeat="(col, val) in item">
									({{col}}): {{val}}
								</li>
							</ul>
						</div>
					</ul>
				</div>
				<h3>Delete</h3>
				<div ng-repeat="tableType in tableTypes">
					<b>{{tableType}}</b>
					<ul>
						<li ng-repeat="item in changesToDelete[tableType]">
							<div> {{item.rowId}} </div>
						</li>
					</ul>
				</div>
			</div>
			<div class="modal-footer">
				##<p><input type="checkbox" ng-model="saveDialogVariables.makeBackup"> make backup (ie. keep copy of previous data before applying changes)</p>
				<p style="margin-top:10px;">
					<button ng-click="saveChanges()">confirm</button> 
					<button ng-click="closeConfirmSaveDialog()">cancel</button>
				</p>
			</div>
		</modal-dialog>
</%def>
<%
import json
userlist = [user.to_json() for user in users]
groups
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<head>
<title>Haemosphere - User Account Page</title>

<%namespace name="common_elements" file="common.mako"/>
${common_elements.header_elements()}

<style type="text/css">
table.main td {
	margin-left:100px;
	padding-top: 10px;
	padding-right: 5px;
	vertical-align: top;
}

div.form-group {
  transition:background-color 1s;
}
div.form-group.form-error { 
  color:#ff6767;
  /* background-color:white; */
  /* background-color:rgba(255,0,0,0.3); */
}
</style>

<script type="text/javascript">
app.controller("UsersController", ["$scope", "$http", "CommonService", function ($scope, $http, CommonService)
{
	$scope.users = ${json.dumps(userlist) | n};
	$scope.allgroups = ${json.dumps(groups) | n};

	//$scope.actions = ["add new user", "add new group", "email all users", "show usage"];
	$scope.actions = ["add new user", "add new group", "email all users"];
	$scope.selectedAction = null;
	$scope.showUsage = false;
    $scope.showEmailDialog = false;

	// Functions for all users/groups -----------------------------------------
	$scope.runAction = function()
	{
		if ($scope.selectedAction=="add new user")
		{
			var details = prompt("Enter username, fullname, email, password, separated by commas");
			if (details!=null)
			{
				var userinfo = details.split(",");
				if (userinfo.length!=4)
					alert("There should be 4 entries.");
				else {
					user = {'username':userinfo[0].trim(), 'fullname':userinfo[1].trim(), 'email':userinfo[2].trim(), 'password':userinfo[3].trim(), 'groups':[]};
					CommonService.showLoadingImage();
					$http.post("/user/manage", {'action':'create_user', 'username':user.username, 'fullname':user.fullname, 'email':user.email, 'password':user.password}).
						then(function(response) {
							CommonService.hideLoadingImage();
							if (response.data["error"])
								alert("There was an unexpected error with user creation: " + response.data["error"]);
							else {	// assume success
								$scope.users.push(user);
							}
						}, function(response) {
							CommonService.hideLoadingImage();
							alert('There was an unexpected error with user creation.');
						});
				}
			}
		}
		else if ($scope.selectedAction=="add new group")
		{
			var group = prompt("Enter group name");
			if (group!=null)
			{
				if ($scope.allgroups.indexOf(group)!=-1)
					alert("Group exists already.");
				else {
					CommonService.showLoadingImage();
					$http.post("/user/manage", { "action": "create_group", "name": group }).
						then(function(response) {
							CommonService.hideLoadingImage();
							if (response.data["error"])
								alert("There was an unexpected error with group creation: " + response.data["error"]);
							else {	// assume success
								$scope.allgroups.push(group);
								//$scope.$apply();
							}
						}, function(response) {
							CommonService.hideLoadingImage();
							alert('There was an unexpected error with group creation.');
						});
				}
			}
		}
		else if ($scope.selectedAction=="email all users")
		{
            $scope.formData.recipients = ""
            for (var i=0; i<$scope.users.length; i++) {
                $scope.formData.recipients += $scope.users[i].username + ",";
            }
            $scope.formData.recipients = $scope.formData.recipients.slice(0, -1);
            $scope.showEmailDialog = true;
		}
		else if ($scope.selectedAction=="show usage")
		{
            // view /user/usage is not currently implemented
            // TODO implement it!
			CommonService.showLoadingImage();
            $http.post("/user/usage", {})
                .then(function(response) {
                    CommonService.hideLoadingImage();
                    $scope.showUsage = true;
                    plotUsage(response.data);
                }, function(response) {
                    CommonService.hideLoadingImage();
                    alert("There was an unexpected error when showing usage.");
                });
		}
		$scope.selectedAction = null;	// reset action selector
	}

	// Functions per user -----------------------------------------
	$scope.manageUser = function(action, user)
	{
		if (action=='addGroup') {	// add group to user
			var group = prompt("Enter group for " + user.username + "\nAvailable groups are:\n" + $scope.allgroups.join(", "), "");
			if (group==null) return;
			else if ($scope.allgroups.indexOf(group)==-1) {
				alert("This group does not exist: " + group);
				return;
			}
				CommonService.showLoadingImage();
				$http.post("/user/manage", { "action": "add_group_to_user", "username": user.username, "groupname":group }).
					then(function(response) {
						CommonService.hideLoadingImage();
						if (response.data["error"])
							alert("There was an unexpected error with adding group to user: " + response.data["error"]);
						else {	// assume success, update attributes user
							user.groups.push(group);
							//$scope.$apply();
						}
					}, function(response) {
						CommonService.hideLoadingImage();
						alert('There was an unexpected error with adding group to user.');
					});
		}
		else if (action=='removeGroup') {	// remove group from user
			var group = prompt("Enter group to remove from " + user.username + "\nAvailable groups are:\n" + user.groups.join(", "), "");
			if (group==null) return;
			else if ($scope.allgroups.indexOf(group)==-1) {
				alert("This group does not exist: " + group);
				return;
			}
			else if (user.groups.indexOf(group)==-1) {
				alert("User " + user.username + " does not belong to group: " + group);
				return;
			}
				CommonService.showLoadingImage();
				$http.post("/user/manage", { "action": "remove_group_from_user", "username": user.username, "groupname":group }).
					then(function(response) {
						CommonService.hideLoadingImage();
						if (response.data["error"])
							alert("There was an unexpected error with removing group from user: " + response.data["error"]);
						else {	// assume success, update attributes user
                            user.groups.splice(user.groups.indexOf(group), 1);
							//$scope.$apply();
						}
					}, function(response) {
						CommonService.hideLoadingImage();
						alert('There was an unexpected error with removing group from user.');
					});
		}
		else if (action=='deleteUser') {
			if (confirm("Are you sure you want to delete this user '" + user.username + "' from the system? This step can't be undone.")) {
				CommonService.showLoadingImage();
				$http.post("/user/manage", { "action": "delete_user", "username": user.username }).
					then(function(response) {
						CommonService.hideLoadingImage();
						if (response.data["error"])
							alert("There was an unexpected error with user update: " + response.data["error"]);
						else {	// assume success, update attributes on $scope.user
							$scope.users.splice($scope.users.map(function(d) { return d.username; }).indexOf(user.username), 1);
							//$scope.$apply();
						}
					}, function(response) {
						CommonService.hideLoadingImage();
						alert('There was an unexpected error with user update.');
					});
			}
		}
		else if (action=='editUser') {
			var details = prompt("Change any of the following fields. username will be checked for uniqueness in the system.",
								 [user.username,user.fullname,user.email].join(','));
			if (details!=null)
			{
				var userinfo = details.split(",");
				if (userinfo.length!=3) {
					alert("There should be 3 entries (separated by commas).");
                    return;
				} else if (user.username!=userinfo[0].trim() && $scope.users.map(function(d) { return d.username; }).indexOf(userinfo[0].trim())!=-1) {
					alert("This username is already used.");
                    return;
				} else {
					CommonService.showLoadingImage();
                    $http.post("/user/manage", { "action": "edit_user",
                                                 "currentUsername": user.username,
                                                 "newUsername": userinfo[0].trim(),
                                                 "fullname": userinfo[1].trim(),
                                                 "email": userinfo[2].trim(), }
                        ).then(function(response) {
                            CommonService.hideLoadingImage();
                            if (response.data["error"])
                                alert("There was an unexpected error with user edit: " + response.data["error"]);
                            else {	// assume success, update attributes on matching user
								for (var i=0; i<$scope.users.length; i++) {
                                    if ($scope.users[i].username==user.username) {
                                        $scope.users[i].username = userinfo[0].trim();
                                        $scope.users[i].fullname = userinfo[1].trim();
                                        $scope.users[i].email = userinfo[2].trim();
                                        //$scope.$apply();
                                    }
                                }
                            }
                        }, function(response) {
                            CommonService.hideLoadingImage();
                            alert('There was an unexpected error with user edit.');
                        });
				}
			} else {
				alert("No user details entered.");
				return;
            }
		}
		else if (action=='emailUser') {
            $scope.formData.recipients = user.username;
            $scope.showEmailDialog = true;
        }
		else if (action=='resetPassword') {
			if (confirm("Are you sure you want to reset the password for " + user.username + "?")) {
				CommonService.showLoadingImage();
                $http.post("/user/manage", { "action": "reset_password", "username": user.username })
                    .then(function(response) {
                        CommonService.hideLoadingImage();
                        if (response.data["error"])
                            alert("There was an unexpected error with password reset: " + response.data["error"]);
                        else {	// assume success, update attributes on matching user
                            user.password = response.data['password'];
                            alert("Password for user " + user.username + " reset to their email address.");
                            return;
                        }
                    }, function(response) {
                        CommonService.hideLoadingImage();
                        alert('There was an unexpected error with password reset.');
                    });
			}
		}
	}

	function plotUsage(data)
	{
		// plot number of users for each date; data looks like
		// {"2015-04-09:jarny":[["11:25:47","/user/users"],["11:26:58","/user/manage"],...], ...}
		var dataByDate = {};
		for (var key in data) {
			var date = key.split(':')[0];
			var username = key.split(':')[1];
			if (!(date in dataByDate)) dataByDate[date] = [];

			// get all actions performed by this user on this date
			var actions = [];
			for (var i=0; i<data[key].length; i++) {
				var action = data[key][i][1];
				if (action.indexOf('/preferences')!=0 && action.indexOf('/logout')!=0 && actions.indexOf(action)==-1) actions.push(action);
			}

			if (username!='None' && actions.length>0)
				dataByDate[date].push({'username':username, 'actions':actions});
		}

		// Parse the date / time
		var parseDate = d3.time.format("%Y-%m-%d").parse;

		// convert dataByDate into an array
		var sortedDates = Object.keys(dataByDate).sort();
		var data = [];
		for (var i=0; i<sortedDates.length; i++)
			data.push({'date':parseDate(sortedDates[i]), 'uses':dataByDate[sortedDates[i]]});
		// data = [{"date":"2015-04-09","uses":[{"username":"jarny","actions":["/user/users","/user/manage"]},...]}, ...]

		var svgWidth = 800;
		var svgHeight = 300;
		var margin = {top: 20, right: 20, bottom: 70, left: 40},
			width = svgWidth - margin.left - margin.right,
			height = svgHeight - margin.top - margin.bottom;

		var x = d3.scale.ordinal()
			.domain(data.map(function(d) { return d.date; }))
			.rangeRoundBands([0, width], .05, 1);

		var y = d3.scale.linear()
			.domain([0, d3.max(data, function(d) { return d.uses.length; })])
			.range([height, 0]);

		var xAxis = d3.svg.axis()
			.scale(x)
			.orient("bottom")
			.tickFormat(d3.time.format("%Y-%m-%d"));

		var yAxis = d3.svg.axis()
			.scale(y)
			.orient("left")
			.ticks(4);

		d3.select('#usagePlotDiv').select("svg").remove();
		var svg = d3.select('#usagePlotDiv').append("svg")
			.attr("width", svgWidth)
			.attr("height", svgHeight)
			.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

		svg.selectAll("bar")
			.data(data)
		.enter().append("rect")
			.style("fill", "steelblue")
			.attr("x", function(d) { return x(d.date); })
			.attr("width", x.rangeBand())
			.attr("y", function(d) { return y(d.uses.length); })
			.attr("height", function(d) { return height - y(d.uses.length); })
			.on("mouseover", function(d,i) {
				d3.select(this).style('opacity',0.5);
				var lines = [];
				for (var j=0; j<d.uses.length; j++)
					lines.push(d.uses[j].username);
				d3.select("div#modalTooltipDiv").html(lines.join("<br/>"))
					.style({"opacity":.9, "left":event.pageX - 380 + "px", "top":event.pageY - 140 + "px"});
				//CommonService.showTooltip(JSON.stringify(d.uses),$event);
			})
			.on("mouseout", function(d,i) {
				d3.select(this).style('opacity',1);
				hideTooltip();
			});

		svg.append("g")
			.attr("class", "x axis")
			.attr("transform", "translate(0," + height + ")")
			.call(xAxis)
		.selectAll("text")
			.style("text-anchor", "end")
			.attr("dx", "-.8em")
			.attr("dy", "-.55em")
			.attr("transform", "rotate(-90)" );

		svg.append("g")
			.attr("class", "y axis")
			.call(yAxis)
		.append("text")
			.attr("transform", "rotate(-90)")
			.attr("y", 6)
			.attr("dy", ".71em")
			.style("text-anchor", "end")
			.text("number of users");

	}

    $scope.formData = {};
    $scope.processEmailForm = function() {
        CommonService.showLoadingImage();
        $scope.showEmailDialog = false;
        $http.post("/user/sendemail", { data: $scope.formData, headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })
            .then(function(response) {
                CommonService.hideLoadingImage();
                alert(response.data.message);
            }, function(response) {
                CommonService.hideLoadingImage();
                alert("Unexpected error occurred in emailing users.");
            });
    }
}]);

</script>

</head>

<body>
<div id="wrap"> 
${common_elements.banner()}
	<div id="content" ng-controller="UsersController">
		<div id="shadow"></div>
		<div style="padding-left:40px; padding-right:40px;">
			<table st-table="users" class="dataTable" style="border-top:0px;">
				<thead>
				<tr style="background:white;">
					<th colspan="5" style="border:0px; width:100%;">
						<h1 class="marquee" style="display:inline;">User Management</h1> &nbsp; &nbsp;({{users.length}} users)
						<input st-search="" placeholder="search ..." type="text" style="margin-left:400px;"/>&nbsp; &nbsp;
						<select ng-model="selectedAction" ng-options="action for action in actions" ng-change="runAction()"><option value="">[actions...]</option></select>
					</th>
				</tr>
				<tr>
					<th st-sort="username">username</th>
					<th st-sort="fullname">fullname</th>
					<th st-sort="email">email</th>
					<th st-sort="password" style="width:350px;">password</th>
					<th st-sort="groups">groups</th>
					<th>actions</th>
				</tr>
				</thead>
				<tbody>
				<tr ng-repeat="user in users">
					<td>{{user.username}}</td>
					<td>{{user.fullname}}</td>
					<td>{{user.email}}</td>
					<td style="width:350px;">{{user.password}}</td>
					<td>{{user.groups.join(", ")}}</td>
					<td>
						<a href="#" ng-click="manageUser('addGroup',user)">add group</a>&nbsp;&#47;
						<a href="#" ng-click="manageUser('removeGroup',user)">remove group</a>&nbsp;&#47;
						<a href="#" ng-click="manageUser('deleteUser',user)">delete</a>&nbsp;&#47;
						<a href="#" ng-click="manageUser('editUser',user)">edit</a>&nbsp;&#47;
						<a href="#" ng-click="manageUser('emailUser',user)">email</a>&nbsp;&#47;
						<a href="#" ng-click="manageUser('resetPassword',user)">reset passwd</a>
					</td>
				</tr>
				</tbody>
			</table>
		</div>

		<modal-dialog show='showUsage'>
		<div id="usagePlotDiv" style="overflow:auto;"></div><div id="modalTooltipDiv" class="tooltipDiv"></div>
		</modal-dialog>

		<modal-dialog show='showEmailDialog'>
          <h2 class="marquee">Email Users</h2>
          <form name="sendEmailForm" novalidate>
            <!-- recipients -->
            <h3>Recipients</h3>
            <div ng-class="{'form-error':sendEmailForm.recipients.$dirty && sendEmailForm.recipients.$invalid, 'form-group':true}">
              <input type="text" name="recipients" ng-model="formData.recipients" required="" style="width:500px;" />
              <span ng-show="sendEmailForm.recipients.$dirty && sendEmailForm.recipients.$invalid">
                  <span ng-show="sendEmailForm.recipients.$error.required">At least one recipient must be specified.</span>
              </span>
            </div>
            <!-- subject -->
            <h3>Subject</h3>
            <div ng-class="{'form-error':sendEmailForm.subject.$dirty && sendEmailForm.subject.$invalid, 'form-group':true}">
              <input type="text" name="subject" ng-model="formData.subject" placeholder="Subject" required="" />
              <span ng-show="sendEmailForm.subject.$dirty && sendEmailForm.subject.$invalid">
                  <span ng-show="sendEmailForm.subject.$error.required">Subject required.</span>
              </span>
            </div>
            <!-- body -->
            <h3>Body</h3>
            Dear (username),
            <br />
            <div ng-class="{'form-error':sendEmailForm.body.$dirty && sendEmailForm.body.$invalid, 'form-group':true}">
              <textarea name="body" ng-model="formData.body" cols="40" rows="8" required=""></textarea>
              <span ng-show="sendEmailForm.body.$dirty && sendEmailForm.body.$invalid">
                  <span ng-show="sendEmailForm.body.$error.required">Body required.</span>
              </span>
            </div>
            <br />
            Regards,<br />
            Haemosphere Team<br />
            haemosphere.org<br />
            <br />
            <!-- submit -->
            <input type="submit" ng-click="processEmailForm()" ng-disabled="sendEmailForm.$invalid" value="Send Email to {{formData.recipients.split(',').length}} Users" />
          </form>
		</modal-dialog>

		<br style="clear:both;" />
	${common_elements.footer()}
	</div> <!-- content -->

</div> <!-- wrap -->
</body>
</html>

<%
'''
Input variables:
user: users.User instance
groupPages: [{'url':'/hematlas/samples', 'display':'View/edit all samples', 'group':'HiltonLab'},...]
'''
import json
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
ul.groupPages {
	padding-left:15px;
}
ul.groupPages li {
	margin-bottom:10px;
}
</style>

<script type="text/javascript">
app.controller("UserController", ["$scope", "$http", "CommonService", function ($scope, $http, CommonService) 
{	
	// parse input
	$scope.user = ${json.dumps(user.to_json()) if user else {}| n};  // {'name':'smith', 'fullname':'John Smith', 'email':'smith@gmail.com', 'password':'42c432gbadewvdv', 'groups':[]}
	$scope.groupPages = ${json.dumps(groupPages) |n};
	
	$scope.showAttrUpdate = {"fullname":false, "email":false, "password":false};
	$scope.newAttr = {"fullname": $scope.user.fullname, "email":$scope.user.email, "password":"", "password2":""};
	$scope.updateUser = function(attr)
	{
		if (attr=="password") {
			if ($scope.newAttr["password"]!=$scope.newAttr["password2"]) {
				alert("Passwords do not match");
				return;
			}
		}
		else if ($scope.newAttr[attr]==$scope.user[attr]) return;
		
		CommonService.showLoadingImage();
		$http.post("/user/update", { "attr": attr, "value": $scope.newAttr[attr] }).
			then(function(response) {	
				CommonService.hideLoadingImage();
				if (response.data["error"])
					alert("There was an unexpected error with user update: " + response.data["error"]);
				else {	// assume success, update attributes on $scope.user
					$scope.user[attr] = $scope.newAttr[attr];
					$scope.showAttrUpdate[attr] = false;
				}			
			}, function(response) {
				CommonService.hideLoadingImage();
				alert('There was an unexpected error with user update.');
			});
	}
}]);

</script>

</head>

<body>
<div id="wrap">  
${common_elements.banner()}

	<div id="content" ng-controller="UserController">
		<div id="shadow"></div>
		
		<h1 class="marquee" style="margin-left:100px;">Account Management</h1>
		<table class="main" style="margin-left:100px;"><tr>
			<td>
			<table>
				<tr><td><b>Username:</b></td><td>{{user.username}}</td></tr>
				<tr><td><b>Full Name:</b></td>
					<td>
						<span ng-show="!showAttrUpdate['fullname']">{{user.fullname}} (<a href="#" ng-click="showAttrUpdate['fullname']=true">update</a>)</span>
						<span ng-show="showAttrUpdate['fullname']">
							<input type="text" ng-model=newAttr['fullname'] value={{user.fullname}}/>
							<button ng-click="updateUser('fullname')">update</button>
							<button ng-click="showAttrUpdate['fullname']=false">cancel</button>
						</span>
					</td>
				</tr>
				<tr><td><b>Email:</b></td>
					<td>
						<span ng-show="!showAttrUpdate['email']">{{user.email}} (<a href="#" ng-click="showAttrUpdate['email']=true">update</a>)</span>
						<span ng-show="showAttrUpdate['email']">
							<input type="text" ng-model=newAttr['email'] value={{user.email}}/>
							<button ng-click="updateUser('email')">update</button>
							<button ng-click="showAttrUpdate['email']=false">cancel</button>
						</span>
					</td>
				</tr>
				<tr><td><b>Password:</b></td>
					<td>
						<button ng-show="!showAttrUpdate['password']" ng-click="showAttrUpdate['password']=true">Reset...</button>
						<span ng-show="showAttrUpdate['password']">
							Enter the new password twice:<br/>
							<input type="password" ng-model="newAttr['password']" style="margin-top:5px;"/><br/>
							<input type="password" ng-model="newAttr['password2']" style="margin-top:5px;"/><br/>
							<button ng-click="updateUser('password')" style="margin-top:5px;">update</button>
							<button ng-click="showAttrUpdate['password']=false">cancel</button>
						</span>
					</td>
				</tr>
				% if len(user.groups)>0:
				<tr><td><b>Groups:</b></td><td>{{user.groups.join(', ')}}</td></tr>
				% endif
				<tr><td><b>Logout:</b></td><td><button onclick="window.location.assign('/logout')">Logout</button></td></tr>
			</table>
			</td>
			<td>
				<div ng-show="groupPages.length>0" style="margin-left:100px;">
					<h2 style="font-weight:normal">Group Specific Pages</h2>
					<ul class="groupPages">
					<li ng-repeat="item in groupPages"><a href="{{item.url}}">{{item.display}}</li>
					</ul>
				</div>
			</td>
		</tr></table>
		<br style="clear:both;" />
	
	${common_elements.footer()}
	</div> <!-- content -->

</div> <!-- wrap -->  
</body>
</html>

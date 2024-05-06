<%
'''
Input variables:
message: string to use as a message to show the user - useful for failed logins.
'''
import json
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<head>
<title>Haemosphere - Login</title>

<%namespace name="common_elements" file="common.mako"/>
${common_elements.header_elements()}

<style type="text/css">
table.login, table.register {
	font-size: 14px;
}
table.login td {
	padding-top: 20px;
}
table.login input, table.register input {
	line-height: 18px;
}
table.register span {
	color:#ff6767;
}
</style>

<script type="text/javascript">
app.controller('LoginController', ['$scope', '$http', 'CommonService', function ($scope, $http, CommonService) 
{
	// inputs
	$scope.message = ${json.dumps(message) | n};
	$scope.pageIndex = 0;	// 0 for showing login page, 1 for showing registration page
	$scope.commonService = CommonService;
	$scope.helptext = "<div style='width:300px;'><p>Registering enables you to save gene sets on the server and create custom data subsets that you can save. " + 
		"Registration is free and only requires a few basic fields.</p></div>";
	$scope.newuser = {'email':'', 'emailCopy':'', 'username':'', 'fullname':'', 'password':'', 'passwordCopy':''};
	$scope.modalVars = {'email':""};
	
	// Invoke the password retrieval url - should be triggered from the modal
	$scope.retrieve = function()
	{
		if (!$scope.modalVars.email) {
			alert("No email supplied");
			return;
		}
		$scope.showDialog = false;
		
		CommonService.showLoadingImage();
		$http.post("/user/retrieve", { email: $scope.modalVars.email }).
			then(function(response) {	
				CommonService.hideLoadingImage();
				$scope.message = response.data['message'];
			}, function(response) {
				CommonService.hideLoadingImage();
				alert('There was an unexpected error with email retrieval.');
			});
	}
	
	// check username availability on the server
	$scope.checkUsername = function()
	{
		var username = $scope.newuser.username;
		if (username=="") {
			$scope.message = "No username supplied.";
			return;
		}
		
		CommonService.showLoadingImage();
		$http.get("/user/checkusername", {
			params: { username:username }
		}).
		success(function(response) {	
			CommonService.hideLoadingImage();
			$scope.message = response['usernameAvailable']? "username available" : "username unavailable";
		}).
		error(function(response) {
			CommonService.hideLoadingImage();
			$scope.message = 'There was an unexpected error while checking for username availability.';
		});
	}
	
	// Validate the form for new user registration and invoke the appropriate url
	$scope.registerNewUser = function()
	{
		// validate
		var nu = $scope.newuser;
		var error = "";
		if (nu.username=="") error = "No username supplied";
		else if (nu.fullname=="") error = "No full name supplied";
		else if (nu.email=="") error = "No email supplied";
		else if (nu.password=="") error = "No password supplied";
		else if (nu.email!=nu.emailCopy) error = "Emails do not match";
		else if (nu.password!=nu.passwordCopy) error = "Passwords do not match";
		
		if (error!="") {
			$scope.message = error;
			return;
		}
				
		CommonService.showLoadingImage();
		$http.post("/user/emailconfirm", { user: nu }).
			then(function(response) {	
				CommonService.hideLoadingImage();
				$scope.message = response.data['message'];
			}, function(response) {
				CommonService.hideLoadingImage();
				alert('There was an unexpected error with registration email.');
			});		
	}
}]);
</script>

</head>

<body>
<div id="wrap">
${common_elements.banner()}

<div id="content" ng-controller="LoginController">
	<div id="shadow"></div>
	<div ng-show="pageIndex==0" style="padding-top:30px; margin:auto; width:800px; overflow:hidden;">
		<h1 class="marquee">Login</h1>
		<form action="/login" method="POST">
			<table class="login">
				<tr><td colspan="2" style="padding-bottom:30px;">
					Login is only required to save gene sets and custom subsets of datasets on the server.<br/> 
					All other functions are available without login.
				</td></tr>
				<tr><td colspan="2" style="color:red;">{{message}}</td></tr>
				<tr>
					<td>Username &#47; Email:</td>
					<td><input type="text" size="40" name="username"/></td>
				</tr>
				<tr>
					<td>Password:</td>
					<td><input type="password" size="40" name="password"/> &nbsp; <a href="#" ng-click="showDialog=true" style="font-size:12px;">forgot</a></td>
					<input type="hidden" name="form.submitted" value="1"/>
				</tr>
				<tr>
					<td style="padding-top:40px;"><input type="submit" value="Login" style="width:80px; font-size:100%;"/></td>
					<td style="padding-top:40px;"><a href="#" ng-click="pageIndex=1" ng-mouseover="commonService.showTooltip(helptext,$event)" ng-mouseout="commonService.hideTooltip()">register</a></td>
				</tr>
			</table>
		</form>
	</div>

	<div ng-show="pageIndex==1" style="padding-top:30px; margin:auto; width:800px; overflow:hidden;">
		<h1 class="marquee">Register</h1>
		<form name="registerForm" ng-model-options="{ debounce: 1000 }" novalidate>
			<table class="register">
				<tr><td colspan="2" style="padding-bottom:30px;">
					Registration is only required to save gene sets and custom subsets of datasets on the server.<br/> 
					All other functions are available without registration.
				</td></tr>
				<tr><td colspan="2" style="color:red; padding-bottom:30px;">{{message}}</td></tr>
				<tr>
					<td>Username:</td>
					<td><input type="text" size="40" name="username" ng-model="newuser.username" required/>
						<span ng-show="registerForm.username.$dirty && registerForm.username.$invalid">
							<span ng-show="registerForm.username.$error.required"> Username is required.</span>
						</span>
						<a ng-show="!(registerForm.username.$dirty && registerForm.username.$invalid)" href='#' ng-click="checkUsername()"> check availability</a>
					</td>
				</tr>
				<tr>
					<td>Full Name:</td>
					<td><input type="text" size="40" name="fullname" ng-model="newuser.fullname" required/>
						<span ng-show="registerForm.fullname.$dirty && registerForm.fullname.$invalid">
							<span ng-show="registerForm.fullname.$error.required"> Name is required.</span>
						</span>
					</td>
				</tr>
				<tr><td colspan="2" style="padding:10px;"></td></tr>
				<tr>
					<td>Email:</td>
					<td><input type="email" size="40" name="email" ng-model="newuser.email" required/>
						<span ng-show="registerForm.email.$dirty && registerForm.email.$invalid">
							<span ng-show="registerForm.email.$error.required"> Email is required.</span>
							<span ng-show="registerForm.email.$error.email"> Invalid email address.</span>
						</span>
					</td>
				</tr>
				<tr>
					<td>Re-enter email:</td>
					<td><input type="email" size="40" name="emailCopy" ng-model="newuser.emailCopy" required/>
						<span ng-show="gForm.emailCopy.$dirty && registerForm.email.$viewValue!=registerForm.emailCopy.$viewValue"> Emails do not match.</span>
					</td>
				</tr>
				<tr><td colspan="2" style="padding:10px;"></td></tr>
				<tr>
					<td>Password:</td>
					<td><input type="password" size="40" name="password" ng-model="newuser.password" required/>
						<span ng-show="registerForm.password.$dirty && registerForm.password.$error.required"> Password is required.</span>
					</td>
				</tr>
				<tr>
					<td>Re-enter password:</td>
					<td><input type="password" size="40" name="passwordCopy" ng-model="newuser.passwordCopy" required/>
						<span ng-show="registerForm.passwordCopy.$dirty && registerForm.password.$viewValue!=registerForm.passwordCopy.$viewValue"> Passwords do not match.</span>
					</td>
				</tr>
				<tr>
					<td style="padding-top:40px;"><a href="#" ng-click="pageIndex=0">login</a></td>
					<td style="padding-top:40px;">
						<input type="submit" value="Registration" ng-click="registerNewUser()"
							ng-show="true",
                            ng-disabled="registerForm.username.$dirty && registerForm.username.$invalid || registerForm.email.$dirty && registerForm.email.$invalid || registerForm.fullname.$dirty && registerForm.fullname.$invalid || registerForm.password.$dirty && registerForm.password.$invalid"
                            style="width:80px; font-size:100%;"/>
					</td>
				</tr>
			</table>
		</form>
	</div>
	<br style="clear:both;" />

	<modal-dialog show='showDialog'>
		<div style="padding:10px;">
			<h3>Forgot username/password</h3>
			<p>If you can't remember your username or password, enter your email address associated with this account and click on the retrieve button.
			This will send an email, which will contain a link to reset your password.</p>
			<p><input type="text" size="50" ng-model="modalVars.email"/>
			<p><button ng-click="retrieve()">retrieve</button></p>
		</div>
	</modal-dialog>
	
	${common_elements.footer()}
</div> <!-- content -->

</div> <!-- wrap -->  
</body>
</html>

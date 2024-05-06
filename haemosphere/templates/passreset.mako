<%
'''
Input variables: either token or error will be present, not both
token: string (original token used to initiate the password reset process)
error: string

This page uses % if instead of assigning the vars in javascript section for extra security.
'''
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<head>
<title>Haemosphere - Password Reset Page</title>

<%namespace name="common_elements" file="common.mako"/>
${common_elements.header_elements()}

<style type="text/css">
table.main {
	font-size: 14px;
}
table.main td {
	padding-top: 20px;
}
table.main input {
	line-height: 18px;
}
</style>

<script type="text/javascript">
app.controller("PassresetController", ["$scope", "$http", "CommonService", function ($scope, $http, CommonService) 
{		
	$scope.password1 = "";
	$scope.password2 = "";
	$scope.message = "Enter a new password twice";
		
	$scope.updatePassword = function(token)
	{
		// check for valid password strings
		if ($scope.password1=="" || $scope.password2=="") return;
		else if ($scope.password1!=$scope.password2) {
			$scope.message = "Passwords don't match.";
			return;
		}
		
		CommonService.showLoadingImage();
		$http.post("/user/passreset", { "token":token, "password": $scope.password1}).
			then(function(response) {	
				CommonService.hideLoadingImage();
				$scope.message = response.data['passwordChanged']? "Password changed. You can login using the new password via the login page." : 
					"There was an error in password change. Perhaps you timed out? Password reset is only valid for 1 hour after the initial request.";
			}, function(response) {
				CommonService.hideLoadingImage();
				$scope.message = 'There was an unexpected error with password reset.';
			});
	}
}]);

</script>

</head>

<body>
<div id="wrap">  
${common_elements.banner()}

	<div id="content" ng-controller="PassresetController">
		<div id="shadow"></div>	
		<div style="padding-top:60px; margin:auto; width:600px; overflow:hidden;">
			<h1 class="marquee">Password Reset</h1>
			<table class="main">
			% if token:
				<tr><td style="color:#ff6767;">{{message}}</td></tr>
				<tr><td><input type="password" ng-model="password1" size="40"/></td></tr>
				<tr><td><input type="password" ng-model="password2" size="40"/></td></tr>
				<tr><td style="padding-top:40px;"><button ng-click="updatePassword('${token}')">reset</button></td></tr>
			% else:
				<tr><td style="color:#ffcc66;">${error}</td></tr>
			% endif
			</table>
		</div>
		<br style="clear:both;" />
	
	${common_elements.footer()}
	</div> <!-- content -->

</div> <!-- wrap -->  
</body>
</html>

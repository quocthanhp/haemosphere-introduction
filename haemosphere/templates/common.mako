<%def name="header_elements()">
<%
env = request.registry.settings['haemosphere.env']   # {'dev','private','public'}
%>

<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
<meta name="keywords" content="python web application haemopedia gene expression" />
<meta name="description" content="Gene Expression Analysis Tool" />
<meta name="author" content="Jarny Choi, Hilton Lab, WEHI" />

<link type="text/css" href="/css/screen.css" rel="stylesheet" />
<link rel="shortcut icon" href="/images/favicon.ico">

<style type="text/css">
% if env=='dev' or env=='public':
body { background: #f5e8d0; }
% elif env=='private':
body { background: #d0ddf5; }
% endif
</style>

<link href="/css/introjs.min.css" rel="stylesheet">
<link href="/css/bootstrap-responsive.min.css" rel="stylesheet">

<script type="text/javascript" src="/js/intro.min.js"></script>
<script type="text/javascript" src="/js/angular.min.js"></script>
<script type="text/javascript" src="/js/smart-table.min.js"></script>
<script type="text/javascript" src="/js/d3.v3.min.js"></script>
<script type="text/javascript" src="/js/expbarplot.js"></script>

% if env=='public':
<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

  ga('create', 'UA-40688713-2', 'auto');
  ga('send', 'pageview');

</script>
% endif

<script type="text/javascript">
// This will be an application global variable
var app = angular.module('haemosphere',['smart-table']);

/* -----------------------------------------------------
Directive to show modal dialog - from http://jsbin.com/aDuJIku/2/edit
----------------------------------------------------- 
To bind a controller scope variable to custom content here, use the dot trick as mentioned here 
http://stackoverflow.com/questions/24701829/ng-model-inside-ng-transclude. Otherwise variable inside the custom
content doesn't really get bound to parent scope.

So inside the controller, define scope like this
$scope.email = {'email':'smith@gmail.com'}

followed by something like this inside the custom content
<input type="text" ng-model="email.email"/>
*/
app.directive('modalDialog',






 function() {
  return {
    restrict: 'E',
    scope: {
      show: '='
    },
    replace: true, // Replace with the template below
    transclude: true, // we want to insert custom content inside the directive
    link: function(scope, element, attrs) {
      scope.dialogStyle = {};
      if (attrs.width)
        scope.dialogStyle.width = attrs.width;
      if (attrs.height)
        scope.dialogStyle.height = attrs.height;
      scope.hideModal = function() {
        scope.show = false;
        
      };      
    },
    template: "<div class='ng-modal' ng-show='show'><div class='ng-modal-overlay' ng-click='hideModal()'></div><div class='ng-modal-dialog' ng-style='dialogStyle'><div class='ng-modal-close' ng-click='hideModal()'>X</div><div class='ng-modal-dialog-content' ng-transclude></div></div></div>",
    controller: function($scope, $element, $attrs, $location) {
    }
  };
});


/* -----------------------------------------------------
Directive to auto focus the cursor on the tag defined with 'auto-focus' i.e. 
	<input type="text" auto-focus="<booleanVariableToShowModal>">
----------------------------------------------------- */

app.directive('autoFocus', function($timeout, $parse) {
	return {
		link: function(scope, element, attrs) {
			var model = $parse(attrs.autoFocus);
			scope.$watch(model, function(value) {
				$timeout(function() {
					element[0].focus(); 
				});
			});
		}
	};
});

/* -----------------------------------------------------
Service accessible by multiple controllers
----------------------------------------------------- */
app.service('CommonService', function($http) {	
	var distinctColours = [
		"#FF34FF", "#FF4A46", "#008941", "#006FA6", "#A30059", "#7A4900", "#0000A6", "#B79762", "#012C58",
		"#004D43", "#8FB0FF", "#997D87", "#5A0007", "#809693", "#1B4400", "#4FC601", "#3B5DFF", "#4A3B53", 
		"#FF2F80", "#61615A", "#BA0900", "#6B7900", "#00C2A0", "#FFAA92", "#FF90C9", "#B903AA", "#D16100",
		"#000035", "#7B4F4B", "#A1C299", "#300018", "#0AA6D8", "#013349", "#00846F", "#372101", "#FFB500", 
		"#A079BF", "#CC0744", "#C0B9B2", "#001E09", "#00489C", "#6F0062", "#0CBD66", "#456D75", "#B77B68", 
		"#7A87A1", "#788D66", "#885578", "#FF8A9A", "#D157A0", "#BEC459", "#456648", "#0086ED", "#886F4C",
		"#34362D", "#B4A8BD", "#00A6AA", "#452C2C", "#636375", "#A3C8C9", "#FF913F", "#938A81", "#575329", 
		"#B05B6F", "#8CD0FF", "#3B9700", "#04F757", "#C8A1A1", "#1E6E00", "#7900D7", "#A77500", "#6367A9", 
		"#A05837", "#6B002C", "#772600", "#D790FF", "#9B9700", "#549E79", "#201625", "#72418F", "#BC23FF", 
		"#3A2465", "#922329", "#5B4534", "#404E55", "#0089A3", "#CB7E98", "#A4E804", "#324E72", "#6A3A4C",
		"#83AB58", "#001C1E", "#004B28", "#A3A489", "#806C66", "#222800", "#BF5650", "#E83000", "#66796D", 
		"#DA007C", "#FF1A59", "#1E0200", "#5B4E51", "#C895C5", "#320033", "#FF6832", "#D0AC94", "#7ED379"];
	
	function showTooltip(content, evt, params)
	{
		var leftOffset = params && params.leftOffset? params.leftOffset : 5;
		var topOffset = params && params.topOffset? params.topOffset : -28;
		// try to get mouse position - seems tricky to find a solution for all browsers
		if (evt==null) evt = window.event;	// won't work on firefox
		if (evt==null) evt = d3.event;	// won't work on non-svgs (I think)
		var x = params && params.x? params.x : evt.clientX;
		var y = params && params.y? params.y : evt.clientY;
		d3.select("div.tooltipDiv").html(content)
			.style({"opacity":.9, "left":x + leftOffset + "px", "top":y + topOffset + "px"});
	}
	
	function hideTooltip()
	{
		d3.select("div.tooltipDiv").style("opacity", 0);	
	}

	function showLoadingImage()
	{
		d3.select("#loadingImage").style("display","block");
	}
	
	function hideLoadingImage()
	{
		d3.select("#loadingImage").style("display","none");
	}

	// Return array of distinct values for an associative array
	function uniqueValues(assocArray) 
	{
		var values = [];
		for (var key in assocArray) {
			if (values.indexOf(assocArray[key])==-1) values.push(assocArray[key]);
		}
		return values;
	}
	
	// Perform keyword search for genes. Multiple controllers may perform this function, hence placed here.
	function keywordSearch(searchString, searchScope, species, exactMatch)
	{
		showLoadingImage();
		$http.post("/search/keyword", { searchString: searchString, searchScope: searchScope, species: species, exactMatch: exactMatch }).
			then(function(response) {	
				hideLoadingImage();
				// search/keyword places new geneset in session, so return current geneset page if geneset is not null
				if (response.data['genesetSize']>0)
					window.location.assign("/geneset/current");
				else
					alert("No matching genes found");
			}, function(response) {
				hideLoadingImage();
				alert('There was an unexpected error with keyword search.');
			});
	}
	
	// Set selectedDataset on the server
	function setSelectedDataset(datasetName)
	{
		$http.post("/session/selecteddataset", { datasetName: datasetName }).
			then(function(response) {	
			}, function(response) {
			});
	}

	// public api - everything else will remain private
	return {
		distinctColours : distinctColours,
		uniqueValues : uniqueValues,
		showTooltip : showTooltip,
		hideTooltip : hideTooltip,
		showLoadingImage : showLoadingImage,
		hideLoadingImage : hideLoadingImage,
		keywordSearch : keywordSearch
	};	

});
</script>
</%def>

<!--------------------------------------------------------------------------------------->
<%def name="banner()">
<%
user = None
from haemosphere.models.users import User
username = request.authenticated_userid
if username:
    user = request.dbsession.query(User).filter_by(username=username).first()
%>
<div id="banner">
	<div id="logo">
	  <table><tr>
	  	<td><a href="/"><img src="/images/logo.gif" alt="Haemoshere" border="0" /></a></td>
	  	<td style="padding-left:20px;"><img id="loadingImage" src="/images/ajax-loader.gif" border="0" style="display:none;"/></td>
	  </tr></table>
	</div>
	<script type="text/javascript">
		app.controller('QuickSearchController', function ($scope, CommonService) {
			$scope.searchString = "";
			$scope.commonService = CommonService;
			$scope.search = function()
			{
				CommonService.keywordSearch($scope.searchString.trim(), "general");
			}
		});
		app.controller('UserAccountController', function ($scope, CommonService) {
		});
	</script>

	<div id="tools" style="font-size:100%" ng-controller="QuickSearchController">
		<span>
			<input type="text" style="color:#cccccc" placeholder="quick search..." ng-model="searchString" ng-keyup='$event.keyCode == 13 ? search() : null'  data-step="1" data-intro='Search for a gene <br/>("gata1" or "p53").'/>
		</span>
		<span class="dot">&bull;</span><a href="/about">About</a>
		<span class="dot">&bull;</span><a href="/searches" data-step="2" data-intro="More complex searches here, including differential expression.">Searches</a>
		<span class="dot">&bull;</span><a href="/datasets/show" data-step="3" data-intro="View all datasets here, show samples and plot sample relationships.">Datasets</a>
		<span class="dot">&bull;</span><a href="/geneset/current" data-step="4" data-intro="Show results of gene searches.">Genes</a>
		% if user and user.isAdmin():
		<span class="dot">&bull;</span><a href="/user/users">Users</a>
		% endif
		% if user: # show username
		<span><span class="dot">&bull;</span><a href="/user/account">${user.username}</a></span>
		% else:	# show login link
		<span><span class="dot">&bull;</span><a href="/login">Login</a></span>
		% endif
		<img src="/images/question_mark.png" data-step="5" data-intro="Many pages will show a quick tour like this when you click on this symbol." 
			ng-mouseover="commonService.showTooltip('Click on me for a quick tour of the menus.',$event,{leftOffset:-100, topOffset:10})" ng-mouseout="commonService.hideTooltip()"
			onclick="javascript:introJs('#banner').start();"
			width="20px" height="20px" style="margin-bottom:-6px; margin-left:10px;">
	</div>
</div>
</%def>

<!--------------------------------------------------------------------------------------->
<%def name="footer()">
<%
import json
from haemosphere.views.utility import versionInfo
versionInfo = versionInfo(request)[::-1] # reverse order with latest version info first
%>
<script type="text/javascript">
app.controller('FooterController', function ($scope, CommonService) {
	$scope.versionInfo = ${json.dumps(versionInfo) |n};  // [{'version':'2.1', 'notes':['note1',...]}, ...]
	$scope.showVersionInfo = false;
});
</script>

<div id="footer" ng-controller="FooterController">
  <table width="98%">
    <tr>
      <td align="left">
		<br>Citation: <a href="https://doi.org/10.1093/nar/gky1020">Haemopedia RNA-seq: a database of gene expression during haematopoiesis in mice and humans <i>Nucl. Acids Res.</i> (2019)</a> </br>
		<a href='#' ng-click="showVersionInfo=true">Version {{versionInfo[0].version}}</a> &nbsp; &copy; 2021 &nbsp; Walter and Eliza Hall Institute
      </td>
      <td align="right">
		<a href="http://www.wehi.edu.au/" target="_blank" border="0">
		  <img src="/images/wehi-logo.png" class="logo-image" alt="Walter and Eliza Hall Institute" width="160" height="40" />
		</a>
      </td>
    </tr>
  </table>
  <modal-dialog show='showVersionInfo'>
	<div style="height:500px; padding-left:10px; overflow:auto;">
	  <h2>Haemosphere Release Notes</h2>
	  <p ng-repeat="item in versionInfo" style="color:#666666"><b>Version {{item.version}}</b><br/><span ng-repeat="note in item.notes">- {{note}}<br/></span></p>
  	</div>
  </modal-dialog>
</div> <!-- footer -->
<div class="tooltipDiv" style="opacity:0;"></div>
<!--
<div ng-controller="ModalController" class='ng-modal' ng-show='show'>
	<div class='ng-modal-overlay' ng-click='show=false'></div>
	<div class='ng-modal-dialog' ng-style='dialogStyle'>
		<div class='ng-modal-close' ng-click='show=false'>X</div>
		<div class='ng-modal-dialog-content' ng-transclude></div>
	</div>
</div>
-->
</%def>


<!-- Render flash messages placed in request.session.flash queue -->
<%def name="flashMessage(queue)">
	% if request.session.peek_flash(queue):
		<div id="flash" style="color: black; font-size: 20px; background-color: #B15252; text-align: center; padding-bottom: 5px; padding-top: 5px;">
			<% flash = request.session.pop_flash(queue) %>
			% for message in flash:
				${message}<br>
			% endfor
		</div>
	% endif
</%def>

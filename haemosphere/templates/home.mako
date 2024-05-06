<% 
'''
Input params:
'''
import json
env = request.registry.settings['haemosphere.env']   # {'dev','private','public'}
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" ng-app="haemosphere">
<head>
<title>Haemosphere</title>

<%namespace name="common_elements" file="common.mako"/>
${common_elements.header_elements()}
	
<style type="text/css">
/* take tour style scrolling divs */
#tour {
	width: 700px;
	margin-left: auto;
	margin-right: auto;
}
#takethetour {
	float: left;
	padding-top: 17px;
}
#tourlogos {
	float: right;
}
#tourredline {
	border-top: solid 1px rgb(186,20,0);
	clear: both;
	margin-top: 5px;
	margin-bottom: 5px;
}
#tourcontainer {
	border: solid 1px #ddd;
	padding: 30px;
	white-space: nowrap;
	height: 270px;
}

.tourcontentitem {
	display: inline-block;
	width: 698px;
}

.tourtext {
	white-space: normal;
	float: left;
	width: 200px;
	border: solid 1px rgb(186,20,0);
	border-radius:10px;
	-webkit-border-radius:10px;
	-moz-border-radius:10px;
	padding: 10px;
	font-size: 16px;
	color: rgb(186,20,0);
	line-height: 150%;
	font-family: Verdana, Geneva, sans-serif;
}

#tourspeechbubblepoint {
        float: left;
        position: relative;
        z-index: 2;
        top: 90px;
        left: -2px;
}

.tournews {
	font-size: 14px;
	float: left;
	width: 500px;
	border: solid 1px rgb(186,20,0);
	border-radius:10px;
	-webkit-border-radius:10px;
	-moz-border-radius:10px;
	padding: 20px;
}

.tournews ul li {
	margin-bottom: 5px;
}

</style>

<script type="text/javascript">
app.controller('HomePageController', function ($scope) {
	$scope.shownDivIndex = 0;	// index of div currently shown
});

</script>
</head>

<body>
<div id="wrap">
            
${common_elements.banner()}
      
	<div id="content">
	
	<div id="shadow"></div>
	
	<div id="tour" ng-controller="HomePageController">
		<div>
			<img ng-show="shownDivIndex==0" ng-src="images/tourtype5.png" alt="news" />
			<img ng-show="shownDivIndex==1" ng-src="images/tourtype0.png" alt="about haemosphere" />
			<img ng-show="shownDivIndex==2" ng-src="images/tourtype1.png" alt="show searches" />
			<img ng-show="shownDivIndex==3" ng-src="images/tourtype2.png" alt="browse datasets" />
			<img ng-show="shownDivIndex==4" ng-src="images/tourtype3.png" alt="browse samples" />
			<a style="margin-left:200px;" href="/"><img ng-src="images/tourlogos/{{shownDivIndex==0 && 'on' || 'off'}}/logo0.png" alt="news logo" ng-mouseover="shownDivIndex=0; "/></a> 
			<a href="/about"><img ng-src="images/tourlogos/{{shownDivIndex==1 && 'on' || 'off'}}/logo1.png" alt="about haemosphere logo" ng-mouseover="shownDivIndex=1"/></a>
			<a href="/searches"><img ng-src="images/tourlogos/{{shownDivIndex==2 && 'on' || 'off'}}/logo2.png" alt="search genes logo" ng-mouseover="shownDivIndex=2"/></a>
			<a href="/datasets/show"><img ng-src="images/tourlogos/{{shownDivIndex==3 && 'on' || 'off'}}/logo3.png" alt="browse datasets logo" ng-mouseover="shownDivIndex=3"/></a>
			<a href="/datasets/samples"><img ng-src="images/tourlogos/{{shownDivIndex==4 && 'on' || 'off'}}/logo4.png" alt="browse samples logo" ng-mouseover="shownDivIndex=4"/></a>
		</div>
		<div id="tourredline"></div>
		<div id="tourcontainer">
			<div class="tourcontentitem" ng-show="shownDivIndex==0">
				<div class="tourtext" style="width:610px;">
					<p style="margin-left:10px;">Version 4.9.5 released (February 2019)</p>
					<ul style="font-size:14px; color:black;">
					<li>Haemopedia RNA-seq now published at <a href="https://doi.org/10.1093/nar/gky1020">﻿Haemopedia RNA-seq: a database of gene expression during haematopoiesis in mice and humans NAR (2019)</a> 
						</li>
					<li>RNA-seq data is now normalised as TPM (transcripts per million) rather than RPKM (reads per kilobase million)</li>
					<li>A tour of Haemosphere can be accessed by clicking the question marks</li>
					<li>Gene expression can now be <a href="expression/multispecies?geneId=ENSMUSG00000030724">viewed</a> across multiple datasets and species.</li>
					<li>Gene vs gene <a href="expression/genevsgene?gene1=ENSMUSG00000002111&gene2=ENSMUSG00000028163&datasetName=Haemopedia-Mouse-RNASeq">expression</a> 
					     plots are now available.</li>
					</ul>
				</div>
				<br style="clear:both;" />
			</div>
			<div class="tourcontentitem" ng-show="shownDivIndex==1">
				<div class="tourtext">Haemosphere is a web portal to explore gene expression data on haematopoietic cell types. 
				Features include differential expression analysis, gene set management and visualisation tools.
				<a href="/about">more...</a></div>
				<div id="tourspeechbubblepoint"><img src="/images/speechbubblepoint.gif" alt="" /></div>
				<div> <img src="/images/tourslide0.png" height="250" width="385" alt=""/> </div>
				<br style="clear:both;" />
			</div>
			<div class="tourcontentitem" ng-show="shownDivIndex==2">
				<div class="tourtext">Search genes based on symbol or synonym matches or by uploading a list of genes. 
				Perform differential expression analysis using R/Bioconductor as analysis engine.</div>
				<div id="tourspeechbubblepoint"><img src="/images/speechbubblepoint.gif" alt="" /></div>
				<div> <img src="/images/tourslide1.png" alt=""/> </div>
				<br style="clear:both;" />
			</div>
			<div class="tourcontentitem" ng-show="shownDivIndex==3">
				<div class="tourtext">Haemosphere acts as a single point of entry for some key datasets of value to haematopoiesis
				research community. View datasets and perform principal components analysis on cell types.</div>
				<div id="tourspeechbubblepoint"><img src="/images/speechbubblepoint.gif" alt="" /></div>
				<div> <img src="/images/tourslide2.png" alt=""/> </div>
				<br style="clear:both;" />
			</div>
			<div class="tourcontentitem" ng-show="shownDivIndex==4">
				<div class="tourtext">View metadata for each dataset, such as cell type, tissue of origin, mouse strains or FACS markers.</div>
				<div id="tourspeechbubblepoint"><img src="/images/speechbubblepoint.gif" alt="" /></div>
				<div> <img src="/images/tourslide3.png" alt=""/> </div>
				<br style="clear:both;" />
			</div>
			<br style="clear:both;" />
		</div>
	</div>
	
	<br style="clear:both;" />
	${common_elements.footer()}
	</div> <!-- content -->
</div>
    
</body>
</html>

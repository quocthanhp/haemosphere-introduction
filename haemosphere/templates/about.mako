<%
%>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" id="haemosphere" ng-app="haemosphere">

<head>
<title>Haemosphere - About Heamosphere Page</title>

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
</style>

<script type="text/javascript">
app.controller('AboutController', ['$scope', 'CommonService', function ($scope, CommonService) 
{
	$scope.pages = ['About Haemosphere','About Datasets','About Genes','Privacy Policy','Contact Us'];
	$scope.selectedPage = $scope.pages[0];
	
	$scope.setPage = function(page)
	{
		$scope.selectedPage = page;
	}
}]);

</script>

</head>

<body>
<div id="wrap">  
${common_elements.banner()}

	<div id="content" ng-controller="AboutController">
		<div id="shadow"></div>
		
		<table style="margin-left:30px;">
		<tr>
			<td></td>
			<td><h1 class="marquee" style="margin-left:20px;">{{selectedPage}}</h1></td>
			<td></td>
		</tr>
		<tr>
			<td style="display:table-cell; vertical-align:top; width:150px;">
				<ul><li class="search-mode {{page==selectedPage && 'current-search' || ''}}" ng-repeat="page in pages"><a href="#" ng-click="setPage(page)">{{page}}</a></li></ul>
			</td>
			<td style="vertical-align:top; padding-left:20px; padding-right:20px;">
				<div ng-show="pages.indexOf(selectedPage)==0">
					<p>Haemosphere is a data portal designed for the bench biologist, providing intuitive interfaces to access and analyse the Haemopedia datasets and some other key datasets
					of interest to the haematopoiesis community.</p>
					<p>The user can <a href="/searches?selectedSearch=0">search</a> for genes of interest, view their expression profiles across a range of 
					cell types within a dataset, perform <a href="/searches?selectedSearch=1">differential expression analyses</a> and 
					<a href="/geneset/current">manage gene</a> sets easily. The main principle behind Haemosphere’s design is to provide an exploratory tool, 
					with minimum filtering and interpretation, while making the presentation of this data very accessible.</p>
				</div>

				<div ng-show="pages.indexOf(selectedPage)==1">
					<p>The Haemopedia datasets were created at the Walter and Eliza Hall Institute of Medical Research and aim to capture the key cells across normal haematopoiesis. We have datasets that cover both mouse and human.  
					<p>The Haemopedia RNA-Seq datasets were sequenced on Illumina HiSeq 2500 with 100 bp reads and aligned with RSubread and aggregated with featureCounts. For more details see <a href="https://doi.org/10.1093/nar/gky1020">Haemopedia RNA-seq: a database of gene expression during haematopoiesis in mice and humans</a>.
					<p>The Haemopedia Mouse Microrray dataset pipeline uses <a href="http://web.mit.edu/~r/current/arch/i386_linux26/lib/R/library/limma/html/nec.html" target="_blank">neqc</a> 
					function from the <a href="http://bioconductor.org/packages/release/bioc/html/limma.html" target="_blank">limma</a> package in 
					<a href="http://www.bioconductor.org/" target="_blank">R&#47;Bioconductor</a>, and filtering of bad or non matching probes to currently annotated genes 
					(<a href="http://www.ncbi.nlm.nih.gov/pubmed/19923232" target="_blank">ReMOAT</a> project has been used for Illumina probe annotations).For more details please see <a href="http://dx.doi.org/10.1016/j.stemcr.2016.07.007">Haemopedia: An Expression Atlas of Murine Hematopoietic Cells</a>.</p>
					<p>We have additionally made available some other haematopoeitic expression datasets so they can also be visualised and compared through the Haemosphere interface.</p>
					<p>Note that you can download each dataset by going to the Datasets page and clicking on the download link. In addition, the
					haemopedia dataset can also be accessed from Gene Expression Omnibus (GEO) id of 
					<a href="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE77098" target="_blank">GSE77098</a>.
				</div>

				<div ng-show="pages.indexOf(selectedPage)==2">
					<p>To provide optimal usefulness to the user, Haemosphere uses gene annotation from a combination of sources. 
					Ensembl genes ids are used as unique gene identifiers in the system, but each Ensembl gene is also carefully matched against Entrez genes 
					in order to obtain synonym information. Then MGI is used to obtain gene orthologues.</p>
					<p>Current gene information comes from the following sources:
					<ul style="margin-left:15px">
					<li style="list-style-type:disc; padding:2px;">Ensembl genes 83 from <a href="http://www.ensembl.org/biomart/martview" target="_blank">biomart</a></li>
					<li style="list-style-type:disc; padding:2px;">Entrez <a href="ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/Mammalia" target="_blank">gene_info file</a> downloaded on 2 Feb 2016</li>
					<li style="list-style-type:disc; padding:2px;">Mouse human homology report from <a href="http://www.informatics.jax.org/downloads/reports/index.html#homology" target="_blank">MGI</a> downloaded on 2 Feb 2016</li>
					</p>
				</div>

				<div ng-show="pages.indexOf(selectedPage)==3">
					<p><b>Haemosphere is bound by the Privacy Act 1988 (Crh), which sets out a number of principles concerning the privacy of individuals.</b></p>
					<p>There are many aspects of the site which can be viewed without providing personal information. However, for access to some 
					features of Haemosphere you are required to become a registered user and submit personally identifiable information. 
					This may include, but is not limited to, a valid e-mail address and password. As a registered user, your personal information 
					will be treated as confidential. While Haemosphere may use this information to track usage, personal information will not be 
					made available to third parties without your permission.</p>
					<p>For each visitor to reach the site, we collect the following non-personally identifiable information, including but not 
					limited to browser type, version and language, operating system, pages viewed while browsing the Site, page access times and 
					referring website address. This collected information is used solely internally for the purpose of gauging visitor traffic, trends, 
					and improving the utility of the site. It is collected by Google Analytics, stored anonymously, and will not be passed on to any 
					other third party without your permission.</p>
					<p>When enquiries are e-mailed to us, we will store the question and e-mail address so that we can respond electronically. 
					E-mail addresses and other contact information provided to Haemosphere will be held in an internal list, which will not 
					be made available to third parties without the prior consent of the user.</p>
					<p>From time to time, we may use customer information for new, unanticipated uses not previously disclosed in our privacy notice. 
					If our information practices change at some time in the future we will use for these new purposes only, 
					data collected from the time of the policy change forward will adhere to our updated practices.</p>
					<p>Haemosphere reserves the right to make amendments to this Privacy Policy at any time. 
					If you have objections to the Privacy Policy, you should not access or use the Site.</p>
				</div>

				<div ng-show="pages.indexOf(selectedPage)==4">
					<p>We will be happy to receive any feedback or suggestions regarding Haemosphere, and we will do our best to respond in a timely manner.</p>
					<p><h3>admin@haemosphere.org</h3>
				</div>
			</td>
			<td style="vertical-align:top; width:350px; padding-right:20px;">
				<div ng-show="pages.indexOf(selectedPage)==0">
					<h3>Citing Haemosphere</h3>
					<br><b>Haemopedia-RNA-Seq datasets and Haemosphere derived plots</b></br>
					<p>Choi et al. Haemopedia RNA-seq: a database of gene expression during haematopoiesis in mice and humans. <i>Nucleic Acids Research</i> (2018), <a href="https://doi.org/10.1093/nar/gky1020">https://doi.org/10.1093/nar/gky1020</a>  </p>

					<br><b> Haemopedia Mouse Microarray </b></br>
					<p>de Graaf et al., Haemopedia: An Expression Atlas of Murine Hematopoietic Cells, <i>Stem Cell Reports</i> (2016), <a href="http://dx.doi.org/10.1016/j.stemcr.2016.07.007">http://dx.doi.org/10.1016/j.stemcr.2016.07.007</a></p>

					<br><b>Underlying Haemosphere architecture and BioPyramid</b></br>
					<p>Stephenson et al. Building online genomics applications using BioPyramid. <i>Bioinformatics</i> (2018) <a href="https://doi.org/10.1093/bioinformatics/bty207">https://doi.org/10.1093/bioinformatics/bty207</a></p>
	

				</div>
				<div ng-show="pages.indexOf(selectedPage)==1">
					<h3>With each dataset you can:</h3>
					<p><a href="/datasets/samples">View sample information</a></p>
					<p><a href="/datasets/analyse">Perform principal components analysis</a></p>
					<p><a href="/searches?selectedSearch=1">Find differentially expressed genes</a></p>
				</div>
				<div ng-show="pages.indexOf(selectedPage)==2">
					<h3>Gene Resources:</h3>
					<p><a href="/downloadfile?filetype=AllGenes">Download all gene information</a> (text file)</p>
					<p>Download all gene symbols: <a href="/downloadfile?filetype=AllMouseGeneSymbols">mouse</a> &#47; 
					<a href="/downloadfile?filetype=AllHumanGeneSymbols">human</a></p>
				</div>
				<div ng-show="pages.indexOf(selectedPage)==3">
					<h3>Disclaimer:</h3>
					<p>No medical advice is provided on the website, and information obtained here should not be used for such a purpose.</p>
					<p>The views and opinions of authors expressed on Haemosphere websites do not necessarily state or reflect those of the 
					contributing organisations, and they may not be used for advertising or product endorsement purposes without the author's explicit written permission</p>
				</div>
			</td>
		</tr>
		</table>		
		<br style="clear:both;" />
	
	${common_elements.footer()}
	</div> <!-- content -->

</div> <!-- wrap -->  
</body>
</html>

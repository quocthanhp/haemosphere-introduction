##Haemosphere Upgrade Tests
####26th October 2021
####Carolyn de Graaf 
####Bugs resolved by Nirmala Rao Dhanawada on Version 5

45.113.233.137


Testing the main functionality after Nirmala has upgraded Haemosphere from Python 2.7 to 3.6. Tests run on https://prod.haemosphere.org (3.6) and compared to functionality observed on https://haemosphere.org (2.7)

Most issues (or places for potential improvement) have been there in both versions. Only issues that are likely to have been introduced during the upgrade process (eg can’t reproduce on the old version) are highlighted in red as a priority for fixing. 

##Front Page
Now goes to about page – improvement on previous page

About Genes Text needs editing

##Header
Capital letter for login (or disable entirely)

##Search
Works as previously. Improving ranking of sort priority for next update. 

##Expression Profile
https://prod.haemosphere.org/expression/show?geneId=ENSG00000120458
Changing datasets is a bit clunky – sometimes it selects it and doesn’t change dataset. The loading of new datasets is also quite slow. (Not specific to this build).
Grouping by lineages doesn’t colour the lineages correctly. Have option to colour by – but there is nothing to select – should have cell_lineage in there as the default option. (Not specific to this build).

##Multispecies Plot 
https://prod.haemosphere.org/expression/multispecies?geneId=ENSG00000120458
https://prod.haemosphere.org/expression/multispecies?geneId=ENSG00000120458&selectedDataset=MusMusculus_none&selectedDataset=Haemopedia-Human-RNASeq&selectedDataset=Linsley&selectedDataset=DMAP&selectedDataset=Rapin-BloodSpot&selectedDataset=Schultze&selectedDataset=Watkins
Works and can add / delete datasets! Again would be nice if this was faster
Future thought – should by default show all the (large) datasets when this page is loaded rather than just a couple of favourites. 
Download works from Safari, but not Chrome. Chrome gives it a name like “.com.google.Chrome.Mu3PMz” rather than “Haemosphere_LineageExpression_MSANTD2_Linsley.png”. Can rename to .png and the correct graph is there.  
 
##Find Similar Genes
Looks good. Can only access from expression plot page, but no reason why this couldn’t be a link from the gene search results tab. Also the link to show the gene vs gene plot is only under the expression tab, but should also put it as a hyper link the correlation column. 

##Gene vs Gene
Looks good. Perhaps good to add a note to tell the users to click on a gene name to change which genes are being correlated as might not be immediately obvious. 

##Datasets
Page loads correctly

##Datasets: Downloads
Displays correctly
All actions disabled unless logged in. When logged in then reordering of the datasets doesn’t work. This is as before. 
Link to MDS plot (clicking on the dataset name) for this doesn’t work. This is a 3.6 error. 
Will still need to test Saving Figure from this page. 

##Datasets: Samples
Loads correctly.
Select columns works as expected
Create subset – doesn’t work as expected – perhaps should be hidden until we get that working
You can download the sample info from the dataset page, but maybe should also be on this page?

##Genes Tab
Shows history of previous search results. Allows you to go back to previous gene sets. 

##Orthologue Swap
Works

##Heatmap
Selected from a single species gene list on the genes tab. Correctly shows the geneset. For future want to be able to choose between absolute and relative colouring of the heatmap. 
Save Figure downloads the picture on a black background. The other images saved from Haemosphere don’t do this. 

##Gene Annotation
Gene annotation swap hasn’t gone in. When search “Septin” or “March” can see Excel error in gene names. Need to include the updated file “hsgenesetExon.txt”

##Search: Differential Expression Search
Returned a message saying it had failed on haemopedia-Mouse-RNASeq LSK vs MegTPO after 1 minute. I think I had tested it last week and it worked, so I think it is a time out error. It works ok on a smaller dataset.
Takes 55 seconds on the www.haemosphere.org for the same comparison that failed on prod. Not the most pressing issue as I don’t think the functionality has changed, but we do need to find out if there some way we can optimise this?? Unless there is some way we can process it faster on the new server?

##Search: High Expression Search
18 seconds 2.7  19 seconds 3.6 

##Search: Gene vs Gene Plot
Correctly takes you to the plot

##Search: Correlated Gene Search
Just tells you that it exists 

##Footnote
Update to Version 5.0.0 with appropriate release notes

##Login
Lets you login but none of the features work except for admin user management.
from locust import HttpLocust, TaskSet, task
	

class ResearcherBehavior(TaskSet):
    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.login()

    def login(self):
        self.client.post("/login", {"form.submitted":True, "username":"yosh", "password":"newpassword"})

    @task(1)
    def index(self):
        self.client.get("/")

    # -------------------------------------------------------
    # Dataset pages
    # -------------------------------------------------------
    @task(10)
    def dataset_list(self):
        self.client.get("/datasets/show")

    @task(6)
    def plot_dataset(self):
        self.client.get("/datasets/analyse?datasetName=haemopedia")	
		
#     @task(3)
#     def view_dataset_samples(self):
#         self.client.get("/datasets/samples?datasetName=gxcommons")		

#     @task(1)
#     def create_subset(self):
#         self.client.post("/datasets/createsubset", {"datasetName":"gxcommons","subsetName":"testing","subsetDescription":"[subset of gxcommons]","sampleIds":["GSM854035","GSM854036"],"sampleGroupsDisplayed":["celltype","cell_lineage"]})
					
    # -------------------------------------------------------
    # Gene Expression pages
    # -------------------------------------------------------

    @task(3)
    def geneset_list(self):
        self.client.get("/geneset/current")
	
    @task(6)
    def expression_show(self):
        self.client.get("/expression/show?geneId=ENSMUSG00000048481")

#     @task(1)
#     def heatmap(self):
#         self.client.post("/geneset/heatmap", {"geneId":"ENSG00000125414%26ENSG00000176182", "datasetName":"rapin"})
	
    @task(1)
    def find_similar(self):
        self.client.get("/geneset/corr?datasetName=haemopedia&featureId=ILMN_1221700")


class UserBehavior(TaskSet):
    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.login()

    def login(self):
        self.client.post("/login", {"form.submitted":True, "username":"yosh", "password":"newpassword"})

    @task(1)
    def index(self):
        self.client.get("/")
        
    @task(1)
    def about(self):
        self.client.get("/about")

    # -----------------------------------------------
    # Searching
    # -----------------------------------------------
    @task(2)
    def search_page(self):
        self.client.get("/searches")

#     @task(2)
#     def search_keyword(self):
#         self.client.post("/search/keyword", {"searchString":"x","searchScope":"general","species":null,"exactMatch":false})

#     @task(2)
#     def search_diff_expr(self):
#         self.client.get("/search/expression?dataset=haemopedia&filterCpm=0.5&minFilterSample=2&normalisation=TMM&sampleGroup=celltype&sampleGroupItem1=LTHSC&sampleGroupItem2=STHSC")

class Downloads(TaskSet):

    # -----------------------------------------------
    # About Genes downloads
    # -----------------------------------------------
    @task
    def AllGenes(self):
        self.client.get("/downloadfile?filetype=AllGenes")

    @task
    def mouseSymbols(self):
        self.client.get("/downloadfile?filetype=AllMouseGeneSymbols")

    @task
    def humanSymbols(self):
        self.client.get("/downloadfile?filetype=AllHumanGeneSymbols")

    # -----------------------------------------------
    # Datasets/show downloads
    # -----------------------------------------------
    @task
    def expr_matrix(self):
        self.client.get("/downloadfile?&filetype=dataset&datasetName=haemopedia&datasetFile=expression")
		
    @task
    def probe_gene_mapping(self):
        self.client.get("/downloadfile?&filetype=dataset&datasetName=haemopedia&datasetFile=probes")
		
    @task
    def sample_table(self):
        self.client.get("/downloadfile?&filetype=dataset&datasetName=haemopedia&datasetFile=samples")


class WebsiteUser(HttpLocust):
    task_set = ResearcherBehavior
    min_wait=1000
    max_wait=10000

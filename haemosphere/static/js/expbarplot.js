(function(exports)
{

	/* -----------------------------------------------------------------------------------
	ExpressionPlot class deals with expression profile plot using d3.
	 
	data looks like:
	{'values' : 
		{
			'ILMN_1234':{'B.1':1.2, 'B.2':1.5, 'B.3':1.7, 'T.1':3.2, 'T.2':4.3, 'Eo.1':3.3, 'Eo.2':5.2, 'LSK.1':4.4, 'LSK.2':5.2, 'Mpp.1':6.3},
			'ILMN_5678':{'B.1':2.2, 'B.2':2.5, 'B.3':3.7, 'T.1':1.2, 'T.2':2.3, 'Eo.1':3.3, 'Eo.2':4.2, 'LSK.1':4.3, 'LSK.2':3.4, 'Mpp.1':7.7}
		},
	'valueRange': [0,9],
	'groupBy':
		[
			{'name':'B', 'samples':['B.1','B.2','B.3']},
			{'name':'T', 'samples':['T.1','T.2']},
			{'name':'Eo', 'samples':['Eo.1','Eo.2']},
			{'name':'LSK', 'samples':['LSK.1','LSK.2']},
			{'name':'MPP', 'samples':['Mpp.1']}
		],
	'colourBy':
		[
			{'name':'Multi', 'groups':['LSK','MPP'], 'color':'grey'},
			{'name':'Lymphoid', 'groups':['B','T']},
			{'name':'Eos', 'groups':['Eo'], 'color':'blue'}
		],
	'value-axis-label':'expression value (log2)',
	'group-axis-label':'',
	'featureGroups':
		{
			'ENSG000001':['ILMN_1234'],
			'ENSG0001212':['ILMN_5678']
		},
	'featureGroupNames':
		{
			'ENSG000001':'Gene1',
			'ENSG0001212':'Gene2'
		}
	};
	*/
	
	// Contructor
	var ExpressionPlot = function(params) {
		this.targetDiv = params['targetDiv'];
		this.legendDiv = params['legendDiv'];
		this.controlPanelDiv = params['controlPanelDiv'];
		this.showTooltipFunction = params['showTooltipFunction'];
		this.hideTooltipFunction = params['hideTooltipFunction'];
		this.minTickInterval = params['minTickInterval'];	// some data should not be scaled too finely on the value axis
		
		// Set these later during plots; can't use (eg) d3.select(this.targetDiv).selectAll('rect') later, 
		// because these don't exist at initialisation.
		this.targetSvg; 
		this.legendSvg;
	
		this.data;	// see above for what this should look like	
		this.vo = false;	// if true, samples are on y axis with values on x
		this.selectedFeatureId;	// useful if a selection has been made on a lineplot
		this.currentPlot;	// may be 'lineplot' or 'barplot'
		this.showColourBy = false;	// true if current lineplot is showing background blocks of colour
		this.showLinePoints = true;	// true if current lineplot is showing individual points along the line
		this.collapsedColourByItems = [];	// each collection of bars may be collapsed by clicking on colourBy item - keep track of these
		
		// Define margins and sizes inside svg area. Since the plot can be rotated, instead of referring to x and y axes, refer to value and label axes.
		// valueAxis would be y axis if verticalOrientation=false, for example, and would plot expression values (eg. [4.3, 5.2, ...]) there,
		// whereas labelAxis would plot the item labels (eg. ['B','T',...]) along the x axis in this example.
		// dataArea, which refers to the area used by the plot of data only and not including the areas used by axes and their labels, is calculated using these margins.
		this.margin = {'padding':10,	// padding inside targetDiv before svg is drawn
					   'valueAxis':50,	// space used by value axis (eg. 'expression value')
					   //'labelAxis':100,	// space used by label axis (eg. 'cell type')
					   // commented out to check to see if increasing this solves cell type name cut off problem
					   //have not worked out where the total plot size is...
					   'labelAxis':200,	// space used by label axis (eg. 'cell type')
					   
					   'other':15	// right side margin, away from any labeling
					   };
		
		// Define min and max bar size. Note that min size includes padding between bars for simplicity.
		this.barsizeRange = {'min':12, 'max':100};
		// many elements change opacity with mouseover, so it's good to know what default value it should go back to
		this.defaultOpacity = {'bar-over':0.5, 'bar-off':1, 'block-show':0.6, 'block-over':0.3};	
		this.usedColours = [];	// keep track of which colours have been used, so that next distinct colour can be selected	

	}

	//-------------------------------------------------
	// Methods for dealing with data
	//-------------------------------------------------
	ExpressionPlot.prototype.featureIds = function()
	{
		return Object.keys(this.data['values']);
	}
	
	ExpressionPlot.prototype.featureGroupFromFeatureId = function(featureId)
	{
		for (var groupName in this.data['featureGroups']) {
			if (this.data['featureGroups'][groupName].indexOf(featureId)!=-1) {
				return groupName;
			}
		}
		return null;
	}
	
	// Return an array of name values from this.data['colourBy'], eg. ['Multi','Eos','Lymphoid']
	ExpressionPlot.prototype.colourByItems = function()
	{
		return this.data['colourBy'].map(function(d) { return d.name; });
	}

	// Return an array of name values from this.data['groupBy'], eg. ['B','T1','T2']
	ExpressionPlot.prototype.groupByItems = function(colourByItem)
	{
		var colourBy = this.data['colourBy'];
		for (var i=0; i<colourBy.length; i++)
			if (colourBy[i].name==colourByItem) return colourBy[i].groups;
		return null;
	}
	
	// eg. ep.samples('ILMN_1234','B') may return {'mean':3.4, 'min':2.3, 'max':4.3, 'samples':[{'name':'B.1','value':2.3}, ...]}
	// 'mean' is the average of all sample values which belong to featureId, groupItem, 
	// and may be null if there are no sample values for groupItem. Any sample with missing value will be skipped.
	ExpressionPlot.prototype.sampleData = function(featureId, groupItem)
	{
		var sampleNames = this.data['groupBy'].filter(function(d) { return d.name==groupItem; })[0].samples;
		var data = {}, samples = [];
		var valueSum = 0, n = 0;
		var min, max;
		for (var i=0; i<sampleNames.length; i++) {
			var value = this.data['values'][featureId][sampleNames[i]];
			if (value==null) continue;
			samples.push({'name':sampleNames[i], 'value':value});
			valueSum += value;
			n += 1;
			if (!min || value<min) min = value;
			if (!max || value>max) max = value;
		}
		return {'mean':n>0? valueSum/n : null, 'min':min, 'max':max, 'samples':samples};
	}
	
	// Return colour (eg. '#FF34FF'), given value, key combo such as 'Multi','colourBy'.
	// Looks up the colour value corresponding to key in this.data, and tries to return it. 
	// Returns next unused colour failing that, which also works if value or key is omitted altogether.
	ExpressionPlot.prototype.colour = function(value, key)
	{
		var self = this;
		var colour;
		if (key=='colourBy') {	// return colour assigned to colourBy element
			var matchingColourBy = self.data['colourBy'].filter(function(d) { return d.name==value; });
			if (matchingColourBy.length==1)
				colour = matchingColourBy[0].colour;
		}
		if (!colour) colour = self.nextUnusedColour();
		self.usedColours.push(colour);
		return colour;
	}

	// Return a colour which is not yet used on the plot. Uses this.usedColours for this.
	ExpressionPlot.prototype.nextUnusedColour = function()
	{
	
		//Swapped the color order around here to stop it starting out with the bright pink	
		var distinctColours = ["#1B4400", "#4FC601", "#3B5DFF", 
		"#FF2F80", "#61615A", "#BA0900", "#6B7900", "#00C2A0", "#FFAA92", "#FF90C9", "#B903AA", "#4A3B53",  "#D16100",
		"#000035", "#7B4F4B", "#A1C299", "#300018", "#0AA6D8", "#013349", "#00846F", "#372101", "#FFB500", 
		"#A079BF", "#CC0744", "#C0B9B2", "#001E09", "#00489C", "#6F0062", "#0CBD66", "#456D75", "#B77B68", 
		"#7A87A1", "#788D66", "#885578", "#FF8A9A", "#D157A0", "#BEC459", "#456648", "#0086ED", "#886F4C",
		"#34362D", "#B4A8BD", "#00A6AA", "#452C2C", "#636375", "#A3C8C9", "#FF913F", "#938A81", "#575329", 
		"#B05B6F", "#8CD0FF", "#3B9700", "#04F757", "#C8A1A1", "#1E6E00", "#7900D7", "#A77500", "#6367A9", 
		"#A05837", "#6B002C", "#772600", "#D790FF", "#9B9700", "#549E79", "#201625", "#72418F", "#BC23FF", 
		"#3A2465", "#922329", "#5B4534", "#404E55", "#0089A3", "#CB7E98", "#A4E804", "#324E72", "#6A3A4C",
		"#83AB58", "#001C1E", "#004B28", "#A3A489", "#806C66", "#222800", "#BF5650", "#E83000", "#66796D", 
		"#DA007C", "#FF1A59", "#1E0200", "#5B4E51", "#C895C5", "#320033", "#FF6832", "#D0AC94", "#7ED379",
		"#FF34FF", "#FF4A46", "#008941", "#006FA6", "#A30059", "#7A4900", "#0000A6", "#B79762", "#012C58",
		"#004D43", "#8FB0FF", "#997D87", "#5A0007", "#809693",     "#000000"];
	
		var usedColours = this.usedColours.map(function(d) { return d.toUpperCase(); });
		
		for (var i=0; i<distinctColours.length; i++) {
			if (usedColours.indexOf(distinctColours[i])==-1) return distinctColours[i];
		}
		return "#E6E6E6";
	}
		
	//-------------------------------------------------
	// Methods for drawing/plotting
	//-------------------------------------------------
	/* Return svg width and height, as well as dataArea width and height.
	dataArea is the left over area inside svg, used for plotting and not for axes or labels.
	labelLength is the number of labels (or bars) which will be displayed. This is used in conjunction with this.barsizeRange['min']
	to change the svg size if needed.
	*/ 
	ExpressionPlot.prototype.sizes = function(labelLength)
	{
		var self = this;	// avoids conflicting use of 'this' unknowingly inside anonymous functions
		
		// Define svg area = targetDiv area - padding 
		var padding = self.margin['padding'];
		var svgWidth = parseInt(d3.select(self.targetDiv).style('width')) - padding;
		var svgHeight = parseInt(d3.select(self.targetDiv).style('height')) - padding;
	
		// margin inside each side of svg
		var margin = {	top: (self.vo)? self.margin['valueAxis'] : self.margin['other'], 
						right: self.margin['other'], 
						bottom: (self.vo)? self.margin['other'] : self.margin['labelAxis'], 
						left: (self.vo)? self.margin['labelAxis'] : self.margin['valueAxis'] };
	
		// Calculate the amount of svg area needed given minimum bar size (for large datasets). Then change svg size to suit
		if (self.vo && self.barsizeRange['min']*labelLength>svgHeight-margin.top-margin.bottom) {	// expand the svg vertically
			svgHeight = self.barsizeRange['min']*labelLength + margin.top + margin.bottom;
			d3.select(self.targetDiv).style('overflow','auto');
		}
		else if (!self.vo && self.barsizeRange['min']*labelLength>svgWidth-margin.left-margin.right) {	// expand the svg horizontally
			svgWidth = self.barsizeRange['min']*labelLength + margin.left + margin.right;
			d3.select(self.targetDiv).style('overflow','auto');
		}
	
		return {
			'svg':{'width':svgWidth, 'height':svgHeight}, 
			'dataArea':{'width':svgWidth - margin.left - margin.right, 'height':svgHeight - margin.top - margin.bottom},
			'margin': margin
		};
	}
	
	ExpressionPlot.prototype.drawAxes = function(svg, valueScale, labelScale, dataAreaHeight, valueAxisLabel, topMargin, leftMargin)
	{
		var self = this;
		
		// Define axis
		var xAxis = d3.svg.axis()
			.scale((self.vo)? valueScale : labelScale)
			.orient((self.vo)? 'top' : 'bottom');

		var yAxis = d3.svg.axis()
			.scale((self.vo)? labelScale : valueScale)
			.orient('left');

		if (self.vo)
			yAxis.ticks(5);
		else
			xAxis.ticks(5);
		
		// Draw x-axis
		var xline = svg.append('g')
			.attr("class", "x axis")
			.call(xAxis);
			
		if (!self.vo) {	// translate x-axis, and rotate x-axis labels
			xline.attr('transform', 'translate(0,' + dataAreaHeight + ')')
			xline.selectAll("text")  
				.style("text-anchor", "end")
				.style("font-family", "Arial")
				.style("font", "10px sans-serif")
				.attr("dx", "-.6em")
				.attr("dy", ".12em")
				.attr("transform", function(d) { return "rotate(-55)"  });		 
		}
		
		// Draw y-axis
		svg.append('g')
			.attr("class", "y axis")
			.call(yAxis);
			
		// Draw value axis title
		var valueTitle = svg.append("text")
			.style("font-family", "Arial")
			.style('font', '12px sans-serif')
			.text(valueAxisLabel? valueAxisLabel : 'expression value');
		if (self.vo) {
			valueTitle.attr('x', 0)
				.attr('y', -topMargin/2);
		} else {
			valueTitle.attr("transform", "rotate(-90)")
				.attr("y", -leftMargin*0.9)
				.attr("x", -leftMargin)
				.attr("dy", ".71em")
				.style("text-anchor", "end");
		}
	}
	
	/* Lineplot draws a line for each key of this.data['values'], and plots a point for each key of this.data['groupBy'],
	using mean value over samples. 
	*/
	ExpressionPlot.prototype.lineplot = function()
	{
		var self = this;
		self.usedColours = [];	// reset
		self.currentPlot = 'lineplot';
		
		// Create data needed for the plot	
		var minValue = self.data['valueRange'][0]? self.data['valueRange'][0] : 0;	// used to set value scale
		var maxValue = 0;	// will get set after the loop below
		var pathData = [];	// used for line and points plotting - contains 'points' key, whose value is an array of all points on the same line which belong together
		var colourByData = [];	// used for block plotting, where each element corresponds to one item of self.colourByItems()
		var legendData = [];	// used for legend plotting
		
		var colourBy = self.colourByItems();	// eg ['Multi','Lymphoid',...]
		
		var featureGroupColour = {};	// eg {'gene1':'#04F757',...}; if features are grouped, use same colour for all features in the same group
		for (var featureId in self.data['values'])
		{
			var pointData = [];
			var seenGroupNames = [];
			for (var i=0; i<colourBy.length; i++) 
			{
				var groups = self.groupByItems(colourBy[i]);	// eg ['LSK','MPP']
				if (colourByData.length<colourBy.length) {	// only needs to run once per featureId loop
					colourByData.push({'name':colourBy[i], 'colour':self.colour(colourBy[i], 'colourBy')});
				}
	
				// Collect data for each group item using mean over all sample values
				for (var j=0; j<groups.length; j++) {
					if (seenGroupNames.indexOf(groups[j])!=-1)	// it's possible for multiple colourBy items to be assigned to the same group item - what to do?
						continue;
					seenGroupNames.push(groups[j]);
	
					var mean = self.sampleData(featureId, groups[j]).mean;
					// If there is no mean value associated with this groupItem, assign some default value.
					// Since it's possible for this groupItem to have mean value for the next featureId, can't really skip this.
					if (mean==null) mean = 0;
					pointData.push({'name':groups[j], 'value':mean, 'colour':colourByData[i]['colour'], 'colourBy':colourBy[i]});
					if (mean>maxValue) maxValue = mean;
				}
				
			}
			
			// Work out what colour to use for this line
			var pathColour;
			var matchingGroup;	// find feature group matching this featureId
			var featureGroups = Object.keys(self.data['featureGroups']);
			if (featureGroups.length>1 && featureGroups[0]!=self.data['featureGroups'][featureGroups[0]][0]) {	// pathColour should be according to featureGroup
				matchingGroup = self.featureGroupFromFeatureId(featureId);
				if (!(matchingGroup in featureGroupColour))	// assign colour using this feature's group
					featureGroupColour[matchingGroup] = self.colour();
				pathColour = featureGroupColour[matchingGroup];
			} else 
				pathColour = self.colour();
			
			var geneSymbol = self.data['featureGroupNames'][self.featureGroupFromFeatureId(featureId)];
			pathData.push({'name':geneSymbol? geneSymbol + ' (' + featureId + ')' : featureId, 'featureId':featureId, 'colour':pathColour, 'points':pointData});
			legendData.push({'name':geneSymbol? geneSymbol + ' (' + featureId + ')' : featureId, 'featureId':featureId, 'colour':pathColour});
		}
		
		/* pathData should look like:
		[{"name":"ILMN_1234","colour":"#FF4A46","points":[{"name":"B","value":1.48,"colour":"#FF34FF"},{"name":"T","value":3.75,"colour":"#FF34FF"},{"name":"LSK","value":4.81,"colour":"grey"},{"name":"MPP","value":6.3,"colour":"grey"},{"name":"Eo","value":4.25,"colour":"blue"}]},
		 {"name":"ILMN_5678","colour":"#008941","points":[{"name":"B","value":2.83,"colour":"#FF34FF"},{"name":"T","value":1.75,"colour":"#FF34FF"},{"name":"LSK","value":3.84,"colour":"grey"},{"name":"MPP","value":7.7,"colour":"grey"},{"name":"Eo","value":3.75,"colour":"blue"}]}] 
		*/
		
		// Add colourByData to legend so that both are shown
		legendData.push({'name':null, 'colour':null});	// special data point used to draw a line between the two types of legends
		for (var i=0; i<colourByData.length; i++)
			legendData.push(colourByData[i]);
			
		var defaultOpacity = 0.5;
		
		// Now sizes can be determined
		var sizes = self.sizes(pathData[0]['points'].length);
	
		// Define scales. Change maxValue if necessary - see barplot method for exactly same code
		if (self.minTickInterval) {
			if (100*(maxValue - minValue)/self.minTickInterval < sizes.dataArea.height)
				maxValue = sizes.dataArea.height/100*self.minTickInterval + minValue;
		}
		var pointNameScale = d3.scale.ordinal()
			.domain(pathData[0]['points'].map(function(d) { return d['name']; }))	
			.rangeRoundBands([0, (self.vo)? sizes.dataArea.height : sizes.dataArea.width], 0.05, 0);
		var pointIndexScale = d3.scale.ordinal()
			.domain(pathData[0]['points'].map(function(d,i) { return i; }))
			.rangeRoundBands([0, (self.vo)? sizes.dataArea.height : sizes.dataArea.width], 0.05, 0);
		var colourByScale = d3.scale.ordinal()
			.domain(pathData[0]['points'].map(function(d,i) { return i; }))
			.rangeRoundBands([0, (self.vo)? sizes.dataArea.height : sizes.dataArea.width], 0, 0);
		var valueScale = d3.scale.linear()
			.domain([minValue, maxValue])
			.range((self.vo)? [0,sizes.dataArea.width] : [sizes.dataArea.height,0]);
	
		// Clear any existing svg in targetDiv and create svg
		d3.select(self.targetDiv).select('svg').remove();
		self.targetSvg = d3.select(self.targetDiv).append('svg')
			.attr('width', sizes.svg.width)
			.attr('height', sizes.svg.height)
			.append('g')
				.attr("transform", "translate(" + sizes.margin.left + "," + sizes.margin.top + ")");
	
		self.drawAxes(self.targetSvg, valueScale, pointNameScale, sizes.dataArea.height, self.data['value-axis-label'], sizes.margin.top, sizes.margin.left);
		
		// These form background blocks of colour
		var blocks = self.targetSvg.selectAll('.background')
			.data(pathData[0]['points'])
			.enter().append('rect')
				.attr('class','background')
				.attr("x", function(d,i) { return (self.vo)? valueScale(minValue) : colourByScale(i); })
				.attr("y", function(d,i) { return (self.vo)? colourByScale(i) : valueScale(maxValue); })
				.attr("height", (self.vo)? colourByScale.rangeBand() : sizes.dataArea.height)
				.attr("width", (self.vo)? sizes.dataArea.width: colourByScale.rangeBand())
				.style('fill', function(d) { return d.colour; })
				.style('opacity',self.showColourBy? self.defaultOpacity['block-show'] : 0);		
	
		// Define line generator
		var lineFunction = d3.svg.line()
			.x(function(d,i) { return (self.vo)? d.value==0? valueScale(minvalue) : valueScale(d.value) : pointIndexScale(i) + pointIndexScale.rangeBand()/2; })
			.y(function(d,i) { return (self.vo)? pointIndexScale(i) + pointIndexScale.rangeBand()/2 : d.value==0? valueScale(minValue) : valueScale(d.value); })
			.interpolate("linear");
	
		// Attach data to a group element, so each element of data corresponds to a single path
		var series = self.targetSvg.selectAll('.series')
			.data(pathData)
			.enter().append('g')
				.attr('class','series');
			
		// Draw path, consisting of lines between points
		var path = series.append('path')
			.attr('class','path')
			.attr('d', function(d) { return lineFunction(d.points); })
			.attr("stroke", function(d) { return d.colour; })
			.attr("stroke-width", 1)
			.style('opacity',defaultOpacity)
			.attr("fill", "none");
	
		// Because line is very thin, mouseover event doesn't work so well, so draw a thicker line on top and control its opacity on mouseover
		var overlayedPath = series.append('path')
			.attr('class','overlayedPath')
			.attr('d', function(d) { return lineFunction(d.points); })
			.attr("stroke", function(d) { return d.colour; })
			.attr('stroke-width', 3)
			.style('opacity',0)
			.attr("fill", "none")
			.on("mouseover", function(d,i) {
				d3.select(this).style('opacity',1);
				self.highlightLegend(i);
			})
			.on("mouseout", function(d,i) {
				d3.select(this).style('opacity',0);
				self.removeHighlightLegend();
			})
			.on("click", function(d) {
				self.selectedFeatureId = d.featureId;
				self.barplot(d.featureId);
			});
		
		if (self.showLinePoints)	// Draw points using the array under the 'points' key
		{
			var point = series.selectAll('.point')
				.data(function(d) { return d.points; })
				.enter().append('circle')
					.attr('class','point')
					.attr('cx', function(d,i) { return (self.vo)? valueScale(d.value) : pointIndexScale(i) + pointIndexScale.rangeBand()/2; })
					.attr('cy', function(d,i) { return (self.vo)? pointIndexScale(i) + pointIndexScale.rangeBand()/2 : valueScale(d.value); })
					.attr('r', 3)
					.style('fill', function(d) { return d.colour; })
					.on("mouseover", function(d,i) {
						d3.select(this).attr('r',4);
						if (self.showTooltipFunction) self.showTooltipFunction('<b>' + d.name + '</b>: ' + d.value);
					})
					.on("mouseout", function(d,i) {
						d3.select(this).attr('r',3);
						if (self.hideTooltipFunction) self.hideTooltipFunction();
					});
		}
		
		self.legendplot(legendData);
		self.setControlPanel();
	}
	
	ExpressionPlot.prototype.barplot = function(featureId)
	{
		var self = this;
		self.usedColours = [];	// reset
		if (!featureId) featureId = self.selectedFeatureId? self.selectedFeatureId : self.featureIds()[0];
		self.currentPlot = 'barplot';
		
		// Create data needed for the plot	
		var minValue = self.data['valueRange'][0]? self.data['valueRange'][0] : 0;	// used to set value scale
		//var maxValue = self.data['valueRange'][1]? self.data['valueRange'][1] : maxValue;
		var maxValue = 0;
		var barData = [];	// used for bar plotting, where each bar corresponds to a group item
		var pointData = [];	// used for point plotting, where sample points now belong to each bar
		var legendData = [];	// used for legend plotting
		
		var colourBy = self.colourByItems();	// eg ['Multi','Lymphoid',...]
		var index = 0;	// index to use for pointData, which will be same as the order of the parent bar (so i=0 is first bar, etc)
		// Each point will have this index assigned so it knows which bar it belongs to.
		var seenGroupNames = [];
		for (var i=0; i<colourBy.length; i++) 
		{
			var groups = self.groupByItems(colourBy[i]);	// eg ['LSK','MPP']
			var colour = self.colour(colourBy[i], 'colourBy');
			
			if (self.collapsedColourByItems.indexOf(colourBy[i])!=-1) {	// this colourBy item has been "collapsed", hence only show one bar
				// value of the bar is the mean of all samples for all groups, and points also span across all groups
				var sum = 0;
				var sumLength = 0;
				for (var j=0; j<groups.length; j++) 
				{
					var sampleData = self.sampleData(featureId, groups[j]);
					for (var k=0; k<sampleData.samples.length; k++) {
						pointData.push({'name':sampleData.samples[k].name, 'value':sampleData.samples[k].value, 'index':index});
						if (sampleData.samples[k].value>0) {
							sum += sampleData.samples[k].value;
							sumLength += 1;
						}
					}
					if (sampleData.max>maxValue) maxValue = sampleData.max;
				}
				barData.push({'name':colourBy[i], 'value':sumLength>0? sum/sumLength : 0, 'colour':colour, 'colourBy':colourBy[i]});
				index += 1;
			}
			else {
				for (var j=0; j<groups.length; j++) 
				{
					if (seenGroupNames.indexOf(groups[j])!=-1)	// it's possible for multiple colourBy items to be assigned to the same group item - what to do?
						continue;
					seenGroupNames.push(groups[j]);
				
					var sampleData = self.sampleData(featureId, groups[j]);
				
					// If there is no mean value associated with this groupItem, assign some default value (?)
					// For barplot, we can in theory skip this groupItem, but show same default value as lineplot, to be less confusing.
					barData.push({'name':groups[j], 'value':sampleData.mean? sampleData.mean : 0, 'colour':colour, 'colourBy':colourBy[i]});
					if (sampleData.max>maxValue) maxValue = sampleData.max;
				
					for (var k=0; k<sampleData.samples.length; k++)
						pointData.push({'name':sampleData.samples[k].name, 'value':sampleData.samples[k].value, 'index':index});
					index += 1;
					
				}
			}
			legendData.push({'name':colourBy[i], 'colour':colour, 'groups':groups});
		}
		
		/*
		barData = [{"name":"B","value":2.8000000000000003,"colour":"#FF34FF"},{"name":"T","value":1.75,"colour":"#FF34FF"},{"name":"LSK","value":3.8499999999999996,"colour":"grey"},{"name":"MPP","value":7.7,"colour":"grey"},{"name":"Eo","value":3.75,"colour":"blue"}];
		pointData = [{"name":"B.1","value":2.2,"index":0},{"name":"B.2","value":2.5,"index":0},{"name":"B.3","value":3.7,"index":0},{"name":"T.1","value":1.2,"index":1},{"name":"T.2","value":2.3,"index":1},{"name":"LSK.1","value":4.3,"index":0},{"name":"LSK.2","value":3.4,"index":0},{"name":"Mpp.1","value":7.7,"index":1},{"name":"Eo.1","value":3.3,"index":0},{"name":"Eo.2","value":4.2,"index":0}];
		*/
	
		// Now sizes can be determined
		var sizes = self.sizes(barData.length);
	
		// Define scales. If it looks like there won't be enough gap between minValue,maxValue when minTickInterval is
		// specified, increase maxValue. Aim for 100 pixels per tick interval
		if (self.minTickInterval) {
			if (100*(maxValue - minValue)/self.minTickInterval < sizes.dataArea.height)
				maxValue = sizes.dataArea.height/100*self.minTickInterval + minValue;
		}
		var barScale = d3.scale.ordinal()
			.domain(barData.map(function(d) { return d['name']; }))	
			.rangeRoundBands([0, (self.vo)? sizes.dataArea.height : sizes.dataArea.width], 0.05, 0);
		var valueScale = d3.scale.linear()
			.domain([minValue, maxValue])
			.range((self.vo)? [0,sizes.dataArea.width] : [sizes.dataArea.height,0]);
	
		// For barplot, it doesn't look so good to have really thick bars, so reduce the rangeBand of barScale in this case by creating a greater outerPadding.
		// Note that outerPadding is specified as a percentage, so we need to work out what to put there.
		if (barScale.rangeBand()>self.barsizeRange.max) {
			var width = barScale.rangeExtent()[1]-barScale.rangeExtent()[0];
			var outerPadding = (width - self.barsizeRange.max*barData.length - self.barsizeRange.max*0.05*(barData.length-1))/2/self.barsizeRange.max;
			barScale.rangeRoundBands([0, (self.vo)? sizes.dataArea.height : sizes.dataArea.width], 0.05, outerPadding);
		}
	
		// Clear any existing svg in targetDiv and create svg
		d3.select(self.targetDiv).select('svg').remove();
		self.targetSvg = d3.select(self.targetDiv).append('svg')
			.attr('width', sizes.svg.width)
			.attr('height', sizes.svg.height)
			.append('g')
				.attr("transform", "translate(" + sizes.margin.left + "," + sizes.margin.top + ")");
	
		self.drawAxes(self.targetSvg, valueScale, barScale, sizes.dataArea.height, self.data['value-axis-label'], sizes.margin.top, sizes.margin.left);
		
		// Draw bars
		var bars = self.targetSvg.selectAll('.bar')
			.data(barData)
			.enter().append('rect')
				.attr('class','bar')
				.attr("x", function(d) { return (self.vo)? valueScale(minValue) : barScale(d.name); })
				.attr("y", function(d) { return (self.vo)? barScale(d.name) : valueScale(minValue); })
				.attr("height", (self.vo)? barScale.rangeBand() : 0)
				.attr("width", (self.vo)? 0: barScale.rangeBand())
				.style('fill', function(d) { return d.colour; })
				.on("mouseover", function(d) {
					d3.select(this).style('opacity',self.defaultOpacity['bar-over']);
					self.highlightLegend(null, d.colourBy);
					if (self.showTooltipFunction) self.showTooltipFunction('<b>' + d.name + '</b> (' + d.colourBy + '): ' + d.value);
				})
				.on("mouseout", function(d) {
					d3.select(this).style('opacity',self.defaultOpacity['bar-off']);
					self.removeHighlightLegend();
					if (self.hideTooltipFunction) self.hideTooltipFunction();
				});
			
		// Apply transition to the bars
		var trans = bars.transition()
			.duration(500)
			.delay(100);
		if (self.vo) {
			trans.attr("width", function(d) { return d.value==0? 0: valueScale(d.value); });
		} else {
			trans.attr("y",  function(d) { return valueScale(d.value); })
				 .attr("height", function(d) { return d.value==0? 0 : sizes.dataArea.height - valueScale(d.value); });
		}
	
		// Multiple points with zero values can end up at the same position on top of each other.
		// To avoid this, create offset along the width of the bar. Use d3's scale function for this, defined along 80% of the bar widths.
		var jitterScale = {};	// indexed on bar index
		for (var i=0; i<barData.length; i++) {
			jitterScale[i] = d3.scale.ordinal()
				.domain(pointData.filter(function(d) { return d.index==i && d.value==0; }).map(function(d) { return d.name; }))
				.rangePoints([-barScale.rangeBand()*0.8/2, barScale.rangeBand()*0.8/2]);
		}
		
		// Draw points
		var points = self.targetSvg.selectAll('.point')
			.data(pointData)
			.enter().append('circle')
				.attr('class','point')
				.style('fill', function(d) {
					return  'white';
					//return (valueScale(d.value)<=valueScale(barData[d.index].value))? 'grey' : 'white';
				})
				.style('stroke', 'grey')
				.attr('cx', function(d,i) { return (self.vo)? valueScale(0) : d.value==0?  barScale(barData[d.index].name) + jitterScale[d.index](d.name) : barScale(barData[d.index].name); })
				.attr('cy', function(d) { return (self.vo)?d.value==0?  barScale(barData[d.index].name) + jitterScale[d.index](d.name) : barScale(barData[d.index].name) : valueScale(0); })
				.attr('r', 2)
				.on("mouseover", function(d) {
					d3.select(this).attr('r',4);
					if (self.showTooltipFunction) self.showTooltipFunction('<b>' + d.name + '</b> (' + barData[d.index].name + '): ' + d.value);
				})
				.on("mouseout", function(d) {
					d3.select(this).attr('r',2);
					if (self.hideTooltipFunction) self.hideTooltipFunction();
				});
	
		if (self.vo)
			points.attr('transform', 'translate(0,' + barScale.rangeBand()/2 + ')');
		else
			points.attr('transform', 'translate(' + barScale.rangeBand()/2 + ',0)');
		
		// Apply transition to the points
		points.transition()
			.attr(self.vo? 'cx' : 'cy', function(d) { return valueScale(d.value); })
			.duration(500)
			.delay(100);
	
		self.legendplot(legendData);
		self.setControlPanel();
	}
	
	//-------------------------------------------------
	// Control panel and its related methods
	//-------------------------------------------------
	ExpressionPlot.prototype.setControlPanel = function()
	{
		var self = this;
		
		// Construct html elements to be used in the controlPanelDiv
		d3.select(self.controlPanelDiv).selectAll('*').remove();
		
		// Checkbox for rotate
		d3.select(self.controlPanelDiv).append('input')
			.attr('type','checkbox')
			.property('checked', self.vo)
			.on('change', function(d) { self.rotate(this.checked); });
		d3.select(self.controlPanelDiv).append('span')
			.style('margin-right','50px')
			.text('rotate');
	
		if (self.currentPlot=='lineplot') 
		{
			// append colour by checkbox
			d3.select(self.controlPanelDiv).append('input')
				.attr('type','checkbox')
				.property('checked', self.showColourBy)
				.on('change', function(d) { 
					self.showColourBy = this.checked;
					self.targetSvg.selectAll('.background').style('opacity',this.checked? self.defaultOpacity['block-show'] : 0);
				});
			d3.select(self.controlPanelDiv).append('span')
				.style('margin-right','50px')
				.text('show colour by');
				
			// append show line points checkbox
			d3.select(self.controlPanelDiv).append('input')
				.attr('type','checkbox')
				.property('checked', self.showLinePoints)
				.on('change', function(d) {
					self.showLinePoints = this.checked;
					self.lineplot();
				});
			d3.select(self.controlPanelDiv).append('span')
				.style('margin-right','50px')
				.text('show points');
				
			// append span to display how many features are being shown
			d3.select(self.controlPanelDiv)
				.append('span')
				.text('Showing ' + self.featureIds().length + ' features');
		} 
		else // assume barplot
		{
			var plotStateSpan = d3.select(self.controlPanelDiv).append('span');
			if (self.featureIds().length>1) {	// show link to get back to lineplot since there are multiple features
				plotStateSpan
					.append('a')
						.text('All features')
						.attr('href','#')
						.on('click', function(d) { self.lineplot(); });
				plotStateSpan.append('span').text(' > ');
			}
			if (self.selectedFeatureId) {	// show currently selected feature id
				var displayString = self.data['featureGroupNames'][self.featureGroupFromFeatureId(self.selectedFeatureId)]; // gene symbol
				var featureGroups = Object.keys(self.data['featureGroups']);
				if (featureGroups.length>1 && featureGroups[0]!=self.data['featureGroups'][featureGroups[0]][0]) {
					// multiple probes for selected gene, so show gene and probe
					displayString += ' (' + self.selectedFeatureId + ')';
				}
				plotStateSpan.append('span').text(displayString);
			}
		}
	}
	
	// Rotate the plot, preserving the current plot type. vertialOrientation is boolean.
	ExpressionPlot.prototype.rotate = function(verticalOrientation)
	{
		if (verticalOrientation==null || this.vo==verticalOrientation) return;
		this.vo = verticalOrientation;
		if (this.currentPlot=='lineplot') this.lineplot();
		else this.barplot();
	}
	
	//-------------------------------------------------
	// Methods for legend handling
	//-------------------------------------------------
	ExpressionPlot.prototype.legendplot = function(legendData)
	{
		var self = this;
		
		// Draw legend using legendData
		d3.select(self.legendDiv).select('svg').remove();
		self.legendSvg = d3.select(self.legendDiv).append('svg')
			.attr('width', parseInt(d3.select(self.legendDiv).style('width'))*0.9)
			.attr('height', parseInt(d3.select(self.legendDiv).style('height'))*0.9);
	
		var legend = self.legendSvg.selectAll(".legend")
			.data(legendData)
			.enter().append("g")
				.attr("class", "legend");
	
		var legendRect = legend.append("rect")
			.attr("x", 10)
			.attr("y", function(d,i) { return d.name? 6+15*i : 10+15*i; })
			.attr("width", function(d) { return d.name? 10 : 50; })
			.attr("height", function(d) { return d.name? 10 : 1; })
			.style("fill", function(d) { return d.colour? d.colour : 'grey'; })
			.style("opacity", 0.5)
			.on("mouseover", function(d,i) {
				self.highlightLegend(i);
				if (self.currentPlot=='lineplot') self.highlightPath(d.name);
				else self.highlightBars(d.name);
			})
			.on("mouseout", function(d) {
				d3.select(this).style('opacity',0.5);
				self.removeHighlightLegend();
				self.removeHighlightPath();
				self.removeHighlightBars();
			})
			.on("click", function(d,i) {
				if (self.currentPlot=='lineplot' && i<self.featureIds().length) {
					self.selectedFeatureId = d.featureId;
					self.barplot(d.featureId);
				}
			});
	
		var legendText = legend.append("text")
			.attr("class","legendText")
			.attr("x", 25)
			.attr("y", function(d,i) { return 6+15*i; })
			.attr("dy", ".80em")
			.text(function (d) { return d.name? d.name : ''; })
			.style("font-family", "Arial")
			.style('font','10px sans-serif')
			.style('font-weight', function(d) { return (self.currentPlot=='barplot' && self.collapsedColourByItems.indexOf(d.name)!=-1)? 'bold' : 'normal'; })
			.on("mouseover", function(d,i) {
				self.highlightLegend(i);
				if (self.currentPlot=='lineplot') self.highlightPath(d.name);
				else self.highlightBars(d.name);
			})
			.on("mouseout", function(d) {
				self.removeHighlightLegend();
				self.removeHighlightPath();
				self.removeHighlightBars();
			})
			.on("click", function(d,i) {
				if (self.currentPlot=='lineplot' && i<self.featureIds().length) {
					self.selectedFeatureId = d.featureId;
					self.barplot(d.featureId);
				} else if (self.currentPlot=='barplot') {
					// collapse or expand all bars under the current legend item appropriately
					if (self.groupByItems(d.name).length<2) return;	// ignore if there is only one bar under this legend anyway
					var index = self.collapsedColourByItems.indexOf(d.name);
					if (index==-1) {	// not currently collapsed
						self.collapsedColourByItems.push(d.name);
					} else { // currently collapsed
						self.collapsedColourByItems.splice(index,1);
					}
					// draw barplot again, since data has changed
					self.barplot();
				}
			});
	}
	
	ExpressionPlot.prototype.highlightLegend = function(index, legendName)
	{
		var self = this;
		self.legendSvg.selectAll('rect').each(function(d,i) {
			if (index!=null && i==index || legendName==d.name) d3.select(this).style('opacity',1);
		});
		self.legendSvg.selectAll('text').each(function(d,i) {
			if (index!=null && i==index || legendName==d.name) d3.select(this).style('font-weight','bold');
		});
	}
	
	ExpressionPlot.prototype.removeHighlightLegend = function()
	{
		var self = this;
		self.legendSvg.selectAll('rect').each(function(d) {
			d3.select(this).style('opacity',0.5);
		});
		self.legendSvg.selectAll('text').each(function(d) {	// only put font weight back to normal if it's not a collapsed item
			if (self.collapsedColourByItems.indexOf(d.name)==-1)
				d3.select(this).style('font-weight','normal');
		});
	}
	
	ExpressionPlot.prototype.highlightPath = function(legendName)
	{
		var self = this;
		// highlight matching .overlayedPath
		self.targetSvg.selectAll('.overlayedPath').each(function(d) {
			if (d.name==legendName) d3.select(this).style('opacity',0.8);
		});
		// highlight matching .background
		self.targetSvg.selectAll('.background').each(function(d) {
			if (d.colourBy==legendName) d3.select(this).style('opacity',self.defaultOpacity['block-over']);
		});
	}
	
	ExpressionPlot.prototype.removeHighlightPath = function()
	{
		var self = this;
		self.targetSvg.selectAll('.overlayedPath').each(function(d) {
			d3.select(this).style('opacity',0);
		});
		self.targetSvg.selectAll('.background').each(function(d) {
			d3.select(this).style('opacity',self.showColourBy? self.defaultOpacity['block-show'] : 0);
		});
	}
	
	ExpressionPlot.prototype.highlightBars = function(legendName)
	{
		var self = this;
		// highlight matching .bar
		var groupByItems = self.groupByItems(legendName);
		self.targetSvg.selectAll('.bar').each(function(d) {
			if (groupByItems.indexOf(d.name)!=-1)
				d3.select(this).style('opacity',self.defaultOpacity['bar-over']);
		});
	}
	
	ExpressionPlot.prototype.removeHighlightBars = function()
	{
		var self = this;
		self.targetSvg.selectAll('.bar').each(function(d,i) {
			d3.select(this).style('opacity',self.defaultOpacity['bar-off']);
		});
	}
	
	//-------------------------------------------------
	// 
	//-------------------------------------------------
	// Run either lineplot or barplot, depending on data
	ExpressionPlot.prototype.draw = function(data)
	{
		if (data && data['values'])	
			this.data = data;
	
		if (this.featureIds().indexOf(this.selectedFeatureId)==-1)
			this.selectedFeatureId = null;
	
		if (this.featureIds().length==1) {	// always draw barplot
			this.selectedFeatureId = this.featureIds()[0];
			this.barplot();
		}
		else {	// depends on some other states
			if (this.selectedFeatureId!=null)	// already have a valid selected a feature
				this.barplot();
			else 
				this.lineplot();
		}		
	}
	
	// Return this.targetSvg and this.legendSvg as html strings. An array is returned, one for each svg.
	ExpressionPlot.prototype.svgsAsHtml = function()
	{
		// Was trying to clone the svg in order to add elements/styles before returning the html,
		// but couldn't make this work.
// 		var attr = this.targetSvg.node().attributes;
// 		var length = attr.length;
// 		var node_name = this.targetSvg.property("nodeName");
// 		var parent = d3.select(this.targetSvg.node().parentNode);
// 		var cloned = parent.append(node_name);
// 		for (var j = 0; j < length; j++) {
// 			cloned.attr(attr[j].name,attr[j].value);
// 		}
// 		cloned.selectAll(".axis path").style({'stroke':'#cfcfcf', 'stroke-width':'1px', 'fill':'none'});	// this doesn't work
// 		cloned.selectAll(".axis text").style({'font-size':'11px', 'color':'#cfcfcf'});
//		return [cloned.node().parentNode.outerHTML, this.legendSvg.node().parentNode.outerHTML];
		
		// After trying various ways to incorporate the styles coming from css, just using this hack for now.
		// Note that if currentPlot=='lineplot', it will have path element, which already has style attribute
		// assigned (via opacity). So we need to remove this before adding another style
		var currentPathStyle = this.targetSvg.selectAll('path').attr('style');
		this.targetSvg.selectAll('path').attr('style',null);
		
		var targetSvgString = this.targetSvg.node().parentNode.outerHTML
			.replace(/<path /g, "<path style='stroke:#cfcfcf; stroke-width:1px; fill:none;' ")
			.replace(/<line /g, "<line style='stroke:#cfcfcf; stroke-width:1px; fill:none; shape-rendering: crispEdges;' ")
			.replace(/<svg .*?>/, "<svg width=\"2188\" height=\"1080\" viewBox=\"0 0 1094 540\" preserveAspectRatio=\"xMinYMax meet\">");
		
		var legendSvgString = this.legendSvg.node().parentNode.outerHTML
			.replace(/<div id="legend-div" .*?>/, '')
			.replace(/<svg .*?>/, "<svg width=\"400\" height=\"1000\" viewBox=\"0 0 200 500\" preserveAspectRatio=\"xMinYMax meet\">")
			.replace(/<\/svg><\/div>/, "</svg>");

		// replace removed path style
		this.targetSvg.selectAll('path').attr('style',currentPathStyle);

		return [targetSvgString, legendSvgString];
		
		// This only returns the <g> element onwards rather than whole <svg>
		//return (new XMLSerializer).serializeToString(this.targetSvg.node());

		/* some experimental code playing with trying to pick up styles from stylesheets
		var sheets = document.styleSheets;
		for (var i = 0; i < sheets.length; i++) {
			var rules = sheets[i].cssRules;
			for (var j = 0; j < rules.length; j++) {
				var rule = rules[j].selectorText;

				if (typeof(rules[j].style) != "undefined") {
				//console.log(i,j,rule);
				if (rule.indexOf("axis")>-1) {
					var splitText = rule.split(" ");
					for (var k=0; k<splitText.length; k++) {
						if (!splitText[k].startsWith("."))
							console.log(rule, this.targetSvg.node().querySelectorAll(splitText[k]));
					}
				}
				//if (rule.startsWith(".") || rule.startsWith("[") || rule.startsWith("ng:")) continue;
				//var elems = this.targetSvg.node().querySelectorAll(rule);
				//if (elems.length > 0) {
				//  console.log(rule.selectorText, JSON.stringify(elems));
				//}
				}
			}
		}
		*/
	}
/*
	// Base class used by both bar and line plots
	var Base = function(params) {
		var self = this;
		
		// Parse params
		// svg: if string, assume id that we can select using d3.select, otherwise it's a selection
		self.svg = (typeof params['svg'] === 'string' || params['svg'] instanceof String)?
			d3.select(params['svg']) : self.svg = params['svg'];
		
		self.svgWidth =  parseInt(self.svg.style("width"));
		self.svgHeight = parseInt(self.svg.style("height"));

	}
*/	
	exports.ExpressionBarplot = ExpressionPlot;
	
})(this.expbarplot = {});

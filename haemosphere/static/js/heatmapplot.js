(function(exports)
{

	/* -----------------------------------------------------------------------------------
	Example:
	var sp = HeatmapPlot({'div':d3.select('#mainDiv')});
	var data = {{'matrix':[{'x':2.4, 'y':-1.3, 'name':'cell1', 'value':2.3},...],...}, 
				{'rowLabels':['x','y',...]}, {'columnLabels':['a','b',...]}, {'colours':['#ccc',...]}
			   }  // colours is optional
	sp.draw(data); 	

	*/
	
	// Contructor
	var HeatmapPlot = function(params) {
		var self = this;

		self.svg = params['svg'],
		self.data = params['data'];
		self.mouseoverFunction = params['mouseover'];
		self.mouseoutFunction = params['mouseout'];
		self.clickFunction = params['click'];
	
		// svg elements
		self.circle;
		self.label;
		self.xAxis;
		self.yAxis;
		self.xScale;
		self.yScale;
	
		self.svgWidth = function() { return parseInt(this.mainDiv.style("width")); }
		self.svgHeight;
		
		self.headerHeight = function() { return parseInt(this.topDiv.style("height")); }

		self.div = params['div'];
		self.rowLabelWidth = params['rowLabelWidth']? params['rowLabelWidth'] : 100;	// amount of space taken up by row labels
		self.minSquareWidth = params['minSquareWidth']? params['minSquareWidth'] : 15;	// don't make each square smaller than this
		self.minSquareHeight = params['minSquareHeight']? params['minSquareHeight'] : 15;	// don't make each square smaller than this
		self.rowLabelClickFunction = params['rowLabelClickFunction'];
	
		// Divide div into two divs, one for column headers, the other for main area
		self.topDiv = self.div.append("div")
			.style("width", self.div.style("width"))
			.style("height", "120px")
			.style("overflow","auto");

		self.mainDiv = self.div.append("div")
			.style("width", self.div.style("width"))
			.style("height", "450px")
			.style("overflow","auto");
	}

	HeatmapPlot.prototype.draw = function(data)
	{
		var self = this;
		if (data!=null) self.data = data;

		// process data - this determines svg size
		var columnLabels = data['columnLabels'];
		var rowLabels = data['rowLabels'];
		var matrix = data['matrix'];
		if (data['valueRange']!=null) {	// valueRange has already been specified, so no need to work it out
			self.minValue = data['valueRange'][0];
			self.maxValue = data['valueRange'][1];
		} else {	// work it out
			self.minValue = matrix[0].value,
			self.maxValue = self.minValue;
			for (var i=0; i<matrix.length; i++) {
				if (matrix[i].value>self.maxValue) self.maxValue = matrix[i].value;
				else if (matrix[i].value<self.minValue) self.minValue = matrix[i].value;
			}
		}
	
		var svgWidth = parseInt(self.mainDiv.style('width')) - 20;	// 20px padding within the div
		if (self.minSquareWidth*columnLabels.length > svgWidth) // expand svg width
			svgWidth = self.minSquareWidth*columnLabels.length;
		var columnLabelHeight = parseInt(self.topDiv.style('height'));	// how high to make column label area
	
		// matrix is sub-part of main svg for drawing the heatmap (ie. it's main svg - row label svg)
		var matrixWidth = svgWidth - self.rowLabelWidth;
		var matrixHeight = self.minSquareHeight*rowLabels.length*1.1;
		var squareWidth = matrixWidth/columnLabels.length-2;	// create 2 pixel border around each rectangle
 		self.svgHeight = matrixHeight;

		// set scales
		var xScale = d3.scale.linear()
			.domain([0, columnLabels.length])
			.range([0, matrixWidth]);
		var yScale = d3.scale.linear()
			.domain([0, rowLabels.length])
			.range([0, matrixHeight]);	// keep top-left as (0,0) coordinate for heatmap
		self.colourScale = d3.scale.linear()
			.domain([self.minValue,self.maxValue*0.5,self.maxValue])
			.range(['blue','white','red']);
		var barScale = d3.scale.linear()	// to be used for barplot
			.domain([self.minValue, self.maxValue])
			.range([2,columnLabelHeight]);

		// remove all previous items
		self.topDiv.selectAll('svg').remove();
		self.mainDiv.selectAll('svg').remove();
	
		// there are 2 svg areas, one that fills topDiv, the other inside mainDiv; the mainSvg is also broken into two areas
		self.topSvg = self.topDiv.append('svg')
			.attr( "width", svgWidth)
			.attr( "height", columnLabelHeight);
		
		self.mainSvg = self.mainDiv.append('svg')
			.attr( "width", svgWidth)
			.attr( "height", matrixHeight);
		
		self.matrixArea = self.mainSvg.append('g')
			.attr('class','matrix')
			.attr('transform', 'translate(' + self.rowLabelWidth + ',0)');

		// This can synchronise topDiv and mainDiv on horizontal scroll!
		// But only when mainDiv scrolls - can't do this symmetrically else we just get into a loop
		self.mainDiv.on('scroll', function () {
			self.topDiv.property('scrollLeft', d3.select(this).property('scrollLeft'));
		});

		// Draw each square of heatmap
		self.square = self.matrixArea.selectAll('rect.square')
			.data(matrix)
			.enter()
			.append('rect')
				.attr('class','square')
				.attr('width', squareWidth)
				.attr('height',self.minSquareHeight)
				.attr('x', function(d) { return xScale(d.x); })
				.attr('y', function(d) { return yScale(d.y); })
				.style('fill', function(d) { return self.colourScale(d.value); })
				//.style('opacity', '0.7')
				//.style('stroke-width','1px')
				//.style('stroke','white')
				.on("mouseover", function(d,i) {
					d3.select(this).style('stroke','black').style('stroke-width','2px');
					if (self.mouseoverFunction) self.mouseoverFunction(d.name);
				})
				.on("mouseout", function() {
					d3.select(this).style('stroke','none');
					if (self.mouseoutFunction) self.mouseoutFunction();
				});

		// Draw row labels
		self.rowLabels = self.mainSvg.append('g')
			.attr('class','label')
			//.attr('transform', 'translate(5,0)')
			.selectAll('text.label')
			.data(rowLabels)
			.enter()
			.append('text')
				.style('text-anchor', 'end')
				.attr('class','label')
				.attr('font-size', 12)
				.text(function(d){ return d.displayString.length>14? d.displayString.substr(0,11) + '...' : d.displayString; })
				.attr('x', self.rowLabelWidth)	
				.attr('y', function(d,i){ return yScale(i)+self.minSquareHeight; })  // need to add square height to align bottom of text with bottom of square
				.on("mouseover", function(d,i) {
					d3.select(this).style('font-weight','bold');
					if (self.mouseoverFunction) self.mouseoverFunction(d.displayString + ' (' + d.featureId + ')');
					showBarplot(i);
				})
				.on("mouseout", function() {
					d3.select(this).style('font-weight','normal');
					if (self.mouseoutFunction) self.mouseoutFunction();
					hideBarplot();
				})
				.on("click", function(d,i) {
					//reorder(i,0);
					if (self.rowLabelClickFunction) self.rowLabelClickFunction(d);
				});

		// Draw column labels - note that x,y coordinates define the bottom left point of text, 
		// so we need to rotate translate this appropriately to fit into the topSvg.
		// Ensure that x,y in "transform=rotate(270, x, y)" is the same as the x,y of text, 
		// otherwise rotated text will end up somewhere else since it rotates around the origin (0,0) by default
		self.columnLabels = self.topSvg.selectAll('text.column')
			.data(columnLabels)
			.enter()
			.append('g');
		self.columnLabels.append('rect')
				.attr('class','barplot')
				.attr('width', squareWidth)
				.attr('height',0)
				.attr('x', function(d,i){ return xScale(i) + self.rowLabelWidth; })			
				.attr('y', function(d){ return 0; })
				.style('opacity', '0.7');
		self.columnLabels.append('text')
				.style('text-anchor', 'start')
				.attr('font-size', squareWidth<12? squareWidth : 12)
				.text(function(d){ return d.length>18? d.substr(0,15) + '...' : d; })
				.attr('x', function(d,i){ return xScale(i) + self.rowLabelWidth + squareWidth; })			
				.attr('y', columnLabelHeight)
				.attr('transform', function(d,i){ return 'rotate(270 ' + (xScale(i) + self.rowLabelWidth + squareWidth) + ',' + columnLabelHeight + ')'; })
				.on("mouseover", function(d,i) {
					d3.select(this).style('font-weight','bold');
					if (self.mouseoverFunction) self.mouseoverFunction(d);
				})
				.on("mouseout", function() {
					d3.select(this).style('font-weight','normal');
					if (self.mouseoutFunction) self.mouseoutFunction();
				});

		// activated on a hover event, this function can be used to show barplot of selected rowId
		var showBarplot = function(rowIndex)
		{
			// Fetch all data points matching rowIndex
			var values = [];
			for (var i=0; i<matrix.length; i++)
				if (matrix[i].y==rowIndex) values.push(matrix[i]);
		
			// Modify height of .barplot rectangles
			self.topDiv.selectAll('rect.barplot').each(function(d,i) {
				if (barScale(values[i].value)) {
					d3.select(this)
						.attr('y', columnLabelHeight-barScale(values[i].value))
						.attr('height', barScale(values[i].value))
						.style('fill', self.data.colours!=null? self.data.colours[i] : '#ccc');
				}
			});
		}
	
		var hideBarplot = function()
		{
			self.topDiv.selectAll('rect.barplot').each(function(d,i) {
				d3.select(this).attr('height', 0);
			});
		}

		var reorder = function(index, axis)
		{
			// parse input
			var attr = ['x','y'][axis];	// which attribute of matrix should be changed
			var compAttr = ['y','x'][axis];	// complementary to attr, this attribute is used to match the corresponding values,
			// so when we're reordering rows (axis=0), we need to look at 'y' value to match index.
			var rowOrCol = axis==0? self.rowLabels : self.columnLabels;
		
			// First get all matrix items values along the axis at the specified index.
			// If index=2 and axis=1 for example, we want all items with attribute x=2
			var items = [];	// [{'x':3,'y':5,'value':3.54,'name':'some name'},...]
			for (var i=0; i<matrix.length; i++) {
				if (matrix[i][compAttr]==index)
					items.push(matrix[i]);
			}
		
			// Now sort items with highest to lowest on value
			items.sort(function(item1,item2) {
				if (item1.value>item2.value) return -1;
				else if (item1.value<item2.value) return 1;
				else return 0;
			});
		
			// Extract values of targetAttr from sorted array
			var orderedArray = Array(items.length);	// eg. [20,33,32,18,...]
			for (var i=0; i<items.length; i++) 
				orderedArray[items[i][attr]] = i;	// this time we're reordering the attribute along the same line as axis
	
			// So orderedArray holds new position relative to old.
			// Eg: [20,33,32,...] and axis=0 means matrix elements should change y values so that 20=>0, 33=>1, etc.
			var newRowOrCol = Array(orderedArray.length);
			for (var i=0; i<orderedArray.length; i++) {
				// Find all matrix elements with compAttr=orderedArray[i]
				for (var j=0; j<matrix.length; j++) {
					if (matrix[compAttr]==orderedArray[i])
						matrix[compAttr] = i;
				}
				// insert corresponding element to newRowOrCol 
				newRowOrCol[orderedArray[i]] = rowOrCol[i];
			}
			console.log(JSON.stringify(newRowOrCol));
			return;

			self.draw(axis==0? {'rowLabels':newRowOrCol, 'columnLabels':self.data.columnLabels, 'matrix':matrix} : 
							   {'rowLabels':self.data.rowLabels, 'columnLabels':newRowOrCol, 'matrix':matrix});
		}
	}

	HeatmapPlot.prototype.svgAsHtml = function()
	{		
		var self = this;
		var bodyHeight = self.svgHeight+20;
		var width = self.svgWidth();
		var headerHeight = self.headerHeight();
		
		var headerString = this.topDiv.node().outerHTML
			.replace(/.*<svg .*?>/, "<svg width=\"" + width * 2 + "\" height=\"" + (headerHeight) * 2 + "\" viewBox=\"0 0 " + width + " " + (headerHeight) + " \" preserveAspectRatio=\"xMinYMax meet\">");
		
		var bodyString = this.mainDiv.node().parentNode.outerHTML
			.replace(/.*<svg .*?>/, "<svg width=\"" + width * 2 + "\" height=\"" + (bodyHeight) * 2 + "\" viewBox=\"0 0 " + width + " " + (bodyHeight) + " \" preserveAspectRatio=\"xMinYMax meet\">");
		
		return [headerString, bodyString, headerHeight, bodyHeight, width];
	}

	exports.HeatmapPlot = HeatmapPlot;
	
})(this.heatmapplot = {});

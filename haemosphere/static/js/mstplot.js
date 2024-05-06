(function(exports)
{

	/* -----------------------------------------------------------------------------------
	djset class as defined by Toby, used by mst calculations.
	*/
	var djset = function(N) {
		this.reset(N);
	};

	djset.prototype.reset = function(N) {
		this.n_sets = N;
		this.set = [];
		for (var i = 0; i < N; ++i) {
			this.set.push([i, 0])
		}
	};

	djset.prototype.find_set_head = function(a) {
		var a_head;
		if (a === this.set[a][0]) return a;

		a_head = a;
		while (this.set[a_head][0] != a_head) {
			a_head = this.set[a_head][0];
		}

		this.set[a] = [ a_head, this.set[a][1] ];
		return a_head;
	};

	djset.prototype.same_set = function(a, b) {
		return this.find_set_head(a) == this.find_set_head(b);
	};

	djset.prototype.merge_sets = function(a, b) {
		a = this.find_set_head(a);
		b = this.find_set_head(b);
		if (a != b) {
			this.n_sets -= 1;
			if (this.set[a][1] < this.set[b][1]) {
				this.set[a] = [ b, this.set[a][1] ];
			} else if (this.set[b][1] < this.set[a][1]) {
				this.set[b] = [ a, this.set[b][1] ];
			} else {
			  this.set[a] = [ this.set[a][0], this.set[a][1] + 1 ]
			  this.set[b] = [ a, this.set[b][1] ]
			}
		}
	};

	/* -----------------------------------------------------------------------------------
	heap class as defined by Toby, used by mst calculations.
	*/
	var heap = function(pred) {
		this.pred = pred || (function (a,b) { return a < b; });
	};

	heap.prototype.is_heap = function(array, len) {
		var parent = 0;

		for (var child = 1; child < len; ++child) {
			if (this.pred(array[parent], array[child])) return false;
			if (++child == len) break;
			if (this.pred(array[parent], array[child])) return false;
			++parent;
		}
		return true;
	};

	heap.prototype.remove = function(array, pos, len) {
		--len;
		if (pos != len) {
			var removed = array[pos];
			this.adjust(array, pos, len, array[len]);
			array[len] = removed;
		}
	};

	heap.prototype.pop = function(array, len) {
		this.remove(array, 0, len);
	};

	heap.prototype.sort = function(array, len) {
		while (len > 1) {
			this.remove(array, 0, len--);
		}
	};

	heap.prototype.push = function(array, pos, val) {
		var parent = (pos - 1) >> 1;
		while (pos > 0 && this.pred(array[parent], val)) {
			array[pos] = array[parent];
			pos = parent;
			parent = (pos - 1) >> 1;
		}
		array[pos] = val;
	};

	heap.prototype.adjust = function(array, pos, len, val) {
		var top = pos;
		var child = pos * 2 + 2;
		while (child < len) {
			if (this.pred(array[child], array[child-1])) --child;
			array[pos] = array[child];
			pos = child;
			child = pos * 2 + 2;
		}
		if (child == len) {
			--child;
			array[pos] = array[child];
			pos = child;
		}
		var parent = (pos - 1) >> 1;
		while (pos > top && this.pred(array[parent], val)) {
			array[pos] = array[parent];
			pos = parent;
			parent = (pos - 1) >> 1;
		}
		array[pos] = val;
	};

	heap.prototype.make = function(array, len) {
		for (var pos = len >> 1; pos > 0;) {
			--pos;
			this.adjust(array, pos, len, array[pos]);
		}
	};

	/* -----------------------------------------------------------------------------------
	prim as defined by Toby, used by mst calculations.
	*/
	var prim = function(dist, N) {
		var H = new heap(function(a,b) {
			return dist(a%N,Math.floor(a/N)) > dist(b%N,Math.floor(b/N));
		});

		var arr = new Uint32Array(N * (N-1) >> 1);
		var arrlen = 0;
		for (var i = 0; i < N; ++i) {
			for (var j = i + 1; j < N; ++j) {
				if (dist(i,j) > 0.0) {
					arr[arrlen++] = i + j*N;
				}
			}
		}

		H.make(arr, arrlen);

		var groups = new djset(N);
		var edges = [];

		while (edges.length < N-1) {
			while (true) {
				H.pop(arr, arrlen);
				var edge = arr[--arrlen];
				var a = edge%N;
				var b = Math.floor(edge/N);
				if (!groups.same_set(a, b)) {
					groups.merge_sets(a, b);
					edges.push([a,b]);
					break;
				}
			}
		}

		return edges;
	};
	
	/* -----------------------------------------------------------------------------------
	Main MstPlot class used for plotting.
	Example:
		>> var mstPlot = new mstplot.MstPlot({'svg':d3.select("#mainSvg")});
		>> mstPlot.draw({'data': [[0,2,3,2],[2,0,4,1],[3,4,0,5],[2,1,5,0]],
						 'labels':[{'name':'a','display':'A','colour':'#ccc'},
						 		   {'name':'b','display':'A','colour':'#ccc'},
						 		   {'name':'c','display':'B','colour':'#ccc'},
						 		   {'name':'d','display':'B','colour':'#ccc'}]});

	Note that 'name' must be unique in 'labels', otherwise loops will form.
	draw function basically converts 'data' and 'labels' into links and nodes first, then renders
	them using force layout.
	*/
	var MstPlot = function(params) {
	
		this.svg = params['svg'],
		this.data = params['data'];
		this.mouseoverFunction = params['mouseover'];
		this.mouseoutFunction = params['mouseout'];
		this.clickFunction = params['click'];
	
		// svg elements
		this.circle;
		this.label;
		this.line;	// this is the line connecting the nodes
		this.force;	
	}

	// Function to convert distance matrix into links and nodes.
	function mstDataFromDist(distMatrix, labels)
	{
		var dist = function(x,y) { return distMatrix[x][y]; }; // this is the accessor for your distance matrix.
		// if dist(x,y) returns a value <= 0 for some x,y then the edge x,y is not considered in the MST. dist() will always be called with x<y.

		// Build edges/links
		var edges = prim(dist, distMatrix.length); // arguments - the distance accessor, and the number of nodes.
		var links = [];
		for (var i=1; i<edges.length; i++) 
			links.push({'source':labels[edges[i][0]].name, 'target':labels[edges[i][1]].name, 'colour':"#cccccc"});

		// Build nodes based on edges
		var nodes = {};
		for (var i=0; i<links.length; i++) {
			links[i].source = nodes[links[i].source] || (nodes[links[i].source] = {'name':links[i].source, 'colour':labels[edges[i][0]].colour, 'message':labels[edges[i][0]].display});
			links[i].target = nodes[links[i].target] || (nodes[links[i].target] = {'name':links[i].target, 'colour':labels[edges[i][1]].colour, 'message':labels[edges[i][1]].display});
		}
	
		return {'links':links, 'nodes':nodes};
	}

	MstPlot.prototype.draw = function(data)
	{
		var self = this;
		if (data) self.data = data;	// save data passed on

		var data = mstDataFromDist(data['data'], data['labels']);	// define links and nodes data required for drawing
		var links = data['links'];
		var nodes = data['nodes'];
		var radius = 5;
		var width = parseInt(self.svg.style('width'));
		var height = parseInt(self.svg.style('height'));
		
		// remove all previous items
		self.svg.selectAll('*').remove();
											
		// Define force
		self.force = d3.layout.force()
			.nodes(d3.values(nodes))
			.links(links)
			.size([width, height])
			//.linkDistance(20)
			.charge(-250)
			.start();
				
		// Draw edges/links
		self.line = self.svg.selectAll("line")
			.data(links)
		.enter().append("line")
			.style("stroke", "#ccc")
			.style("stroke-width", 1);
		
		// Draw circles
		self.circle = self.svg.append("g").selectAll("circle")
			.data(self.force.nodes())
		  .enter().append("circle")
			.attr("r", radius)
			.attr("rx", radius)
			.attr("ry", radius)
			.style("fill", function(d) { return d.colour; })
			.attr("shape-rendering", "auto")
			.on("mouseover", function(d,i) {
				self.highlightCircle(d,i);
				self.highlightLabel(d,i);
				if (self.mouseoverFunction) self.mouseoverFunction(d);
			})
			.on("mouseout", function(d,i) {
				self.removeHighlightCircle(d.name);
				self.removeHighlightLabel(d.name);
				if (self.mouseoutFunction) self.mouseoutFunction(d);
			})
			.on("click", function(d) { 
				if (self.clickFunction) self.clickFunction(d,i);
			})
			.call(self.force.drag);

		// Draw text
		self.label = this.svg.append("g").selectAll("text")
			.data(self.force.nodes())
		  .enter().append("text")
			.attr("x", 10)
			.attr("y", 10)
			.text(function(d) { return d.message; })
			.style("font-size","10px")
			.on("mouseover", function(d,i) {
				self.highlightCircle(d,i);
				self.highlightLabel(d,i);
				if (self.mouseoverFunction) self.mouseoverFunction(d);
			})
			.on("mouseout", function(d,i) {
				self.removeHighlightCircle(d.name);
				self.removeHighlightLabel(d.name);
				if (self.mouseoutFunction) self.mouseoutFunction(d);
			})
			.on("click", function(d) { 
				if (self.clickFunction) self.clickFunction(d,i);
			});

		// Run the Force effect
		self.force.on("tick", function() {
		   self.line.attr("x1", function(d) { return d.source.x; })
					.attr("y1", function(d) { return d.source.y; })
					.attr("x2", function(d) { return d.target.x; })
					.attr("y2", function(d) { return d.target.y; });

			//self.circle.attr("cx", function(d) { return d.x = Math.max(radius, Math.min(width - radius, d.x)); })
			//		   .attr("cy", function(d) { return d.y = Math.max(radius, Math.min(height - radius, d.y)); });
				
			self.circle.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
			self.label.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
								   
		}); // End tick func

		var zoom = d3.behavior.zoom().scaleExtent([0.1,7]);
		zoom.on("zoom", function() {
			self.circle.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
			self.label.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
		});
		//self.svg.call(zoom);	  

	}
	
	// Highlight matching circle
	MstPlot.prototype.highlightCircle = function(d,i)
	{
		var self = this;
		self.circle.each(function(x,j) {
			if (j!=i) d3.select(this).style("opacity", 0.3);
		});
	}
	MstPlot.prototype.removeHighlightCircle = function(d,i)
	{
		var self = this;
		self.circle.each(function(x) {
			d3.select(this).style("opacity", 1);
		});
	}

	// Highlight matching label
	MstPlot.prototype.highlightLabel = function(d,i)
	{
		var self = this;
		self.label.each(function(x,j) {
			if (j!=i) d3.select(this).style("opacity", 0.3);
		});
	}
	MstPlot.prototype.removeHighlightLabel = function(d,i)
	{
		var self = this;
		self.label.each(function(x) {
			d3.select(this).style("opacity", 1);
		});
	}
		
	// Return this.svg as html string
	MstPlot.prototype.svgAsHtml = function()
	{		
		var svgString = this.svg.node().parentNode.outerHTML
			.replace(/(<svg .*? width=\").*?(\".*)/, '$1400$2');	// replace <svg ... width="135.9" ...> with <svg width="400" ...>
		
		return svgString;
	}

	exports.MstPlot = MstPlot;
	
})(this.mstplot = {});

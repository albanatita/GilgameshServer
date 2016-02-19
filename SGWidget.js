define(['jquery', 'nbextensions/widgets/widgets/js/widget'], function($, widget) {

	var MyWidgetView = widget.DOMWidgetView.extend({
		render: function() {
			var that = this;
					//console.log('tototot1');
			$("head").append([
			"<link href='/static/slick/slick.grid.css' rel='stylesheet'>",
			"<link href='/static/slick/slick-default-theme.css' rel='stylesheet'>",
			"<link rel='stylesheet' href='/static/slick/css/smoothness/jquery-ui-1.8.16.custom.css' type='text/css'/>",
			"<link href='https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.10.4/css/jquery-ui.min.css' rel='stylesheet'>",
			"<link href='/static/qgrid.css' rel='stylesheet'>"
			]);
			var path_dictionary = {
				slick_core:  "/static/slick/slick.core",
				slick_data_view:  "/static/slick/slick.dataview",
				slick_grid:  "/static/slick/slick.grid",
				jquery_drag: "/static/slick/lib/jquery.event.drag-2.2",
				slick_row_selection_model: "/static/slick/plugins/slick.rowselectionmodel"
			};
		 require.config({
				paths: path_dictionary
			});


			require([
				'jquery_drag',				
				'slick_core',
				'slick_data_view',
				'slick_row_selection_model',
			],
			function() {
				require(['jquery','slick_grid'], function($,Slick) {
						   // console.log('tototo2');
							//that.setupTable(dgrid);
/* 							that.$el.addClass('q-grid-container');
							var table = that.$el.append('div');
							table.addClass('q-grid');
							that.tableDiv = table[0];
							that.tableDiv.setAttribute("style", "width: 500px;");
							that.tableDiv.setAttribute("style", "height: 500px;");
							 var parent = that.el.parentElement;
							while (parent.className !== 'widget-area') {
								parent = parent.parentElement;
							}
							var width = (parent.clientWidth - parent.childNodes[0].clientWidth);
							that.el.setAttribute("style", "max-width:" + String(width) + "px;");
							that.drawTable();
						 */
						 that.$el.append('<div id="myGrid" style="width:900px;height:500px;"></div>');
						 //that.model.on('msg:custom', that.handleMsg, that);
						 that.drawTable();
				});
			});
			
		},

		drawTable: function() {
			var that = this;

			var df = JSON.parse(this.model.get('value'));
			var columns = JSON.parse(this.model.get('columns'));


			var slickgrid=new Slick.Grid("#myGrid", df,columns);
			slickgrid.setSelectionModel(new Slick.RowSelectionModel());
			slickgrid.onSelectedRowsChanged.subscribe(function(e, args) {
                var rows = args.rows;
				
                that.model.set({'selection':rows});
				that.model.trigger("change:selection");
				that.touch();
				
			});
		}

			
	});
	
	 var load_ipython_extension = require(['jquery','base/js/namespace','nbextensions/widgets/widgets/js/widget'], function($,Jupyter,widget){
    
	});
    return {
        MyWidgetView: MyWidgetView,
		load_ipython_extension:load_ipython_extension
    }
});
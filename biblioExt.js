define(['jquery','base/js/namespace','base/js/utils'], function($,Jupyter,utils){


	var load_ipython_extension = require(['base/js/namespace'], function(Jupyter){

		"use strict";
    
	var generateReferences=function(){
		console.log('okkkkk!');
		
		var listcells=IPython.notebook.get_cells();
		$.each(listcells,function(i,cell){
			console.log(cell);	
		//var cell=IPython.notebook.get_selected_cell();
			if (cell.cell_type == "markdown" ) {
					var text = cell.code_mirror.getValue();
					var labels=[];
					var text2=text.replace(/\\cite\[(.*?)\]/, function(match,p1){
						labels.push(p1);
						var text3="<div id="+p1+">tmp</div>"	;
						console.log(text3);
						return text3;
					});
					cell.set_rendered(text2);
					var uniqueLabels=[];
					$.each(labels, function(i, el){
						if($.inArray(el, uniqueLabels) === -1) uniqueLabels.push(el);
					});
					var liste=JSON.stringify(uniqueLabels);
					$.ajax({
						 type: "POST",
						 url: "/sendBiblio",
						 data: {list: liste },
						 success: function(ret){
							var result = JSON.parse(ret);
							var url=result[0].howpublished;
							var id=result[0].ID;
							$('#'+id).replaceWith('<a href="'+url+'" target="_blank">['+id+']</a>');
						 }
					});
			}
		});
		
	}

	Jupyter.toolbar.add_buttons_group([
 
				{
			id: 'doBiblio',
			label   : 'Read bibliography and generate references section',
			icon    : 'fa-book',
			callback: generateReferences
				}
            ]);
	});
	
	
	
    return {load_ipython_extension: load_ipython_extension };
})
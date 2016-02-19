"use strict";
define(['jquery','base/js/namespace','base/js/utils'], function($,Jupyter,utils){

	var shareServer=function(selected){

		$.ajax({
			     type: "POST",
				 url: "/push",
				 data: 'file='+ selected ,
				 //dataType: "json",
				 success: function(ret){
					  alert("file shared.");
				 },
				 error: function(x,e){
					 alert("error occured");
				 } 
			});
		
	};

	var _share=function(){
		var body="";
		$('.list_item :checked').each(function(index, item) {
            var parent = $(item).parent().parent();
			body=parent.data('path');
		});
		
		var selected=body;
		body="Sharing the file <i>"+selected+"</i> with other users.";
		
		Jupyter.dialog.modal({
            title: "Share Files",
            body: body,
            buttons : {
                "OK": {click:function(){shareServer(selected);}},
				"Cancel":{}
            }
        });
		
	};

    function _on_load(){
        var input = document.createElement('input');
        input.setAttribute('type', 'button');
		input.setAttribute('value', 'Share File');
		input.setAttribute('class','share-button btn btn-default');
        $('#notebook_list_header').append(input);
		$('#notebook_list_header').on("click",".share-button",_share);
    };

    return {load_ipython_extension: _on_load };
})
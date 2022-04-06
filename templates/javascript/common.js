const saveMark = ()=>{
    let marks = $('.mark').map(function(){
        let overridedMark = $("#"+ this.id + "-locked").html();
        console.log(overridedMark);
        return {id: this.id.replace('mark-',''), mark: $(this).val(), overridedMark: overridedMark};
    }).get(); 

    data = {"type":"mark","data": marks};
    $.ajax({                    
        data: JSON.stringify(data),
        type: "POST",
        dataType: "json",
        contentType: "application/json;charset=utf-8",
        success: function(returnData){
            console.log("Mark saved in server!");
        },
        error: function(xhr, ajaxOptions, thrownError){
            console.error(xhr.status);
            console.error(thrownError);
            alert(thrownError);
        }
    });                
    return marks;
};


const loadMark = ()=>{               
    $.ajax({
        url: $(location).attr('href').replace('index.html',"mark.json"),                   
        type: "GET",
        dataType: "json",
        contentType: "application/json;charset=utf-8",
        success: function(returnData){
            console.log("loaded Mark");   
            returnData.forEach(element => {
                $("#mark-"+ element.id).val(element.mark);
                if(element.overridedMark)
                    $("#mark-"+ element.id + "-locked").html(element.overridedMark);
            });                        
        },
        error: function(xhr, ajaxOptions, thrownError){
            console.log("Cannot reload Mark");                             
        }
    });
};

const convertFormToJSON = form => {
  return $("#controlForm")
    .serializeArray()
    .reduce(function (json, { name, value }) {
      json[name] = value;
      return json;
    }, {});
}

const saveControlForm = () => {                
    data = {"type":"control", "data": convertFormToJSON()};
    $.ajax({                    
        data: JSON.stringify(data),
        type: "POST",
        dataType: "json",
        contentType: "application/json;charset=utf-8",
        success: function(returnData){
            console.log("Control Form saved in server!");
        },
        error: function(xhr, ajaxOptions, thrownError){
            console.error(xhr.status);
            console.error(thrownError);
            alert(thrownError);
        }
    }); 
};

const loadControlForm = () =>{
    $.ajax({
        url: $(location).attr('href').replace('index.html',"control.json"),                   
        type: "GET",
        dataType: "json",
        contentType: "application/json;charset=utf-8",
        success: function(returnData){
            console.log("loaded control form");   
            for (let i in returnData) {                            
                $('#'+i).val(returnData[i]);        
            }
            if(returnData.fullMark && returnData.granularity)
            {
                $('.mark')
                    .attr("max",returnData.fullMark)
                    .attr("step",returnData.granularity);
            }
        },
        error: function(xhr, ajaxOptions, thrownError){
            console.log("Cannot reload Mark");                             
        }
    });
};

$(document).ready(() => {     
    loadControlForm();     
    loadMark();
    saveMark();   
    
    $('a.toggle-vis').on( 'click', function (e) {
        e.preventDefault();
        // Get the column API object
        let column = table.column( $(this).attr('data-column') );
        // Toggle the visibility
        column.visible( ! column.visible() );
    } );


    $('#dialog').dialog({ 
        autoOpen: false, show: false,
        maxHeight: $(window).height() - 100, 
        minWidth: $(window).width() - 100 ,
        resizable: true
    })

    $('.answerImage').on('click',function(e){
        e.preventDefault();
        console.log($(this).data());
        let left = $(this).data('left');
        let top = $(this).data('top');
        let width = $(this).data('width');
        let height = $(this).data('height');

        $('#left').val(left);
        $('#top').val(top);
        $('#width').val(width);
        $('#height').val(height);

        $('#dialog').dialog('open');
        $('#largeImage').attr('src', $(this).attr('src'));              
    });

    $('.mark').on('keyup input', e => {
        let mark = e.target.value;
        $("#" + e.target.id + "-locked").html(mark);
        saveMark();
    });

    $('.lock').on('click', e => {
        $("#" + e.target.id).html("");
    });
    
    $('#controlForm').on('keyup change paste', 'input, select, textarea', function(){
        console.log('Form changed!');
        saveControlForm();
    });

} );
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


const loadMark = (callback)=>{               
    $.ajax({
        url: $(location).attr('href').replace('index.html',"mark.json"),                   
        type: "GET",
        dataType: "json",
        contentType: "application/json;charset=utf-8",
        success: function(returnData){            
            returnData.forEach(element => {
                $("#mark-"+ element.id).val(element.mark);
                if(element.overridedMark)
                    $("#mark-"+ element.id + "-locked").html(element.overridedMark);
            });
            console.log("loaded Mark");   
            if(callback) callback();
        },
        error: function(xhr, ajaxOptions, thrownError){
            console.log("Cannot reload Mark"); 
            if(callback) callback();
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

const loadControlForm = (callback) =>{
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
            if(callback) callback();
        },
        error: function(xhr, ajaxOptions, thrownError){
            console.log("Cannot reload control form");
            if(callback) callback();
        }
    });
};

const zoomImage = (callback)=>{                
    const zoom = $('#zoom').val();
    
    const boundingBoxMode = $('input[name="boundingBoxMode"]:checked').val();
    const commonLeft = boundingBoxMode === 'manual'? $('#left').val() : boundingBoxMode === 'tractractTrimedMean'? textractTrimedMeanBoundingBoxes.left: undefined;
    const commonTop = boundingBoxMode === 'manual'? $('#top').val() : boundingBoxMode === 'tractractTrimedMean'? textractTrimedMeanBoundingBoxes.top: undefined;
    const commonWidth = boundingBoxMode === 'manual'? $('#width').val() : boundingBoxMode === 'tractractTrimedMean'? textractTrimedMeanBoundingBoxes.width: undefined;
    const commonHeight = boundingBoxMode === 'manual'? $('#height').val() : boundingBoxMode === 'tractractTrimedMean'? textractTrimedMeanBoundingBoxes.height: undefined;

    console.log("zoomImage", boundingBoxMode, commonLeft,commonTop,commonWidth,commonHeight);

    let left, top, width, height, imageWidth, imageHeight;

    for(let b of boundingBoxes){
        left = commonLeft || b.left * zoom;
        top = commonTop || b.top * zoom;
        width = commonWidth || b.width * zoom;
        height = commonHeight || b.height * zoom;
        $('#crop-'+ b.id)
            .css('object-fit','none')
            .css('width', width + "px")
            .css('height', height + "px")
            .css('object-position', "-"+ left + "px -"+ top +"px")
            .css('transform-origin', "left top")
            .css('transform', `scale(${zoom})`);
    }
    
    $('.changeBoundBox').prop('disabled', boundingBoxMode !== "manual");
    if(callback) callback();
};

$(document).ready(() => {     
    loadControlForm(()=>loadMark(()=>zoomImage(()=>saveMark())));  
    
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
    
    $('#controlForm').on('keyup change paste', 'input, select, textarea', e => {
        console.log('Form changed:' + e.target.id +","+ e.target.name);
        saveControlForm();
        
        if("boundingBoxMode" ===  e.target.name){           
            zoomImage();             
        }
    });
    
    $('#zoom').on('change', e => {
        $('#currentZoom').html(e.target.value);
        zoomImage();
    });

    $('.changeBoundBox').on('change', e =>{             
        zoomImage();                
    });      

} );
const boundingBoxes = [
{% for index, row in dataTable.iterrows() -%}     
{
    'id': {{row["RowNumber"]}},
    'left':{{row["left"]}},
    'top': {{row["top"]}},
    'width': {{row["width"]}},
    'height': {{row["height"]}}
},        
{% endfor %}
];
 
const textractTrimedMeanBoundingBoxes ={   
    'left':{{estimatedBoundingBox["left"]}},
    'top': {{estimatedBoundingBox["top"]}},
    'width': {{estimatedBoundingBox["width"]}},
    'height': {{estimatedBoundingBox["height"]}}
};
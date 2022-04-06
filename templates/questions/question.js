const boundingBoxes = [
{% for index, row in dataTable.iterrows() -%}     
{
    'id': {{row["RowNumber"]}},
    'left':{{row["BoundingBox"]["left"]}},
    'top': {{row["BoundingBox"]["top"]}},
    'width': {{row["BoundingBox"]["width"]}},
    'height': {{row["BoundingBox"]["height"]}}
},        
{% endfor %}
];
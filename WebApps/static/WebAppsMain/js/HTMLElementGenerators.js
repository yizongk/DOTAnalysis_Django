/*
* Given an array, this function will return a Select Element populated with that content of the array, or an customized version of it.
*/
function createSelectElement({
    id=null,            // Leave this null if you don't want to add an ID to the select element
    arr=[],             // The array of items that will go into the select list
    set_val_fct=null,   // Set this to a function if you want to customize the value that go into each option element.
                        // Each item in the @arr will be pass into this function as the only argument.
                        // The function must return the value to be set for the option element's value
    set_txt_fct=null,   // Set this to a function if you want to customize the test that go into each option element.
                        // Each item in the @arr will be pass into this function as the only argument.
                        // The function must return the value to be set for the option element's text
    class_names=null,   // Leave this null if you don't want to add class names to the select element. A single string containing one or more class names
}={} ) {
    // Creates dropdown with customizations
    select = document.createElement('select');

    arr.forEach( (each) => {
        var option = document.createElement('option');
        if (id != null) { select.id = id; }
        if (class_names != null) { select.class = class_names; }

        if (set_val_fct != null) {
            option.value = set_val_fct(each);
        } else {
            option.value = each
        }

        if (set_txt_fct != null) {
            option.text = set_txt_fct(each);
        } else {
            option.text = each;
        }

        select.appendChild(option);
    });

    return select
}
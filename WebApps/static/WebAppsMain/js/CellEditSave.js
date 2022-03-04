// Written by Yi Zong Kuang
// Works well with well structured html table, with: table, thead, tbody, tr, td
// And for the attribute for the td: class, data-id, data-table, data-column

/* Use Instruction
    1. For any cells (td) that you want to edit add the following class to your td tag, like so:
        <td class="editable" >Some data here</td>            // This is for inputting direct values
        <td class="editable-select" >Some data here</td>     // This is for selecting from a list

        // =========================Examples=========================================
        <td class="editable"        data-id="{{ entry.user_permission_id }}" data-table="Users" data-column="Login">{{ entry.user.login }}</td>
        <td class="editable-select" data-id="{{ entry.user_permission_id }}" data-table="Users" data-column="Login">{{ entry.user.login }}</td>

    2. Then add the following js code (It's a template, change it to make it work for your use case)

        // =========================Examples=========================================
        //// ==========================For cell edit mode===============================

        $(document).on("dblclick", ".editable", function () {
            enterCellEditMode($(this))
        });

        $(document).on("keyup", ".input-data", function (e) {
            var key = e.which;
            if (key === 13) { // 13 is the return key, aka 'ENTER' key
                sendCellToServer(this, link_to_your_api, "input", function(td_node, json_response) {            // provide link_to_your_api, like "/PerInd/user_permissions_panel_api_update_data". And optionally, provide a call back function to do some work after the api call is successful
                    console.log(`Hi, call back called sendCellToServer(): ${json_response.post_msg}`)
                });
            }
            if (key === 27) { // 27 is the ESC key
                cancelEditMode(this);
            }
        });

        //// ==========================For cell select mode===============================

        $(document).on("dblclick", ".editable-select", function () {
            values_array = some_array                                                                           // provide values_array here, such as values_array = ["Option A", "Option B", "Option C"], or converting a python json obj to array: logins_array = {{ user_logins_json|safe }}
            // Move current select element to the top of the array
            var current_value = $(this).text()
            values_array.sort(function(x, y) {
                return x == current_value ? -1 : y == current_value ? 1 : 0;
            });
            enterCellEditSelectMode($(this), values_array)
        });

        $(document).on("keyup", ".input-data-select", function (e) {
            var key = e.which;
            if (key === 27) { // 27 is the ESC key
                cancelSelectMode(this);
            }
        });

        $(document).on("change", ".input-data-select", function () {
            sendCellToServer(this, link_to_your_api, "select", function(td_node, json_response) {               // provide link_to_your_api, like "/PerInd/user_permissions_panel_api_update_data". And optionally, provide a call back function to do some work after the api call is successful
                console.log(`Hi, call back called sendCellToServer(): ${json_response.post_msg}`)
            });
        });
*/





$(document).ajaxStart(function () {
    $("body").addClass("loading");
})
.ajaxStop(function () {
    $("body").removeClass("loading");
});


function finishCellEditMode(td_node) {
    td_node.addClass("editable");
};


function finishCellSelectMode(td_node) {
    td_node.addClass("editable-select");
};


function enterCellEditMode(td_node) {
    var old_value = td_node.text();
    var input = "<input type='text' class='input-data' old_value='" + old_value + "' value='" + old_value + "' class='form-control'>";
    td_node.html(input);
    td_node.removeClass("editable");
};

/*
 * Set @selections to your default list of Select values, expects an array of values
 * Set @use_custom_display to true if you want to pass in a @custom_display_fct
 * @custom_display_fct will take in a @param json obj which will contain @selections as the first element "selections", and @custom_data_json as the second element "custom_data_json"
 * @custom_display_fct must return a string of
 * `
 * <options>...</option>
 * ...
 * <options>...</option>
 * `
 *
 * @custom_data_json is an JSON Object that is passed to @custom_display_fct to do what every that fct wants
 * Set @old_value to something if you want the select list to retain the old value in the html
 */
function getSelectModeHtml(selections=[], old_value=null, use_custom_display=false, custom_data_json={}, custom_display_fct=null) {
    if (use_custom_display == true && !custom_data_json) {
        console.log(`Error: getSelectModeHtml(): paremeter use_custom_display is set to true, but paremeter custom_data_json is null: ${custom_data_json}`)
        return
    }

    if (use_custom_display == true) {
        var options = custom_display_fct({"selections": selections, "custom_data_json": custom_data_json});
    } else {
        var options = selections.map(function (each_select) {
            return `<option value='${each_select}'>${each_select}</option>`
        }).join('')
    }

    if (old_value == null) {
        return `
            <select class='input-data-select'>
                ${options}
            </select>
        `
    } else {
        return `
            <select class='input-data-select' old_value='${old_value}'>
                ${options}
            </select>
        `
    }
}

// param selections is a array of strings that will populate the selection list. If use_custom_display is true, custom_data_json must be a json with the param selections as index and it element will be used to attach on to the option in the select list
function enterCellEditSelectMode(td_node=null, selections=[], use_custom_display=false, custom_data_json={}, custom_display_fct=null) {
    var old_value = td_node.text();

    // Sort the selections arrary so that the current old value is at the top of the list
    selections.sort(function(x, y) {
        return x == old_value ? -1 : y == old_value ? 1 : 0;
    });

    var select_html = getSelectModeHtml(
        selections          = selections,
        old_value           = old_value,
        use_custom_display  = use_custom_display,
        custom_data_json    = custom_data_json,
        custom_display_fct  = custom_display_fct
    );

    td_node.html(select_html);
    td_node.removeClass("editable-select");
};


function cancelEditMode(node) {
    var old_val = $(node).attr("value")
    var td_node = $(node).parent("td");
    td_node.html(old_val);
    finishCellEditMode(td_node);
};


function cancelSelectMode(node) {
    var old_val = $(node).attr("old_value")
    var td_node = $(node).parent("td");
    td_node.html(old_val);
    finishCellSelectMode(td_node);
}


function finishEditMode(td_node, cell_html_type) {
    if (cell_html_type == "input") {
        finishCellEditMode(td_node);
    } else if (cell_html_type == "select") {
        finishCellSelectMode(td_node)
    } else {
        console.log(`Warning: Unknown finish cell mode: ${cell_html_type}`)
    }
}


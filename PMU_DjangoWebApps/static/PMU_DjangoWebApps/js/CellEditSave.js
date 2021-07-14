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


function setDatabaseStatus(good, msg) {
    // Set status light and error message to red and response error msg
    if (good == true) {
        $('.status_info.led_light').html("Database Status: <div class='led_green'></div>");
        $('.status_info.err_msg').html("");
    } else {
        $('.status_info.led_light').html("Database Status: <div class='led_red'></div>");
        $('.status_info.err_msg').html("Error: " + msg);
    }
};


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


// param selections is a array of strings that will populate the selection list. If has_selection_additional_info is true, selection_additional_info_json must be a json with the param selections as index and it element will be used to attach on to the option in the select list
// param how_display_additional_info specify the order of data in the option display
function enterCellEditSelectMode(td_node, selections, has_selection_additional_info, selection_additional_info_json, how_display_additional_info) {
    var old_value = td_node.text();
    // var input = "<input type='text' class='input-data' value='" + old_value + "' class='form-control'>";
    if (has_selection_additional_info == true && !selection_additional_info_json) {
        console.log(`Error: enterCellEditSelectMode(): paremeter has_selection_additional_info is set to true, but paremeter selection_additional_info_json is null: ${selection_additional_info_json}`)
        return
    }

    if (has_selection_additional_info == true) {
        if (how_display_additional_info == "display additional first") {
            var options = selections.map(function (each_select) {
                return `<option value='${each_select}'>${selection_additional_info_json[each_select]} | ${each_select}</option>`
            }).join('')
        } else {
            var options = selections.map(function (each_select) {
                return `<option value='${each_select}'>${each_select} | ${selection_additional_info_json[each_select]}</option>`
            }).join('')
        }
    } else {
        var options = selections.map(function (each_select) {
            return `<option value='${each_select}'>${each_select}</option>`
        }).join('')
    }


    var input = `
        <select class='input-data-select' old_value='${old_value}'>
            ${options}
        </select>
    `
    td_node.html(input);
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


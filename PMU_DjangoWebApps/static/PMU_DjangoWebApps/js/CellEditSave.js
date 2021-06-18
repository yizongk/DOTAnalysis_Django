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

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
};

// Sends a json blob to the api end point. Assumes the api end will know how to handle the json blob
// Expects a json obj in response, and must have the following variable "post_success" and "post_msg", ex. json_response["post_success"] and json_response["post_msg"]
// successCallbackFct and failCallbackFct's optional first param, must be the json_response obj. The success/fail fct can be used to do any work after the respective successful/fail api call, such as displaying a message etc
    // success/fail not as in server connectivity, but success as in connectivity is success, and successfuly processed the data. And failure as in connectivity is sucess but something prevented the server from processing the data in its functions.
    // For its optional 2nd param, it must be props, which contains some props in json form from the parent calling function
// ajaxFailCallbackFct is called when ajax fails because of connection issues, etc. The optional first param must be jqXHR. You can access jqXHR.status and jqXHR.responseText.
    // For its optional 2nd param, it must be props, which contains some props in json form from the parent calling function
// ajaxFailCallbackFct stores calling parent data that can be pass to the various callback function
// Returns a promise containing the POST call response data if call was successful.
async function sentJsonBlobToApi( json_blob, api_url, http_request_method="POST", successCallbackFct=function() { return; }, failCallbackFct=function() { return; }, ajaxFailCallbackFct=function() { return; }, props={} ) {
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", Cookies.get('csrftoken'));
            }
        }
    });

    return await $.ajax({
        url: api_url,
        type: http_request_method,
        data: JSON.stringify(json_blob),
        contentType: "application/json",
    })
    .done(function (json_response) {
        if (json_response["post_success"] == false) {
            console.log(`Error: Ajax calling '${api_url}'\nServer Response: ${json_response["post_msg"]}`);
            alert(`Something went wrong while trying to send form data to server.\nPlease contact ykuang@dot.nyc.gov if this error continues:\n\nAjax calling api endpoint: '${api_url}'\nServer Response:\n\n${json_response["post_msg"]}`);

            failCallbackFct(json_response, props)
            // Set status light and error message to red and response error msg
            setDatabaseStatus(good=false, msg=json_response["post_msg"]);
        } else { // Api call successful
            successCallbackFct(json_response, props);
            setDatabaseStatus(good=true, msg="");
        }

        return json_response['post_data'];
    })
    .fail(function (jqXHR) {
        var errorMessage = `Server might be down, try to reload the web page to confirm. If error is still happening, contact ykuang@dot.nyc.gov\n xhr response: ${jqXHR.status}\n xhr response text: ${jqXHR.responseText}`;
        ajaxFailCallbackFct(jqXHR, props)
        setDatabaseStatus(good=false, msg=errorMessage);

        console.log(`Ajax Post: Error Occured: ${errorMessage}`);
        alert(`Ajax Post: Error Occured:\n\n${errorMessage}`);
        return false;
    });
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

// THIS IS THE ENTRY POINT
// For its first param, the td_node, and then for its second param, the api_url, and for the third, the cell_html_type. The cell_html_type must either by 'select' or 'input'
// Return a promise returned by sentJsonBlobToApi(), which should contain the POST response data if the api call was successful, and also returns the calling td_node, not the node it self, since the node it self is the select list and it's temporary, and it's a child of the td_node, and the td_node is the cell of the table
// sql: INSERT
async function sendCellToServer( node, api_url, http_request_method="POST", cell_html_type ) {
    // console.log(id, new_value, table, column, td_node, old_val);
    var old_val = $(node).attr("old_value")
    var new_value = $(node).val().trim();
    var td_node = $(node).parent("td");
    $(node).remove();

    id = td_node.data("id")
    table = td_node.data("table")
    column = td_node.data("column")

    json_obj_to_server = {
        "id": id,
        "new_value": new_value,
        "table": table,
        "column": column
    }

    props = {
        'td_node': td_node,
        'old_val': old_val,
        'new_value': new_value,
        'cell_html_type': cell_html_type,
    }

    api_json_response = await sentJsonBlobToApi( json_blob=json_obj_to_server, api_url=api_url, http_request_method=http_request_method,
        successCallbackFct=function(json_response, props) {
            // successful api call call-back fct
            td_node = props['td_node']
            new_value = props['new_value']
            cell_html_type = props['cell_html_type']

            td_node.html(new_value);
            finishEditMode(td_node, cell_html_type)
        }, failCallbackFct=function(json_response, props) {
            // bad api call call-back fct
            td_node = props['td_node']
            old_val = props['old_val']
            cell_html_type = props['cell_html_type']

            td_node.html(old_val);
            finishEditMode(td_node, cell_html_type)
        }, ajaxFailCallbackFct=function(jqXHR, props) {
            // bad ajax call
            td_node = props['td_node']
            old_val = props['old_val']
            cell_html_type = props['cell_html_type']

            td_node.html(old_val);
            finishEditMode(td_node, cell_html_type)
        },
        props
    );
    result = {
        'td_node': td_node,
        'api_json_response': api_json_response
    }

    return result

};

// sql: UPDATE
async function sendModalFormDataToServer( json_blob, api_url, http_request_method="PUT", successCallbackFct=function() { return; }, failCallbackFct=function() { return; }, ajaxFailCallbackFct=function() { return; }, props={} ) {
    await sentJsonBlobToApi(json_blob=json_blob, api_url=api_url, http_request_method=http_request_method, successCallbackFct=successCallbackFct, failCallbackFct=failCallbackFct, ajaxFailCallbackFct=ajaxFailCallbackFct, props);
};

// sql: DELETE
async function deleteRecordToServer( json_blob, api_url, http_request_method="DELETE", successCallbackFct=function() { return; }, failCallbackFct=function() { return; }, ajaxFailCallbackFct=function() { return; }, props={} ) {
    await sentJsonBlobToApi(json_blob=json_blob, api_url=api_url, http_request_method=http_request_method, successCallbackFct=successCallbackFct, failCallbackFct=failCallbackFct, ajaxFailCallbackFct=ajaxFailCallbackFct, props);
}
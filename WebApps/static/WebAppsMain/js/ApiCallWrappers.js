function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
};


function setErrorStatus(set_error=true, error_msg='') {
    // Set status light and error message to red and response error msg
    if (set_error == true) {
        $('.status_info.led_light').html("Database Status: <div class='led_red'></div>");
        $('.status_info.err_msg').html("Error: " + error_msg);
    } else {
        $('.status_info.led_light').html("Database Status: <div class='led_green'></div>");
        $('.status_info.err_msg').html("");
    }
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
// Note: Cookies.get() comes from https://github.com/js-cookie/js-cookie/, so be sure to include this script in your html doc \<head\> tag like
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
            setErrorStatus(set_error=true, error_msg=json_response["post_msg"]);
        } else { // Api call successful
            successCallbackFct(json_response, props);
            setErrorStatus(set_error=false, error_msg="");
        }

        return json_response['post_data'];
    })
    .fail(function (jqXHR) {
        var errorMessage = `Server might be down, try to reload the web page to confirm. If error is still happening, contact ykuang@dot.nyc.gov\n xhr response: ${jqXHR.status}\n xhr response text: ${jqXHR.responseText}`;
        ajaxFailCallbackFct(jqXHR, props)
        setErrorStatus(set_error=true, error_msg=errorMessage);

        console.log(`Ajax Post: Error Occured: ${errorMessage}`);
        alert(`Ajax Post: Error Occured:\n\n${errorMessage}`);
        return false;
    });
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
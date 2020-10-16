// Written by Yi Zong Kuang
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

function enterCellEditMode(td_node) {
    var old_value = td_node.text();
    var input = "<input type='text' class='input-data' value='" + old_value + "' class='form-control'>";
    td_node.html(input);
    td_node.removeClass("editable");
};

function cancelEditMode(node) {
    var old_val = $(node).attr("value")
    var td_node = $(node).parent("td");
    td_node.html(old_val);
    finishCellEditMode(td_node);
};

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
};

// THIS IS THE ENTRY POINT
// callbackFct must take in for its first param, the td_node, and then for its second param, the json_response obj. callbackFct can be used to do any work after a successful api call, such as updating some element on the html beside the new cell value (The new cell value is updated to the edited cell during the sendCellToServer() function).
function sendCellToServer( node, api_url, callbackFct=function() { return; } ) {
    // console.log(id, new_value, table, column, td_node, old_val);
    var old_val = $(node).attr("value")
    var new_value = $(node).val();
    var td_node = $(node).parent("td");
    $(node).remove();

    id = td_node.data("id")
    table = td_node.data("table")
    column = td_node.data("column")

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", Cookies.get('csrftoken'));
            }
        }
    });

    $.ajax({
        url: api_url,
        type: "POST",
        data: {
            id: id,
            new_value: new_value,
            table: table,
            column: column,
        },
    })
    .done(function (json_response) {
        // console.log("JSON RESPONSE", json_response);
        if (json_response["post_success"] == false) {
            td_node.html(old_val);
            console.log(`Error: Ajax calling SavePerIndDataApi: Server Response: ${json_response["post_msg"]}`);
            alert(`Something went wrong while trying to update Indicator Value.\nPlease contact ykuang@dot.nyc.gov if this error continues:\n\nAjax calling SavePerIndDataApi: Server Response: ${json_response["post_msg"]}`);

            // Set status light and error message to red and response error msg
            setDatabaseStatus(good = false, msg = json_response["post_msg"]);
        } else { // Api call successful
            td_node.html(new_value);
            callbackFct(td_node, json_response);
            setDatabaseStatus(good = true, msg = "");
        }
        finishCellEditMode(td_node);

        return true;
    })
    .fail(function (jqXHR) {
        td_node.html(old_val);
        var errorMessage = `Server might be down, try to reload the web page to confirm. Otherwise, try again and if error is still happening, contact ykuang@dot.nyc.gov\n xhr response: ${jqXHR.status}\n xhr response text: ${jqXHR.responseText}`;
        setDatabaseStatus(good = false, msg = errorMessage);
        finishCellEditMode(td_node);

        console.log(`Ajax Post: Error Occured: ${errorMessage}`);
        alert(`Ajax Post: Error Occured:\n\n${errorMessage}`);
        return false;
    });
};
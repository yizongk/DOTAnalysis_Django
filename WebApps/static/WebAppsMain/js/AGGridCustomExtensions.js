class BaseAGGridCellValueSetter {
    /**
     * A bas class to be reused for any AG Grid Cell value setting
     *
     * Contains multiple member functions that implements various type of feature
     * For example, setting a cell value and then calling an API call to save the value to database.
     * Etc.
     *
     * Usages:
     * function cellValueSetter(ag_node) {
     *     post_params = {
     *         api_json_blob   : {
     *             'to_pms'        : ag_node.data.pms,
     *             'column_name'   : ag_node.colDef.headerName,
     *             'new_value'     : ag_node.newValue,
     *         },
     *         ag_node              : ag_node,
     *         post_url             : "update_employee_data",
     *         on_success_callback  : function(json_response, props) {...}, // Optional
     *         on_fail_callback     : function(json_response, props) {...}, // Optional
     *     }
     *
     *     return BaseAGGridCellValueSetter.setAndPOST(post_params);
     * }
     * ...
     * ag_column['valueSetter'] = cellValueSetter;  // Sets a specific AG column's valueSetter to cellValueSetter()
     */

    static setAndPOST(params) { // Static so it can be called without instantiating the class
        /**
         * Expects params to have properties:
         *      - api_json_blob         : This will be the object that is POST to the API.
         *      - ag_node               : A reference to the AG node (Really the cell calls it) that called thsi function.
         *      - post_url              : The API URL that the request will POST to.
         *      - on_success_callback   : (Optional) Expects two arguments json_response and props. Functions to be called on successful POST request
         *      - on_fail_callback      : (Optional) Expects two arguments json_response and props. Functions to be called on failed POST request
         */

        let props = {
            'ag_node': params.ag_node,
        }

        let success_callback = null;
        if (params.on_success_callback == null) {
            // default callbacks
            success_callback = function(json_response, props) {
                let ag_node = props.ag_node;
                ag_node.data[ag_node.colDef.field] = ag_node.newValue;
                ag_node.api.refreshCells({
                    rowNodes: [ag_node.node],   // List of row nodes to restrict operation to
                    columns: [ag_node.column],  // List of columns to restrict operation to
                });
            }
        } else {
            success_callback = params.on_success_callback;
        }

        let fail_callback = null;
        if (params.on_success_callback == null) {
            // default callbacks
            fail_callback = function(json_response, props) {
                console.log(`API ${params.post_url}(): bad api call`)
            };
        } else {
            fail_callback = params.on_fail_callback;
        }

        let response = sentJsonBlobToApi({
            json_blob           : params.api_json_blob,
            api_url             : params.post_url,
            http_request_method : "POST",
            successCallbackFct  : success_callback,
            failCallbackFct     : fail_callback,
            ajaxFailCallbackFct : function(jqXHR, props) {
                console.log(`API ${params.post_url}(): fail ajax call`)
            },
            props               : props
        })

        // Always return false, so AG Grid don't immediately update the cell. Let the sentJsonBlobToApi() successCallbackFct handle the update of the cell.
        return false;
    }
}

class BaseAGGridCellRenderer {
    /**
     * A base class to be reused for any AG Grid Cell rendering
     *
     * Usage:
     * Class someClassName extends BaseAGGridCellRenderer {
     *     init(ag_cell) {
     *         let some_text = ...
     *         let super_params = {
     *             rendered_text : some_text
     *         }
     *         this.initBase(super_params);
     *     }
     * }
     */
    initBase(params) {
        /**
         * Expects params to have properties:
         *      - rendered_text: Will be use to be display on the AG Grid Cell
         */
        this.eGui = document.createElement('div');
        this.eGui.innerHTML = params.rendered_text;
    }

    getGui() {
        return this.eGui;
    }
}

class BaseAGGridCellSelectEditor {
    /**
     * A base class to be reused for any AG Grid Cell select editing
     *
     * Usage:
     * class SupervisorCellEditor extends BaseAGGridCellSelectEditor {
     *     init(ag_cell) {
     *         let super_params = {
     *             ag_cell                         : ag_cell,
     *             select_array                    : [...],
     *             select_array_sort_fct           : function(x, y) {
     *                                                 return x < y ? -1 : x > y ? 1 : 0;
     *                                             },
     *             ag_cell_val_bubble_up_sort_fct  : function(x, y) {
     *                                                 return x == ag_cell.value ? -1 : y == ag_cell.value ? 1 : 0;
     *                                             },
     *             select_element_id               : 'some_id_for_your_select_element',
     *             option_element_set_val_fct      : (each) => { return each.some_property; },
     *             option_element_set_txt_fct      : (each) => { return `${each.some_property} - ${each.some_property2}`; },
     *         }
     *         this.initBase(super_params)
     *     }
     * }
     */
    initBase(params) {
        /**
         * Expects params to have properties:
         *      - ag_cell                           : A reference to the AG Cell that called thsi class
         *      - select_array                      : The array of items for the Select list
         *      - select_array_sort_fct             : (Optional) A function that will be used to sort the Select list.
         *                                              If none is provided, it will use JS native sort()
         *      - ag_cell_val_bubble_up_sort_fct    : (Optional) After Select list is sorted by select_array_sort_fct,
         *                                              this function will be used to bring the current selected value up to the top of the Select list.
         *                                              If none is provided, it will use JS native sort()
         *      - select_element_id                 : (Optional)) Will be assigned as the Select list's ID in the DOM
         *      - option_element_set_val_fct        : (Optional)) Will be called to set the value for each of the options in the Select list.
         *                                              Takes in select_array as an argument.
         *                                              If none is provided, each item in select_array will be set as the value
         *      - option_element_set_txt_fct        : (Optional)) Will be called to set the text for each of the options in the Select list.
         *                                              Takes in select_array as an argument.
         *                                              If none is provided, each item in select_array will be set as the text
         */
        this.ag_cell                            = params.ag_cell;
        this.select_array                       = params.select_array;
        this.select_array_sort_fct              = params.select_array_sort_fct;
        this.ag_cell_val_bubble_up_sort_fct     = params.ag_cell_val_bubble_up_sort_fct;
        this.select_element_id                  = params.select_element_id;
        this.option_element_set_val_fct         = params.option_element_set_val_fct;
        this.option_element_set_txt_fct         = params.option_element_set_txt_fct;

        // Reset select list's sort. Uses default sort if @select_array_sort_fct is not provided
        if (this.select_array_sort_fct == null) {
            this.select_array.sort();
        } else {
            this.select_array.sort(this.select_array_sort_fct);
        }

        // Bring current selection to top of the select list
        if (this.ag_cell_val_bubble_up_sort_fct == null) {
            this.select_array.sort(
                function(x, y) {
                    if ( this.select_array.filter(x => x == this.ag_cell.value) > 0 ) {
                        // ag_cell.value exists in the select_array, bubble the option up to the top of the select list.
                        return x == this.ag_cell.value ? -1 : y == this.ag_cell.value ? 1 : 0;
                    } else {
                        // If ag_cell.value is not in the select_array, bubble up the null option to the top of the select list.
                        // This is needed so the select list won't bug out, and not trigger the change function of AG Grid.
                        return x == null ? -1 : y == null ? 1 : 0;
                    }
                }
            )
        } else {
            this.select_array.sort(this.ag_cell_val_bubble_up_sort_fct)
        }

        this.select_element = createSelectDropdown({ // From HTMLElementGenerator.js
            id          : this.select_element_id,
            arr         : this.select_array,
            set_val_fct : this.option_element_set_val_fct,
            set_txt_fct : this.option_element_set_txt_fct,
        })

        this.select_element.addEventListener('input', (event) => {
            // Javascript null = html empty string '', and since event.target.value is an HTML value, '' will be considered as null
            this.ag_cell.value = (event.target.value == '') ? '' : event.target.value;
            this.ag_cell.stopEditing();
        });

    }

    /* Component Editor Lifecycle methods */
    // gets called once before editing starts, to give editor a chance to cancel the editing before it even starts
    isCancelBeforeStart() { return false; }

    // gets called once when grid ready to insert the element
    getGui() { return this.select_element; }

    // after this component has been created and inserted into the grid
    afterGuiAttached() { this.select_element.focus(); }

    // gets called once when editing is finished (eg if Enter is pressed)
    // if you return true, then the result of the edit will be ignored
    isCancelAfterEnd() { return false; }

    // the final value to sent to the grid, on completion of editing
    getValue() { return this.ag_cell.value; }
}
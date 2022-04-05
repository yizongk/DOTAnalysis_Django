function initialize_fomantic_dropdown({parent_id=null, select_id=null, arr=null}={}) {
    /**
    * Initializes a Fomantic UI Dropdown on the given HTML element ID
    *
    * @param {string} id The HTML element ID that will be used to initialize the Fomantic UI Dropdown on.
    * @param {array} arr The array of options that will be in the initialized Fomantic UI Dropdown.
    *   Expected to be in this format:
    *   [
    *       {
    *           value: ...      value that is returned when the item is selected on the dropdown list
    *           ,text: ...      text representing the item that is shown on the dropdown list
    *           ,name: ...      name of the item
    *           ,selected: ...  true/false, only one item should be true. The true item will be selected by default after dropdown is initialized
    *       }
    *       ,{
    *           ...
    *       }
    *       ...
    *   ]
    */
    try {
        if (parent_id === null || select_id === null || arr === null) {
            throw 'parent_id, select_id and arr cannot be null';
        }

        let dropdown_html = createSelectElement({
            id: select_id,
            arr: arr,
            set_val_fct: x => {return x.value},
            set_txt_fct: x => {return x.text},
            class_name: "ui selection dropdown",
        });

        //$(`#${select_id}`).dropdown('destroy')
        //$(`#${select_id}`).remove()
        // Seems to remove existing fomantic dropdown if there is any
        $(`#${parent_id}`).html(dropdown_html);
        $(`#${select_id}`).dropdown();
    } catch(e) {
        throw `initialize_fomantic_dropdown(): ${e}`;
    }
}
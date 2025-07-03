// customer_item_custody.js (Client-side script)
frappe.ui.form.on('Customer Item Custody', {
    refresh: function(frm) {
        frm.trigger('bind_events');
        frm.trigger('setup_table_restrictions');
        
        // Make sure all fields are visible and rendered correctly
        frm.refresh_fields();
        
        // Set focus to scan field
        if(frm.fields_dict.scan_barcode) {
            $(frm.fields_dict.scan_barcode.input).focus();
        }
    },
    
    setup_table_restrictions: function(frm) {
        // Disable add/remove buttons for items table
        frm.get_field('items').grid.cannot_add_rows = true;
        
        // Hide the add row button
        frm.fields_dict.items.grid.wrapper.find('.grid-add-row').hide();
        
        // Disable delete button for each row
        frm.fields_dict.items.grid.wrapper.find('.grid-row-check').hide();
        frm.fields_dict.items.grid.wrapper.find('.btn-open-row').hide();
        
        // Add CSS to hide delete icons and prevent manual editing
        frappe.dom.add_css(`
            .grid-delete-row { display: none !important; }
            .grid-duplicate-row { display: none !important; }
            .grid-move-row { display: none !important; }
            .grid-add-row { display: none !important; }
            .grid-remove-rows { display: none !important; }
        `);
        
        // Make table fields readonly except for status
        if(frm.fields_dict.items && frm.fields_dict.items.grid) {
            frm.fields_dict.items.grid.grid_rows.forEach(function(row) {
                if(row.doc) {
                    row.toggle_editable('serial_no', false);
                    row.toggle_editable('item_code', false);
                    row.toggle_editable('item_name', false);
                    row.toggle_editable('scanned_at', false);
                }
            });
        }
    },
    
    setup: function(frm) {
        // Make sure the form is fully set up
        frm.refresh_fields();
    },
    
    bind_events: function(frm) {
        console.log("Binding barcode scanning events for Customer Item Custody");
        
        // Set search_field to the scan_barcode field
        frm.search_field = frm.fields_dict.scan_barcode;
        
        // Make sure field is actually visible
        if(frm.fields_dict.scan_barcode) {
            $(frm.fields_dict.scan_barcode.input).focus();
        }
        
        if(!window.onScan) {
            console.log("Loading onScan.js library");
            
            // Load onScan.js dynamically (adjust path as needed for your setup)
            frappe.require('/assets/posnext/node_modules/onscan.js/onscan.min.js')
                .then(() => {
                    console.log("onScan.js loaded successfully");
                    setup_scanner(frm);
                })
                .catch(err => {
                    console.error("Failed to load onScan.js:", err);
                    // Fallback to manual entry if scanner library fails
                    setup_manual_entry(frm);
                });
        } else {
            console.log("onScan.js already loaded");
            setup_scanner(frm);
        }
        
        function setup_scanner(frm) {
            window.onScan.decodeKeyEvent = function (oEvent) {
                var iCode = this._getNormalizedKeyNum(oEvent);
                switch (true) {
                    case iCode >= 48 && iCode <= 90: // numbers and letters
                    case iCode >= 106 && iCode <= 111: // operations on numeric keypad (+, -, etc.)
                    case (iCode >= 160 && iCode <= 164) || iCode == 170: // ^ ! # $ *
                    case iCode >= 186 && iCode <= 194: // (; = , - . / `)
                    case iCode >= 219 && iCode <= 222: // ([ \ ] ')
                    case iCode == 32: // spacebar
                        if (oEvent.key !== undefined && oEvent.key !== '') {
                            return oEvent.key;
                        }
                        var sDecoded = String.fromCharCode(iCode);
                        switch (oEvent.shiftKey) {
                            case false: sDecoded = sDecoded.toLowerCase(); break;
                            case true: sDecoded = sDecoded.toUpperCase(); break;
                        }
                        return sDecoded;
                    case iCode >= 96 && iCode <= 105: // numbers on numeric keypad
                        return 0 + (iCode - 96);
                }
                return '';
            };

            window.onScan.attachTo(document, {
                onScan: (sScancode) => {
                    console.log("Barcode scanned:", sScancode);
                    if (frm.search_field && $(frm.search_field.wrapper).is(':visible')) {
                        frm.search_field.set_focus();
                        frm.search_field.set_value(sScancode);
                        frm.events.add_item_from_scan(frm, sScancode);
                    }
                }
            });
        }
        
        function setup_manual_entry(frm) {
            // Fallback for manual barcode entry
            frm.fields_dict.scan_barcode.$input.on('keypress', function(e) {
                if(e.which === 13) { // Enter key
                    var barcode = $(this).val();
                    if(barcode.trim()) {
                        frm.events.add_item_from_scan(frm, barcode.trim());
                    }
                }
            });
        }
    },
    
    add_item_from_scan: function(frm, serial_no) {
        if(!serial_no || serial_no.trim() === '') return;
        
        // Check if serial number already exists in the table
        const existing_rows = frm.doc.items || [];
        const existing_row = existing_rows.find(row => row.serial_no === serial_no);
        
        if(existing_row) {
            // Check current status of the item
            if(existing_row.status === 'In Custody') {
                // Item is currently in custody, ask if it's being returned
                frappe.confirm(
                    __(`Item ${serial_no} is currently in custody. Are you returning it to the customer?`),
                    () => {
                        // User confirmed return
                        frappe.model.set_value(existing_row.doctype, existing_row.name, 'status', 'Returned');
                        frappe.model.set_value(existing_row.doctype, existing_row.name, 'returned_at', frappe.datetime.now_datetime());
                        frm.refresh_field('items');
                        frm.set_value('scan_barcode', '');
                        
                        frappe.show_alert({
                            message: __(`Item ${serial_no} marked as returned to customer`),
                            indicator: 'green'
                        });
                        
                        frm.dirty();
                    },
                    () => {
                        // User cancelled
                        frm.set_value('scan_barcode', '');
                        frappe.show_alert({
                            message: __(`Operation cancelled for ${serial_no}`),
                            indicator: 'orange'
                        });
                    }
                );
            } else if(existing_row.status === 'Returned') {
                // Item was previously returned, ask if taking custody again
                frappe.confirm(
                    __(`Item ${serial_no} was previously returned. Are you taking custody again?`),
                    () => {
                        // User confirmed taking custody again
                        frappe.model.set_value(existing_row.doctype, existing_row.name, 'status', 'In Custody');
                        frappe.model.set_value(existing_row.doctype, existing_row.name, 'scanned_at', frappe.datetime.now_datetime());
                        frappe.model.set_value(existing_row.doctype, existing_row.name, 'returned_at', '');
                        frm.refresh_field('items');
                        frm.set_value('scan_barcode', '');
                        
                        frappe.show_alert({
                            message: __(`Item ${serial_no} back in custody`),
                            indicator: 'blue'
                        });
                        
                        frm.dirty();
                    },
                    () => {
                        // User cancelled
                        frm.set_value('scan_barcode', '');
                        frappe.show_alert({
                            message: __(`Operation cancelled for ${serial_no}`),
                            indicator: 'orange'
                        });
                    }
                );
            }
            return;
        }
        
        // Get item details from the serial number (adjust table name as needed)
        frappe.db.get_value('Tenacity Serial No', serial_no, ['item_code', 'item_name'])
            .then(r => {
                if(r.message && r.message.item_code) {
                    const {item_code, item_name} = r.message;
                    
                    // Add new item to custody
                    frm.add_child('items', {
                        serial_no: serial_no,
                        item_code: item_code,
                        item_name: item_name,
                        status: 'In Custody',
                        scanned_at: frappe.datetime.now_datetime()
                    });
                    
                    frm.refresh_field('items');
                    frm.set_value('scan_barcode', '');
                    
                    frappe.show_alert({
                        message: __(`Added item ${serial_no} to custody`),
                        indicator: 'green'
                    });
                    
                    frm.dirty();
                } else {
                    // If no item found in Tenacity Serial No, add it anyway with serial number only
                    frm.add_child('items', {
                        serial_no: serial_no,
                        item_code: '',
                        item_name: '',
                        status: 'In Custody',
                        scanned_at: frappe.datetime.now_datetime()
                    });
                    
                    frm.refresh_field('items');
                    frm.set_value('scan_barcode', '');
                    
                    frappe.show_alert({
                        message: __(`Added item ${serial_no} to custody (item details not found)`),
                        indicator: 'yellow'
                    });
                    
                    frm.dirty();
                }
            })
            .catch(err => {
                // On error, still add the item with just the serial number
                frm.add_child('items', {
                    serial_no: serial_no,
                    item_code: '',
                    item_name: '',
                    status: 'In Custody',
                    scanned_at: frappe.datetime.now_datetime()
                });
                
                frm.refresh_field('items');
                frm.set_value('scan_barcode', '');
                
                frappe.show_alert({
                    message: __(`Added item ${serial_no} to custody (could not fetch item details)`),
                    indicator: 'yellow'
                });
                
                frm.dirty();
                console.error('Error fetching serial number details:', err);
            });
    }
});

// Restrict manual editing of items table
frappe.ui.form.on('Customer Item Custody Item', {
    before_items_remove: function(frm, cdt, cdn) {
        frappe.throw(__('Manual removal of items is not allowed. Use barcode scanning to manage items.'));
    }
});
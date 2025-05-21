
// pos_serial_validation.js (Client-side script)
frappe.ui.form.on('POS Serial Validation', {
    refresh: function(frm) {
        frm.trigger('bind_events');
        
        // Make sure all fields are visible and rendered correctly
        frm.refresh_fields();
    },
    
    setup: function(frm) {
        // Make sure the form is fully set up
        frm.refresh_fields();
    },
    
    // When POS Opening Entry is selected, set the posting date
    pos_opening_entry: function(frm) {
        if(frm.doc.pos_opening_entry) {
            frappe.db.get_value('POS Opening Entry', frm.doc.pos_opening_entry, 'posting_date')
                .then(r => {
                    if(r.message && r.message.posting_date) {
                        frm.set_value('posting_date', r.message.posting_date);
                        frm.refresh_field('posting_date');
                    }
                });
        }
    },
    
    bind_events: function(frm) {
        console.log("Binding barcode scanning events");
        
        // Set search_field to the scan_barcode field
        frm.search_field = frm.fields_dict.scan_barcode;
        
        // Make sure field is actually visible
        if(frm.fields_dict.scan_barcode) {
            $(frm.fields_dict.scan_barcode.input).focus();
        }
        
        if(!window.onScan) {
            console.log("Loading onScan.js library");
            
            // Load onScan.js dynamically
            frappe.require('/assets/posnext/node_modules/onscan.js/onscan.min.js')
                .then(() => {
                    console.log("onScan.js loaded successfully");
                    setup_scanner(frm);
                })
                .catch(err => {
                    console.error("Failed to load onScan.js:", err);
                    frappe.msgprint(__("Failed to load barcode scanner library. Please check console for details."));
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
                        frm.events.add_serial_from_scan(frm, sScancode);
                    }
                }
            });
        }
    },
    
    add_serial_from_scan: function(frm, serial_no) {
        if(!serial_no || serial_no.trim() === '') return;
        
        // Check if serial number already exists in the table
        const existing_rows = frm.doc.serial_numbers || [];
        const exists = existing_rows.some(row => row.serial_no === serial_no);
        
        if(exists) {
            frappe.show_alert({
                message: __(`Serial Number ${serial_no} already added`),
                indicator: 'orange'
            });
            return;
        }
        
        // Get item details from the serial number
        frappe.db.get_value('Serial No', serial_no, ['item_code', 'item_name'])
            .then(r => {
                if(r.message) {
                    const {item_code, item_name} = r.message;
                    
                    if(item_code) {
                        frm.add_child('serial_numbers', {
                            serial_no: serial_no,
                            item_code: item_code,
                            item_name: item_name
                        });
                        
                        frm.refresh_field('serial_numbers');
                        frm.set_value('scan_barcode', '');
                        
                        frappe.show_alert({
                            message: __(`Added Serial Number: ${serial_no}`),
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __(`No item found for Serial Number: ${serial_no}`),
                            indicator: 'red'
                        });
                    }
                } else {
                    frappe.show_alert({
                        message: __(`Serial Number not found: ${serial_no}`),
                        indicator: 'red'
                    });
                }
            });
    }
});
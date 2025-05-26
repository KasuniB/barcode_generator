// pos_serial_validation.js (Client-side script)
frappe.ui.form.on('POS Serial Validation', {
    refresh: function(frm) {
        frm.trigger('bind_events');
        frm.trigger('setup_autosave');
        frm.trigger('setup_table_restrictions');
        
        // Make sure all fields are visible and rendered correctly
        frm.refresh_fields();
    },
    
    setup_table_restrictions: function(frm) {
        // Disable add/remove buttons for serial_numbers table
        frm.get_field('serial_numbers').grid.cannot_add_rows = true;
        
        // Hide the add row button
        frm.fields_dict.serial_numbers.grid.wrapper.find('.grid-add-row').hide();
        
        // Disable delete button for each row
        frm.fields_dict.serial_numbers.grid.wrapper.find('.grid-row-check').hide();
        frm.fields_dict.serial_numbers.grid.wrapper.find('.btn-open-row').hide();
        
        // Add CSS to hide delete icons and prevent manual editing
        frappe.dom.add_css(`
            .grid-delete-row { display: none !important; }
            .grid-duplicate-row { display: none !important; }
            .grid-move-row { display: none !important; }
            .grid-add-row { display: none !important; }
            .grid-remove-rows { display: none !important; }
        `);
        
        // Make table fields readonly except for scanning
        if(frm.fields_dict.serial_numbers && frm.fields_dict.serial_numbers.grid) {
            frm.fields_dict.serial_numbers.grid.grid_rows.forEach(function(row) {
                if(row.doc) {
                    row.toggle_editable('serial_no', false);
                    row.toggle_editable('item_code', false);
                    row.toggle_editable('item_name', false);
                    row.toggle_editable('qty', false);
                }
            });
        }
    },
    
    setup_autosave: function(frm) {
        // Clear any existing autosave timer
        if(frm.autosave_timer) {
            clearTimeout(frm.autosave_timer);
        }
        
        // Set autosave interval (10 seconds = 10000 milliseconds)
        frm.autosave_interval = 10000;
        
        // Function to perform autosave
        frm.perform_autosave = function() {
            // Only autosave if document is in draft state (docstatus = 0)
            if(frm.is_dirty() && !frm.is_new() && frm.doc.docstatus === 0) {
                console.log("Performing autosave...");
                frm.save().then(() => {
                    console.log("Autosave successful");
                    frappe.show_alert({
                        message: __('Document auto-saved'),
                        indicator: 'green'
                    });
                }).catch(err => {
                    console.error("Autosave failed:", err);
                    frappe.show_alert({
                        message: __('Autosave failed'),
                        indicator: 'red'
                    });
                });
            } else {
                console.log("No changes to autosave, document is new, or document is submitted");
            }
        };
        
        // Function to schedule autosave
        frm.schedule_autosave = function() {
            if(frm.autosave_timer) {
                clearTimeout(frm.autosave_timer);
            }
            
            console.log("Scheduling autosave in", frm.autosave_interval / 1000, "seconds");
            frm.autosave_timer = setTimeout(() => {
                frm.perform_autosave();
            }, frm.autosave_interval);
        };
        
        // Also set up periodic autosave that runs continuously
        frm.start_periodic_autosave = function() {
            if(frm.periodic_autosave_timer) {
                clearInterval(frm.periodic_autosave_timer);
            }
            
            frm.periodic_autosave_timer = setInterval(() => {
                if(frm.is_dirty() && !frm.is_new() && frm.doc.docstatus === 0) {
                    frm.perform_autosave();
                }
            }, frm.autosave_interval);
        };
        
        // Start periodic autosave
        frm.start_periodic_autosave();
    },
    
    setup_submit_button: function(frm) {
        // Add custom submit button for submittable documents
        if(frm.doc.docstatus === 0) { // Draft state
            frm.add_custom_button(__('Submit Document'), function() {
                frm.submit();
            }, __('Actions')).addClass('btn-primary');
        }
        
        if(frm.doc.docstatus === 1) { // Submitted state
            frm.add_custom_button(__('Cancel Document'), function() {
                frm.cancel();
            }, __('Actions')).addClass('btn-danger');
        }
        
        if(frm.doc.docstatus === 2) { // Cancelled state
            frm.add_custom_button(__('Amend Document'), function() {
                frm.amend_doc();
            }, __('Actions')).addClass('btn-warning');
        }
    },
    
    setup: function(frm) {
        // Make sure the form is fully set up
        frm.refresh_fields();
        frm.set_query('pos_opening_entry', () => {
            return {
                filters: {
                    status: 'Open'
                }
            };
        });
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
    
    // Handle submission workflow - update statuses after successful submit
    on_submit: function(frm) {
        // Update serial number statuses after successful submission
        frm.update_serial_statuses().then(() => {
            frappe.show_alert({
                message: __('Serial number statuses updated successfully'),
                indicator: 'green'
            });
        }).catch(err => {
            frappe.msgprint(__('Warning: Document submitted but failed to update serial number statuses: ') + err.message);
            console.error('Failed to update serial statuses:', err);
        });
    },
    
    // Function to update serial number statuses on submission
    update_serial_statuses: function(frm) {
    return new Promise((resolve, reject) => {
        const serial_updates = [];
        
        frm.doc.serial_numbers.forEach(row => {
            if(row.qty === 1) {
                // Change from Active to Consumed for sales
                serial_updates.push({
                    serial_no: row.serial_no,
                    status: 'Consumed'
                });
            } else if(row.qty === -1) {
                // Change from Consumed (or Delivered) to Active for returns
                serial_updates.push({
                    serial_no: row.serial_no,
                    status: 'Active'
                });
            }
        });
        
        if(serial_updates.length === 0) {
            resolve();
            return;
        }
        
        // Call server method to update serial statuses
        frappe.call({
            method: 'frappe.client.bulk_update',
            args: {
                docs: serial_updates.map(update => ({
                    doctype: 'Tenacity Serial No',
                    name: update.serial_no,
                    status: update.status
                }))
            },
            callback: function(r) {
                if(r.message) {
                    console.log('Serial number statuses updated successfully');
                    resolve();
                } else {
                    reject(new Error('Failed to update serial statuses'));
                }
            },
            error: function(err) {
                reject(err);
            }
        });
    });
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
        
        // Prevent scanning if document is submitted
        if(frm.doc.docstatus === 1) {
            frappe.show_alert({
                message: __('Cannot modify submitted document'),
                indicator: 'red'
            });
            frm.set_value('scan_barcode', '');
            return;
        }
        
        // Check if serial number already exists in the table
        const existing_rows = frm.doc.serial_numbers || [];
        const existing_row = existing_rows.find(row => row.serial_no === serial_no);
        
        if(existing_row) {
            // Check if the item is currently marked for return (qty = -1)
            if(existing_row.qty === -1) {
                // If qty is -1, change it to 1 (item sold after return)
                frappe.model.set_value(existing_row.doctype, existing_row.name, 'qty', 1);
                frm.refresh_field('serial_numbers');
                frm.set_value('scan_barcode', '');
                
                frappe.show_alert({
                    message: __(`Serial Number ${serial_no} changed from return to sale (qty: 1)`),
                    indicator: 'green'
                });
                
                // Trigger autosave and mark as dirty
                frm.schedule_autosave();
                frm.dirty();
                return;
            }
            
            // If qty is not -1, show dialog asking if user wants to return the item
            frappe.confirm(
                __(`Serial Number ${serial_no} already exists. Do you want to return this item?`),
                () => {
                    // User clicked "Yes" - Set quantity to -1 for return
                    frappe.model.set_value(existing_row.doctype, existing_row.name, 'qty', -1);
                    frm.refresh_field('serial_numbers');
                    frm.set_value('scan_barcode', '');
                    
                    frappe.show_alert({
                        message: __(`Serial Number ${serial_no} marked for return (qty: -1)`),
                        indicator: 'blue'
                    });
                    
                    // Trigger autosave after marking for return
                    frm.schedule_autosave();
                    frm.dirty();
                },
                () => {
                    // User clicked "No" - Continue with normal operations (do nothing)
                    frm.set_value('scan_barcode', '');
                    
                    frappe.show_alert({
                        message: __(`Operation cancelled for Serial Number ${serial_no}`),
                        indicator: 'orange'
                    });
                }
            );
            return;
        }
        
        // Get item details and status from the serial number
        frappe.db.get_value('Tenacity Serial No', serial_no, ['item_code', 'item_name', 'status'])
            .then(r => {
                if(r.message) {
                    const {item_code, item_name, status} = r.message;
                    
                    if(!item_code) {
                        frappe.show_alert({
                            message: __(`No item found for Serial Number: ${serial_no}`),
                            indicator: 'red'
                        });
                        frm.set_value('scan_barcode', '');
                        return;
                    }
                    
                    // Check serial number status
                    if(status === 'Delivered') {
                        // Item is delivered, ask if it's a return
                        frappe.confirm(
                            __(`Serial Number ${serial_no} is currently delivered. Is this a return?`),
                            () => {
                                // User confirmed it's a return
                                frm.add_child('serial_numbers', {
                                    serial_no: serial_no,
                                    item_code: item_code,
                                    item_name: item_name,
                                    qty: -1 // Return quantity
                                });
                                
                                frm.refresh_field('serial_numbers');
                                frm.set_value('scan_barcode', '');
                                
                                frappe.show_alert({
                                    message: __(`Added Serial Number ${serial_no} as return (qty: -1)`),
                                    indicator: 'blue'
                                });
                                
                                frm.schedule_autosave();
                                frm.dirty();
                            },
                            () => {
                                // User said it's not a return
                                frappe.show_alert({
                                    message: __(`Operation cancelled. Serial Number ${serial_no} is not available for sale (status: Delivered)`),
                                    indicator: 'orange'
                                });
                                frm.set_value('scan_barcode', '');
                            }
                        );
                    } else if(status === 'Active') {
                        // Item is active, proceed with normal sale
                        frm.add_child('serial_numbers', {
                            serial_no: serial_no,
                            item_code: item_code,
                            item_name: item_name,
                            qty: 1 // Default quantity for sale
                        });
                        
                        frm.refresh_field('serial_numbers');
                        frm.set_value('scan_barcode', '');
                        
                        frappe.show_alert({
                            message: __(`Added Serial Number: ${serial_no} for sale (qty: 1)`),
                            indicator: 'green'
                        });
                        
                        frm.schedule_autosave();
                        frm.dirty();
                    } else {
                        // Item has other status (Inactive, etc.)
                        frappe.show_alert({
                            message: __(`Serial Number ${serial_no} is not available for sale (status: ${status})`),
                            indicator: 'red'
                        });
                        frm.set_value('scan_barcode', '');
                    }
                } else {
                    frappe.show_alert({
                        message: __(`Serial Number not found: ${serial_no}`),
                        indicator: 'red'
                    });
                    frm.set_value('scan_barcode', '');
                }
            })
            .catch(err => {
                frappe.show_alert({
                    message: __(`Error retrieving Serial Number: ${serial_no}`),
                    indicator: 'red'
                });
                frm.set_value('scan_barcode', '');
                console.error('Error fetching serial number:', err);
            });
    }
});

// Restrict manual editing of serial_numbers table
frappe.ui.form.on('POS Serial Validation Item', {
    before_serial_numbers_remove: function(frm, cdt, cdn) {
        frappe.throw(__('Manual removal of items is not allowed. Use barcode scanning only.'));
    }
});

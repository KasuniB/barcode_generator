
frappe.ui.form.on('ItemDailyTracker', {
    refresh: function(frm) {
        // Add custom button to manually trigger population (optional)
        frm.add_custom_button(__('Fetch Data'), function() {
            if (frm.doc.pos_opening_entry) {
                frappe.call({
                    method: "your_app_name.your_module_name.doctype.item_daily_tracker.item_daily_tracker.populate_items",
                    args: {
                        docname: frm.doc.name || null,
                        pos_opening_entry: frm.doc.pos_opening_entry
                    },
                    freeze: true,
                    freeze_message: __("Fetching items..."),
                    callback: function(response) {
                        if (response.message && response.message.status === "success") {
                            frm.set_value('items', response.message.items);
                            frm.set_value('name', response.message.docname);
                            frm.refresh_field('items');
                            frm.refresh();
                        }
                    }
                });
            } else {
                frappe.msgprint(__("Please select a POS Opening Entry."));
            }
        });
        
        // Highlight differences in the items table
        frm.fields_dict['items'].grid.wrapper.find('.grid-row').each(function(i, item) {
            var row = frm.doc.items[i];
            if (row && row.difference !== 0) {
                $(item).css('background-color', '#fff9f9');
            }
        });
    },
    
    pos_opening_entry: function(frm) {
        // When POS Opening Entry changes, fetch company, date, and populate items
        if (frm.doc.pos_opening_entry) {
            // Save the form if it's new to get a docname
            if (!frm.doc.name) {
                frm.save('Draft', function() {
                    frappe.call({
                        method: 'frappe.client.get_value',
                        args: {
                            doctype: 'POS Opening Entry',
                            filters: {
                                name: frm.doc.pos_opening_entry
                            },
                            fieldname: ['company', 'period_start_date']
                        },
                        callback: function(response) {
                            var data = response.message;
                            if (data) {
                                frm.set_value('company', data.company);
                                frm.set_value('date', data.period_start_date);
                            }
                            // Trigger item population
                            frappe.call({
                                method: "your_app_name.your_module_name.doctype.item_daily_tracker.item_daily_tracker.populate_items",
                                args: {
                                    docname: frm.doc.name || null,
                                    pos_opening_entry: frm.doc.pos_opening_entry
                                },
                                freeze: true,
                                freeze_message: __("Fetching items..."),
                                callback: function(response) {
                                    if (response.message && response.message.status === "success") {
                                        frm.set_value('items', response.message.items);
                                        frm.set_value('name', response.message.docname);
                                        frm.refresh_field('items');
                                        frm.refresh();
                                    }
                                }
                            });
                        }
                    });
                });
            } else {
                frappe.call({
                    method: 'frappe.client.get_value',
                    args: {
                        doctype: 'POS Opening Entry',
                        filters: {
                            name: frm.doc.pos_opening_entry
                        },
                        fieldname: ['company', 'period_start_date']
                    },
                    callback: function(response) {
                        var data = response.message;
                        if (data) {
                            frm.set_value('company', data.company);
                            frm.set_value('date', data.period_start_date);
                        }
                        // Trigger item population
                        frappe.call({
                            method: "your_app_name.your_module_name.doctype.item_daily_tracker.item_daily_tracker.populate_items",
                            args: {
                                docname: frm.doc.name || null,
                                pos_opening_entry: frm.doc.pos_opening_entry
                            },
                            freeze: true,
                            freeze_message: __("Fetching items..."),
                            callback: function(response) {
                                if (response.message && response.message.status === "success") {
                                    frm.set_value('items', response.message.items);
                                    frm.set_value('name', response.message.docname);
                                    frm.refresh_field('items');
                                    frm.refresh();
                                }
                            }
                        });
                    }
                });
            }
        } else {
            // Clear fields and items if pos_opening_entry is unset
            frm.set_value('company', '');
            frm.set_value('date', '');
            frm.set_value('items', []);
            frm.refresh_field('items');
        }
    }
});

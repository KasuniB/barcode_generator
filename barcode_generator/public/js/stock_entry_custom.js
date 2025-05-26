frappe.ui.form.on('Purchase Receipt', {
    refresh: function(frm) {
        // Only add button if document is submitted
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Print Item Barcodes'), function() {
                frappe.show_alert({
                    message: __('Generating serial numbers and barcodes, please wait...'),
                    indicator: 'blue'
                });
                
                frappe.call({
                    method: 'your_app_name.barcode_generator.api.print_barcodes_for_stock_entry',
                    args: {
                        'stock_entry_name': frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            // Open the PDF link in a new tab
                            window.open(r.message, '_blank');
                            frappe.show_alert({
                                message: __('Serial numbers generated and barcode PDF is ready for download/print.'),
                                indicator: 'green'
                            });
                        } else {
                            frappe.show_alert({
                                message: __('Could not generate barcode PDF. Check error log.'),
                                indicator: 'red'
                            });
                        }
                    },
                    error: function(r) {
                        frappe.show_alert({
                            message: __('Error generating barcodes. Please check the error log.'),
                            indicator: 'red'
                        });
                        console.error('Barcode generation error:', r);
                    }
                });
            }, __('Actions'));

            // Optional: Add a button to just generate serial numbers without printing
            frm.add_custom_button(__('Generate Serial Numbers'), function() {
                frappe.show_alert({
                    message: __('Generating serial numbers, please wait...'),
                    indicator: 'blue'
                });
                
                frappe.call({
                    method: 'your_app_name.barcode_generator.api.generate_serials_for_purchase_receipt',
                    args: {
                        'purchase_receipt_name': frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message && r.message.length > 0) {
                            frappe.show_alert({
                                message: __(`Generated ${r.message.length} serial numbers successfully.`),
                                indicator: 'green'
                            });
                            
                            // Show a message with the generated serial numbers
                            frappe.msgprint({
                                title: __('Serial Numbers Generated'),
                                message: __('Generated Serial Numbers:') + '<br>' + r.message.join('<br>'),
                                indicator: 'green'
                            });
                        } else {
                            frappe.show_alert({
                                message: __('No serial numbers were generated. Check if items exist in the receipt.'),
                                indicator: 'orange'
                            });
                        }
                    },
                    error: function(r) {
                        frappe.show_alert({
                            message: __('Error generating serial numbers. Please check the error log.'),
                            indicator: 'red'
                        });
                        console.error('Serial generation error:', r);
                    }
                });
            }, __('Actions'));
        }
    }
});
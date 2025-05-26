frappe.ui.form.on('Stock Entry', {
    refresh: function(frm) {
        // Only add button if document is submitted
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Print Item Barcodes'), function() {
                frappe.show_alert({
                    message: __('Generating barcodes, please wait...'),
                    indicator: 'blue'
                });
                
                frappe.call({
                    method: 'barcode_generator.utils.api.print_barcodes_for_stock_entry',
                    args: {
                        'stock_entry_name': frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            // Open the PDF link in a new tab
                            window.open(r.message, '_blank');
                            frappe.show_alert({
                                message: __('Barcode PDF generated and ready for download/print.'),
                                indicator: 'green'
                            });
                        } else {
                            frappe.show_alert({
                                message: __('Could not generate barcode PDF. Check error log.'),
                                indicator: 'red'
                            });
                        }
                    }
                });
            }, __('Actions'));
        }
    }
});

frappe.ui.form.on('Serial No', {
    refresh: function(frm) {
        // Only add button if document is submitted
        frm.add_custom_button(__('Print Barcode'), function() {
            frappe.show_alert({
                message: __('Generating barcode, please wait...'),
                indicator: 'blue'
            });
            
            frappe.call({
                method: 'barcode_generator.utils.api.print_barcode_for_serial_no',
                args: {
                    'serial_no': frm.doc.name
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
});

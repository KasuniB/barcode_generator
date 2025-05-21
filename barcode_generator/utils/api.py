import frappe
from . import barcode_generator

@frappe.whitelist()
def generate_barcodes_for_stock_entry(stock_entry_name):
    """API endpoint to generate barcodes for stock entry"""
    if not frappe.has_permission("Stock Entry", "write"):
        frappe.throw("Insufficient permissions to generate barcodes")
        
    return barcode_generator.generate_barcodes_for_stock_entry(stock_entry_name)

@frappe.whitelist()
def print_barcodes_for_stock_entry(stock_entry_name):
    """API endpoint to print barcodes for stock entry"""
    if not frappe.has_permission("Stock Entry", "read"):
        frappe.throw("Insufficient permissions to print barcodes")
        
    return barcode_generator.print_barcodes_for_stock_entry(stock_entry_name)

@frappe.whitelist()
def print_barcode_for_serial_no(serial_no):
    """API endpoint to print barcode for a single serial number"""
    if not frappe.has_permission("Serial No", "read"):
        frappe.throw("Insufficient permissions to print barcode")
        
    return barcode_generator.print_barcode_for_serial_no(serial_no)

def stock_entry_after_submit(doc, method):
    """Hook for Stock Entry after submission"""
    # We don't want to auto-generate barcodes here, just let the user click the button
    pass

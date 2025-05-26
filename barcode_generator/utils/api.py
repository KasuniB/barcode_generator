import frappe
from . import tenacity_serial_generator

@frappe.whitelist()
def generate_barcodes_for_stock_entry(stock_entry_name):
    """API endpoint to generate barcodes for purchase receipt (keeping original function name)"""
    if not frappe.has_permission("Purchase Receipt", "write"):
        frappe.throw("Insufficient permissions to generate barcodes")
    
    # Generate serial numbers first, then barcodes
    result = tenacity_serial_generator.process_purchase_receipt(stock_entry_name)
    return result.get("barcodes", [])

@frappe.whitelist()
def print_barcodes_for_stock_entry(stock_entry_name):
    """API endpoint to print barcodes for purchase receipt (keeping original function name)"""
    if not frappe.has_permission("Purchase Receipt", "read"):
        frappe.throw("Insufficient permissions to print barcodes")
    
    # First ensure serial numbers and barcodes are generated
    tenacity_serial_generator.process_purchase_receipt(stock_entry_name)
    
    # Then generate the PDF
    return tenacity_serial_generator.print_barcodes_for_purchase_receipt(stock_entry_name)

@frappe.whitelist()
def print_barcode_for_serial_no(serial_no):
    """API endpoint to print barcode for a single Tenacity serial number"""
    if not frappe.has_permission("Tenacity Serial No", "read"):
        frappe.throw("Insufficient permissions to print barcode")
    
    return tenacity_serial_generator.print_barcode_for_tenacity_serial(serial_no)

# Additional API endpoints for direct access
@frappe.whitelist()
def generate_serials_for_purchase_receipt(purchase_receipt_name):
    """API endpoint to generate serial numbers for purchase receipt"""
    if not frappe.has_permission("Purchase Receipt", "write"):
        frappe.throw("Insufficient permissions to generate serial numbers")
    
    return tenacity_serial_generator.generate_serials_for_purchase_receipt(purchase_receipt_name)

@frappe.whitelist()
def process_purchase_receipt(purchase_receipt_name):
    """API endpoint to process entire purchase receipt (generate serials + barcodes)"""
    if not frappe.has_permission("Purchase Receipt", "write"):
        frappe.throw("Insufficient permissions to process purchase receipt")
    
    return tenacity_serial_generator.process_purchase_receipt(purchase_receipt_name)

# Additional API endpoints for status management
@frappe.whitelist()
def update_serial_status(serial_no, status):
    """API endpoint to update serial number status"""
    if not frappe.has_permission("Tenacity Serial No", "write"):
        frappe.throw("Insufficient permissions to update serial number status")
    
    return tenacity_serial_generator.update_serial_status(serial_no, status)

@frappe.whitelist()
def consume_serial_number(serial_no):
    """API endpoint to mark a serial number as consumed"""
    if not frappe.has_permission("Tenacity Serial No", "write"):
        frappe.throw("Insufficient permissions to consume serial number")
    
    return tenacity_serial_generator.consume_serial_number(serial_no)

@frappe.whitelist()
def activate_serial_number(serial_no):
    """API endpoint to mark a serial number as active"""
    if not frappe.has_permission("Tenacity Serial No", "write"):
        frappe.throw("Insufficient permissions to activate serial number")
    
    return tenacity_serial_generator.activate_serial_number(serial_no)

@frappe.whitelist()
def get_serials_by_status(status=None, item_code=None, purchase_receipt=None):
    """API endpoint to get serial numbers by status"""
    if not frappe.has_permission("Tenacity Serial No", "read"):
        frappe.throw("Insufficient permissions to read serial numbers")
    
    return tenacity_serial_generator.get_serials_by_status(status, item_code, purchase_receipt)

@frappe.whitelist()
def get_available_serials_for_item(item_code, limit=None):
    """API endpoint to get available serial numbers for an item"""
    if not frappe.has_permission("Tenacity Serial No", "read"):
        frappe.throw("Insufficient permissions to read serial numbers")
    
    if limit:
        limit = int(limit)
    
    return tenacity_serial_generator.get_available_serials_for_item(item_code, limit)

@frappe.whitelist()
def consume_serials_for_delivery(item_code, qty):
    """API endpoint to consume serial numbers for delivery"""
    if not frappe.has_permission("Tenacity Serial No", "write"):
        frappe.throw("Insufficient permissions to consume serial numbers")
    
    qty = int(qty)
    return tenacity_serial_generator.consume_serials_for_delivery(item_code, qty)

def purchase_receipt_after_submit(doc, method):
    """Hook for Purchase Receipt after submission"""
    # We don't want to auto-generate barcodes here, just let the user click the button
    pass

def stock_entry_after_submit(doc, method):
    """Hook for Stock Entry after submission (keeping for compatibility)"""
    # We don't want to auto-generate barcodes here, just let the user click the button
    pass
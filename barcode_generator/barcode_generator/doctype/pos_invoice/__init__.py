import frappe
from barcode_generator.doctype.pos_invoice import pos_invoice as custom_pos_invoice
import erpnext.accounts.report.general_ledger.general_ledger

# Replace the original execute function with your custom one
erpnext.accounts.doctype.pos_invoice.pos_invoice = custom_pos_invoice
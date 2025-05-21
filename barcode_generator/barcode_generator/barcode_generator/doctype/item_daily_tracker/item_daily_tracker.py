# Copyright (c) 2025, YourCompany and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ItemDailyTracker(Document):
    def validate(self):
        # Optional: Clear and repopulate items on save
        self.items = []
        if self.pos_opening_entry:
            self.fetch_reconciliation_data()

    def fetch_reconciliation_data(self):
        """
        Fetches data from POS Serial Validation and POS Closing Entry,
        compares counts for each item, and populates the items child table.
        """
        # Initialize dictionaries to store item counts
        serial_items = {}
        invoice_items = {}

        # Fetch items from POS Serial Validation
        serial_validations = frappe.get_all(
            "POS Serial Validation",
            filters={"pos_opening_entry": self.pos_opening_entry},
            fields=["name"]
        )
        frappe.log_error(f"Found {len(serial_validations)} POS Serial Validations for {self.pos_opening_entry}")

        for validation in serial_validations:
            serial_details = frappe.get_all(
                "Serial Numbers Table",
                filters={"parent": validation.name},
                fields=["item_code", "item_name", "serial_no"]
            )
            frappe.log_error(f"Found {len(serial_details)} serial details for validation {validation.name}")
            
            for detail in serial_details:
                item_code = detail.item_code
                if item_code not in serial_items:
                    serial_items[item_code] = {
                        "item_name": detail.item_name,
                        "serial_count": 0,
                        "serials": []
                    }
                
                if detail.serial_no not in serial_items[item_code]["serials"]:
                    serial_items[item_code]["serials"].append(detail.serial_no)
                    serial_items[item_code]["serial_count"] += 1
        
        # Fetch items from POS Closing Entry
        closing_entries = frappe.get_all(
            "POS Closing Entry",
            filters={"pos_opening_entry": self.pos_opening_entry},
            fields=["name"]
        )
        frappe.log_error(f"Found {len(closing_entries)} POS Closing Entries for {self.pos_opening_entry}")
        
        for closing in closing_entries:
            invoices = frappe.get_all(
                "POS Invoice Reference",
                filters={"parent": closing.name},
                fields=["pos_invoice"]
            )
            
            for inv in invoices:
                items = frappe.get_all(
                    "POS Invoice Item",
                    filters={"parent": inv.pos_invoice},
                    fields=["item_code", "item_name", "qty"]
                )
                
                for item in items:
                    item_code = item.item_code
                    if item_code not in invoice_items:
                        invoice_items[item_code] = {
                            "item_name": item.item_name,
                            "invoice_count": 0
                        }
                    
                    invoice_items[item_code]["invoice_count"] += item.qty
        
        # Clear existing items
        self.items = []
        
        # Combine data and populate the items child table
        all_item_codes = set(list(serial_items.keys()) + list(invoice_items.keys()))
        frappe.log_error(f"Total unique item codes: {len(all_item_codes)}")
        
        for item_code in all_item_codes:
            serial_count = serial_items.get(item_code, {}).get("serial_count", 0)
            invoice_count = invoice_items.get(item_code, {}).get("invoice_count", 0)
            item_name = serial_items.get(item_code, {}).get("item_name") or invoice_items.get(item_code, {}).get("item_name") or ""
            
            difference = serial_count - invoice_count
            
            self.append("items", {
                "item_code": item_code,
                "item_name": item_name,
                "serial_count": serial_count,
                "invoice_count": invoice_count,
                "difference": difference
            })
        
        if not all_item_codes:
            frappe.msgprint(__("No items found for the selected POS Opening Entry."))

@frappe.whitelist()
def populate_items(docname, pos_opening_entry):
    """
    Whitelisted method to populate the items child table based on pos_opening_entry.
    Works for both new and existing documents.
    """
    try:
        # Load or create the document
        if docname and frappe.db.exists("ItemDailyTracker", docname):
            doc = frappe.get_doc("ItemDailyTracker", docname)
        else:
            doc = frappe.new_doc("ItemDailyTracker")
            docname = doc.name  # Get the name of the new document

        doc.pos_opening_entry = pos_opening_entry
        doc.items = []  # Clear any existing items
        if pos_opening_entry:
            doc.fetch_reconciliation_data()
            doc.save()  # Save to persist the changes
            frappe.log_error(f"Populated {len(doc.items)} items for ItemDailyTracker {docname}")
        else:
            frappe.msgprint(__("No POS Opening Entry provided."))
        
        return {
            "status": "success",
            "docname": docname,
            "items": [item.as_dict() for item in doc.items]
        }
    except Exception as e:
        frappe.log_error(f"Error populating items for ItemDailyTracker {docname}: {str(e)}")
        frappe.msgprint(__("An error occurred while populating items: {0}").format(str(e)))
        return {"status": "error", "message": str(e)}


def handle_pos_closing_submit(doc, method):
    """
    Fired when a POS Closing Entry is submitted.
    Finds or creates the matching ItemDailyTracker for the same
    POS Opening Entry, populates its items, saves (and submits) it.
    """
    pos_opening = doc.pos_opening_entry
    if not pos_opening:
        frappe.log_error(f"No POS Opening Entry on Closing Entry {doc.name}", "Item Daily Tracker")
        return

    # Try to fetch an existing tracker
    tracker_name = frappe.db.get_value(
        "Item Daily Tracker",
        {"pos_opening_entry": pos_opening},
        "name"
    )

    if tracker_name:
        tracker = frappe.get_doc("Item Daily Tracker", tracker_name)
    else:
        tracker = frappe.new_doc("Item Daily Tracker")
        tracker.pos_opening_entry = pos_opening

    # Populate (this will clear and refill .items)
    tracker.fetch_reconciliation_data()

    # Save or update
    if tracker.docstatus == 0:
        tracker.save()
        # Optionally submit the tracker if you want it to be a submitted doc
        try:
            tracker.submit()
        except frappe.ValidationError:
            # If your tracker is meant to stay as a Draft, you can skip submission
            pass
    else:
        # Already submitted—just update and re-submit if needed
        tracker.save(ignore_permissions=True)
        # no need to re-submit if unchanged

    frappe.log_error(f"Auto‑populated Item Daily Tracker {tracker.name} on POS Closing Entry {doc.name}", "Item Daily Tracker")

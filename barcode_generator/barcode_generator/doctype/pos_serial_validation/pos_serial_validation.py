import frappe
from frappe import _
from frappe.model.document import Document

class POSSerialValidation(Document):
    def onload(self):
        """Set defaults and fetch values when the document is loaded"""
        # Ensure the client-side script is triggered
        if not self.is_new():
            return
            
    def validate(self):
        self.validate_pos_opening_entry()
        self.validate_unique_serial_numbers()
    
    def validate_pos_opening_entry(self):
        """Validate that the selected POS Opening Entry is pending"""
        if self.pos_opening_entry:
            pos_status = frappe.db.get_value("POS Opening Entry", self.pos_opening_entry, "status")
            if pos_status != "Open":
                frappe.throw(_("Selected POS Opening Entry must be in 'Open' status"))
    
    def validate_unique_serial_numbers(self):
        """Ensure serial numbers are unique in the table"""
        if not self.serial_numbers:
            return
            
        serial_numbers = []
        for row in self.serial_numbers:
            if row.serial_no in serial_numbers:
                frappe.throw(_("Serial Number {0} is entered multiple times").format(row.serial_no))
            serial_numbers.append(row.serial_no)
    
    def on_submit(self):
        """Update Tenacity Serial No status to Consumed for qty=1 and Active for qty=-1 on submission"""
        try:
            frappe.log_error(f"Debug: on_submit triggered for POS Serial Validation: {self.name}", "POS Serial Validation")
            frappe.log_error(f"Debug: Docstatus: {self.docstatus}", "POS Serial Validation")
            frappe.log_error(f"Debug: Serial numbers count: {len(self.serial_numbers or [])}", "POS Serial Validation")

            if not self.serial_numbers:
                frappe.log_error("Debug: No serial numbers in child table", "POS Serial Validation")
                frappe.msgprint(_("No serial numbers to update"), title="Warning")
                return

            serial_updates = []
            for row in self.serial_numbers:
                frappe.log_error(f"Debug: Processing serial_no: {row.serial_no}, qty: {row.qty}", "POS Serial Validation")
                if row.qty == 1:
                    serial_updates.append({
                        "serial_no": row.serial_no,
                        "status": "Consumed"
                    })
                elif row.qty == -1:
                    serial_updates.append({
                        "serial_no": row.serial_no,
                        "status": "Active"
                    })
                else:
                    frappe.log_error(f"Debug: Invalid qty for serial_no: {row.serial_no}, qty: {row.qty}", "POS Serial Validation")
                    continue

            if not serial_updates:
                frappe.log_error("Debug: No valid serial updates to process", "POS Serial Validation")
                frappe.msgprint(_("No valid serial numbers to update"), title="Warning")
                return

            for update in serial_updates:
                try:
                    # Fetch Tenacity Serial No document by serial_no
                    serial_doc = frappe.get_last_doc("Tenacity Serial No", filters={"serial_no": update["serial_no"]})
                    frappe.log_error(f"Debug: Found Tenacity Serial No: {serial_doc.name}, current status: {serial_doc.status}", "POS Serial Validation")
                    serial_doc.status = update["status"]
                    serial_doc.save(ignore_permissions=True)
                    frappe.log_error(f"Debug: Updated serial_no: {update['serial_no']} to status: {serial_doc.status}", "POS Serial Validation")
                except frappe.DoesNotExistError:
                    frappe.log_error(f"Debug: Tenacity Serial No not found for serial_no: {update['serial_no']}", "POS Serial Validation")
                    frappe.msgprint(_("Serial number {0} not found in Tenacity Serial No").format(update["serial_no"]), title="Error")
                    continue
                except Exception as e:
                    frappe.log_error(f"Debug: Error updating serial_no: {update['serial_no']}, error: {str(e)}", "POS Serial Validation")
                    frappe.msgprint(_("Failed to update serial number {0}: {1}").format(update["serial_no"], str(e)), title="Error")
                    continue

            frappe.db.commit()
            frappe.msgprint(_("Serial number statuses updated successfully"), title="Success")

        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(f"Error in on_submit for POS Serial Validation: {str(e)}", "POS Serial Validation")
            frappe.msgprint(_("Failed to update serial number statuses: {0}").format(str(e)), title="Error")

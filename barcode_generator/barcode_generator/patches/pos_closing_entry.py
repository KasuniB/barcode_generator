import frappe
from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import POSClosingEntry

class CustomPOSClosingEntry(POSClosingEntry):
    def validate(self):
        super().validate()
        # Validate the waiters_pos_opening_entry
        if self.waiters_pos_opening_entry:
            opening_entry = frappe.get_doc("POS Opening Entry", self.waiters_pos_opening_entry)
            if opening_entry.status != "Open":
                frappe.throw(
                    _("Selected Waiter's POS Opening Entry should be open."),
                    title=_("Invalid Waiter's Opening Entry")
                )

    def on_submit(self):
        super().on_submit()
        # Update the waiter's POS Opening Entry with the closing entry reference
        if self.waiters_pos_opening_entry:
            frappe.db.set_value(
                "POS Opening Entry",
                self.waiters_pos_opening_entry,
                "pos_closing_entry",
                self.name
            )

    def on_cancel(self):
        super().on_cancel()
        # Clear the closing entry reference from waiter's POS Opening Entry
        if self.waiters_pos_opening_entry:
            frappe.db.set_value(
                "POS Opening Entry",
                self.waiters_pos_opening_entry,
                "pos_closing_entry",
                None
            )

# Override the original POSClosingEntry with the custom class
frappe.utils.monkey.patch_class(
    "erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry.POSClosingEntry",
    CustomPOSClosingEntry
)

# my_custom_app/patches/pos_closing_entry.py

import frappe
from frappe.utils import get_datetime

@frappe.whitelist()
def get_waiter_pos_invoices(start, end, pos_opening_entry):
    data = frappe.db.sql(
        """
        select
            name, timestamp(posting_date, posting_time) as "timestamp"
        from
            `tabPOS Invoice`
        where
            pos_opening_entry = %s and docstatus = 1 and ifnull(consolidated_invoice,'') = ''
        """,
        (pos_opening_entry,),
        as_dict=1,
    )

    data = [d for d in data if get_datetime(start) <= get_datetime(d.timestamp) <= get_datetime(end)]
    data = [frappe.get_doc("POS Invoice", d.name).as_dict() for d in data]
    return data

@frappe.whitelist()
def get_waiter_sales_invoices(start, end, pos_opening_entry):
    data = frappe.db.sql(
        """
        select
            name, timestamp(posting_date, posting_time) as "timestamp"
        from
            `tabSales Invoice`
        where
            pos_opening_entry = %s
            and docstatus = 1
            and is_pos = 1
            and is_created_using_pos = 1
            and ifnull(pos_closing_entry,'') = ''
        """,
        (pos_opening_entry,),
        as_dict=1,
    )

    data = [d for d in data if get_datetime(start) <= get_datetime(d.timestamp) <= get_datetime(end)]
    data = [frappe.get_doc("Sales Invoice", d.name).as_dict() for d in data]
    return data

    @frappe.whitelist()
def get_pos_invoices(start, end, pos_profile, user):
    if "POS Manager" in frappe.get_roles(frappe.session.user):
        data = frappe.db.sql(
            """
            select
                name, timestamp(posting_date, posting_time) as "timestamp"
            from
                `tabPOS Invoice`
            where
                docstatus = 1 and pos_profile = %s and ifnull(consolidated_invoice,'') = ''
            """,
            (pos_profile,),
            as_dict=1,
        )
    else:
        data = frappe.db.sql(
            """
            select
                name, timestamp(posting_date, posting_time) as "timestamp"
            from
                `tabPOS Invoice`
            where
                owner = %s and docstatus = 1 and pos_profile = %s and ifnull(consolidated_invoice,'') = ''
            """,
            (user, pos_profile),
            as_dict=1,
        )

    data = [d for d in data if get_datetime(start) <= get_datetime(d.timestamp) <= get_datetime(end)]
    data = [frappe.get_doc("POS Invoice", d.name).as_dict() for d in data]
    return data

@frappe.whitelist()
def get_sales_invoices(start, end, pos_profile, user):
    if "POS Manager" in frappe.get_roles(frappe.session.user):
        data = frappe.db.sql(
            """
            select
                name, timestamp(posting_date, posting_time) as "timestamp"
            from
                `tabSales Invoice`
            where
                docstatus = 1
                and is_pos = 1
                and pos_profile = %s
                and is_created_using_pos = 1
                and ifnull(pos_closing_entry,'') = ''
            """,
            (pos_profile,),
            as_dict=1,
        )
    else:
        data = frappe.db.sql(
            """
            select
                name, timestamp(posting_date, posting_time) as "timestamp"
            from
                `tabSales Invoice`
            where
                owner = %s
                and docstatus = 1
                and is_pos = 1
                and pos_profile = %s
                and is_created_using_pos = 1
                and ifnull(pos_closing_entry,'') = ''
            """,
            (user, pos_profile),
            as_dict=1,
        )

    data = [d for d in data if get_datetime(start) <= get_datetime(d.timestamp) <= get_datetime(end)]
    data = [frappe.get_doc("Sales Invoice", d.name).as_dict() for d in data]
    return data
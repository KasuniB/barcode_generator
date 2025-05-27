// my_custom_app/public/js/pos_closing_entry.js

frappe.ui.form.on("POS Closing Entry", {
    refresh: function(frm) {
        // Set query for waiters_pos_opening_entry
        frm.set_query("waiters_pos_opening_entry", function() {
            return {
                filters: {
                    status: "Open",
                    docstatus: 1
                }
            };
        });
    },

    waiters_pos_opening_entry: function(frm) {
        if (frm.doc.waiters_pos_opening_entry && frm.doc.period_start_date && frm.doc.period_end_date) {
            frappe.run_serially([
                () => frappe.dom.freeze(__("Loading Waiter's Invoices! Please Wait...")),
                () => frm.trigger("set_waiter_opening_amounts"),
                () => frm.trigger("get_waiter_pos_invoices"),
                () => frm.trigger("get_waiter_sales_invoices"),
                () => frappe.dom.unfreeze()
            ]);
        }
    },

    set_waiter_opening_amounts: function(frm) {
        return frappe.db
            .get_doc("POS Opening Entry", frm.doc.waiters_pos_opening_entry)
            .then(({ balance_details }) => {
                balance_details.forEach((detail) => {
                    let exists = frm.doc.payment_reconciliation.find(
                        (row) => row.mode_of_payment === detail.mode_of_payment
                    );
                    if (!exists) {
                        frm.add_child("payment_reconciliation", {
                            mode_of_payment: detail.mode_of_payment,
                            opening_amount: detail.opening_amount,
                            expected_amount: detail.opening_amount
                        });
                    }
                });
                frm.refresh_field("payment_reconciliation");
            });
    },

    get_waiter_pos_invoices: function(frm) {
        return frappe.call({
            method: "barcode_generator.barcode_generator.patches.pos_closing_entry.get_waiter_pos_invoices",
            args: {
                start: frappe.datetime.get_datetime_as_string(frm.doc.period_start_date),
                end: frappe.datetime.get_datetime_as_string(frm.doc.period_end_date),
                pos_opening_entry: frm.doc.waiters_pos_opening_entry
            },
            callback: (r) => {
                let pos_docs = r.message;
                pos_docs.forEach((d) => {
                    frm.add_child("pos_transactions", {
                        pos_invoice: d.name,
                        posting_date: d.posting_date,
                        grand_total: d.grand_total,
                        customer: d.customer
                    });
                    frm.doc.grand_total += flt(d.grand_total);
                    frm.doc.net_total += flt(d.net_total);
                    frm.doc.total_quantity += flt(d.total_qty);
                    d.payments.forEach((p) => {
                        let payment = frm.doc.payment_reconciliation.find(
                            (pay) => pay.mode_of_payment === p.mode_of_payment
                        );
                        if (p.account == d.account_for_change_amount) {
                            p.amount -= flt(d.change_amount);
                        }
                        if (payment) {
                            payment.expected_amount += flt(p.amount);
                            payment.closing_amount = payment.expected_amount;
                            payment.difference = payment.closing_amount - payment.expected_amount;
                        } else {
                            frm.add_child("payment_reconciliation", {
                                mode_of_payment: p.mode_of_payment,
                                opening_amount: 0,
                                expected_amount: p.amount,
                                closing_amount: p.amount
                            });
                        }
                    });
                    d.taxes.forEach((t) => {
                        let tax = frm.doc.taxes.find(
                            (tx) => tx.account_head === t.account_head && tx.rate === t.rate
                        );
                        if (tax) {
                            tax.amount += flt(t.tax_amount);
                        } else {
                            frm.add_child("taxes", {
                                account_head: t.account_head,
                                rate: t.rate,
                                amount: t.tax_amount
                            });
                        }
                    });
                });
                frm.refresh_field("pos_transactions");
                frm.refresh_field("payment_reconciliation");
                frm.refresh_field("taxes");
                frm.refresh_field("grand_total");
                frm.refresh_field("net_total");
                frm.refresh_field("total_quantity");
                set_html_data(frm);
            }
        });
    },

    get_waiter_sales_invoices: function(frm) {
        return frappe.call({
            method: "barcode_generator.barcode_generator.patches.pos_closing_entry.get_waiter_sales_invoices",
            args: {
                start: frappe.datetime.get_datetime_as_string(frm.doc.period_start_date),
                end: frappe.datetime.get_datetime_as_string(frm.doc.period_end_date),
                pos_opening_entry: frm.doc.waiters_pos_opening_entry
            },
            callback: (r) => {
                let sales_docs = r.message;
                sales_docs.forEach((d) => {
                    frm.add_child("sales_invoice_transactions", {
                        sales_invoice: d.name,
                        posting_date: d.posting_date,
                        grand_total: d.grand_total,
                        customer: d.customer
                    });
                    frm.doc.grand_total += flt(d.grand_total);
                    frm.doc.net_total += flt(d.net_total);
                    frm.doc.total_quantity += flt(d.total_qty);
                    d.payments.forEach((p) => {
                        let payment = frm.doc.payment_reconciliation.find(
                            (pay) => pay.mode_of_payment === p.mode_of_payment
                        );
                        if (p.account == d.account_for_change_amount) {
                            p.amount -= flt(d.change_amount);
                        }
                        if (payment) {
                            payment.expected_amount += flt(p.amount);
                            payment.closing_amount = payment.expected_amount;
                            payment.difference = payment.closing_amount - payment.expected_amount;
                        } else {
                            frm.add_child("payment_reconciliation", {
                                mode_of_payment: p.mode_of_payment,
                                opening_amount: 0,
                                expected_amount: p.amount,
                                closing_amount: p.amount
                            });
                        }
                    });
                    d.taxes.forEach((t) => {
                        let tax = frm.doc.taxes.find(
                            (tx) => tx.account_head === t.account_head && tx.rate === t.rate
                        );
                        if (tax) {
                            tax.amount += flt(t.tax_amount);
                        } else {
                            frm.add_child("taxes", {
                                account_head: t.account_head,
                                rate: t.rate,
                                amount: t.tax_amount
                            });
                        }
                    });
                });
                frm.refresh_field("sales_invoice_transactions");
                frm.refresh_field("payment_reconciliation");
                frm.refresh_field("taxes");
                frm.refresh_field("grand_total");
                frm.refresh_field("net_total");
                frm.refresh_field("total_quantity");
                set_html_data(frm);
            }
        });
    }
});
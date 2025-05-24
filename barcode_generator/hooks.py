app_name = "barcode_generator"
app_title = "Barcode Generator"
app_publisher = "KasuniB"
app_description = "Generate barcodes for ERPNext serial numbers"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@example.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/barcode_generator/css/barcode_generator.css"
# app_include_js = "/assets/barcode_generator/js/barcode_generator.js"

# include js, css files in header of web template
# web_include_css = "/assets/barcode_generator/css/barcode_generator.css"
# web_include_js = "/assets/barcode_generator/js/barcode_generator.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "barcode_generator/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Purchase Receipt": "public/js/stock_entry_custom.js",
    "Serial No": "public/js/serial_no_custom.js"
	
	
}

"""app_include_js = [
    "barcode_generator/doctype/pos_invoice/pos_invoice.js"
]"""

# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "barcode_generator.install.before_install"
# after_install = "barcode_generator.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "barcode_generator.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Purchase Receipt": {
        "on_submit": "barcode_generator.utils.api.stock_entry_after_submit"
    }
}

doc_events = {
    "POS Closing Entry": {
       "before_submit": "barcode_generator.barcode_generator.doctype.item_daily_tracker.item_daily_tracker.handle_pos_closing_with_validation"
   }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"barcode_generator.tasks.all"
# 	],
# 	"daily": [
# 		"barcode_generator.tasks.daily"
# 	],
# 	"hourly": [
# 		"barcode_generator.tasks.hourly"
# 	],
# 	"weekly": [
# 		"barcode_generator.tasks.weekly"
# 	]
# 	"monthly": [
# 		"barcode_generator.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "barcode_generator.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "barcode_generator.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "barcode_generator.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Request Events
# ----------------
# before_request = ["barcode_generator.utils.before_request"]
# after_request = ["barcode_generator.utils.after_request"]

# Job Events
# ----------
# before_job = ["barcode_generator.utils.before_job"]
# after_job = ["barcode_generator.utils.after_job"]

# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

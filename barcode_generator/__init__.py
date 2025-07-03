__version__ = "0.1.0"

import sys
from barcode_generator.utils.custom_script import pos_closing_entry as custom_pos_script
import erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry

# Replace the module in sys.modules
sys.modules['erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry'] = custom_pos_script
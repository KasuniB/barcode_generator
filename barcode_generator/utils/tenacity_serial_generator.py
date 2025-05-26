import frappe
import os
import barcode
from io import BytesIO
from PIL import Image
import base64
from fpdf import FPDF
import qrcode

# Setup logger for debugging
logger = frappe.logger("tenacity_serial_generator")

class TenacitySerialGenerator:
    """
    A class to generate and manage serial numbers and barcodes for Tenacity Serial No doctype.
    Generates serial numbers in format: Tenacity-item_code-####
    """

    def __init__(self):
        """Initialize the serial number generator"""
        pass

    def generate_serial_number(self, item_code):
        """Generate a new serial number for the given item code"""
        try:
            # Get the next sequential number for this item code
            existing_serials = frappe.get_all(
                "Tenacity Serial No",
                filters={"item_code": item_code},
                fields=["name"],
                order_by="creation desc",
                limit=1
            )
            
            if existing_serials:
                # Extract the number from the last serial number
                last_serial = existing_serials[0].name
                # Format: Tenacity-item_code-####
                parts = last_serial.split('-')
                if len(parts) >= 3:
                    try:
                        last_number = int(parts[-1])
                        next_number = last_number + 1
                    except ValueError:
                        next_number = 1
                else:
                    next_number = 1
            else:
                next_number = 1
            
            # Generate the new serial number
            serial_no = f"Tenacity-{item_code}-{next_number:04d}"
            return serial_no
            
        except Exception as e:
            logger.error(f"Error generating serial number for {item_code}: {str(e)}")
            return None

    def create_tenacity_serial_no(self, item_code, purchase_receipt=None, qty=1):
        """Create Tenacity Serial No documents for the given item"""
        created_serials = []
        
        try:
            # Debug: Check if item exists first
            if not frappe.db.exists("Item", item_code):
                logger.error(f"Item {item_code} does not exist in the database")
                return []
            
            # Get item details first
            item_doc = frappe.get_doc("Item", item_code)
            logger.info(f"Processing item: {item_code}, item_name: {item_doc.item_name}")
            
            # Debug: Check if Tenacity Serial No doctype exists
            if not frappe.db.exists("DocType", "Tenacity Serial No"):
                logger.error("DocType 'Tenacity Serial No' does not exist")
                return []
            
            for i in range(qty):
                # Generate serial number
                serial_no = self.generate_serial_number(item_code)
                if not serial_no:
                    logger.error(f"Failed to generate serial number for {item_code}")
                    continue
                
                logger.info(f"Generated serial number: {serial_no}")
                
                # Create Tenacity Serial No document
                try:
                    # Debug: Log the document data being created
                    doc_data = {
                        "doctype": "Tenacity Serial No",
                        "item_code": item_code,
                        "item_name": item_doc.item_name,
                        "purchase_document_no": purchase_receipt,
                        "status": "Active"  # Status options: Active, Consumed
                    }
                    logger.info(f"Creating document with data: {doc_data}")
                    
                    serial_doc = frappe.get_doc(doc_data)
                    
                    # Set the name manually
                    serial_doc.name = serial_no
                    
                    # Debug: Check permissions and validation
                    logger.info(f"Attempting to insert document with name: {serial_no}")
                    
                    # Try to insert with more detailed error handling
                    serial_doc.insert(ignore_permissions=True)
                    
                    # Commit the transaction
                    frappe.db.commit()
                    
                    created_serials.append(serial_no)
                    logger.info(f"Successfully created Tenacity Serial No: {serial_no}")
                    
                except frappe.DuplicateEntryError:
                    logger.warning(f"Serial number {serial_no} already exists, skipping")
                    continue
                except frappe.ValidationError as ve:
                    logger.error(f"Validation error creating serial doc {serial_no}: {str(ve)}")
                    continue
                except frappe.PermissionError as pe:
                    logger.error(f"Permission error creating serial doc {serial_no}: {str(pe)}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error creating serial doc {serial_no}: {str(e)}")
                    logger.error(f"Error type: {type(e).__name__}")
                    # Log the full traceback for debugging
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    continue
                
        except Exception as e:
            logger.error(f"Error creating Tenacity Serial No for {item_code}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            frappe.log_error(f"Error creating Tenacity Serial No for {item_code}: {str(e)}", "Tenacity Serial Generator")
            
        logger.info(f"Total serials created: {len(created_serials)}")
        return created_serials

    # Alternative method without setting name manually
    def create_tenacity_serial_no_auto_name(self, item_code, purchase_receipt=None, qty=1):
        """Create Tenacity Serial No documents with auto-generated names"""
        created_serials = []
        
        try:
            # Check if item exists first
            if not frappe.db.exists("Item", item_code):
                logger.error(f"Item {item_code} does not exist in the database")
                return []
            
            # Get item details
            item_doc = frappe.get_doc("Item", item_code)
            
            for i in range(qty):
                try:
                    # Create document without setting name manually
                    serial_doc = frappe.get_doc({
                        "doctype": "Tenacity Serial No",
                        "item_code": item_code,
                        "item_name": item_doc.item_name,
                        "purchase_document_no": purchase_receipt,
                        "status": "Active"
                    })
                    
                    # Let Frappe auto-generate the name
                    serial_doc.insert(ignore_permissions=True)
                    frappe.db.commit()
                    
                    created_serials.append(serial_doc.name)
                    logger.info(f"Created Tenacity Serial No with auto name: {serial_doc.name}")
                    
                except Exception as e:
                    logger.error(f"Error creating serial doc (auto-name): {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in create_tenacity_serial_no_auto_name: {str(e)}")
            
        return created_serials

    # Debug method to check doctype structure
    def debug_doctype_structure(self):
        """Debug method to check the Tenacity Serial No doctype structure"""
        try:
            # Check if doctype exists
            if not frappe.db.exists("DocType", "Tenacity Serial No"):
                logger.error("DocType 'Tenacity Serial No' does not exist")
                return False
            
            # Get doctype structure
            doctype = frappe.get_doc("DocType", "Tenacity Serial No")
            logger.info(f"DocType found: {doctype.name}")
            logger.info(f"Is custom: {doctype.custom}")
            logger.info(f"Naming rule: {doctype.naming_rule if hasattr(doctype, 'naming_rule') else 'Not set'}")
            logger.info(f"Autoname: {doctype.autoname if hasattr(doctype, 'autoname') else 'Not set'}")
            
            # List all fields
            logger.info("Fields in Tenacity Serial No:")
            for field in doctype.fields:
                logger.info(f"  - {field.fieldname}: {field.fieldtype} (Required: {field.reqd})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking doctype structure: {str(e)}")
            return False

    # Method to test database connectivity and permissions
    def test_database_operations(self, item_code):
        """Test basic database operations"""
        try:
            # Test 1: Check if we can read from Item doctype
            logger.info("Test 1: Reading Item doctype")
            if frappe.db.exists("Item", item_code):
                item = frappe.get_doc("Item", item_code)
                logger.info(f"Successfully read item: {item.name}")
            else:
                logger.error(f"Item {item_code} not found")
                return False
            
            # Test 2: Check if we can read from Tenacity Serial No
            logger.info("Test 2: Reading Tenacity Serial No doctype")
            existing_serials = frappe.get_all("Tenacity Serial No", limit=1)
            logger.info(f"Found {len(existing_serials)} existing serial numbers")
            
            # Test 3: Check permissions
            logger.info("Test 3: Checking permissions")
            can_create = frappe.has_permission("Tenacity Serial No", "create")
            can_write = frappe.has_permission("Tenacity Serial No", "write")
            logger.info(f"Can create: {can_create}, Can write: {can_write}")
            
            return True
            
        except Exception as e:
            logger.error(f"Database test failed: {str(e)}")
            return False

    def create_barcode_image(self, serial_no):
        """Generate a QR code image for the given serial number"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(serial_no)
            qr.make(fit=True)

            image = qr.make_image(fill_color="black", back_color="white")
            return image

        except Exception as e:
            logger.error(f"QR code generation error for {serial_no}: {str(e)}")
            return None

    def save_or_get_barcode_image(self, serial_no):
        """Create a barcode image and save it to the file system, or retrieve existing one"""
        
        try:
            # Check if barcode already exists for this serial number
            existing_files = frappe.get_all(
                "File",
                filters={
                    "attached_to_doctype": "Tenacity Serial No",
                    "attached_to_name": serial_no,
                    "file_name": f"tenacity_barcodes/{serial_no}.png"
                },
                fields=["name", "file_url"]
            )

            if existing_files:
                return existing_files[0].file_url

            # Generate new barcode image
            barcode_image = self.create_barcode_image(serial_no)

            if not barcode_image:
                logger.error(f"Failed to generate barcode for {serial_no}")
                return None

            # Define file path and name
            file_url = f"/files/tenacity_barcodes/{serial_no}.png"
            file_name = f"{serial_no}.png"

            # Ensure the barcode folder exists
            barcode_folder = frappe.get_site_path('public', 'files', 'tenacity_barcodes')
            if not os.path.exists(barcode_folder):
                os.makedirs(barcode_folder)

            # Save the barcode image
            try:
                barcode_image.save(os.path.join(barcode_folder, file_name))
            except Exception as e:
                logger.error(f"Error saving barcode image for {serial_no}: {str(e)}")
                return None

            # Create a File document in ERPNext
            try:
                file_doc = frappe.get_doc({
                    "doctype": "File",
                    "file_name": file_name,
                    "file_url": file_url,
                    "attached_to_doctype": "Tenacity Serial No",
                    "attached_to_name": serial_no
                })
                file_doc.insert(ignore_permissions=True)
            except Exception as e:
                logger.error(f"Error creating File document for {serial_no}: {str(e)}")
                return None

            # Update Tenacity Serial No with barcode image reference (if custom field exists)
            try:
                serial_doc = frappe.get_doc("Tenacity Serial No", serial_no)
                if hasattr(serial_doc, 'barcode_image'):
                    serial_doc.barcode_image = file_url
                    serial_doc.save(ignore_permissions=True)
            except Exception as e:
                logger.error(f"Error updating Tenacity Serial No {serial_no}: {str(e)}")

            return file_url

        except Exception as e:
            logger.error(f"Error in save_or_get_barcode_image for {serial_no}: {str(e)}")
            return None

# Debugging functions
def debug_tenacity_serial_creation(item_code):
    """Debug function to test serial creation"""
    generator = TenacitySerialGenerator()
    
    logger.info("=== DEBUGGING TENACITY SERIAL CREATION ===")
    
    # Test 1: Check doctype structure
    logger.info("Step 1: Checking doctype structure")
    generator.debug_doctype_structure()
    
    # Test 2: Test database operations
    logger.info("Step 2: Testing database operations")
    generator.test_database_operations(item_code)
    
    # Test 3: Try to generate serial number
    logger.info("Step 3: Generating serial number")
    serial_no = generator.generate_serial_number(item_code)
    logger.info(f"Generated serial: {serial_no}")
    
    # Test 4: Try to create with auto-naming
    logger.info("Step 4: Trying auto-naming approach")
    auto_serials = generator.create_tenacity_serial_no_auto_name(item_code, qty=1)
    logger.info(f"Auto-named serials: {auto_serials}")
    
    # Test 5: Try original method
    logger.info("Step 5: Trying original method")
    manual_serials = generator.create_tenacity_serial_no(item_code, qty=1)
    logger.info(f"Manual serials: {manual_serials}")
    
    return {
        "generated_serial": serial_no,
        "auto_serials": auto_serials,
        "manual_serials": manual_serials
    }

# Rest of the functions remain the same...
def generate_serials_for_purchase_receipt(purchase_receipt_name):
    """
    Generate Tenacity Serial Numbers for all items in a purchase receipt.
    Creates serial numbers in format: Tenacity-item_code-####
    """
    try:
        # Get the purchase receipt
        purchase_receipt = frappe.get_doc("Purchase Receipt", purchase_receipt_name)
        generator = TenacitySerialGenerator()
        created_serials = []

        logger.info(f"Processing Purchase Receipt: {purchase_receipt_name}")
        logger.info(f"Number of items in receipt: {len(purchase_receipt.items)}")

        # Process each item in the purchase receipt
        for item in purchase_receipt.items:
            item_code = item.item_code
            qty = int(item.qty) if item.qty else 1
            
            logger.info(f"Processing item: {item_code}, qty: {qty}")
            
            # Check if item exists
            if not frappe.db.exists("Item", item_code):
                logger.error(f"Item {item_code} does not exist")
                continue
            
            # Create serial numbers for this item
            try:
                serials = generator.create_tenacity_serial_no(
                    item_code=item_code,
                    purchase_receipt=purchase_receipt_name,
                    qty=qty
                )
                
                created_serials.extend(serials)
                logger.info(f"Created {len(serials)} serials for item {item_code}")
                
            except Exception as e:
                logger.error(f"Error creating serials for item {item_code}: {str(e)}")
                frappe.log_error(f"Error creating serials for item {item_code}: {str(e)}", "Tenacity Serial Generator")
                continue

        if not created_serials:
            error_msg = f"No serial numbers created for purchase receipt {purchase_receipt_name}"
            logger.error(error_msg)
            frappe.log_error(error_msg, "Tenacity Serial Generator")
            return []

        frappe.db.commit()
        logger.info(f"Successfully created {len(created_serials)} serial numbers")
        return created_serials

    except Exception as e:
        frappe.db.rollback()
        error_msg = f"Error generating serial numbers for {purchase_receipt_name}: {str(e)}"
        logger.error(error_msg)
        frappe.log_error(error_msg, "Tenacity Serial Generator")
        return []
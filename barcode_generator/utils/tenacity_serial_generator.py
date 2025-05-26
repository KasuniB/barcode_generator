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
            for i in range(qty):
                # Generate serial number
                serial_no = self.generate_serial_number(item_code)
                if not serial_no:
                    continue
                
                # Get item details
                item_doc = frappe.get_doc("Item", item_code)
                
                # Create Tenacity Serial No document
                serial_doc = frappe.get_doc({
                    "doctype": "Tenacity Serial No",
                    "name": serial_no,
                    "item_code": item_code,
                    "item_name": item_doc.item_name,
                    "purchase_document_no": purchase_receipt,
                    "status": "Active"  # Adjust field name as per your doctype
                })
                
                serial_doc.insert(ignore_permissions=True)
                created_serials.append(serial_no)
                
        except Exception as e:
            logger.error(f"Error creating Tenacity Serial No for {item_code}: {str(e)}")
            
        return created_serials

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

        # Process each item in the purchase receipt
        for item in purchase_receipt.items:
            item_code = item.item_code
            qty = int(item.qty) if item.qty else 1
            
            # Create serial numbers for this item
            serials = generator.create_tenacity_serial_no(
                item_code=item_code,
                purchase_receipt=purchase_receipt_name,
                qty=qty
            )
            
            created_serials.extend(serials)

        if not created_serials:
            frappe.log_error(f"No serial numbers created for purchase receipt {purchase_receipt_name}", "Tenacity Serial Generator")
            return []

        frappe.db.commit()
        return created_serials

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error generating serial numbers: {str(e)}", "Tenacity Serial Generator")
        return []

def generate_barcodes_for_purchase_receipt(purchase_receipt_name):
    """
    Generate barcodes for all Tenacity Serial Numbers linked to a purchase receipt.
    """
    try:
        generator = TenacitySerialGenerator()
        barcode_urls = []

        # Fetch Tenacity Serial Numbers where purchase_document_no matches the purchase receipt name
        serial_nos = frappe.get_all(
            "Tenacity Serial No",
            filters={"purchase_document_no": purchase_receipt_name},
            fields=["name", "item_code"]
        )

        # Process each serial number
        for serial in serial_nos:
            serial_no = serial.name
            # Generate or get existing barcode
            barcode_url = generator.save_or_get_barcode_image(serial_no)
            if barcode_url:
                barcode_urls.append({
                    "serial_no": serial_no,
                    "item_code": serial.item_code,
                    "barcode_url": barcode_url
                })

        if not barcode_urls:
            frappe.log_error(f"No serial numbers found for purchase receipt {purchase_receipt_name}", "Tenacity Serial Generator")
            return []

        frappe.db.commit()
        return barcode_urls

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error generating barcodes: {str(e)}", "Tenacity Serial Generator")
        return []

def print_barcodes_for_purchase_receipt(purchase_receipt_name):
    """Generate a PDF with one barcode per page for a purchase receipt, compatible with label printers"""
    try:
        # First, ensure barcodes are generated
        barcodes = generate_barcodes_for_purchase_receipt(purchase_receipt_name)
        
        if not barcodes:
            frappe.log_error(f"No serial numbers found for purchase receipt {purchase_receipt_name}", "Tenacity Serial Generator")
            return None
        
        # Create a PDF document - Use custom dimensions for label printer (100mm x 50mm)
        pdf = FPDF(orientation='L', unit='mm', format=(50, 100))
        
        # Get company logo for branding
        company = frappe.get_value("Purchase Receipt", purchase_receipt_name, "company")
        company_logo = frappe.get_value("Company", company, "company_logo") if company else None
        logo_path = None
        
        if company_logo:
            logo_path = frappe.get_site_path('public', company_logo.lstrip('/'))
            if not os.path.exists(logo_path):
                logo_path = None
        
        # Create each barcode on its own page
        for barcode in barcodes:
            # Add a new page for each barcode
            pdf.add_page()
            
            # Set margins
            margin_x = 3
            margin_y = 5
            text_width = 40
            qr_width = 57
            
            # Add company logo if available (in the top-left)
            if logo_path and os.path.exists(logo_path):
                pdf.image(logo_path, margin_x, margin_y, w=15)
                text_start_y = margin_y + 15
            else:
                text_start_y = margin_y
            
            # Add item code
            pdf.set_xy(margin_x + 1, text_start_y + 5)
            pdf.set_font("Arial", style="B", size=15)
            pdf.cell(0, 5, f" Item: {barcode['item_code']}")

            # Add item name
            item_name = frappe.get_value("Item", barcode['item_code'], "item_name") or barcode['item_code']
            pdf.set_xy(margin_x + 1, text_start_y + 11)
            pdf.set_font("Arial", style="B", size=18)
            pdf.multi_cell(w=35, h=4, txt=f"{item_name}", align='L')
            
            # Add serial number at the bottom
            pdf.set_xy(margin_x + 1, text_start_y + 35)
            pdf.set_font("Arial", size=8)
            pdf.cell(0, 5, f"S/N: {barcode['serial_no']}")
    
            # Add QR code image (right side, larger size)
            barcode_path = frappe.get_site_path('public', barcode['barcode_url'].lstrip('/'))
            if os.path.exists(barcode_path):
                # Position QR code on the right, centered vertically
                qr_x = margin_x + text_width
                qr_y = margin_y
                qr_size = 40  # 40mm to fit height minus margins
                pdf.image(barcode_path, qr_x, qr_y, w=qr_size, h=qr_size)
        
        # Save the PDF
        pdf_folder = frappe.get_site_path('public', 'files', 'tenacity_barcode_prints')
        if not os.path.exists(pdf_folder):
            os.makedirs(pdf_folder)
        
        file_path = os.path.join(pdf_folder, f"{purchase_receipt_name}_tenacity_barcodes.pdf")
        pdf.output(file_path)
        
        # Create File document
        file_url = f"/files/tenacity_barcode_prints/{purchase_receipt_name}_tenacity_barcodes.pdf"
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": f"{purchase_receipt_name}_tenacity_barcodes.pdf",
            "file_url": file_url,
            "attached_to_doctype": "Purchase Receipt",
            "attached_to_name": purchase_receipt_name
        })
        file_doc.insert(ignore_permissions=True)
        
        return file_url
    
    except Exception as e:
        frappe.log_error(f"Error generating barcode PDF: {str(e)}", "Tenacity Serial Generator")
        return None

def print_barcode_for_tenacity_serial(serial_no):
    """Generate a PDF with a single barcode for a Tenacity Serial Number"""
    try:
        # Get the serial number details
        serial = frappe.get_doc("Tenacity Serial No", serial_no)
        generator = TenacitySerialGenerator()

        # Generate or get existing barcode
        barcode_url = generator.save_or_get_barcode_image(serial_no)
        if not barcode_url:
            return None

        # Create a PDF document
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()

        # Define constants
        label_width = 100
        label_height = 50
        margin_x = (210 - label_width) / 2  # Center horizontally
        margin_y = 20

        # Get company logo for branding
        company = frappe.get_value("Tenacity Serial No", serial_no, "company")
        company_logo = frappe.get_value("Company", company, "company_logo") if company else None
        logo_path = None

        if company_logo:
            logo_path = frappe.get_site_path('public', company_logo.lstrip('/'))

        # Draw label border
        pdf.rect(margin_x, margin_y, label_width, label_height)

        # Add company logo if available
        if logo_path and os.path.exists(logo_path):
            pdf.image(logo_path, margin_x + 5, margin_y + 5, w=15)
            start_y = margin_y + 15
        else:
            start_y = margin_y + 5

        # Add serial number
        pdf.set_xy(margin_x + 5, start_y)
        pdf.set_font("Arial", size=8)
        pdf.cell(0, 5, f"S/N: {serial_no}")

        # Add item code
        pdf.set_xy(margin_x + 5, start_y + 7)
        pdf.set_font("Arial", size=8)
        pdf.cell(0, 5, f"Item: {serial.item_code}")

        # Add barcode image
        barcode_path = frappe.get_site_path('public', barcode_url.lstrip('/'))
        if os.path.exists(barcode_path):
            pdf.image(barcode_path, margin_x + 25, start_y + 12, w=50)

        # Save the PDF
        pdf_folder = frappe.get_site_path('public', 'files', 'tenacity_barcode_prints')
        if not os.path.exists(pdf_folder):
            os.makedirs(pdf_folder)

        file_path = os.path.join(pdf_folder, f"{serial_no}_barcode.pdf")
        pdf.output(file_path)

        # Create File document
        file_url = f"/files/tenacity_barcode_prints/{serial_no}_barcode.pdf"
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": f"{serial_no}_barcode.pdf",
            "file_url": file_url,
            "attached_to_doctype": "Tenacity Serial No",
            "attached_to_name": serial_no
        })
        file_doc.insert(ignore_permissions=True)

        return file_url

    except Exception as e:
        frappe.log_error(f"Error printing barcode: {str(e)}", "Tenacity Serial Generator")
        return None

# Convenience function to generate both serials and barcodes
def process_purchase_receipt(purchase_receipt_name):
    """Generate serial numbers and barcodes for a purchase receipt"""
    try:
        # First generate serial numbers
        serials = generate_serials_for_purchase_receipt(purchase_receipt_name)
        
        if serials:
            # Then generate barcodes for the created serials
            barcodes = generate_barcodes_for_purchase_receipt(purchase_receipt_name)
            return {
                "serials": serials,
                "barcodes": barcodes
            }
        else:
            return {"serials": [], "barcodes": []}
            
    except Exception as e:
        frappe.log_error(f"Error processing purchase receipt {purchase_receipt_name}: {str(e)}", "Tenacity Serial Generator")
        return {"serials": [], "barcodes": []}
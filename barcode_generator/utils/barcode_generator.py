import frappe
import os
import barcode
##from barcode.writer import ImageWriter
from io import BytesIO
from PIL import Image
import base64
from fpdf import FPDF
import qrcode

# Setup logger for debugging
logger = frappe.logger("barcode_generator")

class BarcodeGenerator:
    """
    A class to generate and manage barcodes for ERPNext serial numbers.
    Uses existing serial numbers instead of generating them.
    """

    def __init__(self):
        """Initialize the barcode generator"""
        pass

    """ def create_barcode_image(self, serial_no, barcode_type="code128"):
        ""Generate a barcode image for the given serial number""
        try:
            # Create barcode instance
            barcode_class = barcode.get_barcode_class(barcode_type)
            barcode_instance = barcode_class(serial_no, writer=ImageWriter())

            # Generate barcode image
            buffer = BytesIO()
            barcode_instance.write(buffer)
            buffer.seek(0)

            # Return the image for further processing
            image = Image.open(buffer)
            return image

        except Exception as e:
            logger.error(f"Barcode generation error for {serial_no}: {str(e)}")
            return None """
    
    def create_barcode_image(self, serial_no):
        """Generate a barcode image for the given serial number"""
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

    """def create_qr_code(self, serial_no):
        ""Generate a QR code for the given serial number""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(serial_no)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            return img

        except Exception as e:
            logger.error(f"QR code generation error for {serial_no}: {str(e)}")
            return None"""

    def get_base64_image(self, image):
        """Convert image to base64 string for embedding in documents"""
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()

    def save_or_get_barcode_image(self, serial_no):
        """Create a barcode image and save it to the file system, or retrieve existing one"""
        logger.info(f"Processing barcode wonderful for serial_no: {serial_no}")
        try:
            # Check if barcode already exists for this serial number
            existing_files = frappe.get_all(
                "File",
                filters={
                    "attached_to_doctype": "Tenacity Serial No",
                    "attached_to_name": serial_no,
                    "file_name": f"barcodes/{serial_no}.png"
                },
                fields=["name", "file_url"]
            )

            if existing_files:
                logger.info(f"Existing barcode found for {serial_no}")
                return existing_files[0].file_url

            # Generate new barcode image
            logger.info(f"Generating new barcode for {serial_no}")
            barcode_image = self.create_barcode_image(serial_no)

            if not barcode_image:
                logger.error(f"Failed to generate barcode for {serial_no}")
                return None

            # Define file path and name
            file_url = f"/files/barcodes/{serial_no}.png"
            file_name = f"{serial_no}.png"

            # Ensure the barcode folder exists
            barcode_folder = frappe.get_site_path('public', 'files', 'barcodes')
            if not os.path.exists(barcode_folder):
                os.makedirs(barcode_folder)
                logger.info(f"Created barcode folder: {barcode_folder}")

            # Save the barcode image
            try:
                barcode_image.save(os.path.join(barcode_folder, file_name))
                logger.info(f"Saved barcode image to {file_url}")
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
                logger.info(f"Created File document for {serial_no}")
            except Exception as e:
                logger.error(f"Error creating File document for {serial_no}: {str(e)}")
                return None

            # Update Serial No with barcode image reference (if custom field exists)
            try:
                serial_doc = frappe.get_doc("Tenacity Serial No", serial_no)
                if hasattr(serial_doc, 'custom_barcode_image'):
                    serial_doc.custom_barcode_image = file_url
                    serial_doc.save(ignore_permissions=True)
                    logger.info(f"Updated Serial No {serial_no} with barcode image")
            except Exception as e:
                logger.error(f"Error updating Serial No {serial_no}: {str(e)}")

            return file_url

        except Exception as e:
            logger.error(f"Error in save_or_get_barcode_image for {serial_no}: {str(e)}")
            return None

def generate_barcodes_for_stock_entry(stock_entry_name):
    frappe.log_error(f"Starting barcode generation for: {stock_entry_name}", "Barcode Generator")
    """
    Generate barcodes for serial numbers linked to a stock entry via purchase_document_no.
    Creates new serial numbers in Tenacity Serial No doctype if none exist.
    """
    try:
        # Get the stock entry
        stock_entry = frappe.get_doc("Purchase Receipt", stock_entry_name)
        generator = BarcodeGenerator()
        barcode_urls = []

        # Fetch serial numbers where purchase_document_no matches the stock entry name
        serial_nos = frappe.get_all(
            "Tenacity Serial No",
            filters={"purchase_document_no": stock_entry_name},
            fields=["name", "serial_no", "item_code"]
        )

        # If no serial numbers exist, create them
        if not serial_nos:
            # Get items from stock entry
            items = stock_entry.get("items")
            if not items:
                frappe.log_error(f"No items found in stock entry {stock_entry_name}", "Barcode Generator")
                return []

            for item in items:
                item_code = item.item_code
                qty = int(item.qty)  # Assuming qty is an integer

                # Generate serial numbers for each item based on qty
                for i in range(qty):
                    # Get the last serial number for this item_code to determine the next number
                    last_serial = frappe.get_all(
                        "Tenacity Serial No",
                        filters={"item_code": item_code},
                        fields=["serial_no"],
                        order_by="creation desc",
                        limit=1
                    )

                    # Extract the serial number part (####) or start from 0
                    if last_serial:
                        last_no = last_serial[0]["serial_no"].split('-')[-1]
                        try:
                            serial_count = int(last_no) + 1
                        except ValueError:
                            serial_count = 1
                    else:
                        serial_count = 1

                    # Format serial number: Tenacity-item_code-#### (padded to 4 digits)
                    serial_no = f"Tenacity-{item_code}-{serial_count:04d}"

                    # Create new Tenacity Serial No document
                    serial_doc = frappe.get_doc({
                        "doctype": "Tenacity Serial No",
                        "serial_no": serial_no,
                        "item_code": item_code,
                        "purchase_document_no": stock_entry_name
                    })
                    serial_doc.insert(ignore_permissions=True)
                    logger.info(f"Created Tenacity Serial No: {serial_no} with name {serial_doc.name}")

                    # Add to serial_nos list for barcode generation
                    serial_nos.append({"name": serial_doc.name, "serial_no": serial_no, "item_code": item_code})

        # Process each serial number
        for serial in serial_nos:
            serial_no = serial["serial_no"]  # Use dictionary key access
            # Generate or get existing barcode
            barcode_url = generator.save_or_get_barcode_image(serial_no)
            if barcode_url:
                barcode_urls.append({
                    "serial_no": serial_no,
                    "item_code": serial["item_code"],  # Use dictionary key access
                    "barcode_url": barcode_url
                })

        if not barcode_urls:
            frappe.log_error(f"No serial numbers processed for stock entry {stock_entry_name}", "Barcode Generator")
            return []

        frappe.db.commit()
        return barcode_urls

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error generating barcodes: {str(e)}", "Barcode Generator")
        return []
        
def print_barcodes_for_stock_entry(stock_entry_name):
    """Generate a PDF with one barcode per page for a stock entry, compatible with label printers"""
    try:
        # Check if PDF already exists for this stock entry
        existing_files = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Purchase Receipt",
                "attached_to_name": stock_entry_name,
                "file_name": f"{stock_entry_name}_barcodes.pdf"
            },
            fields=["name", "file_url"]
        )

        if existing_files:
            frappe.log_error(f"Existing barcode PDF found for {stock_entry_name}: {existing_files[0].file_url}", "Barcode Generator")
            return existing_files[0].file_url
        
        # First, ensure barcodes are generated
        barcodes = generate_barcodes_for_stock_entry(stock_entry_name)
        
        if not barcodes:
            frappe.log_error(f"No serial numbers found for stock entry {stock_entry_name}", "Barcode Generator")
            return None
        
        # Create a PDF document - Use custom dimensions for label printer (100mm x 50mm)
        pdf = FPDF(orientation='L', unit='mm', format=(50, 100))
        
        # Get company logo for branding
        company = frappe.get_value("Purchase Receipt", stock_entry_name, "company")
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
            margin_x = 3  # Reduced left margin for text
            margin_y = 5
            label_width = 100
            label_height = 50
            text_width = 40  # Reduced text area to allow larger QR code
            qr_width = 57   # Increased QR code area (100 - 40 - 3)
            
            # Add company logo if available (in the top-left)
            if logo_path and os.path.exists(logo_path):
                pdf.image(logo_path, margin_x, margin_y, w=15)
                text_start_y = margin_y + 15
            else:
                text_start_y = margin_y
            
            # Add only item name (removed item_code display)
            item_name = frappe.get_value("Item", barcode['item_code'], "item_name") or barcode['item_code']
            pdf.set_xy(margin_x + 1, text_start_y + 5)
            pdf.set_font("Arial", style="B", size=12)  # Reduced font size from 18 to 12
            pdf.multi_cell(w=35, h=4, txt=f"{item_name}", align='L')            
    
            # Add QR code image (right side, larger size)
            barcode_path = frappe.get_site_path('public', barcode['barcode_url'].lstrip('/'))
            if os.path.exists(barcode_path):
                # Position QR code on the right, centered vertically
                qr_x = margin_x + text_width
                qr_y = margin_y
                qr_size = label_height - 2 * margin_y  # 40mm to fit height minus margins
                pdf.image(barcode_path, qr_x, qr_y, w=qr_size, h=qr_size)
        
        # Save the PDF
        pdf_folder = frappe.get_site_path('public', 'files', 'barcode_prints')
        if not os.path.exists(pdf_folder):
            os.makedirs(pdf_folder)
        
        file_path = os.path.join(pdf_folder, f"{stock_entry_name}_barcodes.pdf")
        pdf.output(file_path)
        
        # Create File document
        file_url = f"/files/barcode_prints/{stock_entry_name}_barcodes.pdf"
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": f"{stock_entry_name}_barcodes.pdf",
            "file_url": file_url,
            "attached_to_doctype": "Purchase Receipt",
            "attached_to_name": stock_entry_name
        })
        file_doc.insert(ignore_permissions=True)
        
        frappe.log_error(f"Generated new barcode PDF for {stock_entry_name}: {file_url}", "Barcode Generator")
        return file_url
    
    except Exception as e:
        frappe.log_error(f"Error generating barcode PDF: {str(e)}", "Barcode Generator")
        return None
        
def print_barcode_for_serial_no(serial_no):
    """Generate a PDF with a single barcode for a serial number"""
    try:
        # Get the serial number details
        serial = frappe.get_doc("Tenacity Serial No", serial_no)
        generator = BarcodeGenerator()

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
        pdf_folder = frappe.get_site_path('public', 'files', 'barcode_prints')
        if not os.path.exists(pdf_folder):
            os.makedirs(pdf_folder)

        file_path = os.path.join(pdf_folder, f"{serial_no}_barcode.pdf")
        pdf.output(file_path)

        # Create File document
        file_url = f"/files/barcode_prints/{serial_no}_barcode.pdf"
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
        frappe.log_error(f"Error printing barcode: {str(e)}", "Barcode Generator")
        return None
    

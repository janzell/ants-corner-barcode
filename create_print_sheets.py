import os
import glob
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm
import math

def create_barcode_sheets(output_filename="barcode_sheets.pdf", barcodes_per_row=4, barcodes_per_col=5):
    """Create PDF sheets with multiple barcodes for easy printing.
    
    Args:
        output_filename (str): Name of the output PDF file
        barcodes_per_row (int): Number of barcodes per row
        barcodes_per_col (int): Number of barcodes per column
    """
    
    # Get all barcode images
    barcode_files = []
    for folder in glob.glob("*/"):
        if os.path.isdir(folder):
            folder_barcodes = glob.glob(os.path.join(folder, "*.png"))
            barcode_files.extend(folder_barcodes)
    
    if not barcode_files:
        print("No barcode files found. Please run main.py first to generate barcodes.")
        return
    
    print(f"Found {len(barcode_files)} barcode files")
    
    # PDF setup
    page_width, page_height = A4
    c = canvas.Canvas(output_filename, pagesize=A4)
    
    # Calculate barcode dimensions and spacing
    barcode_width = 50 * mm   # 50mm width
    barcode_height = 30 * mm  # 30mm height
    
    # Calculate margins and spacing
    total_barcodes_width = barcodes_per_row * barcode_width
    total_barcodes_height = barcodes_per_col * barcode_height
    
    margin_x = (page_width - total_barcodes_width) / (barcodes_per_row + 1)
    margin_y = (page_height - total_barcodes_height) / (barcodes_per_col + 1)
    
    barcodes_per_page = barcodes_per_row * barcodes_per_col
    total_pages = math.ceil(len(barcode_files) / barcodes_per_page)
    
    print(f"Creating {total_pages} pages with {barcodes_per_page} barcodes per page")
    
    # Process barcodes
    for page_num in range(total_pages):
        print(f"Processing page {page_num + 1}/{total_pages}")
        
        start_idx = page_num * barcodes_per_page
        end_idx = min(start_idx + barcodes_per_page, len(barcode_files))
        page_barcodes = barcode_files[start_idx:end_idx]
        
        # Place barcodes on page
        for i, barcode_file in enumerate(page_barcodes):
            row = i // barcodes_per_row
            col = i % barcodes_per_row
            
            # Calculate position (from bottom-left)
            x = margin_x + col * (barcode_width + margin_x)
            y = page_height - margin_y - (row + 1) * (barcode_height + margin_y)
            
            # Add barcode to PDF
            try:
                c.drawImage(barcode_file, x, y, width=barcode_width, height=barcode_height)
            except Exception as e:
                print(f"Error adding {barcode_file}: {e}")
        
        # Add page info
        c.setFont("Helvetica", 8)
        c.drawString(10, 10, f"Page {page_num + 1} of {total_pages} | Generated from Ant's Corner inventory")
        
        # Start new page if not last page
        if page_num < total_pages - 1:
            c.showPage()
    
    # Save PDF
    c.save()
    print(f"\nPDF created successfully: {output_filename}")
    print(f"Total barcodes: {len(barcode_files)}")
    print(f"Pages: {total_pages}")
    print(f"Layout: {barcodes_per_row} x {barcodes_per_col} barcodes per page")

def create_category_sheets():
    """Create separate PDF sheets for each category."""
    folders = [f for f in glob.glob("*/") if os.path.isdir(f) and glob.glob(os.path.join(f, "*.png"))]
    
    if not folders:
        print("No folders with barcodes found.")
        return
    
    for folder in folders:
        folder_name = folder.rstrip('/')
        barcode_files = glob.glob(os.path.join(folder, "*.png"))
        
        if not barcode_files:
            continue
            
        print(f"\nCreating PDF for {folder_name} ({len(barcode_files)} barcodes)")
        
        # Create PDF for this category
        output_filename = f"{folder_name}_barcodes.pdf"
        
        # Calculate optimal layout based on number of barcodes
        if len(barcode_files) <= 20:
            barcodes_per_row = 4
            barcodes_per_col = 5
        else:
            barcodes_per_row = 5
            barcodes_per_col = 6
        
        # PDF setup
        page_width, page_height = A4
        c = canvas.Canvas(output_filename, pagesize=A4)
        
        # Calculate dimensions
        barcode_width = 50 * mm
        barcode_height = 30 * mm
        
        total_barcodes_width = barcodes_per_row * barcode_width
        total_barcodes_height = barcodes_per_col * barcode_height
        
        margin_x = (page_width - total_barcodes_width) / (barcodes_per_row + 1)
        margin_y = (page_height - total_barcodes_height) / (barcodes_per_col + 1)
        
        barcodes_per_page = barcodes_per_row * barcodes_per_col
        total_pages = math.ceil(len(barcode_files) / barcodes_per_page)
        
        # Process pages
        for page_num in range(total_pages):
            start_idx = page_num * barcodes_per_page
            end_idx = min(start_idx + barcodes_per_page, len(barcode_files))
            page_barcodes = barcode_files[start_idx:end_idx]
            
            # Place barcodes
            for i, barcode_file in enumerate(page_barcodes):
                row = i // barcodes_per_row
                col = i % barcodes_per_row
                
                x = margin_x + col * (barcode_width + margin_x)
                y = page_height - margin_y - (row + 1) * (barcode_height + margin_y)
                
                try:
                    c.drawImage(barcode_file, x, y, width=barcode_width, height=barcode_height)
                except Exception as e:
                    print(f"Error adding {barcode_file}: {e}")
            
            # Add header and page info
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, page_height - 20, f"{folder_name.replace('_', ' ').title()} - Barcodes")
            
            c.setFont("Helvetica", 8)
            c.drawString(10, 10, f"Page {page_num + 1} of {total_pages} | {folder_name} | {len(barcode_files)} total barcodes")
            
            if page_num < total_pages - 1:
                c.showPage()
        
        c.save()
        print(f"Created: {output_filename}")

def main():
    print("Barcode PDF Generator")
    print("====================\n")
    
    choice = input("Choose an option:\n1. Create one PDF with all barcodes\n2. Create separate PDFs by category\n3. Both\nEnter choice (1/2/3): ").strip()
    
    if choice in ['1', '3']:
        print("\nCreating combined PDF...")
        create_barcode_sheets("all_barcodes.pdf")
    
    if choice in ['2', '3']:
        print("\nCreating category-specific PDFs...")
        create_category_sheets()
    
    print("\nDone! You can now print the PDF files.")
    print("\nPrinting tips:")
    print("- Use 'Actual Size' or '100%' scaling when printing")
    print("- Do NOT use 'Fit to Page' as it will change barcode dimensions")
    print("- Each barcode should print as 50mm x 30mm")
    print("- Use good quality white paper for best scanner readability")

if __name__ == "__main__":
    main()


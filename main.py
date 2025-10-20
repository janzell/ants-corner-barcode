import csv
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import os
import re


def clean_filename(filename):
    """Clean filename to remove invalid characters."""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\|?*&]', '', filename)
    filename = filename.replace(' ', '_')
    return filename[:50]  # Limit length


def truncate_text(text, max_length=20):
    """Truncate text if it's too long and add ellipsis."""
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text


def generate_barcode_image(folder, barcode_number, price, sku, item_name):
    """Generates a barcode image optimized for scanner readability.
    
    Args:
        folder (str): The folder to save the image in
        barcode_number (str): The barcode number to generate
        price (str): The item price to display
        sku (str): The SKU for filename
    """
    # Ensure folder exists
    os.makedirs(folder, exist_ok=True)
    
    # Clean filename
    filename = clean_filename(f"{sku}-{barcode_number}")
    img_path = os.path.join(folder, filename)

    # Generate barcode with reduced height for more space for product name
    code = barcode.Code128(barcode_number, writer=ImageWriter())
    options = {
        'module_width': 0.4,
        'module_height': 10.0,  # Reduced barcode height
        'quiet_zone': 4.0,
        'font_size': 12,
        'text_distance': 5.0,
        'background': 'white',
        'foreground': 'black',
        'dpi': 150,
    }
    barcode_img = code.save(img_path, options=options)
    image = Image.open(img_path + '.png')

    # Add extra space at the top for the product name
    extra_top = 30
    extra_bottom = 35 if price else 15
    new_image = Image.new('RGB', (image.width, image.height + extra_top + extra_bottom), 'white')

    # Draw product name at the top, centered and truncated if too long
    draw = ImageDraw.Draw(new_image)
    try:
        font_name = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 16)
    except:
        font_name = ImageFont.load_default()
    max_name_length = 28
    display_name = truncate_text(item_name, max_name_length)
    name_bbox = draw.textbbox((0, 0), display_name, font=font_name)
    name_width = name_bbox[2] - name_bbox[0]
    name_x = (image.width - name_width) // 2
    name_y = 5
    draw.text((name_x, name_y), display_name, fill='black', font=font_name)

    # Paste barcode below the name
    new_image.paste(image, (0, extra_top))

    # Add price at the bottom if available
    if price:
        try:
            font = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 18)
        except:
            font = ImageFont.load_default()
        price_text = f"₱{price}"
        price_bbox = draw.textbbox((0, 0), price_text, font=font)
        price_width = price_bbox[2] - price_bbox[0]
        price_x = (image.width - price_width) // 2
        price_y = image.height + extra_top + 12
        draw.text((price_x, price_y), price_text, fill='black', font=font)

    # Resize to target size (50mm x 30mm ≈ 295x177 pixels at 150 DPI)
    target_size = (295, 177)
    resized_image = new_image.resize(target_size, Image.Resampling.LANCZOS)
    final_path = img_path + '.png'
    resized_image.save(final_path, 'PNG', optimize=True, dpi=(150, 150))
    print(f"Generated barcode: {final_path}")
    temp_file = img_path + '.png'
    if os.path.exists(temp_file) and temp_file != final_path:
        os.remove(temp_file)


def main():
    """Main function to process items.csv and generate barcodes organized by category."""
    csv_file = 'items.csv'
    
    # Column indices based on the CSV structure
    SKU_INDEX = 1
    NAME_INDEX = 2
    CATEGORY_INDEX = 3
    BARCODE_INDEX = 13
    PRICE_INDEX = 18  # Price [Ant's Corner]
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip header row
            next(reader)
            
            processed_count = 0
            skipped_count = 0
            
            for row_num, row in enumerate(reader, start=2):  # Start from 2 since we skipped header
                # Ensure row has enough columns
                if len(row) <= max(SKU_INDEX, NAME_INDEX, CATEGORY_INDEX, BARCODE_INDEX, PRICE_INDEX):
                    print(f"Row {row_num}: Insufficient columns, skipping")
                    skipped_count += 1
                    continue
                
                # Extract data
                sku = row[SKU_INDEX].strip() if len(row) > SKU_INDEX else ""
                item_name = row[NAME_INDEX].strip() if len(row) > NAME_INDEX else ""
                category = row[CATEGORY_INDEX].strip() if len(row) > CATEGORY_INDEX else "Uncategorized"
                barcode_number = row[BARCODE_INDEX].strip() if len(row) > BARCODE_INDEX else ""
                price = row[PRICE_INDEX].strip() if len(row) > PRICE_INDEX else ""
                
                # Skip if no barcode number
                if not barcode_number:
                    print(f"Row {row_num}: No barcode number for {sku} - {item_name}, skipping")
                    skipped_count += 1
                    continue
                
                # Clean category name for folder
                folder_name = clean_filename(category) if category else "Uncategorized"
                
                try:
                    generate_barcode_image(
                        folder=folder_name,
                        barcode_number=barcode_number,
                        price=price,
                        sku=sku,
                        item_name=item_name
                    )
                    processed_count += 1
                    
                except Exception as e:
                    print(f"Error generating barcode for {sku} - {item_name}: {str(e)}")
                    skipped_count += 1
            
            print(f"\nCompleted! Processed: {processed_count}, Skipped: {skipped_count}")
            
    except FileNotFoundError:
        print(f"Error: {csv_file} not found. Please ensure the file exists in the current directory.")
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")


if __name__ == "__main__":
    main()

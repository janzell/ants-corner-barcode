from flask import Flask, render_template, request, send_from_directory, abort, jsonify
from PIL import Image
import os
import subprocess
import tempfile
import shlex

app = Flask(__name__)

# Set the root directory where barcode images are stored (category folders)
BARCODE_ROOT = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/barcode')
def barcode_lookup():
    sku = request.args.get('sku', '').strip()
    if not sku:
        return render_template('index.html', error='Please enter a SKU.')

    # Search for the image file by SKU in all subfolders
    found_path = None
    found_category = None
    for root, dirs, files in os.walk(BARCODE_ROOT):
        for file in files:
            if file.startswith(sku + '-') and file.endswith('.png'):
                found_path = os.path.join(root, file)
                found_category = os.path.relpath(root, BARCODE_ROOT)
                break
        if found_path:
            break

    if not found_path:
        return render_template('index.html', error=f'No barcode image found for SKU: {sku}')

    # Build the relative URL for the image
    rel_image_path = os.path.relpath(found_path, BARCODE_ROOT)
    return render_template('barcode.html', sku=sku, image_path=rel_image_path.replace('\\', '/'))

@app.route('/barcode_image/<path:filename>')
def barcode_image(filename):
    # filename includes category folder, e.g. Baking_Supplies/10000-527341680526.png
    dir_name = os.path.dirname(filename)
    file_name = os.path.basename(filename)
    abs_dir = os.path.join(BARCODE_ROOT, dir_name)
    if not os.path.exists(os.path.join(abs_dir, file_name)):
        abort(404)
    return send_from_directory(abs_dir, file_name)

@app.route('/print_barcode/<path:filename>', methods=['POST'])
def print_barcode(filename):
    abs_path = os.path.join(BARCODE_ROOT, filename)
    if not os.path.exists(abs_path):
        return jsonify({'success': False, 'error': 'File not found'}), 404
    try:
        # Open the image in Preview for printing (macOS only)
        subprocess.run(shlex.split(f'open -a Preview "{abs_path}"'), check=True)
        return jsonify({'success': True, 'message': 'Image opened in Preview for printing!'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

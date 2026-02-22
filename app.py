from flask import Flask, render_template, request, send_from_directory, abort, jsonify
import os
import subprocess
import shlex
import csv
import re

app = Flask(__name__)

# Set the root directory where barcode images are stored (category folders)
BARCODE_ROOT = os.path.dirname(os.path.abspath(__file__))
ITEMS_CSV = os.path.join(BARCODE_ROOT, 'items.csv')

SKU_TO_IMAGE_PATH = {}
NAME_TO_SKUS = {}
SEARCHABLE_ITEMS = []


def normalize_text(text):
    cleaned = re.sub(r'[^a-z0-9]+', ' ', (text or '').lower())
    return ' '.join(cleaned.split())


def build_barcode_index():
    sku_index = {}
    skip_dirs = {'templates', 'install', '.git', '__pycache__'}
    for root, dirs, files in os.walk(BARCODE_ROOT):
        dirs[:] = [directory for directory in dirs if directory not in skip_dirs]
        for file_name in files:
            if not file_name.endswith('.png') or '-' not in file_name:
                continue
            sku = file_name.split('-', 1)[0].strip()
            if not sku:
                continue
            abs_path = os.path.join(root, file_name)
            rel_path = os.path.relpath(abs_path, BARCODE_ROOT).replace('\\', '/')
            sku_index[sku] = rel_path
    return sku_index


def build_name_index():
    name_to_skus = {}
    searchable_items = []

    if not os.path.exists(ITEMS_CSV):
        return name_to_skus, searchable_items

    with open(ITEMS_CSV, 'r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            sku = (row.get('SKU') or '').strip()
            name = (row.get('Name') or '').strip()
            if not sku or not name:
                continue

            normalized_name = normalize_text(name)
            if not normalized_name:
                continue

            if normalized_name not in name_to_skus:
                name_to_skus[normalized_name] = []
            name_to_skus[normalized_name].append(sku)
            searchable_items.append((normalized_name, sku, name))

    return name_to_skus, searchable_items


def rebuild_indexes():
    sku_index = build_barcode_index()
    name_to_skus, searchable_items = build_name_index()

    SKU_TO_IMAGE_PATH.clear()
    SKU_TO_IMAGE_PATH.update(sku_index)
    NAME_TO_SKUS.clear()
    NAME_TO_SKUS.update(name_to_skus)
    SEARCHABLE_ITEMS.clear()
    SEARCHABLE_ITEMS.extend(searchable_items)


def find_name_matches(name_query, max_results=100):
    normalized_query = normalize_text(name_query)
    if not normalized_query:
        return []

    use_wildcard = '*' in name_query
    wildcard_pattern = ''
    if use_wildcard:
        wildcard_pattern = '^' + re.escape(normalized_query).replace('\\*', '.*') + '$'

    matched_items = []
    for normalized_name, sku, display_name in SEARCHABLE_ITEMS:
        if sku not in SKU_TO_IMAGE_PATH:
            continue

        is_match = False
        if use_wildcard:
            is_match = re.search(wildcard_pattern, normalized_name) is not None
        else:
            is_match = normalized_query in normalized_name

        if is_match:
            matched_items.append({'sku': sku, 'name': display_name})

    unique_matches = []
    seen_skus = set()
    for item in matched_items:
        sku = item['sku']
        if sku in seen_skus:
            continue
        seen_skus.add(sku)
        unique_matches.append(item)
        if len(unique_matches) >= max_results:
            break

    unique_matches.sort(key=lambda item: item['name'])
    return unique_matches


rebuild_indexes()

@app.route('/')
def index():
    return render_template('index.html', mode='name')

@app.route('/barcode')
def barcode_lookup():
    mode = request.args.get('mode', 'name').strip().lower()
    sku = request.args.get('sku', '').strip()
    name = request.args.get('name', '').strip()
    selected_sku = request.args.get('selected_sku', '').strip()

    resolved_sku = sku
    matches = []
    info = None
    if mode == 'name':
        if not name:
            return render_template('index.html', error='Please enter an item name.', mode='name', name=name, sku=sku)

        matches = find_name_matches(name)
        if not matches:
            return render_template('index.html', error=f'No item name match found for: {name}', mode='name', name=name, sku=sku)

        if selected_sku:
            valid_skus = {match['sku'] for match in matches}
            if selected_sku not in valid_skus:
                return render_template('index.html', error='Selected item is not in the current results.', mode='name', name=name, sku=sku, matches=matches)
            resolved_sku = selected_sku
            if len(matches) > 1:
                info = f'Found {len(matches)} matches for "{name}". Click an item to open barcode.'
        elif len(matches) > 1:
            return render_template(
                'index.html',
                mode='name',
                name=name,
                sku=sku,
                matches=matches,
                info=f'Found {len(matches)} matches for "{name}". Click an item to open barcode.'
            )
        else:
            resolved_sku = matches[0]['sku']
    else:
        if not sku:
            return render_template('index.html', error='Please enter a SKU.', mode='sku', name=name, sku=sku)

    rel_image_path = SKU_TO_IMAGE_PATH.get(resolved_sku)
    if not rel_image_path:
        return render_template('index.html', error=f'No barcode image found for SKU: {resolved_sku}', mode=mode, name=name, sku=sku)

    return render_template(
        'index.html',
        mode=mode,
        name=name,
        sku=resolved_sku,
        matches=matches,
        info=info,
        modal_open=True,
        modal_sku=resolved_sku,
        modal_image_path=rel_image_path
    )

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
    except (subprocess.CalledProcessError, OSError) as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

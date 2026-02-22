import fs from 'node:fs/promises';
import path from 'node:path';
import bwipjs from 'bwip-js';
import sharp from 'sharp';

const appRoot = process.cwd();
const csvPath = path.join(appRoot, 'items.csv');
const publicDir = path.join(appRoot, 'public');
const barcodePublicRoot = path.join(publicDir, 'barcodes');
const dataDir = path.join(publicDir, 'data');
const outputIndexPath = path.join(dataDir, 'index.json');
const TARGET_WIDTH = 295;
const TARGET_HEIGHT = 177;

function xmlEscape(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function normalizeText(text) {
  return (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim().replace(/\s+/g, ' ');
}

function cleanPathSegment(value, fallback = 'Uncategorized') {
  const cleaned = (value || '')
    .replace(/[<>:"/\\|?*&]/g, '')
    .trim()
    .replace(/\s+/g, '_');
  return cleaned || fallback;
}

function parseCsvLine(line) {
  const values = [];
  let current = '';
  let insideQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const nextChar = line[index + 1];

    if (char === '"') {
      if (insideQuotes && nextChar === '"') {
        current += '"';
        index += 1;
      } else {
        insideQuotes = !insideQuotes;
      }
      continue;
    }

    if (char === ',' && !insideQuotes) {
      values.push(current);
      current = '';
      continue;
    }

    current += char;
  }

  values.push(current);
  return values;
}

async function readItemsFromCsv() {
  const raw = await fs.readFile(csvPath, 'utf-8');
  const lines = raw.split(/\r?\n/).filter(Boolean);
  if (!lines.length) {
    return [];
  }

  const header = parseCsvLine(lines[0]);
  const skuIndex = header.indexOf('SKU');
  const nameIndex = header.indexOf('Name');
  const categoryIndex = header.indexOf('Category');
  const barcodeIndex = header.indexOf('Barcode');
  const priceIndex = header.indexOf("Price [Ant's Corner]");

  if (skuIndex < 0 || nameIndex < 0) {
    throw new Error('items.csv is missing SKU or Name headers.');
  }

  const items = [];
  for (let lineIndex = 1; lineIndex < lines.length; lineIndex += 1) {
    const row = parseCsvLine(lines[lineIndex]);
    const sku = (row[skuIndex] || '').trim();
    const name = (row[nameIndex] || '').trim();
    const category = (categoryIndex >= 0 ? row[categoryIndex] : '').trim();
    const barcode = (barcodeIndex >= 0 ? row[barcodeIndex] : '').trim();
    if (!sku || !name) {
      continue;
    }
    items.push({
      sku,
      name,
      category,
      barcode,
      price: (priceIndex >= 0 ? row[priceIndex] : '').trim(),
      normalizedName: normalizeText(name)
    });
  }

  return items;
}

async function ensureOutputDirs() {
  await fs.mkdir(barcodePublicRoot, { recursive: true });
  await fs.mkdir(dataDir, { recursive: true });
}

async function generateBarcodePng(barcodeText, productName, productPrice, outputPath) {
  const rawBarcodeBuffer = await bwipjs.toBuffer({
    bcid: 'code128',
    text: barcodeText,
    scale: 3,
    height: 10,
    includetext: true,
    textxalign: 'center',
    backgroundcolor: 'FFFFFF'
  });

  const barcodeBuffer = await sharp(rawBarcodeBuffer)
    .resize(TARGET_WIDTH - 12, TARGET_HEIGHT - 64, {
      fit: 'inside',
      withoutEnlargement: true
    })
    .png({ compressionLevel: 9 })
    .toBuffer();

  const barcodeMeta = await sharp(barcodeBuffer).metadata();
  const barcodeWidth = barcodeMeta.width || (TARGET_WIDTH - 12);
  const barcodeHeight = barcodeMeta.height || (TARGET_HEIGHT - 64);

  const barcodeTop = 30;
  const barcodeLeft = Math.max(0, Math.floor((TARGET_WIDTH - barcodeWidth) / 2));
  const priceText = productPrice ? `₱${productPrice}` : '';
  const safeName = xmlEscape(productName || '');
  const safePrice = xmlEscape(priceText);

  const nameSvg = Buffer.from(
    `<svg width="${TARGET_WIDTH}" height="24" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="white" />
      <text x="50%" y="17" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="14" fill="#000">${safeName}</text>
    </svg>`
  );

  const priceSvg = Buffer.from(
    `<svg width="${TARGET_WIDTH}" height="24" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="white" />
      <text x="50%" y="17" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="17" fill="#000">${safePrice}</text>
    </svg>`
  );

  const composedBuffer = await sharp({
    create: {
      width: TARGET_WIDTH,
      height: TARGET_HEIGHT,
      channels: 3,
      background: '#ffffff'
    }
  })
    .composite([
      { input: nameSvg, top: 2, left: 0 },
      { input: barcodeBuffer, top: barcodeTop, left: barcodeLeft },
      ...(productPrice ? [{ input: priceSvg, top: TARGET_HEIGHT - 24, left: 0 }] : [])
    ])
    .png({ compressionLevel: 9 })
    .toBuffer();

  await fs.writeFile(outputPath, composedBuffer);
}

async function buildImageMapping(items) {
  const skuToImagePath = {};
  let generatedCount = 0;

  for (const item of items) {
    if (!item.barcode) {
      continue;
    }

    const categoryFolder = cleanPathSegment(item.category, 'Uncategorized');
    const safeSku = cleanPathSegment(item.sku, item.sku);
    const safeBarcode = cleanPathSegment(item.barcode, item.barcode);
    const fileName = `${safeSku}-${safeBarcode}.png`;
    const categoryDir = path.join(barcodePublicRoot, categoryFolder);
    const outputPath = path.join(categoryDir, fileName);

    await fs.mkdir(categoryDir, { recursive: true });

    await generateBarcodePng(item.barcode, item.name, item.price, outputPath);
    generatedCount += 1;

    skuToImagePath[item.sku] = `/barcodes/${categoryFolder}/${fileName}`;
  }

  return { skuToImagePath, generatedCount };
}

async function main() {
  await ensureOutputDirs();
  const csvItems = await readItemsFromCsv();
  const { skuToImagePath, generatedCount } = await buildImageMapping(csvItems);

  const indexedItems = csvItems
    .map((item) => ({ ...item, imagePath: skuToImagePath[item.sku] || '' }))
    .filter((item) => Boolean(item.imagePath));

  const payload = {
    generatedAt: new Date().toISOString(),
    totalItems: indexedItems.length,
    items: indexedItems
  };

  await fs.writeFile(outputIndexPath, JSON.stringify(payload, null, 2), 'utf-8');
  process.stdout.write(`Prepared ${indexedItems.length} indexed items (${generatedCount} generated).\n`);
}

main().catch((error) => {
  process.stderr.write(`${error.message}\n`);
  process.exit(1);
});

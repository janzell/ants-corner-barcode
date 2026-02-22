# Ants Corner Barcode Finder (Netlify)

This is a JavaScript (React + Vite) version of the Barcode Finder built for Netlify static hosting.

## What it does

- Search by **Name** (default) with substring and `*` wildcard support
- Search by **SKU**
- Show multiple name matches in a clickable list
- Open barcode in a modal
- Open barcode image in a new tab for browser printing

## Project location

- App folder: `netlify-barcode-finder`

## Local run

```bash
cd netlify-barcode-finder
npm install
npm run dev
```

## Build

```bash
cd netlify-barcode-finder
npm install
npm run build
```

The build process runs `prepare:data`, which:

1. Reads `../items.csv`
2. Copies barcode PNG files from category folders into `public/barcodes`
3. Creates `public/data/index.json` for fast frontend search

## Netlify deployment

In Netlify site settings:

- Base directory: `netlify-barcode-finder`
- Build command: `npm run build`
- Publish directory: `dist`

Or keep `netlify.toml` in this folder and configure Base directory only.

## Notes

- This is static-hosting friendly and does not use Flask.
- "Preview Barcode" opens the image in a new tab instead of server-side print.

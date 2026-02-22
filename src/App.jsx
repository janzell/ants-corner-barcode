import React, { useEffect, useMemo, useState } from 'react';

function normalizeText(text) {
  return (text || '').toLowerCase().replace(/[^a-z0-9*]+/g, ' ').trim().replace(/\s+/g, ' ');
}

function wildcardToRegex(pattern) {
  const escaped = String(pattern || '')
    .split('')
    .map((char) => {
      if (char === '*') {
        return '.*';
      }
      return /[\\^$.*+?()[\]{}|]/.test(char) ? `\\${char}` : char;
    })
    .join('');

  try {
    return new RegExp(`^${escaped}$`);
  } catch {
    return null;
  }
}

export default function App() {
  const [mode, setMode] = useState('name');
  const [skuQuery, setSkuQuery] = useState('');
  const [nameQuery, setNameQuery] = useState('');
  const [items, setItems] = useState([]);
  const [skuToItem, setSkuToItem] = useState({});
  const [results, setResults] = useState([]);
  const [info, setInfo] = useState('');
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const onEsc = (event) => {
      if (event.key === 'Escape') {
        setSelected(null);
      }
    };
    window.addEventListener('keydown', onEsc);
    return () => window.removeEventListener('keydown', onEsc);
  }, []);

  useEffect(() => {
    async function loadIndex() {
      try {
        const response = await fetch('/data/index.json', { cache: 'no-store' });
        if (!response.ok) {
          throw new Error('Failed to load barcode index. Run prepare:data before deploy.');
        }
        const payload = await response.json();
        const loadedItems = Array.isArray(payload?.items) ? payload.items : [];
        const mapping = {};
        for (const item of loadedItems) {
          if (!item?.sku) {
            continue;
          }
          mapping[item.sku] = item;
        }
        setItems(loadedItems);
        setSkuToItem(mapping);
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setIsLoading(false);
      }
    }

    loadIndex();
  }, []);

  const resultCountLabel = useMemo(() => {
    if (!results.length) {
      return '';
    }
    return `Found ${results.length} matches. Click an item to view barcode.`;
  }, [results.length]);

  const runSearch = (event) => {
    event.preventDefault();
    setError('');
    setInfo('');
    setResults([]);

    if (mode === 'sku') {
      const sku = skuQuery.trim();
      if (!sku) {
        setError('Please enter a SKU.');
        return;
      }
      const found = skuToItem[sku];
      if (!found) {
        setError(`No barcode image found for SKU: ${sku}`);
        return;
      }
      setSelected(found);
      return;
    }

    const query = nameQuery.trim();
    if (!query) {
      setError('Please enter an item name.');
      return;
    }

    const normalizedQuery = normalizeText(query);
    if (!normalizedQuery) {
      setError('Please enter a valid item name.');
      return;
    }

    const hasWildcard = normalizedQuery.includes('*');
    const wildcardRegex = hasWildcard ? wildcardToRegex(normalizedQuery) : null;
    if (hasWildcard && !wildcardRegex) {
      setError('Invalid wildcard pattern.');
      return;
    }

    const matches = items.filter((item) => {
      if (!item.normalizedName) {
        return false;
      }
      if (hasWildcard) {
        return wildcardRegex.test(item.normalizedName);
      }
      return item.normalizedName.includes(normalizedQuery);
    });

    if (!matches.length) {
      setError(`No item name match found for: ${query}`);
      return;
    }

    if (matches.length === 1) {
      setSelected(matches[0]);
      return;
    }

    setResults(matches);
    setInfo(`Found ${matches.length} matches for "${query}". Click an item to open barcode.`);
  };

  const printBarcode = () => {
    if (!selected?.imagePath) {
      return;
    }
    const printFrame = document.createElement('iframe');
    printFrame.style.position = 'fixed';
    printFrame.style.right = '0';
    printFrame.style.bottom = '0';
    printFrame.style.width = '0';
    printFrame.style.height = '0';
    printFrame.style.border = '0';
    printFrame.setAttribute('aria-hidden', 'true');
    document.body.appendChild(printFrame);

    const frameWindow = printFrame.contentWindow;
    const frameDocument = frameWindow?.document;
    if (!frameWindow || !frameDocument) {
      setError('Unable to open print dialog. Please try again.');
      document.body.removeChild(printFrame);
      return;
    }

    frameDocument.open();
    frameDocument.write(`
      <!doctype html>
      <html>
        <head>
          <title>Print Barcode - SKU ${selected.sku}</title>
          <style>
            html, body { margin: 0; padding: 0; background: #fff; }
            body { display: flex; align-items: center; justify-content: center; min-height: 100vh; }
            img { max-width: 100%; height: auto; }
            @page { margin: 12mm; }
          </style>
        </head>
        <body>
          <img id="barcode-image" src="${selected.imagePath}" alt="Barcode for SKU ${selected.sku}" />
        </body>
      </html>
    `);
    frameDocument.close();

    const imageElement = frameDocument.getElementById('barcode-image');
    if (!imageElement) {
      setError('Unable to prepare print content. Please try again.');
      document.body.removeChild(printFrame);
      return;
    }

    imageElement.addEventListener('load', () => {
      frameWindow.focus();
      frameWindow.print();
      setTimeout(() => {
        if (document.body.contains(printFrame)) {
          document.body.removeChild(printFrame);
        }
      }, 1000);
    });
  };

  return (
    <>
      <div className="container">
        <div className="brand-header">
          <img
            className="brand-logo"
            src="https://antscorner.store/_image?href=%2F_astro%2Flogo.D8MiuDQd.png&f=webp"
            alt="Ants Corner logo"
          />
          <h1 className="brand-gradient-text">Ants Corner Barcode Finder</h1>
        </div>

        <form onSubmit={runSearch}>
          <div className="mode-picker">
            <label>
              <input
                type="radio"
                name="mode"
                value="name"
                checked={mode === 'name'}
                onChange={() => setMode('name')}
              />
              Search by Name
            </label>
            <label>
              <input
                type="radio"
                name="mode"
                value="sku"
                checked={mode === 'sku'}
                onChange={() => setMode('sku')}
              />
              Search by SKU
            </label>
          </div>

          <input
            type="text"
            placeholder="Enter SKU"
            value={skuQuery}
            onChange={(event) => setSkuQuery(event.target.value)}
          />
          <input
            type="text"
            placeholder="Enter item name"
            value={nameQuery}
            onChange={(event) => setNameQuery(event.target.value)}
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Loading...' : 'Search'}
          </button>
        </form>

        {info && <div className="info">{info}</div>}
        {resultCountLabel && !info && <div className="info">{resultCountLabel}</div>}
        {error && <div className="error">{error}</div>}

        {!!results.length && (
          <div className="results">
            <h3>Matching items</h3>
            <ul>
              {results.map((item) => (
                <li key={item.sku}>
                  <button type="button" className="link-button" onClick={() => setSelected(item)}>
                    {item.name} (SKU {item.sku})
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className={`modal-overlay ${selected ? 'open' : ''}`} onClick={(event) => event.target === event.currentTarget && setSelected(null)}>
        <div className="modal">
          <h2>Barcode for SKU: {selected?.sku || ''}</h2>
          {selected?.imagePath && <img src={selected.imagePath} alt={`Barcode for SKU ${selected.sku}`} />}
          <div className="modal-actions">
            <button type="button" onClick={printBarcode}>Print</button>
            <button type="button" className="button-secondary" onClick={() => setSelected(null)}>
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

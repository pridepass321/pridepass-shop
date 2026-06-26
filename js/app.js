const HUE_PRESETS = [
    { label: 'Original', hue: 0, saturation: 100 },
    { label: 'Warm Gold', hue: 30, saturation: 110 },
    { label: 'Rose', hue: 320, saturation: 105 },
    { label: 'Emerald', hue: 90, saturation: 105 },
    { label: 'Ocean', hue: 180, saturation: 110 },
    { label: 'Violet', hue: 270, saturation: 105 }
];

let state = {
    identityId: 'omnisexual',
    name: 'Alex Rivera',
    memberNumber: 'LGB-2026-0847',
    communitySince: '2026',
    pronouns: 'they/them',
    photo: null,
    photoFile: null,
    customBack: false,
    customBackImage: null,
    customBackFile: null,
    shippingMethod: 'standard',
    customerEmail: '',
    hue: 0,
    saturation: 100,
    previewSide: 'front',
    mode: 'builder'
};

let shopConfig = { stripePublishableKey: '' };

let batchPhotos = new Map();

function $(id) {
    return document.getElementById(id);
}

function setMode(mode) {
    state.mode = mode;
    $('panel-builder').classList.toggle('hidden', mode !== 'builder');
    $('panel-batch').classList.toggle('hidden', mode !== 'batch');
    $('tab-builder').classList.toggle('nav-active', mode === 'builder');
    $('tab-batch').classList.toggle('nav-active', mode === 'batch');
}

function buildHuePresets() {
    const container = $('hue-presets');
    if (!container) return;
    container.innerHTML = HUE_PRESETS.map(p => `
        <button type="button" onclick="applyHuePreset(${p.hue}, ${p.saturation})"
            class="hue-preset px-3 py-1.5 rounded-full text-xs font-medium transition-all"
            data-hue="${p.hue}">${p.label}</button>
    `).join('');
    updateHuePresetActive();
}

function updateHuePresetActive() {
    document.querySelectorAll('.hue-preset').forEach(btn => {
        const match = Number(btn.dataset.hue) === state.hue;
        btn.classList.toggle('hue-preset-active', match);
    });
}

function applyHuePreset(hue, saturation) {
    state.hue = hue;
    state.saturation = saturation;
    $('input-hue').value = hue;
    $('input-saturation').value = saturation;
    $('hue-value').textContent = `${hue}°`;
    $('saturation-value').textContent = `${saturation}%`;
    updateHuePresetActive();
    updatePreview();
}

function onHueChange(value) {
    state.hue = Number(value) || 0;
    $('hue-value').textContent = `${state.hue}°`;
    updateHuePresetActive();
    updatePreview();
}

function onSaturationChange(value) {
    state.saturation = Number(value) || 100;
    $('saturation-value').textContent = `${state.saturation}%`;
    updatePreview();
}

function buildIdentitySelect() {
    const select = $('input-identity');
    const groups = [
        ['Core Community Cards', CORE_IDENTITIES],
        ['Sexual Orientations', SEXUAL_IDENTITIES],
        ['Romantic Orientations', ROMANTIC_IDENTITIES],
        ['Gender Identities', GENDER_IDENTITIES]
    ];

    select.innerHTML = '';
    for (const [label, items] of groups) {
        const group = document.createElement('optgroup');
        group.label = label;
        for (const item of items) {
            const opt = document.createElement('option');
            opt.value = item.id;
            opt.textContent = item.label;
            group.appendChild(opt);
        }
        select.appendChild(group);
    }
    select.value = state.identityId;
}

let galleryFilter = 'all';

function buildCardGallery() {
    const gallery = $('card-gallery');
    if (!gallery) return;

    const filtered = galleryFilter === 'all'
        ? ALL_IDENTITIES
        : ALL_IDENTITIES.filter(i => i.category === galleryFilter);

    gallery.innerHTML = filtered.map(identity => {
        const active = state.identityId === identity.id ? ' active' : '';
        const cat = identity.category !== 'Core' ? identity.category : '';
        return `
            <button type="button" onclick="selectTheme('${identity.id}')"
                class="gallery-card${active}" data-id="${identity.id}" title="${identity.label}">
                <img src="${getIdentityImagePath(identity.id)}" alt="${identity.label}" loading="lazy">
                <div class="gallery-card-label">
                    ${identity.label}
                    ${cat ? `<span class="gallery-card-cat">${cat}</span>` : ''}
                </div>
            </button>`;
    }).join('');

    scrollToSelectedCard();
}

function setGalleryFilter(category) {
    galleryFilter = category;
    document.querySelectorAll('.gallery-filter').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.filter === category);
    });
    buildCardGallery();
}

function scrollToSelectedCard() {
    const gallery = $('card-gallery');
    if (!gallery) return;
    const active = gallery.querySelector('.gallery-card.active');
    if (active) {
        active.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
}

function selectTheme(id) {
    state.identityId = id;
    $('input-identity').value = id;
    updateFieldVisibility();

    const identity = IDENTITY_BY_ID[id];
    if (identity && galleryFilter !== 'all' && identity.category !== galleryFilter) {
        galleryFilter = identity.category;
        document.querySelectorAll('.gallery-filter').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.filter === identity.category);
        });
        buildCardGallery();
    } else {
        document.querySelectorAll('.gallery-card').forEach(el => {
            el.classList.toggle('active', el.dataset.id === id);
        });
        scrollToSelectedCard();
    }

    updatePreviewLabel();
    updateMeaning();
    updatePreview();
}

function updateFieldVisibility() {
    const identity = IDENTITY_BY_ID[state.identityId];
    const isMember = identity.fieldType === 'member';
    $('field-member').classList.toggle('hidden', !isMember);
    $('field-community').classList.toggle('hidden', isMember);
}

function updateMeaning() {
    const identity = IDENTITY_BY_ID[state.identityId];
    const el = $('identity-meaning');
    if (identity.meaning) {
        el.textContent = identity.meaning;
        el.classList.remove('hidden');
    } else {
        el.classList.add('hidden');
    }
}

function updatePreviewLabel() {
    const identity = IDENTITY_BY_ID[state.identityId];
    const el = $('preview-identity-label');
    if (el && identity) el.textContent = identity.label;
}

function getCardOptions() {
    return {
        identityId: state.identityId,
        name: state.name,
        memberNumber: state.memberNumber,
        communitySince: state.communitySince,
        pronouns: state.pronouns,
        photo: state.photo,
        hue: state.hue,
        saturation: state.saturation,
        customBack: state.customBack,
        customBackImage: state.customBackImage
    };
}

function toggleCustomBack() {
    state.customBack = !state.customBack;
    const addon = $('addon-custom-back');
    const icon = $('addon-check-icon');
    const upload = $('custom-back-upload');
    addon?.classList.toggle('selected', state.customBack);
    icon?.classList.toggle('hidden', !state.customBack);
    upload?.classList.toggle('hidden', !state.customBack);
    if (!state.customBack) clearCustomBack(false);
    updateShippingUI();
    updateOrderSummary();
    updateBackBadge();
    if (state.previewSide === 'back') updatePreview();
}

function setShipping(method) {
    state.shippingMethod = method;
    document.querySelectorAll('.shipping-option').forEach(el => {
        el.classList.toggle('selected', el.dataset.shipping === method);
    });
    updateOrderSummary();
}

function updateShippingUI() {
    const shipSection = $('shipping-section');
    const freeBanner = $('free-shipping-banner');
    if (state.customBack) {
        shipSection?.classList.add('hidden');
        freeBanner?.classList.remove('hidden');
    } else {
        shipSection?.classList.remove('hidden');
        freeBanner?.classList.add('hidden');
    }
}

function updateBackBadge() {
    const badge = $('back-status-badge');
    if (!badge) return;
    if (state.customBack) {
        badge.innerHTML = state.customBackImage
            ? '<i class="fa-solid fa-image mr-1 text-fuchsia-400"></i>Custom back ready'
            : '<i class="fa-solid fa-upload mr-1 text-violet-400"></i>Upload your custom back below';
        badge.classList.remove('back-locked-badge');
        badge.classList.add('text-fuchsia-300', 'text-xs');
    } else {
        badge.innerHTML = `<i class="fa-solid fa-lock mr-1"></i>Front only — add custom back +${formatMoney(PRICING.customBack)}`;
        badge.className = 'back-locked-badge';
    }
}

function updateOrderSummary() {
    const { total, lines } = calcOrderTotal(state.customBack, state.shippingMethod);
    $('sum-card').textContent = formatMoney(PRICING.card);
    $('sum-back-row')?.classList.toggle('hidden', !state.customBack);
    if (state.customBack) $('sum-back').textContent = formatMoney(PRICING.customBack);

    const shipRow = $('sum-ship-row');
    if (state.customBack) {
        $('sum-ship-label').textContent = 'Shipping';
        $('sum-ship').textContent = 'FREE';
        shipRow?.classList.remove('hidden');
    } else {
        const shipLine = lines.find(l => l.label.includes('shipping'));
        $('sum-ship-label').textContent = shipLine?.label || 'Shipping';
        $('sum-ship').textContent = formatMoney(shipLine?.amount || 0);
        shipRow?.classList.remove('hidden');
    }

    $('sum-total').textContent = formatMoney(total);
    $('btn-checkout-total').textContent = formatMoney(total);
    $('hero-price') && ($('hero-price').textContent = formatMoney(PRICING.card));
}

function checkFrontPhotoDims(img) {
    const side = Math.min(img.naturalWidth || img.width, img.naturalHeight || img.height);
    const el = $('photo-dim-status');
    if (!el) return;
    if (side >= IMAGE_SPECS.front.ideal) {
        el.className = 'photo-ok';
        el.textContent = `${img.naturalWidth}×${img.naturalHeight} — great for 300 DPI`;
    } else if (side >= IMAGE_SPECS.front.min) {
        el.className = 'photo-warn';
        el.textContent = `${img.naturalWidth}×${img.naturalHeight} — OK; ${IMAGE_SPECS.front.ideal}×${IMAGE_SPECS.front.ideal}+ is sharper`;
    } else {
        el.className = 'photo-warn';
        el.textContent = `${img.naturalWidth}×${img.naturalHeight} — below 300 DPI minimum (${IMAGE_SPECS.front.min}×${IMAGE_SPECS.front.min})`;
    }
}

function checkBackPhotoDims(img) {
    const w = img.naturalWidth || img.width;
    const h = img.naturalHeight || img.height;
    const el = $('back-dim-status');
    if (!el) return;
    const { width: needW, height: needH } = IMAGE_SPECS.back;
    if (w >= needW && h >= needH) {
        el.className = 'photo-ok';
        el.textContent = `${w}×${h} — ready for 300 DPI print`;
    } else {
        el.className = 'photo-warn';
        el.textContent = `${w}×${h} — need at least ${needW}×${needH} px @ 300 DPI`;
    }
}

async function handleCustomBackUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    state.customBackFile = file;
    state.customBackImage = await loadPhotoFromFile(file);
    $('back-preview-container')?.classList.remove('hidden');
    $('back-preview-container')?.classList.add('flex');
    $('back-preview-img').src = URL.createObjectURL(file);
    checkBackPhotoDims(state.customBackImage);
    updateBackBadge();
    if (state.previewSide === 'back') updatePreview();
}

function clearCustomBack(clearAddon = true) {
    state.customBackImage = null;
    state.customBackFile = null;
    $('back-photo-input') && ($('back-photo-input').value = '');
    $('back-preview-container')?.classList.add('hidden');
    $('back-preview-container')?.classList.remove('flex');
    if (clearAddon && state.customBack) toggleCustomBack();
    else updateBackBadge();
    if (state.previewSide === 'back') updatePreview();
}

async function proceedToCheckout() {
    const btn = $('btn-checkout');
    const email = ($('input-email')?.value || '').trim();
    if (!state.name.trim()) {
        alert('Please enter your full name on the card.');
        $('input-name')?.focus();
        return;
    }
    if (!email || !email.includes('@')) {
        alert('Please enter a valid email for your order confirmation.');
        $('input-email')?.focus();
        return;
    }
    if (state.customBack && !state.customBackFile) {
        alert('Please upload your custom back image (1011×638 px @ 300 DPI), or remove the custom back add-on.');
        return;
    }
    if (state.customBackFile && state.customBackImage) {
        const w = state.customBackImage.naturalWidth || state.customBackImage.width;
        const h = state.customBackImage.naturalHeight || state.customBackImage.height;
        if (w < IMAGE_SPECS.back.width || h < IMAGE_SPECS.back.height) {
            const ok = confirm(`Your back image is ${w}×${h} px. For crisp 300 DPI print we need ${IMAGE_SPECS.back.width}×${IMAGE_SPECS.back.height} px. Continue anyway?`);
            if (!ok) return;
        }
    }
    if (state.photoFile && state.photo) {
        const side = Math.min(state.photo.naturalWidth || state.photo.width, state.photo.naturalHeight || state.photo.height);
        if (side < IMAGE_SPECS.front.min) {
            const ok = confirm(`Your front photo is small for 300 DPI circle print (min ${IMAGE_SPECS.front.min}×${IMAGE_SPECS.front.min} px). Continue anyway?`);
            if (!ok) return;
        }
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i><span>Preparing secure checkout…</span>';

    try {
        const identity = IDENTITY_BY_ID[state.identityId];
        const order = {
            customBack: state.customBack,
            shippingMethod: state.shippingMethod,
            card: {
                identityId: state.identityId,
                identity_label: identity?.label || state.identityId,
                name: state.name,
                memberNumber: state.memberNumber,
                communitySince: state.communitySince,
                pronouns: state.pronouns,
                hue: state.hue,
                saturation: state.saturation
            },
            customer: { email, name: state.name }
        };

        const form = new FormData();
        form.append('order', JSON.stringify(order));
        if (state.photoFile) form.append('front_photo', state.photoFile);
        if (state.customBackFile) form.append('custom_back', state.customBackFile);

        const res = await fetch('/api/create-checkout-session', { method: 'POST', body: form });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Checkout failed');

        if (data.url) {
            window.location.href = data.url;
            return;
        }
        throw new Error('No checkout URL returned');
    } catch (err) {
        alert(err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-lock"></i><span>Order Now — <span id="btn-checkout-total">${$('sum-total')?.textContent || ''}</span></span>`;
    }
}

async function loadShopConfig() {
    try {
        const res = await fetch('/api/config');
        if (!res.ok) return;
        shopConfig = await res.json();
        if (shopConfig.pricing) {
            Object.assign(PRICING, shopConfig.pricing);
        }
        updateOrderSummary();
    } catch (_) { /* offline / static preview */ }
}

async function updatePreview() {
    const canvas = $('card-preview-canvas');
    await renderPreview(canvas, state.previewSide, getCardOptions());
}

function switchPreviewSide(side) {
    state.previewSide = side;
    $('btn-front').classList.toggle('nav-active', side === 'front');
    $('btn-back').classList.toggle('nav-active', side === 'back');
    $('btn-front').classList.toggle('dim-tab', side !== 'front');
    $('btn-back').classList.toggle('dim-tab', side !== 'back');
    updatePreview();
}

async function handlePhotoUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    state.photoFile = file;
    state.photo = await loadPhotoFromFile(file);
    $('photo-preview-container').classList.remove('hidden');
    $('photo-preview-container').classList.add('flex');
    $('photo-preview-img').src = URL.createObjectURL(file);
    checkFrontPhotoDims(state.photo);
    updatePreview();
}

function clearPhoto() {
    state.photo = null;
    state.photoFile = null;
    $('photo-input').value = '';
    $('photo-preview-container').classList.add('hidden');
    $('photo-preview-container').classList.remove('flex');
    updatePreview();
}

function parseCsv(text) {
    const rows = [];
    let row = [];
    let cell = '';
    let inQuotes = false;

    for (let i = 0; i < text.length; i++) {
        const ch = text[i];
        const next = text[i + 1];
        if (inQuotes) {
            if (ch === '"' && next === '"') { cell += '"'; i++; }
            else if (ch === '"') inQuotes = false;
            else cell += ch;
        } else if (ch === '"') {
            inQuotes = true;
        } else if (ch === ',') {
            row.push(cell.trim());
            cell = '';
        } else if (ch === '\n' || ch === '\r') {
            if (ch === '\r' && next === '\n') i++;
            row.push(cell.trim());
            if (row.some(v => v)) rows.push(row);
            row = [];
            cell = '';
        } else {
            cell += ch;
        }
    }
    if (cell || row.length) {
        row.push(cell.trim());
        if (row.some(v => v)) rows.push(row);
    }
    return rows;
}

function normalizeHeader(header) {
    return normalizeKey(header)
        .replace(/^community-since$/, 'community_since')
        .replace(/^member-number$/, 'member_number')
        .replace(/^member-no$/, 'member_number')
        .replace(/^order-id$/, 'order_id')
        .replace(/^photo-filename$/, 'photo');
}

function isInstructionRow(row) {
    const first = String(row[0] || '').toLowerCase();
    return first.includes('optional') || first.includes('required') || first === 'order_id';
}

function rowsToObjects(rows) {
    if (!rows.length) return [];
    let headerIndex = 0;
    for (let i = 0; i < Math.min(rows.length, 5); i++) {
        if (normalizeHeader(rows[i][0]) === 'name' || normalizeHeader(rows[i][0]) === 'order-id') {
            headerIndex = i;
            break;
        }
    }
    const headers = rows[headerIndex].map(normalizeHeader);
    return rows.slice(headerIndex + 1)
        .filter(row => row.some(v => v) && !isInstructionRow(row))
        .map(cells => {
            const obj = {};
            headers.forEach((h, i) => { obj[h] = cells[i] ?? ''; });
            return obj;
        });
}

async function parseSpreadsheet(file) {
    const name = file.name.toLowerCase();
    if (name.endsWith('.csv') || name.endsWith('.tsv')) {
        const text = await file.text();
        return rowsToObjects(parseCsv(text));
    }
    if (name.endsWith('.xlsx') || name.endsWith('.xls')) {
        const data = await file.arrayBuffer();
        const workbook = XLSX.read(data, { type: 'array' });
        const sheetName = workbook.SheetNames.find(n => n.toLowerCase() === 'orders') || workbook.SheetNames[0];
        const sheet = workbook.Sheets[sheetName];
        const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });
        return rowsToObjects(rows);
    }
    throw new Error('Upload a CSV or Excel (.xlsx) file.');
}

async function handleBatchPhotos(event) {
    batchPhotos.clear();
    const files = Array.from(event.target.files || []);
    for (const file of files) {
        batchPhotos.set(file.name.toLowerCase(), file);
    }
    $('batch-photo-count').textContent = files.length ? `${files.length} photo(s) loaded` : 'No photos loaded';
}

function resolveBatchPhoto(row) {
    const filename = String(row.photo || row.photo_filename || row.image || '').trim().toLowerCase();
    if (!filename) return null;
    const file = batchPhotos.get(filename) || batchPhotos.get(filename.split(/[\\/]/).pop());
    return file || null;
}

async function processBatchPython() {
    const spreadsheet = $('batch-spreadsheet').files?.[0];
    if (!spreadsheet) {
        alert('Upload an orders spreadsheet first.');
        return;
    }

    const log = $('batch-log');
    const btn = $('btn-batch-python');
    btn.disabled = true;
    log.innerHTML = '<div class="log-muted">Python engine processing…</div>';

    try {
        const form = new FormData();
        form.append('spreadsheet', spreadsheet);
        form.append('include_back', $('batch-include-back').checked ? 'true' : 'false');
        const photoInput = $('batch-photos');
        for (const file of photoInput.files || []) {
            form.append('photos', file);
        }

        const res = await fetch('/api/batch-print', { method: 'POST', body: form });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ error: res.statusText }));
            throw new Error(err.error || 'Python batch print failed');
        }

        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `lgbtiqasb-batch-${new Date().toISOString().slice(0, 10)}.pdf`;
        a.click();

        log.innerHTML = `
            <div class="log-success font-medium">PDF generated via Python (server-side)</div>
            <div class="log-muted text-sm mt-1">Faster for large batches • CR80 • Evolis Primacy 2 ready</div>
        `;
    } catch (err) {
        log.innerHTML = `<div class="log-error">${err.message}</div>
            <div class="log-muted text-sm mt-2">Tip: run <code class="text-violet-300">python scripts/batch_print.py orders.xlsx</code> from terminal, or use Browser PDF below.</div>`;
    } finally {
        btn.disabled = false;
    }
}

async function processBatch() {
    const spreadsheet = $('batch-spreadsheet').files?.[0];
    if (!spreadsheet) {
        alert('Upload an orders spreadsheet first.');
        return;
    }

    const log = $('batch-log');
    const btn = $('btn-batch-run');
    btn.disabled = true;
    log.innerHTML = '<div class="log-muted">Browser processing orders…</div>';

    try {
        const rows = await parseSpreadsheet(spreadsheet);
        const cards = [];
        const errors = [];

        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const identity = resolveIdentity(row.identity || row.card || row.design);
            if (!identity) {
                errors.push(`Row ${i + 2}: unknown identity "${row.identity || row.card || row.design}"`);
                continue;
            }

            let photo = null;
            const photoFile = resolveBatchPhoto(row);
            if (photoFile) photo = await loadPhotoFromFile(photoFile);
            else if (row.photo_base64) photo = await loadPhotoFromDataUrl(row.photo_base64);

            cards.push({
                identityId: identity.id,
                name: row.name || row.full_name || '',
                memberNumber: row.member_number || row.member || '',
                communitySince: row.community_since || row.since || row.year || '2026',
                pronouns: row.pronouns || '',
                photo,
                hue: Number(row.hue ?? 0) || 0,
                saturation: Number(row.saturation ?? 100) || 100
            });
        }

        if (!cards.length) {
            log.innerHTML = `<div class="log-error">No valid orders found.</div>${errors.map(e => `<div class="log-warn text-sm">${e}</div>`).join('')}`;
            return;
        }

        const includeBack = $('batch-include-back').checked;
        const pdf = await exportCardsPdf(cards, includeBack);
        pdf.save(`lgbtiqasb-batch-${new Date().toISOString().slice(0, 10)}.pdf`);

        log.innerHTML = `
            <div class="log-success font-medium">${cards.length} card(s) exported to PDF</div>
            <div class="log-muted text-sm mt-1">CR80 • 85.6 × 53.98 mm • Evolis Primacy 2 ready</div>
            ${errors.length ? `<div class="mt-3 log-warn text-sm">${errors.length} row(s) skipped</div>` : ''}
            ${errors.map(e => `<div class="log-warn text-sm">${e}</div>`).join('')}
        `;
    } catch (err) {
        log.innerHTML = `<div class="log-error">${err.message}</div>`;
    } finally {
        btn.disabled = false;
    }
}

function downloadBatchTemplate(format = 'xlsx') {
    if (format === 'xlsx') {
        window.open('templates/lgbtiqasb-orders-template.xlsx', '_blank');
        return;
    }

    const headers = ['order_id', 'name', 'identity', 'pronouns', 'member_number', 'community_since', 'hue', 'photo', 'notes'];
    const desc = ['Optional', 'Required', 'Required — see Valid Identities', 'Optional', 'Core cards only', 'Identity cards only', '0-360 colour shift', 'Photo filename', 'Not printed'];
    const examples = [
        ['ORD-001', 'Alex Rivera', 'Omnisexual', 'they/them', '', '2024', '0', 'alex.jpg', ''],
        ['ORD-002', 'Sam Chen', 'Demigirl', 'she/they', '', '2025', '45', 'sam.png', 'Warm hue'],
        ['ORD-003', 'Jordan Lee', 'Pride', 'he/him', 'LGB-2026-0001', '', '0', '', 'Core card']
    ];
    const csv = [headers, desc, ...examples].map(r => r.map(v => `"${v}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'lgbtiqasb-orders-template.csv';
    a.click();
}

function showInfoModal() {
    $('info-modal').classList.remove('hidden');
}

function hideInfoModal() {
    $('info-modal').classList.add('hidden');
}

function bindEvents() {
    $('input-name').addEventListener('input', e => { state.name = e.target.value; updatePreview(); });
    $('input-member').addEventListener('input', e => { state.memberNumber = e.target.value; updatePreview(); });
    $('input-community').addEventListener('input', e => { state.communitySince = e.target.value; updatePreview(); });
    $('input-pronouns').addEventListener('change', e => { state.pronouns = e.target.value; updatePreview(); });
    $('input-hue').addEventListener('input', e => onHueChange(e.target.value));
    $('input-saturation').addEventListener('input', e => onSaturationChange(e.target.value));
    $('input-identity').addEventListener('change', e => {
        selectTheme(e.target.value);
    });
    $('input-email')?.addEventListener('input', e => { state.customerEmail = e.target.value; });
}

async function initializeApp() {
    await loadShopConfig();
    buildIdentitySelect();
    buildCardGallery();
    buildHuePresets();
    updateFieldVisibility();
    updatePreviewLabel();
    updateMeaning();
    updateShippingUI();
    updateOrderSummary();
    updateBackBadge();
    bindEvents();
    await updatePreview();
}

window.selectTheme = selectTheme;
window.setGalleryFilter = setGalleryFilter;
window.switchPreviewSide = switchPreviewSide;
window.handlePhotoUpload = handlePhotoUpload;
window.clearPhoto = clearPhoto;
window.toggleCustomBack = toggleCustomBack;
window.setShipping = setShipping;
window.handleCustomBackUpload = handleCustomBackUpload;
window.clearCustomBack = clearCustomBack;
window.proceedToCheckout = proceedToCheckout;
window.setMode = setMode;
window.processBatch = processBatch;
window.processBatchPython = processBatchPython;
window.handleBatchPhotos = handleBatchPhotos;
window.downloadBatchTemplate = downloadBatchTemplate;
window.applyHuePreset = applyHuePreset;
window.showInfoModal = showInfoModal;
window.hideInfoModal = hideInfoModal;
window.updatePreview = updatePreview;

window.onload = initializeApp;
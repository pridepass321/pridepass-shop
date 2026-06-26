const imageCache = new Map();
const PREVIEW_SCALE = 0.5;

function buildHueFilter(hue = 0, saturation = 100) {
    const h = Number(hue) || 0;
    const s = Math.max(50, Math.min(150, Number(saturation) || 100));
    if (h === 0 && s === 100) return 'none';
    return `hue-rotate(${h}deg) saturate(${s / 100})`;
}

function drawBackgroundWithHue(ctx, img, width, height, hue, saturation) {
    const filter = buildHueFilter(hue, saturation);
    if (filter === 'none') {
        ctx.drawImage(img, 0, 0, width, height);
        return;
    }
    ctx.save();
    ctx.filter = filter;
    ctx.drawImage(img, 0, 0, width, height);
    ctx.restore();
}

/** Instant live preview — CSS filter on the card frame (no canvas redraw). */
function applyPreviewHueFilter(hue = 0, saturation = 100, enabled = true) {
    const frame = document.querySelector('.preview-hero .card-frame');
    if (!frame) return;
    if (!enabled) {
        frame.style.filter = 'none';
        return;
    }
    const filter = buildHueFilter(hue, saturation);
    frame.style.filter = filter === 'none' ? 'none' : filter;
}

function loadImage(src) {
    if (imageCache.has(src)) return imageCache.get(src);
    const promise = new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error(`Failed to load image: ${src}`));
        img.src = src;
    });
    imageCache.set(src, promise);
    return promise;
}

function resolveLayout(layout, width, height) {
    return {
        photo: {
            cx: layout.photo.cx * width,
            cy: layout.photo.cy * height,
            r: layout.photo.r * height
        },
        name: {
            x: layout.name.x * width,
            y: layout.name.y * height,
            maxWidth: layout.name.maxWidth * width,
            fontSize: layout.name.fontSize * height
        },
        field2: {
            x: layout.field2.x * width,
            y: layout.field2.y * height,
            maxWidth: layout.field2.maxWidth * width,
            fontSize: layout.field2.fontSize * height
        },
        pronouns: {
            x: layout.pronouns.x * width,
            y: layout.pronouns.y * height,
            fontSize: layout.pronouns.fontSize * height
        }
    };
}

function fitText(ctx, text, maxWidth, fontSize, fontWeight = '700') {
    let size = fontSize;
    ctx.font = `${fontWeight} ${size}px Inter, system-ui, sans-serif`;
    while (ctx.measureText(text).width > maxWidth && size > 12) {
        size -= 1;
        ctx.font = `${fontWeight} ${size}px Inter, system-ui, sans-serif`;
    }
    return size;
}

function drawCircularPhoto(ctx, photo, resolved) {
    if (!photo) return;
    const { cx, cy, r } = resolved.photo;
    const pw = photo.naturalWidth || photo.width;
    const ph = photo.naturalHeight || photo.height;
    if (!pw || !ph) return;

    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.closePath();
    ctx.clip();

    const size = r * 2;
    const aspect = pw / ph;
    let drawW, drawH;
    if (aspect >= 1) {
        drawH = size;
        drawW = size * aspect;
    } else {
        drawW = size;
        drawH = size / aspect;
    }
    ctx.drawImage(photo, cx - drawW / 2, cy - drawH / 2, drawW, drawH);
    ctx.restore();
}

function drawFieldText(ctx, text, box, color = '#f8fafc') {
    if (!text) return;
    const size = fitText(ctx, text, box.maxWidth, box.fontSize);
    ctx.fillStyle = color;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.shadowColor = 'rgba(0,0,0,0.65)';
    ctx.shadowBlur = 6;
    ctx.fillText(text, box.x, box.y);
    ctx.shadowBlur = 0;
}

function buildLayoutForIdentity(identityId, width, height) {
    const photoLayout = getPhotoLayout(identityId);
    const layout = {
        ...CARD_LAYOUT,
        photo: photoLayout
    };
    return resolveLayout(layout, width, height);
}

async function renderCardFront(options) {
    const {
        identityId,
        name = '',
        memberNumber = '',
        memberSince = '',
        communitySince = '',
        pronouns = '',
        photo = null,
        hue = 0,
        saturation = 100,
        previewScale = 1,
        overlayText = true,
        applyHue = true
    } = options;

    const identity = IDENTITY_BY_ID[identityId];
    if (!identity) throw new Error(`Unknown identity: ${identityId}`);

    const bg = await loadImage(getIdentityImagePath(identityId));
    const fullW = bg.naturalWidth || CARD_LAYOUT.width;
    const fullH = bg.naturalHeight || CARD_LAYOUT.height;
    const scale = Math.max(0.25, Math.min(1, Number(previewScale) || 1));
    const canvasW = Math.round(fullW * scale);
    const canvasH = Math.round(fullH * scale);

    const canvas = document.createElement('canvas');
    canvas.width = canvasW;
    canvas.height = canvasH;
    const ctx = canvas.getContext('2d');
    const resolved = buildLayoutForIdentity(identityId, canvasW, canvasH);

    const renderHue = applyHue ? hue : 0;
    const renderSat = applyHue ? saturation : 100;
    drawBackgroundWithHue(ctx, bg, canvasW, canvasH, renderHue, renderSat);

    if (photo) drawCircularPhoto(ctx, photo, resolved);

    if (overlayText) {
        drawFieldText(ctx, name, resolved.name);
        const sinceValue = memberSince || communitySince || memberNumber;
        drawFieldText(ctx, sinceValue, resolved.field2);

        if (CARD_LAYOUT.pronouns?.enabled !== false && pronouns && pronouns !== 'name only') {
            ctx.font = `500 ${resolved.pronouns.fontSize}px Inter, system-ui, sans-serif`;
            ctx.fillStyle = 'rgba(248,250,252,0.85)';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'alphabetic';
            ctx.fillText(pronouns, resolved.pronouns.x, resolved.pronouns.y);
        }
    }

    return canvas;
}

function renderCardBackCustom(customBackImage, width = CARD_LAYOUT.width, height = CARD_LAYOUT.height) {
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    const imgAspect = customBackImage.width / customBackImage.height;
    const cardAspect = width / height;
    let drawW, drawH, drawX, drawY;
    if (imgAspect >= cardAspect) {
        drawH = height;
        drawW = height * imgAspect;
        drawX = (width - drawW) / 2;
        drawY = 0;
    } else {
        drawW = width;
        drawH = width / imgAspect;
        drawX = 0;
        drawY = (height - drawH) / 2;
    }
    ctx.drawImage(customBackImage, drawX, drawY, drawW, drawH);
    return canvas;
}

function renderCardBackLocked(width = CARD_LAYOUT.width, height = CARD_LAYOUT.height, hasAddon = false) {
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');

    const grad = ctx.createLinearGradient(0, 0, width, height);
    grad.addColorStop(0, '#0a0a12');
    grad.addColorStop(1, '#1a1030');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, width, height);

    ctx.strokeStyle = 'rgba(167,139,250,0.25)';
    ctx.lineWidth = 3;
    ctx.setLineDash([12, 8]);
    ctx.strokeRect(40, 40, width - 80, height - 80);
    ctx.setLineDash([]);

    ctx.fillStyle = 'rgba(167,139,250,0.9)';
    ctx.font = '700 36px Inter, system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(hasAddon ? 'Upload your custom back' : 'Front only', width / 2, height / 2 - 30);

    ctx.fillStyle = 'rgba(203,213,225,0.75)';
    ctx.font = '500 18px Inter, system-ui, sans-serif';
    const msg = hasAddon
        ? 'Use the upload below — any image you like'
        : `Add custom back for +${formatMoney(PRICING.customBack)}`;
    ctx.fillText(msg, width / 2, height / 2 + 20);

    if (!hasAddon) {
        ctx.fillStyle = 'rgba(52,211,153,0.85)';
        ctx.font = '600 16px Inter, system-ui, sans-serif';
        ctx.fillText('Includes FREE shipping', width / 2, height / 2 + 60);
    }

    return canvas;
}

function renderCardBack(width = CARD_LAYOUT.width, height = CARD_LAYOUT.height) {
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');

    const grad = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    grad.addColorStop(0, '#0f172a');
    grad.addColorStop(0.5, '#1e1b4b');
    grad.addColorStop(1, '#312e81');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = 'rgba(255,255,255,0.12)';
    ctx.lineWidth = 2;
    ctx.strokeRect(24, 24, canvas.width - 48, canvas.height - 48);

    ctx.fillStyle = '#ffffff';
    ctx.font = '700 42px Playfair Display, Georgia, serif';
    ctx.textAlign = 'center';
    ctx.fillText('LGBTIQASB+', canvas.width / 2, 120);

    ctx.font = '500 20px Inter, system-ui, sans-serif';
    ctx.fillStyle = 'rgba(226,232,240,0.9)';
    ctx.fillText('Community Access Card', canvas.width / 2, 165);

    ctx.font = '400 16px Inter, system-ui, sans-serif';
    ctx.fillStyle = 'rgba(203,213,225,0.85)';
    const lines = [
        'This card affirms your identity within our community.',
        'Carry it with pride. You belong here.',
        '',
        'Premium PVC • CR80 • Evolis Primacy 2 ready',
        'Printed in Australia • Respectful • Inclusive'
    ];
    lines.forEach((line, i) => ctx.fillText(line, canvas.width / 2, 250 + i * 34));

    const bottomGrad = ctx.createLinearGradient(0, 535, canvas.width, canvas.height);
    bottomGrad.addColorStop(0, 'rgba(99,102,241,0.25)');
    bottomGrad.addColorStop(1, 'rgba(236,72,153,0.25)');
    ctx.fillStyle = bottomGrad;
    ctx.fillRect(0, 535, canvas.width, 103);

    ctx.fillStyle = '#ffffff';
    ctx.font = '700 16px Inter, system-ui, sans-serif';
    ctx.fillText('YOUR IDENTITY • YOUR COMMUNITY • YOU BELONG', canvas.width / 2, 568);

    ctx.fillStyle = 'rgba(226,232,240,0.55)';
    ctx.font = '400 11px Inter, system-ui, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Premium Community Access Card • Printed on high-quality PVC', 48, 618);

    return canvas;
}

async function composePreviewCanvas(side, options) {
    const { customBack = false, customBackImage = null } = options;
    if (side === 'back') {
        if (customBack && customBackImage) {
            return renderCardBackCustom(customBackImage);
        }
        return renderCardBackLocked(CARD_LAYOUT.width, CARD_LAYOUT.height, customBack);
    }
    return renderCardFront({
        ...options,
        previewScale: options.previewScale ?? PREVIEW_SCALE,
        overlayText: false,
        applyHue: false
    });
}

function commitPreviewCanvas(canvasEl, rendered, side, options) {
    const ctx = canvasEl.getContext('2d');
    canvasEl.width = rendered.width;
    canvasEl.height = rendered.height;
    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);
    ctx.drawImage(rendered, 0, 0);

    if (side === 'front') {
        applyPreviewHueFilter(options.hue, options.saturation, true);
    } else {
        applyPreviewHueFilter(0, 100, false);
    }
}

async function renderPreview(canvasEl, side, options) {
    const rendered = await composePreviewCanvas(side, options);
    commitPreviewCanvas(canvasEl, rendered, side, options);
    return rendered;
}

function canvasToDataUrl(canvas, type = 'image/png', quality = 0.95) {
    return canvas.toDataURL(type, quality);
}

async function exportCardsPdf(cards, includeBack = true, useCustomBack = false) {
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF({
        orientation: 'landscape',
        unit: 'mm',
        format: [85.6, 53.98]
    });

    for (let i = 0; i < cards.length; i++) {
        if (i > 0) pdf.addPage([85.6, 53.98], 'landscape');

        const front = await renderCardFront({ ...cards[i], previewScale: 1, overlayText: true });
        pdf.addImage(canvasToDataUrl(front), 'PNG', 0, 0, 85.6, 53.98, undefined, 'FAST');

        if (includeBack) {
            pdf.addPage([85.6, 53.98], 'landscape');
            const back = useCustomBack && cards[i].customBackImage
                ? renderCardBackCustom(cards[i].customBackImage, front.width, front.height)
                : renderCardBack(front.width, front.height);
            pdf.addImage(canvasToDataUrl(back), 'PNG', 0, 0, 85.6, 53.98, undefined, 'FAST');
        }
    }

    return pdf;
}

async function loadPhotoFromFile(file) {
    if (!file) return null;
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = async () => {
            try {
                const img = await loadImage(reader.result);
                if (img.decode) await img.decode();
                resolve(img);
            } catch (err) {
                reject(err);
            }
        };
        reader.onerror = () => reject(new Error('Failed to read photo'));
        reader.readAsDataURL(file);
    });
}

async function loadPhotoFromDataUrl(dataUrl) {
    if (!dataUrl) return null;
    return loadImage(dataUrl);
}


const PRICING = {
    card: 99.99,
    customBack: 19.99,
    shippingStandard: 7.99,
    shippingExpress: 9.99,
    currency: 'AUD'
};

/** Print specs — CR80 @ 300 DPI */
const IMAGE_SPECS = {
    front: { min: 600, ideal: 900, hint: '600×600 px min (900×900 recommended) @ 300 DPI' },
    back: { width: 1011, height: 638, hint: '1011×638 px @ 300 DPI (CR80 card size)' }
};

/** Print specs — CR80 @ 300 DPI */
const IMAGE_SPECS = {
    front: { min: 600, ideal: 900, label: 'square', hint: '600×600 px min (900×900 recommended) @ 300 DPI' },
    back: { width: 1011, height: 638, hint: '1011×638 px @ 300 DPI (CR80 card size)' }
};

function formatMoney(amount) {
    return `$${amount.toFixed(2)}`;
}

function calcOrderTotal(customBack, shippingMethod) {
    let total = PRICING.card;
    const lines = [{ label: 'PridePass Card (front)', amount: PRICING.card }];

    if (customBack) {
        total += PRICING.customBack;
        lines.push({ label: 'Custom back — upload your design', amount: PRICING.customBack });
        lines.push({ label: 'Shipping', amount: 0, note: 'FREE with custom back' });
    } else {
        const ship = shippingMethod === 'express' ? PRICING.shippingExpress : PRICING.shippingStandard;
        const shipLabel = shippingMethod === 'express' ? 'Express shipping' : 'Standard shipping';
        total += ship;
        lines.push({ label: shipLabel, amount: ship });
    }

    return { total, lines };
}
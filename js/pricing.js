const PRICING = {
    card: 99.99,
    customBack: 19.99,
    shippingStandard: 7.99,
    shippingExpress: 9.99,
    currency: 'AUD'
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
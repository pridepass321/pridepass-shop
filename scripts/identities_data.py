"""Single source of truth for all card identities — used by template, JS, and batch print."""

CARD_LAYOUT = {
    "width": 1619,
    "height": 971,
    "photo": {"cx": 0.801, "cy": 0.407, "r": 0.226},
    "name": {"x": 0.166, "y": 0.536, "maxWidth": 0.356, "fontSize": 0.044},
    "field2": {"x": 0.166, "y": 0.674, "maxWidth": 0.297, "fontSize": 0.038},
    "pronouns": {"x": 0.166, "y": 0.578, "fontSize": 0.022},
}

PRONOUNS = [
    "they/them", "she/her", "he/him", "she/they", "he/they",
    "any pronouns", "name only", "ze/hir", "xe/xem",
]

HUE_PRESETS = [
    ("Original", 0, 100),
    ("Warm Gold", 30, 110),
    ("Rose", 320, 105),
    ("Emerald", 90, 105),
    ("Ocean", 180, 110),
    ("Violet", 270, 105),
]

CORE_IDENTITIES = [
    {"id": "pride", "label": "Pride", "category": "Core", "fieldType": "member"},
    {"id": "ally", "label": "Ally", "category": "Core", "fieldType": "member"},
    {"id": "trans-gender-diverse", "label": "Trans & Gender Diverse", "category": "Core", "fieldType": "member"},
    {"id": "intersex", "label": "Intersex", "category": "Core", "fieldType": "member"},
    {"id": "ace-aro", "label": "Ace & Aro", "category": "Core", "fieldType": "member"},
    {"id": "lgbtqia-plus", "label": "LGBTQIA+", "category": "Core", "fieldType": "member"},
    {"id": "lesbian", "label": "Lesbian", "category": "Core", "fieldType": "community"},
    {"id": "gay", "label": "Gay", "category": "Core", "fieldType": "community"},
    {"id": "bisexual", "label": "Bisexual / Bi", "category": "Core", "fieldType": "community"},
    {"id": "queer", "label": "Queer", "category": "Core", "fieldType": "community"},
    {"id": "questioning", "label": "Questioning", "category": "Core", "fieldType": "community"},
]

SEXUAL_IDENTITIES = [
    {"id": "omnisexual", "label": "Omnisexual", "meaning": "Attracted to all genders, often with gender still being noticed."},
    {"id": "polysexual", "label": "Polysexual", "meaning": "Attracted to multiple genders, not necessarily all."},
    {"id": "abrosexual", "label": "Abrosexual", "meaning": "Sexuality shifts or changes over time."},
    {"id": "greysexual", "label": "Greysexual / Grey-A", "aliases": ["grey-a", "grey a"], "meaning": "Rare or limited sexual attraction."},
    {"id": "aegosexual", "label": "Aegosexual", "meaning": "May enjoy sexual fantasy/content but not want direct sexual involvement."},
    {"id": "cupiosexual", "label": "Cupiosexual", "meaning": "Does not feel sexual attraction but may still want a sexual relationship."},
    {"id": "lithsexual", "label": "Lithsexual / Akoisexual", "aliases": ["akoisexual"], "meaning": "Attraction may fade if it is returned."},
    {"id": "fraysexual", "label": "Fraysexual", "meaning": "Attraction fades after emotional closeness develops."},
    {"id": "reciprosexual", "label": "Reciprosexual", "meaning": "Only feels attraction after knowing attraction is returned."},
    {"id": "apothisexual", "label": "Apothisexual", "meaning": "Asexual and sex-repulsed."},
    {"id": "aceflux", "label": "Aceflux", "meaning": "Asexual-spectrum identity that fluctuates."},
    {"id": "androsexual", "label": "Androsexual", "meaning": "Attraction to masculinity/men/masc-presenting people."},
    {"id": "gynesexual", "label": "Gynesexual / Gynosexual", "aliases": ["gynosexual"], "meaning": "Attraction to femininity/women/femme-presenting people."},
    {"id": "ceterosexual", "label": "Ceterosexual / Skoliosexual", "aliases": ["skoliosexual"], "meaning": "Attraction to non-binary or gender-diverse people."},
    {"id": "uranic", "label": "Uranic", "meaning": "Attraction to men, masculine people, and/or non-binary people, not women."},
    {"id": "neptunic", "label": "Neptunic", "meaning": "Attraction to women, feminine people, and/or non-binary people, not men."},
    {"id": "toric", "label": "Toric", "meaning": "Non-binary person attracted to men."},
    {"id": "trixic", "label": "Trixic", "meaning": "Non-binary person attracted to women."},
    {"id": "diamoric", "label": "Diamoric", "meaning": "Attraction/relationship involving non-binary people, not easily described as straight/gay."},
    {"id": "sapphic", "label": "Sapphic", "meaning": "Women/feminine-aligned people attracted to women."},
    {"id": "achillean", "label": "Achillean / MLM", "aliases": ["mlm"], "meaning": "Men/masculine-aligned people attracted to men."},
    {"id": "vincian", "label": "Vincian", "meaning": "Another term for gay men / men-loving-men."},
]

ROMANTIC_IDENTITIES = [
    {"id": "aromantic", "label": "Aromantic / Aro", "aliases": ["aro"], "meaning": "Little or no romantic attraction."},
    {"id": "greyromantic", "label": "Greyromantic", "meaning": "Rare or limited romantic attraction."},
    {"id": "demiromantic", "label": "Demiromantic", "meaning": "Romantic attraction after strong emotional connection."},
    {"id": "aroflux", "label": "Aroflux", "meaning": "Romantic attraction fluctuates."},
    {"id": "cupioromantic", "label": "Cupioromantic", "meaning": "Does not feel romantic attraction but may still want a romantic relationship."},
    {"id": "lithromantic", "label": "Lithromantic / Akoisromantic", "aliases": ["akoisromantic"], "meaning": "Romantic attraction may fade if returned."},
    {"id": "frayromantic", "label": "Frayromantic", "meaning": "Romantic attraction fades after closeness develops."},
    {"id": "recipromantic", "label": "Recipromantic", "meaning": "Romantic attraction only after knowing it is returned."},
    {"id": "quoiromantic", "label": "Quoiromantic / WTFromantic", "aliases": ["wtfromantic"], "meaning": "Hard to tell whether attraction is romantic, platonic, or something else."},
    {"id": "bellusromantic", "label": "Bellusromantic", "meaning": "Likes romantic gestures/aesthetic but may not want a romantic relationship."},
    {"id": "queerplatonic", "label": "Queerplatonic", "meaning": "A deep committed bond that is not easily friendship or romance."},
]

GENDER_IDENTITIES = [
    {"id": "demigirl", "label": "Demigirl", "meaning": "Partly, but not fully, girl/woman."},
    {"id": "demiboy", "label": "Demiboy", "meaning": "Partly, but not fully, boy/man."},
    {"id": "demigender", "label": "Demigender", "meaning": "Partial connection to a gender."},
    {"id": "bigender", "label": "Bigender", "meaning": "Two genders."},
    {"id": "trigender", "label": "Trigender", "meaning": "Three genders."},
    {"id": "polygender", "label": "Polygender", "meaning": "Multiple genders."},
    {"id": "pangender", "label": "Pangender", "meaning": "Many/all genders."},
]


def _tag(items, category, field_type):
    out = []
    for item in items:
        row = dict(item)
        row.setdefault("category", category)
        row.setdefault("fieldType", field_type)
        out.append(row)
    return out


def all_identities():
    return (
        CORE_IDENTITIES
        + _tag(SEXUAL_IDENTITIES, "Sexuality", "community")
        + _tag(ROMANTIC_IDENTITIES, "Romantic", "community")
        + _tag(GENDER_IDENTITIES, "Gender", "community")
    )


def identity_labels():
    return [i["label"] for i in all_identities()]


def normalize_key(value):
    import re
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()))


def resolve_identity(value):
    if not value:
        return None
    key = normalize_key(str(value).strip())
    for identity in all_identities():
        if identity["id"] == key or normalize_key(identity["label"]) == key:
            return identity
        for alias in identity.get("aliases", []):
            if normalize_key(alias) == key:
                return identity
    return None
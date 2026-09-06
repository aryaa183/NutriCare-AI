"""
NutriCare AI — ingredient text normalization utilities.
Used by match_ingredients.py. Kept as a separate module since both the
matching script and (later) the FastAPI ingestion pipeline will need it.
"""

import re

# ---------------------------------------------------------------------
# Unit -> grams conversion. Deliberately approximate (documented
# assumption, not a fabricated precise value) — recipe ingredient text
# rarely gives weights directly, so this is the pragmatic v1 approach.
# Anything not in this table falls back to a flat per-item default.
# ---------------------------------------------------------------------
UNIT_TO_GRAMS = {
    "kg": 1000, "kilogram": 1000, "kilograms": 1000,
    "gram": 1, "grams": 1, "g": 1, "gm": 1, "gms": 1,
    "cup": 200, "cups": 200,
    "tablespoon": 15, "tablespoons": 15, "tbsp": 15,
    "teaspoon": 5, "teaspoons": 5, "tsp": 5,
    "ml": 1, "milliliter": 1, "millilitre": 1,
    "litre": 1000, "liter": 1000, "l": 1000,
    "inch": 5, "inches": 5,   # for ginger/cinnamon sticks etc.
    "pinch": 0.5,
    "handful": 30,
}

# common whole-item default weights (grams) — used when quantity has no
# unit, e.g. "2 onion", "6 karela"
ITEM_DEFAULT_WEIGHTS = {
    "onion": 110, "tomato": 120, "potato": 150, "egg": 50, "lemon": 60,
    "garlic": 5, "green chilli": 5, "chilli": 5, "capsicum": 120,
    "cucumber": 150, "carrot": 70, "banana": 120, "apple": 150,
    "karela": 90, "brinjal": 80, "okra": 15, "bhindi": 15,
    # seasonings used "to taste" with no explicit quantity — a flat 50g
    # default (fine for a whole onion) would wildly overstate these.
    # These are typical household per-dish amounts, not a fabricated
    # precise figure.
    "salt": 3, "sugar": 5, "turmeric": 2, "asafoetida": 0.5,
}
DEFAULT_ITEM_WEIGHT = 50  # fallback for unrecognized countable items

# leading numeric quantity only (does NOT consume a following word — that
# was a bug: for phrases like "6 Karela" with no explicit unit, an earlier
# version treated "Karela" itself as the unit and stripped it away,
# leaving a blank ingredient name).
LEADING_QUANTITY_RE = re.compile(r"^\s*([\d/.\-]+(?:\s*-\s*[\d/.]+)?)\s*")

# ---------------------------------------------------------------------
# Synonym map: common recipe-ingredient phrasing -> normalized term that
# is more likely to match an IFCT composition-table entry. Not
# exhaustive — extend as unmatched-ingredient review turns up gaps.
# ---------------------------------------------------------------------
SYNONYM_MAP = {
    # NOTE: IFCT's 542-item table has no curd/yogurt/buttermilk entry —
    # "Milk, whole, Cow" is used as the closest available nutritional
    # proxy. This is a documented approximation, not an exact match.
    "curd": "milk, whole, cow", "dahi": "milk, whole, cow",
    "hung curd": "milk, whole, cow", "buttermilk": "milk, whole, cow",
    "yogurt": "milk, whole, cow", "yoghurt": "milk, whole, cow",
    "atta": "wheat flour", "whole wheat flour": "wheat flour",
    "maida": "refined flour", "besan": "gram flour", "chana dal flour": "gram flour",
    "moong dal": "green gram", "yellow moong dal": "green gram",
    "chana dal": "bengal gram", "toor dal": "pigeon pea", "arhar dal": "pigeon pea",
    "urad dal": "black gram", "masoor dal": "red lentil",
    "jeera": "cumin", "cumin seeds": "cumin",
    "haldi": "turmeric", "turmeric powder": "turmeric",
    "dhania": "coriander", "coriander leaves": "coriander", "cilantro": "coriander",
    "mirch": "chilli", "red chilli powder": "chilli", "green chilli": "chilli",
    "pyaz": "onion", "tamatar": "tomato", "aloo": "potato",
    "gud": "jaggery", "gur": "jaggery",
    "rai": "mustard seed", "sarson": "mustard seed",
    "adrak": "ginger", "lehsun": "garlic",
    "sooji": "semolina", "rava": "semolina",
    "poha": "flattened rice", "chivda": "flattened rice",
    "vellai poosanikai": "ash gourd", "karela": "bitter gourd", "pavakkai": "bitter gourd",
    "bhindi": "okra", "brinjal": "eggplant", "baingan": "eggplant",
    "til": "sesame", "gingelly oil": "sesame oil",
    "ajwain": "omum", "carom seeds": "omum",  # Tamil name used in IFCT
    "kasuri methi": "fenugreek seeds",  # dried leaves not in IFCT; seed proxy
    "ginger garlic": "ginger, fresh",
    "hing": "asafoetida",
}

DESCRIPTOR_WORDS = [
    "chopped", "sliced", "diced", "grated", "crushed", "minced", "deseeded",
    "seeded", "peeled", "soaked", "boiled", "cooked", "roasted", "toasted",
    "finely", "coarsely", "thinly", "cut into strips", "cut into pieces",
    "to taste", "for garnish", "for tempering", "as required", "optional",
    "fresh", "dry", "dried", "powder", "paste", "whole", "large", "small",
    "medium", "extra", "or as needed", "washed", "cleaned", "melted",
]


def strip_parenthetical(text: str) -> str:
    return re.sub(r"\([^)]*\)", "", text)


def _parse_qty_value(qty_str: str) -> float:
    qty_str = qty_str.strip().split("-")[-1]  # take upper bound of ranges
    try:
        if "/" in qty_str:
            num, den = qty_str.split("/")
            return float(num) / float(den)
        return float(qty_str)
    except (ValueError, ZeroDivisionError):
        return 1.0


def normalize_ingredient_phrase(phrase: str) -> tuple[str, float, bool]:
    """Returns (normalized_name, estimated_quantity_grams, quantity_was_flagged)."""
    phrase = strip_parenthetical(phrase)
    phrase = phrase.split(" - ")[0]  # drop trailing descriptor clause

    # isolate leading quantity (numbers only)
    qty_match = LEADING_QUANTITY_RE.match(phrase)
    qty_str = qty_match.group(1) if qty_match else None
    rest = phrase[qty_match.end():] if qty_match else phrase

    # only strip the next word too if it's an actual recognized unit —
    # otherwise it's part of the ingredient name (e.g. "Karela", "Onion")
    unit = None
    rest_stripped = rest.strip()
    if rest_stripped:
        first_word, _, remainder = rest_stripped.partition(" ")
        first_word_clean = first_word.lower().strip(".,")
        if first_word_clean in UNIT_TO_GRAMS:
            unit = first_word_clean
            rest = remainder

    name_part = rest.lower()
    name_part = re.sub(r"[^\w\s]", " ", name_part)
    for word in DESCRIPTOR_WORDS:
        name_part = re.sub(rf"\b{re.escape(word)}\b", "", name_part)
    name_part = re.sub(r"\s+", " ", name_part).strip()

    if not name_part:
        return "", 0.0, False

    for raw_term in sorted(SYNONYM_MAP, key=len, reverse=True):
        if raw_term in name_part:
            name_part = SYNONYM_MAP[raw_term]
            break

    qty = _parse_qty_value(qty_str) if qty_str else 1.0
    if unit:
        grams = qty * UNIT_TO_GRAMS[unit]
    else:
        grams = DEFAULT_ITEM_WEIGHT * qty
        for item, weight in ITEM_DEFAULT_WEIGHTS.items():
            if item in name_part:
                grams = weight * qty
                break

    grams, was_corrected = sanity_check_grams(unit, grams)
    return name_part, grams, was_corrected


MAX_PLAUSIBLE_INGREDIENT_G = 3000  # single ingredient line, non-bulk recipe


def sanity_check_grams(unit: str, grams: float) -> tuple[float, bool]:
    """Catches likely source-data unit errors — e.g. a raw recipe listing
    "750 Kg Chicken" for a 5-serving dish is almost certainly a "grams"
    typed as "Kg". Rather than silently propagating a 750,000g ingredient
    into the nutrition total, re-interpret "kg" as "grams" when the
    kg-scaled result is implausible for a single home-recipe ingredient.
    Anything still over the cap after that is clipped, not fabricated
    away — capped values are visible via the returned flag."""
    if grams > MAX_PLAUSIBLE_INGREDIENT_G and unit == "kg":
        return grams / 1000, True
    if grams > MAX_PLAUSIBLE_INGREDIENT_G:
        return MAX_PLAUSIBLE_INGREDIENT_G, True
    return grams, False


def split_ingredient_list(ingredients_text: str) -> list[str]:
    if not isinstance(ingredients_text, str):
        return []
    return [p.strip() for p in ingredients_text.split(",") if p.strip()]

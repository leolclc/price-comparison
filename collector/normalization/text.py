import re
import unicodedata

DOSAGE_PATTERNS = [
    (r"(\d+)\s*mg", r"\1mg"),
    (r"(\d+)\s*mcg", r"\1mcg"),
    (r"(\d+)\s*g(?!\w)", r"\1g"),
    (r"(\d+)\s*ml(?!\w)", r"\1ml"),
    (r"(\d+)\s*ui", r"\1ui"),
    (r"(\d+)\s*%", r"\1%"),
]

UNIT_SYNONYMS: dict[str, str] = {
    "comprimido": "comprimidos",
    "comp": "comprimidos",
    "caps": "capsulas",
    "capsula": "capsulas",
    "cap": "capsulas",
    "cpr": "comprimidos",
    "cps": "capsulas",
    "ampola": "ampolas",
    "amp": "ampolas",
    "supositorio": "supositórios",
}


def normalize_text(text: str) -> str:
    """Normalize text for matching: lowercase, remove accents, clean whitespace."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c))
    lower = ascii_text.lower()
    cleaned = re.sub(r"[^a-z0-9\s\.\-\%]", " ", lower)
    return " ".join(cleaned.split())


def normalize_dosage(dosage: str) -> str:
    """Normalize dosage string (e.g. '500 mg' -> '500mg')."""
    if not dosage:
        return ""
    d = dosage.lower().strip()
    for pattern, replacement in DOSAGE_PATTERNS:
        d = re.sub(pattern, replacement, d, flags=re.IGNORECASE)
    return d.strip()


def normalize_unit(unit: str) -> str:
    """Normalize pharmaceutical unit to canonical form."""
    if not unit:
        return ""
    u = normalize_text(unit).strip()
    return UNIT_SYNONYMS.get(u, u)


def extract_dosage_from_name(name: str) -> str | None:
    """Try to extract dosage from product name."""
    patterns = [
        r"(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|ui|%))(?:\s|$|/|\+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            return normalize_dosage(match.group(1))
    return None


def extract_quantity_from_name(name: str) -> tuple[int | None, str | None]:
    """Try to extract quantity and unit from product name."""
    patterns = [
        r"(\d+)\s*(comprimidos?|comp\.?|capsulas?|caps\.?|ampolas?|ml|g|unidades?|un\.?|sachê|saches?)",
        r"c(?:om|/)\s*(\d+)\s*(comprimidos?|capsulas?|ampolas?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            groups = match.groups()
            qty_str = groups[0] if groups[0].isdigit() else groups[1] if len(groups) > 1 else None
            unit_str = groups[1] if len(groups) > 1 else groups[0]
            if qty_str:
                try:
                    return int(qty_str), normalize_unit(unit_str)
                except (ValueError, TypeError):
                    pass
    return None, None

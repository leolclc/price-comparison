import logging
from dataclasses import dataclass

from models.common import ProductCandidate
from normalization.text import (
    extract_dosage_from_name,
    extract_quantity_from_name,
    normalize_dosage,
    normalize_text,
    normalize_unit,
)

logger = logging.getLogger("MATCHER")


@dataclass
class MatchKey:
    ean: str | None
    active_ingredient: str | None
    dosage: str | None
    quantity: int | None
    unit: str | None
    brand: str | None
    name_normalized: str


def build_match_key(candidate: ProductCandidate) -> MatchKey:
    dosage = candidate.dosage
    quantity = candidate.quantity
    unit = candidate.unit

    if not dosage:
        dosage = extract_dosage_from_name(candidate.name)
    if not quantity:
        quantity, extracted_unit = extract_quantity_from_name(candidate.name)
        if extracted_unit and not unit:
            unit = extracted_unit

    return MatchKey(
        ean=candidate.ean,
        active_ingredient=(
            normalize_text(candidate.active_ingredient)
            if candidate.active_ingredient
            else None
        ),
        dosage=normalize_dosage(dosage) if dosage else None,
        quantity=quantity,
        unit=normalize_unit(unit) if unit else None,
        brand=normalize_text(candidate.brand) if candidate.brand else None,
        name_normalized=normalize_text(candidate.name),
    )


def candidates_match(a: ProductCandidate, b: ProductCandidate) -> bool:
    key_a = build_match_key(a)
    key_b = build_match_key(b)

    # 1. EAN match (most reliable)
    if key_a.ean and key_b.ean:
        if key_a.ean == key_b.ean:
            logger.debug(f"EAN match: {a.name} == {b.name}")
            return True
        else:
            return False

    # 2. Check dosage discrimination
    if key_a.dosage and key_b.dosage and key_a.dosage != key_b.dosage:
        return False

    # 3. Check quantity discrimination
    if key_a.quantity and key_b.quantity and key_a.quantity != key_b.quantity:
        return False

    # 4. Active ingredient + dosage + quantity + unit match
    if (
        key_a.active_ingredient
        and key_b.active_ingredient
        and key_a.active_ingredient == key_b.active_ingredient
        and key_a.dosage
        and key_b.dosage
        and key_a.dosage == key_b.dosage
        and key_a.quantity
        and key_b.quantity
        and key_a.quantity == key_b.quantity
    ):
        logger.debug(f"Attribute match: {a.name} == {b.name}")
        return True

    # 5. Normalized name + brand + dosage + quantity
    if (
        key_a.name_normalized
        and key_b.name_normalized
        and _names_compatible(key_a.name_normalized, key_b.name_normalized)
        and key_a.dosage == key_b.dosage
        and key_a.quantity == key_b.quantity
    ):
        if key_a.brand and key_b.brand and key_a.brand != key_b.brand:
            return False
        logger.debug(f"Name match: {a.name} == {b.name}")
        return True

    return False


def _names_compatible(name_a: str, name_b: str) -> bool:
    tokens_a = set(name_a.split())
    tokens_b = set(name_b.split())

    if not tokens_a or not tokens_b:
        return False

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    similarity = len(intersection) / len(union)

    return similarity >= 0.7


def group_candidates(
    all_candidates: list[ProductCandidate],
) -> list[list[ProductCandidate]]:
    groups: list[list[ProductCandidate]] = []

    for candidate in all_candidates:
        placed = False
        for group in groups:
            if candidates_match(candidate, group[0]):
                group.append(candidate)
                placed = True
                break
        if not placed:
            groups.append([candidate])

    logger.info(f"Grouped {len(all_candidates)} candidates into {len(groups)} products")
    return groups

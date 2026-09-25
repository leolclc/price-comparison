import pytest
from models.common import ProductCandidate
from normalization.matcher import candidates_match, group_candidates


def make_candidate(
    name: str,
    pharmacy: str = "test",
    ean: str | None = None,
    brand: str | None = None,
    dosage: str | None = None,
    quantity: int | None = None,
    unit: str | None = None,
    active_ingredient: str | None = None,
) -> ProductCandidate:
    return ProductCandidate(
        pharmacy=pharmacy,
        external_id=name[:10],
        name=name,
        brand=brand,
        ean=ean,
        dosage=dosage,
        quantity=quantity,
        unit=unit,
        active_ingredient=active_ingredient,
    )


def test_same_ean_matches():
    a = make_candidate("Dipirona 500mg 10 comp", ean="7896714240102")
    b = make_candidate("Dipirona Monoidratada 500mg 10 comprimidos", ean="7896714240102")
    assert candidates_match(a, b) is True


def test_different_ean_no_match():
    a = make_candidate("Dipirona 500mg 10 comp", ean="7896714240102")
    b = make_candidate("Dipirona 500mg 10 comp", ean="1234567890123")
    assert candidates_match(a, b) is False


def test_500mg_vs_1g_are_different():
    a = make_candidate(
        "Dipirona Monoidratada 500mg 10 comprimidos",
        dosage="500mg",
        quantity=10,
        unit="comprimidos",
    )
    b = make_candidate(
        "Dipirona Monoidratada 1g 10 comprimidos",
        dosage="1g",
        quantity=10,
        unit="comprimidos",
    )
    assert candidates_match(a, b) is False


def test_dosage_extracted_from_name():
    a = make_candidate("Dipirona Monoidratada 500mg Neo Quimica 10 Comprimidos")
    b = make_candidate("Dipirona Monoidratada 1g Cimed 10 Comprimidos")
    assert candidates_match(a, b) is False


def test_10_vs_20_comprimidos_are_different():
    a = make_candidate(
        "Dipirona 500mg 10 comprimidos",
        dosage="500mg",
        quantity=10,
        unit="comprimidos",
    )
    b = make_candidate(
        "Dipirona 500mg 20 comprimidos",
        dosage="500mg",
        quantity=20,
        unit="comprimidos",
    )
    assert candidates_match(a, b) is False


def test_same_product_different_pharmacies_match():
    a = make_candidate(
        "Dipirona Monoidratada 500mg Neo Quimica 10 Comprimidos",
        pharmacy="pacheco",
        brand="Neo Quimica",
        dosage="500mg",
        quantity=10,
        unit="comprimidos",
        active_ingredient="Dipirona Monoidratada",
    )
    b = make_candidate(
        "Dipirona Monoidratada 500mg Neo Quimica Genérico 10 Comprimidos",
        pharmacy="pague-menos",
        brand="Neo Quimica",
        dosage="500mg",
        quantity=10,
        unit="comprimidos",
        active_ingredient="Dipirona Monoidratada",
    )
    assert candidates_match(a, b) is True


def test_group_by_ean():
    candidates = [
        make_candidate("Dipirona A", pharmacy="pacheco", ean="7896714240102"),
        make_candidate("Dipirona B", pharmacy="pague-menos", ean="7896714240102"),
        make_candidate("Ibuprofeno 400mg", pharmacy="araujo", ean="9999999999999"),
    ]
    groups = group_candidates(candidates)
    assert len(groups) == 2


def test_group_different_dosages():
    candidates = [
        make_candidate("Dipirona 500mg 10 comp", dosage="500mg", quantity=10),
        make_candidate("Dipirona 1g 10 comp", dosage="1g", quantity=10),
        make_candidate("Dipirona 500mg 20 comp", dosage="500mg", quantity=20),
    ]
    groups = group_candidates(candidates)
    assert len(groups) == 3

import asyncio
import sys
import logging

sys.path.insert(0, 'collector')

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from providers.pacheco import PachecoProvider
from providers.pague_menos import PagueMenosProvider
from providers.araujo import AraujoProvider
from providers.raia import RaiaProvider

async def test_live():
    print("=== TESTE DOS PROVIDERS AO VIVO ===")
    
    # 1. Pacheco
    print("\n--- 1. Pacheco ---")
    try:
        pacheco = PachecoProvider(timeout=15)
        cands = await pacheco.search("dipirona")
        print(f"[PACHECO] Produtos retornados: {len(cands)}")
        for c in cands[:3]:
            print(f"   -> {c.name} (EAN: {c.ean}, Marca: {c.brand})")
    except Exception as e:
        print(f"[PACHECO] Falha: {e}")

    # 2. Pague Menos
    print("\n--- 2. Pague Menos ---")
    try:
        pm = PagueMenosProvider(timeout=15)
        cands = await pm.search("dipirona")
        print(f"[PAGUE MENOS] Produtos retornados: {len(cands)}")
        for c in cands[:3]:
            print(f"   -> {c.name} (EAN: {c.ean}, Marca: {c.brand})")
    except Exception as e:
        print(f"[PAGUE MENOS] Falha: {e}")

    # 3. Araujo
    print("\n--- 3. Araujo ---")
    try:
        araujo = AraujoProvider(timeout=15)
        cands = await araujo.search("dipirona")
        print(f"[ARAUJO] Produtos retornados: {len(cands)}")
        for c in cands[:3]:
            print(f"   -> {c.name} (EAN: {c.ean}, Marca: {c.brand})")
    except Exception as e:
        print(f"[ARAUJO] Falha: {e}")

    # 4. Raia
    print("\n--- 4. Raia ---")
    try:
        raia = RaiaProvider(timeout=15)
        cands = await raia.search("dipirona")
        print(f"[RAIA] Produtos retornados: {len(cands)}")
        for c in cands[:3]:
            print(f"   -> {c.name} (EAN: {c.ean}, Marca: {c.brand})")
    except Exception as e:
        print(f"[RAIA] Falha: {e}")

if __name__ == "__main__":
    asyncio.run(test_live())

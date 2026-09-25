import httpx
import asyncio
import json

async def probe():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9",
    }
    
    # 1. Araujo
    print("Testing Araujo...")
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15) as client:
            r = await client.get("https://www.araujo.com.br/busca?q=dipirona")
            print("Araujo status:", r.status_code)
            if "data-gtmga4data" in r.text or "gtmContainer__productTile" in r.text:
                print("Araujo: found product tiles!")
            else:
                print("Araujo text preview:", r.text[:200])
    except Exception as e:
        print("Araujo exception:", e)

    # 2. Pague Menos
    print("\nTesting Pague Menos...")
    try:
        pm_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.paguemenos.com.br",
            "Referer": "https://www.paguemenos.com.br/",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(headers=pm_headers, timeout=15) as client:
            payload = {"searchUrl": "/busca?q=dipirona&map=ft"}
            r = await client.post("https://prod.apipmenos.com/buscacatalogo/api/searchurl", json=payload)
            print("Pague Menos searchurl status:", r.status_code)
            if r.status_code == 200:
                print("Pague Menos success! Products:", len(r.json().get("products", [])))
            else:
                print("Pague Menos response:", r.text[:200])

            # Also test direct VTEX API if used by Pague Menos
            r_vtex = await client.get("https://www.paguemenos.com.br/api/io/_v/api/intelligent-search/product_search/trade-policy/1?query=dipirona&count=10&page=1")
            print("Pague Menos VTEX intelligent-search status:", r_vtex.status_code)
    except Exception as e:
        print("Pague Menos exception:", e)

    # 3. Raia
    print("\nTesting Raia...")
    try:
        raia_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Referer": "https://www.drogaraia.com.br/",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(headers=raia_headers, timeout=15) as client:
            # Test Raia GraphQL
            query = """
            query ProductBySkuList($skuList: [String!]!, $origin: String) {
              productsBySkuList(skuList: $skuList, origin: $origin) {
                sku
                name
                liveComposition {
                  livePrice {
                    valueTo
                    valueFrom
                  }
                }
              }
            }
            """
            r_gql = await client.post("https://www.drogaraia.com.br/api/next/busca/graphql", json={"query": query, "variables": {"skuList": ["59568", "824264"], "origin": "search"}})
            print("Raia GraphQL status:", r_gql.status_code)
            if r_gql.status_code == 200:
                print("Raia GraphQL response:", r_gql.json())

            # Test Raia search
            r_search = await client.get("https://www.drogaraia.com.br/search?q=dipirona")
            print("Raia web search status:", r_search.status_code)
    except Exception as e:
        print("Raia exception:", e)

asyncio.run(probe())

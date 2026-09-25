import { Pharmacy, PriceHistoryPoint, SearchResult } from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "/api";

export async function searchProducts(query: string): Promise<SearchResult> {
  if (!query.trim()) {
    return { query: "", total: 0, products: [] };
  }
  const res = await fetch(`${API_BASE}/products/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) {
    throw new Error(`Erro na busca: ${res.statusText}`);
  }
  return res.json();
}

export async function getPriceHistory(productId: number): Promise<PriceHistoryPoint[]> {
  const res = await fetch(`${API_BASE}/products/${productId}/history`);
  if (!res.ok) {
    throw new Error(`Erro ao buscar histórico: ${res.statusText}`);
  }
  return res.json();
}

export async function getPharmacies(): Promise<Pharmacy[]> {
  const res = await fetch(`${API_BASE}/pharmacies`);
  if (!res.ok) {
    throw new Error(`Erro ao listar farmácias: ${res.statusText}`);
  }
  return res.json();
}

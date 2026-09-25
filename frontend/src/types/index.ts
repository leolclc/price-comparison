export interface Promotion {
  id: number;
  type: string;
  description: string | null;
  minimum_quantity: number | null;
  promotion_price: string | null;
}

export interface Offer {
  id: number;
  pharmacy_id: number;
  pharmacy_name: string;
  pharmacy_slug: string;
  price: string;
  list_price: string | null;
  price_without_discount: string | null;
  discount_percent: string | null;
  available: boolean;
  collected_at: string;
  external_url: string | null;
  promotions: Promotion[];
}

export interface Product {
  id: number;
  ean: string | null;
  name: string;
  brand: string | null;
  active_ingredient: string | null;
  dosage: string | null;
  pharmaceutical_form: string | null;
  quantity: number | null;
  unit: string | null;
  offers: Offer[];
}

export interface SearchResult {
  query: string;
  total: number;
  products: Product[];
}

export interface PriceHistoryPoint {
  pharmacy_id: number;
  pharmacy_name: string;
  price: string;
  list_price: string | null;
  available: boolean;
  collected_at: string;
}

export interface Pharmacy {
  id: number;
  name: string;
  slug: string;
  active: boolean;
  created_at: string;
}

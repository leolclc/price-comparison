import React, { useState } from "react";
import { History } from "lucide-react";
import { Product } from "../types";
import { OfferList } from "./OfferList";
import { PriceHistoryModal } from "./PriceHistoryModal";

interface ProductCardProps {
  product: Product;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product }) => {
  const [showHistory, setShowHistory] = useState(false);

  // Lowest available price
  const availableOffers = product.offers.filter((o) => o.available);
  const lowestPrice =
    availableOffers.length > 0
      ? Math.min(...availableOffers.map((o) => parseFloat(o.price)))
      : null;

  return (
    <div className="product-card">
      <div className="product-header">
        <div>
          <h2 className="product-title">{product.name}</h2>
          <div className="product-meta">
            {product.brand && <span className="product-pill">{product.brand}</span>}
            {product.dosage && <span className="product-pill">{product.dosage}</span>}
            {product.quantity && (
              <span className="product-pill">
                {product.quantity} {product.unit || "unid."}
              </span>
            )}
            {product.active_ingredient && (
              <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
                ({product.active_ingredient})
              </span>
            )}
            {product.ean && (
              <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                EAN: {product.ean}
              </span>
            )}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "0.5rem" }}>
          {lowestPrice !== null && (
            <div className="best-price-badge">
              <span className="best-price-label">Menor Preço</span>
              R$ {lowestPrice.toFixed(2).replace(".", ",")}
            </div>
          )}
          <button
            type="button"
            className="history-btn"
            onClick={() => setShowHistory(true)}
            title="Ver evolução de preços"
          >
            <History size={14} />
            <span>Histórico</span>
          </button>
        </div>
      </div>

      <OfferList offers={product.offers} />

      {showHistory && (
        <PriceHistoryModal
          productId={product.id}
          productName={product.name}
          onClose={() => setShowHistory(false)}
        />
      )}
    </div>
  );
};

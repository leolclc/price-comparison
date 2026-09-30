import React from "react";
import { ExternalLink, Clock, Tag } from "lucide-react";
import { Offer } from "../types";

interface OfferListProps {
  offers: Offer[];
}

export const OfferList: React.FC<OfferListProps> = ({ offers }) => {
  if (offers.length === 0) {
    return (
      <p style={{ color: "#94a3b8", fontSize: "0.9rem", margin: "1rem 0" }}>
        Nenhuma oferta disponível no momento.
      </p>
    );
  }

  // Find lowest price among available offers
  const availablePrices = offers
    .filter((o) => o.available)
    .map((o) => parseFloat(o.price));
  const minPrice = availablePrices.length > 0 ? Math.min(...availablePrices) : null;
  const bestOffer = offers
    .filter((offer) => offer.available)
    .sort((a, b) => parseFloat(a.price) - parseFloat(b.price))[0];

  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  return (
    <table className="offers-table">
      <thead>
        <tr>
          <th>Melhor loja</th>
          <th>Preço</th>
          <th>Promoção</th>
          <th>Última Coleta</th>
          <th style={{ textAlign: "right" }}>Ação</th>
        </tr>
      </thead>
      <tbody>
        {[bestOffer].filter((offer): offer is Offer => Boolean(offer)).map((offer) => {
          const priceNum = parseFloat(offer.price);
          const isCheapest = minPrice !== null && priceNum === minPrice && offer.available;

          return (
            <tr key={offer.id} className={isCheapest ? "is-cheapest" : ""}>
              <td className="pharmacy-col">
                {isCheapest && <span title="Menor preço">⭐</span>}
                <span>{offer.pharmacy_name}</span>
              </td>
              <td>
                <span className="price-current">
                  R$ {priceNum.toFixed(2).replace(".", ",")}
                </span>
                {offer.list_price && parseFloat(offer.list_price) > priceNum && (
                  <span className="price-old">
                    R$ {parseFloat(offer.list_price).toFixed(2).replace(".", ",")}
                  </span>
                )}
                {offer.discount_percent && parseFloat(offer.discount_percent) > 0 && (
                  <span className="discount-tag">
                    -{Math.round(parseFloat(offer.discount_percent))}%
                  </span>
                )}
              </td>
              <td>
                {offer.promotions && offer.promotions.length > 0 ? (
                  <span className="promo-note">
                    <Tag size={12} style={{ display: "inline", marginRight: "3px" }} />
                    {offer.promotions[0].description}
                    {offer.promotions[0].promotion_price && (
                      <strong> (R$ {parseFloat(offer.promotions[0].promotion_price).toFixed(2).replace(".", ",")})</strong>
                    )}
                  </span>
                ) : (
                  <span style={{ color: "#cbd5e1" }}>—</span>
                )}
              </td>
              <td className="time-col">
                <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                  <Clock size={12} />
                  {formatDate(offer.collected_at)}
                </span>
              </td>
              <td className="action-col">
                {offer.external_url ? (
                  <a
                    href={offer.external_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="buy-link"
                  >
                    <span>Ir à loja</span>
                    <ExternalLink size={13} />
                  </a>
                ) : (
                  <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Link indisponível</span>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

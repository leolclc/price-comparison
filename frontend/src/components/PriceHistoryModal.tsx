import React from "react";
import { useQuery } from "@tanstack/react-query";
import { X, Clock } from "lucide-react";
import { getPriceHistory } from "../services/api";

interface PriceHistoryModalProps {
  productId: number;
  productName: string;
  onClose: () => void;
}

export const PriceHistoryModal: React.FC<PriceHistoryModalProps> = ({
  productId,
  productName,
  onClose,
}) => {
  const { data: history, isLoading, error } = useQuery({
    queryKey: ["priceHistory", productId],
    queryFn: () => getPriceHistory(productId),
  });

  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3 className="modal-title">Histórico de Preços</h3>
            <p style={{ fontSize: "0.85rem", color: "#64748b", marginTop: "0.2rem" }}>
              {productName}
            </p>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {isLoading && <p className="loading-box">Carregando histórico...</p>}
        {error && <p style={{ color: "#ef4444" }}>Erro ao carregar histórico.</p>}

        {history && history.length === 0 && (
          <p style={{ color: "#64748b", textAlign: "center", padding: "1.5rem 0" }}>
            Nenhum histórico registrado ainda.
          </p>
        )}

        {history && history.length > 0 && (
          <div className="history-list">
            {history.map((item, index) => (
              <div key={index} className="history-item">
                <div>
                  <strong style={{ display: "block", color: "#0f172a" }}>
                    {item.pharmacy_name}
                  </strong>
                  <span style={{ fontSize: "0.8rem", color: "#94a3b8", display: "flex", alignItems: "center", gap: "0.25rem", marginTop: "0.15rem" }}>
                    <Clock size={12} />
                    {formatDate(item.collected_at)}
                  </span>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#16a34a" }}>
                    R$ {parseFloat(item.price).toFixed(2).replace(".", ",")}
                  </div>
                  {item.list_price && (
                    <div style={{ fontSize: "0.8rem", textDecoration: "line-through", color: "#94a3b8" }}>
                      R$ {parseFloat(item.list_price).toFixed(2).replace(".", ",")}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

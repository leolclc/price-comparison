import React, { useState } from "react";
import { Search } from "lucide-react";

interface SearchBarProps {
  initialValue?: string;
  onSearch: (term: string) => void;
  isLoading?: boolean;
}

const POPULAR_TERMS = [
  "dipirona",
  "paracetamol",
  "ibuprofeno",
  "omeprazol",
  "loratadina",
  "vitamina c",
  "simeticona",
  "protetor solar",
];

export const SearchBar: React.FC<SearchBarProps> = ({
  initialValue = "",
  onSearch,
  isLoading = false,
}) => {
  const [term, setTerm] = useState(initialValue);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (term.trim()) {
      onSearch(term.trim());
    }
  };

  const handleQuickClick = (quickTerm: string) => {
    setTerm(quickTerm);
    onSearch(quickTerm);
  };

  return (
    <div>
      <form className="search-box" onSubmit={handleSubmit}>
        <input
          type="text"
          className="search-input"
          placeholder="🔎 Buscar medicamento ou produto (ex: dipirona)..."
          value={term}
          onChange={(e) => setTerm(e.target.value)}
        />
        <button type="submit" className="search-button" disabled={isLoading}>
          <Search size={18} />
          <span>{isLoading ? "Buscando..." : "Pesquisar"}</span>
        </button>
      </form>

      <div className="quick-terms">
        <span style={{ fontSize: "0.85rem", color: "#94a3b8", alignSelf: "center" }}>
          Populares:
        </span>
        {POPULAR_TERMS.map((pt) => (
          <button
            key={pt}
            type="button"
            className="quick-term-btn"
            onClick={() => handleQuickClick(pt)}
          >
            {pt}
          </button>
        ))}
      </div>
    </div>
  );
};

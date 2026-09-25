import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { SearchBar } from "../components/SearchBar";
import { ProductCard } from "../components/ProductCard";
import { searchProducts } from "../services/api";

export const SearchPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState("dipirona");

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["search", searchTerm],
    queryFn: () => searchProducts(searchTerm),
    enabled: !!searchTerm,
  });

  return (
    <div className="main-content">
      <section className="hero">
        <h1>Compare Preços de Farmácias</h1>
        <p>
          Encontre os melhores preços em Belo Horizonte entre Araujo, Pague Menos, Drogaria Raia e Pacheco.
        </p>
        <SearchBar
          initialValue={searchTerm}
          onSearch={(term) => setSearchTerm(term)}
          isLoading={isLoading}
        />
      </section>

      {isLoading && (
        <div className="loading-box">
          <p style={{ fontSize: "1.1rem" }}>Buscando produtos...</p>
        </div>
      )}

      {isError && (
        <div className="empty-box">
          <p style={{ color: "#ef4444", fontWeight: 600 }}>
            {error instanceof Error ? error.message : "Erro ao buscar produtos"}
          </p>
          <p style={{ marginTop: "0.5rem", color: "#64748b" }}>
            Verifique se a API backend está em execução.
          </p>
        </div>
      )}

      {!isLoading && !isError && data && (
        <>
          <div className="results-header">
            <span className="results-count">
              <strong>{data.total}</strong> {data.total === 1 ? "produto encontrado" : "produtos encontrados"} para &ldquo;{data.query}&rdquo;
            </span>
          </div>

          {data.products.length === 0 ? (
            <div className="empty-box">
              <p style={{ fontSize: "1.2rem", fontWeight: 600 }}>
                Nenhum produto encontrado para &ldquo;{data.query}&rdquo;
              </p>
              <p style={{ color: "#64748b", marginTop: "0.5rem" }}>
                Tente buscar por &ldquo;dipirona&rdquo;, &ldquo;paracetamol&rdquo;, &ldquo;ibuprofeno&rdquo; ou execute a coleta no collector.
              </p>
            </div>
          ) : (
            <div className="products-grid">
              {data.products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};

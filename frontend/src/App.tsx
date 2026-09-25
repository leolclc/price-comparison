import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Header } from "./components/Header";
import { SearchPage } from "./pages/SearchPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="app-container">
        <Header />
        <SearchPage />
        <footer className="footer">
          <p>
            FarmaCompare — MVP de Comparação de Preços de Farmácias (Belo Horizonte/MG)
          </p>
          <p style={{ marginTop: "0.25rem", fontSize: "0.8rem", color: "#cbd5e1" }}>
            Araujo • Pague Menos • Drogaria Raia • Drogaria Pacheco • Drogasil
          </p>
        </footer>
      </div>
    </QueryClientProvider>
  );
};

export default App;

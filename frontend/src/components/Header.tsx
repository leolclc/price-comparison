import React from "react";
import { Pill } from "lucide-react";

export const Header: React.FC = () => {
  return (
    <header className="header">
      <div className="header-inner">
        <a href="/" className="logo">
          <Pill size={26} color="#2563eb" />
          <span>FarmaCompare</span>
          <span className="logo-badge">BH / MG</span>
        </a>
        <div className="pharmacies-pill">
          <span>Comparando:</span>
          <span className="pharmacy-tag">Araujo</span>
          <span className="pharmacy-tag">Pague Menos</span>
          <span className="pharmacy-tag">Raia</span>
          <span className="pharmacy-tag">Pacheco</span>
          <span className="pharmacy-tag">Drogasil</span>
        </div>
      </div>
    </header>
  );
};

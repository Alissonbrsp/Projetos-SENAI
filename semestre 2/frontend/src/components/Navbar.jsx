// Navbar.jsx
import React from "react";
export default function Navbar({ user, onLogout }) {
  return (
    <nav style={{ background: "#1a1d27", borderBottom: "1px solid #2d3748", padding: "0.75rem 2rem", display: "flex", justifyContent: "space-between", alignItems: "center", fontFamily: "monospace" }}>
      <span style={{ color: "#63b3ed", fontWeight: "bold", fontSize: "1rem" }}>🏭 CTF IIoT Dinâmico</span>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <span style={{ color: "#a0aec0", fontSize: "0.85rem" }}>👤 {user}</span>
        <button onClick={onLogout} style={{ background: "none", border: "1px solid #4a5568", color: "#a0aec0", borderRadius: 4, padding: "0.3rem 0.75rem", cursor: "pointer", fontSize: "0.8rem" }}>Sair</button>
      </div>
    </nav>
  );
}

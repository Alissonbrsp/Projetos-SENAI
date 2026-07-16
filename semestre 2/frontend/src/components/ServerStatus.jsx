// ServerStatus.jsx
import React from "react";

const STATE_LABELS = {
  running:  { label: "🟢 Online",      color: "#48bb78" },
  stopped:  { label: "🔴 Offline",     color: "#fc8181" },
  pending:  { label: "🟡 Iniciando...", color: "#f6e05e" },
  stopping: { label: "🟠 Parando...",  color: "#ed8936" },
  unknown:  { label: "⚪ Desconhecido",color: "#718096" },
};

export default function ServerStatus({ status, onStart, loading, message }) {
  const { label, color } = STATE_LABELS[status.state] || STATE_LABELS.unknown;
  return (
    <div style={styles.card}>
      <h2 style={styles.title}>🖥️ Arena CTF</h2>
      <div style={{ ...styles.badge, background: color + "22", color }}>
        {label}
      </div>
      {status.public_ip && status.ready && (
        <div style={styles.ipBox}>
          <span style={styles.ipLabel}>IP do servidor:</span>
          <code style={styles.ip}>{status.public_ip}</code>
        </div>
      )}
      {message && <div style={styles.msg}>{message}</div>}
      {!status.ready && (
        <button style={styles.btn} onClick={onStart} disabled={loading || status.state === "pending"}>
          {loading ? "Aguarde..." : status.state === "pending" ? "Iniciando..." : "▶ Iniciar Arena"}
        </button>
      )}
      {status.ready && (
        <div style={styles.hint}>
          <p style={styles.hintText}>✅ Arena pronta. Comece o desafio!</p>
          <p style={styles.hintText}>Dica: Explore a porta <code>80</code> do servidor acima.</p>
        </div>
      )}
    </div>
  );
}

const styles = {
  card: { background: "#1a1d27", border: "1px solid #2d3748", borderRadius: 8, padding: "1.5rem" },
  title: { color: "#e2e8f0", marginTop: 0, fontSize: "1.1rem" },
  badge: { display: "inline-block", padding: "0.3rem 0.75rem", borderRadius: 999, fontWeight: "bold", marginBottom: "1rem", fontSize: "0.9rem" },
  ipBox: { background: "#0d1117", borderRadius: 6, padding: "0.75rem", marginBottom: "1rem", fontFamily: "monospace" },
  ipLabel: { color: "#718096", fontSize: "0.8rem", display: "block", marginBottom: "0.25rem" },
  ip: { color: "#63b3ed", fontSize: "1.1rem" },
  msg: { color: "#f6ad55", fontSize: "0.85rem", marginBottom: "1rem" },
  btn: { width: "100%", background: "#3182ce", color: "#fff", border: "none", borderRadius: 4, padding: "0.75rem", cursor: "pointer", fontWeight: "bold", fontSize: "0.95rem" },
  hint: { marginTop: "0.75rem" },
  hintText: { color: "#68d391", fontSize: "0.85rem", margin: "0.25rem 0" },
};

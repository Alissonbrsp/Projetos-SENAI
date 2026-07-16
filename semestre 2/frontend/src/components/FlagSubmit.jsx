// FlagSubmit.jsx
import React, { useState } from "react";
import { flagService } from "../services/api";

const FLAGS = [
  { num: 1, title: "Credenciais no Frontend",    hint: "Inspecione o código-fonte da página." },
  { num: 2, title: "Metadados da EC2",           hint: "Explore o endpoint 169.254.169.254 de dentro do servidor." },
  { num: 3, title: "ACL MQTT Permissiva",        hint: "Assine um tópico wildcard com as credenciais do sensor." },
  { num: 4, title: "Path Traversal — Grafana",   hint: "Identifique a versão do Grafana e pesquise CVEs." },
  { num: 5, title: "Container Escape",           hint: "Quais recursos especiais este container tem?" },
];

export default function FlagSubmit({ arenaIp, arenaReady }) {
  const [selected, setSelected] = useState(1);
  const [value, setValue] = useState("");
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!value.trim()) return;
    setLoading(true);
    try {
      await flagService.submit(selected, value.trim());
      setResults(r => ({ ...r, [selected]: { ok: true, msg: "✅ Flag correta! Parabéns!" } }));
      setValue("");
    } catch (err) {
      const detail = err.response?.data?.detail || "Flag incorreta. Tente novamente.";
      setResults(r => ({ ...r, [selected]: { ok: false, msg: `❌ ${detail}` } }));
    } finally { setLoading(false); }
  };

  const flag = FLAGS.find(f => f.num === selected);
  const result = results[selected];

  return (
    <div style={styles.card}>
      <h2 style={styles.title}>🚩 Submeter Flag</h2>
      <div style={styles.flagList}>
        {FLAGS.map(f => (
          <button key={f.num} onClick={() => setSelected(f.num)}
            style={{ ...styles.flagBtn, ...(selected === f.num ? styles.flagBtnActive : {}), ...(results[f.num]?.ok ? styles.flagBtnDone : {}) }}>
            #{f.num} {results[f.num]?.ok ? "✓" : ""}
          </button>
        ))}
      </div>
      <div style={styles.flagInfo}>
        <strong style={{ color: "#e2e8f0" }}>{flag?.title}</strong>
        <p style={styles.hint}>💡 {flag?.hint}</p>
        {arenaReady && arenaIp && (
          <p style={styles.ipHint}>🖥️ Servidor: <code>{arenaIp}</code></p>
        )}
      </div>
      {result && (
        <div style={{ ...styles.result, color: result.ok ? "#68d391" : "#fc8181" }}>
          {result.msg}
        </div>
      )}
      <form onSubmit={submit} style={{ display: "flex", gap: "0.5rem" }}>
        <input
          style={styles.input}
          placeholder='FLAG{...}'
          value={value}
          onChange={e => setValue(e.target.value)}
          disabled={loading}
        />
        <button style={styles.btn} type="submit" disabled={loading || !value}>
          {loading ? "..." : "Enviar"}
        </button>
      </form>
    </div>
  );
}

const styles = {
  card: { background: "#1a1d27", border: "1px solid #2d3748", borderRadius: 8, padding: "1.5rem" },
  title: { color: "#e2e8f0", marginTop: 0, fontSize: "1.1rem" },
  flagList: { display: "flex", gap: "0.5rem", marginBottom: "1rem", flexWrap: "wrap" },
  flagBtn: { background: "#2d3748", color: "#a0aec0", border: "1px solid #4a5568", borderRadius: 4, padding: "0.3rem 0.6rem", cursor: "pointer", fontSize: "0.8rem" },
  flagBtnActive: { background: "#2b6cb0", color: "#fff", borderColor: "#3182ce" },
  flagBtnDone: { background: "#276749", color: "#68d391", borderColor: "#48bb78" },
  flagInfo: { background: "#0d1117", borderRadius: 6, padding: "0.75rem", marginBottom: "1rem" },
  hint: { color: "#a0aec0", fontSize: "0.8rem", margin: "0.5rem 0 0" },
  ipHint: { color: "#63b3ed", fontSize: "0.8rem", margin: "0.25rem 0 0" },
  result: { marginBottom: "0.75rem", fontSize: "0.85rem", fontWeight: "bold" },
  input: { flex: 1, background: "#2d3748", border: "1px solid #4a5568", borderRadius: 4, padding: "0.6rem", color: "#e2e8f0", fontSize: "0.85rem", fontFamily: "monospace" },
  btn: { background: "#3182ce", color: "#fff", border: "none", borderRadius: 4, padding: "0.6rem 1rem", cursor: "pointer", fontWeight: "bold" },
};

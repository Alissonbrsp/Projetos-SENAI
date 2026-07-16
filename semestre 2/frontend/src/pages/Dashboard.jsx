import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import ServerStatus from "../components/ServerStatus";
import FlagSubmit from "../components/FlagSubmit";
import { sessionService, authService } from "../services/api";
import { STATUS_POLL_INTERVAL } from "../config";

export default function Dashboard() {
  const [status, setStatus] = useState({ state: "unknown", ready: false, public_ip: null });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();
  const user = localStorage.getItem("ctf_user") || "jogador";

  const fetchStatus = useCallback(async () => {
    try {
      const res = await sessionService.getStatus();
      setStatus(res.data);
    } catch { /* silencioso */ }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, STATUS_POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleStart = async () => {
    setLoading(true); setMessage("");
    try {
      const res = await sessionService.start();
      setMessage(res.data.message || "Ambiente iniciando...");
      setTimeout(fetchStatus, 3000);
    } catch (err) {
      setMessage(err.response?.data?.detail || "Erro ao iniciar o ambiente.");
    } finally { setLoading(false); }
  };

  const handleLogout = async () => {
    try { await authService.logout(); } catch {}
    localStorage.clear();
    navigate("/login");
  };

  return (
    <div style={styles.page}>
      <Navbar user={user} onLogout={handleLogout} />
      <div style={styles.content}>
        <div style={styles.grid}>
          <ServerStatus status={status} onStart={handleStart} loading={loading} message={message} />
          <FlagSubmit arenaIp={status.public_ip} arenaReady={status.ready} />
        </div>
        <div style={styles.story}>
          <h3 style={styles.storyTitle}>🏭 Sua Missão</h3>
          <p style={styles.storyText}>
            Você foi contratado como pentester pela <strong>Fábrica Conectada SA</strong>.
            A infraestrutura industrial foi migrada para a nuvem sem auditoria de segurança adequada.
            Encontre as 5 flags escondidas ao longo da cadeia de ataque — do portal web ao servidor de dados industrial.
          </p>
          <p style={styles.storyText}>
            Comece pelo mais óbvio e vá fundo. A flag <strong>#1</strong> está bem na sua frente.
          </p>
        </div>
      </div>
    </div>
  );
}

const styles = {
  page: { minHeight: "100vh", background: "#0f1117", color: "#e2e8f0", fontFamily: "monospace" },
  content: { maxWidth: 1100, margin: "0 auto", padding: "2rem 1rem" },
  grid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "1.5rem" },
  story: { background: "#1a1d27", border: "1px solid #2d3748", borderRadius: 8, padding: "1.5rem" },
  storyTitle: { color: "#63b3ed", marginTop: 0 },
  storyText: { color: "#a0aec0", lineHeight: 1.7, marginBottom: "0.75rem" },
};

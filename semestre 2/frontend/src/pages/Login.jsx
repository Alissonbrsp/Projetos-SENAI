import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { authService } from "../services/api";

export default function Login() {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      if (mode === "register") {
        await authService.register(form);
        setMode("login");
        setError("Conta criada! Faça login.");
      } else {
        const res = await authService.login(form.username, form.password);
        localStorage.setItem("ctf_token", res.data.access_token);
        localStorage.setItem("ctf_user", res.data.username);
        navigate("/dashboard");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Erro ao processar a requisição.");
    } finally { setLoading(false); }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>🏭 CTF IIoT Dinâmico</h1>
        <p style={styles.sub}>Fábrica Conectada SA — Pentest Autorizado</p>
        <h2 style={styles.formTitle}>{mode === "login" ? "Entrar" : "Criar Conta"}</h2>
        {error && <div style={styles.error}>{error}</div>}
        <form onSubmit={submit}>
          <input style={styles.input} name="username" placeholder="Usuário" value={form.username} onChange={handle} required />
          {mode === "register" && <input style={styles.input} name="email" type="email" placeholder="E-mail" value={form.email} onChange={handle} required />}
          <input style={styles.input} name="password" type="password" placeholder="Senha" value={form.password} onChange={handle} required />
          <button style={styles.btn} type="submit" disabled={loading}>
            {loading ? "Aguarde..." : mode === "login" ? "Entrar" : "Criar Conta"}
          </button>
        </form>
        <button style={styles.link} onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "Criar nova conta" : "Já tenho conta"}
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#0f1117", fontFamily: "monospace" },
  card: { background: "#1a1d27", border: "1px solid #2d3748", borderRadius: 8, padding: "2rem", width: 360, color: "#e2e8f0" },
  title: { fontSize: "1.5rem", textAlign: "center", color: "#63b3ed", margin: "0 0 0.5rem" },
  sub: { textAlign: "center", color: "#718096", fontSize: "0.8rem", marginBottom: "1.5rem" },
  formTitle: { fontSize: "1.1rem", marginBottom: "1rem", color: "#a0aec0" },
  error: { background: "#2d1515", color: "#fc8181", padding: "0.5rem", borderRadius: 4, marginBottom: "1rem", fontSize: "0.85rem" },
  input: { width: "100%", background: "#2d3748", border: "1px solid #4a5568", borderRadius: 4, padding: "0.6rem", color: "#e2e8f0", marginBottom: "0.75rem", fontSize: "0.9rem", boxSizing: "border-box" },
  btn: { width: "100%", background: "#3182ce", color: "#fff", border: "none", borderRadius: 4, padding: "0.75rem", cursor: "pointer", fontWeight: "bold", fontSize: "1rem" },
  link: { width: "100%", background: "none", border: "none", color: "#63b3ed", cursor: "pointer", marginTop: "1rem", fontSize: "0.85rem", textDecoration: "underline" },
};

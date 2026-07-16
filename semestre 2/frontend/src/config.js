// =============================================================================
// Fábrica Conectada SA — Configuração do Portal CTF
// =============================================================================

// API base URL — carregada via variável de ambiente de build
export const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// URL do API Gateway (Lambda) para gerenciamento de sessão da VM3
export const SESSION_API_URL = process.env.REACT_APP_SESSION_API_URL || "";

// Timeout padrão para requests (ms)
export const REQUEST_TIMEOUT = 10000;

// Intervalo de polling para status da VM3 (ms)
export const STATUS_POLL_INTERVAL = 5000;

// Número máximo de jogadores simultâneos
export const MAX_PLAYERS = 5;

// ----- CONFIGURAÇÕES DE DESENVOLVIMENTO ----------------------------------------
// TODO: remover antes do deploy final — deixado para debug de conexão SSH
// ssh_debug_user: "ctf-player"
// ssh_debug_pass: "S3nh4_D3_D3bug_Temp0r4ria!"
// FLAG: FLAG{Fr0nt3nd_S0urc3_C0d3_1s_N0t_S3cur3}
// -------------------------------------------------------------------------------

-- =============================================================================
-- Schema PostgreSQL — CTF IIoT Dinâmico
-- VM1: Banco de dados de jogadores e sessões
-- =============================================================================

CREATE TABLE IF NOT EXISTS players (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50) UNIQUE NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    last_login    TIMESTAMPTZ,
    login_count   INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS flag_submissions (
    id          SERIAL PRIMARY KEY,
    player_id   INTEGER REFERENCES players(id) ON DELETE CASCADE,
    flag_number SMALLINT NOT NULL CHECK (flag_number BETWEEN 1 AND 5),
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    correct     BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(player_id, flag_number)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id         SERIAL PRIMARY KEY,
    player_id  INTEGER REFERENCES players(id),
    event_type VARCHAR(50) NOT NULL,
    details    JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_flag_submissions_player ON flag_submissions(player_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_player ON audit_log(player_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at);

-- View: ranking dos jogadores
CREATE OR REPLACE VIEW player_ranking AS
SELECT
    p.username,
    COUNT(CASE WHEN fs.correct THEN 1 END)       AS flags_found,
    MIN(CASE WHEN fs.correct THEN fs.submitted_at END) AS first_flag_at,
    MAX(CASE WHEN fs.correct THEN fs.submitted_at END) AS last_flag_at
FROM players p
LEFT JOIN flag_submissions fs ON fs.player_id = p.id
GROUP BY p.id, p.username
ORDER BY flags_found DESC, last_flag_at ASC;

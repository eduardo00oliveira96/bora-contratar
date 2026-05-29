CREATE TABLE notificacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    vaga_id UUID REFERENCES vagas(id) ON DELETE SET NULL,
    tipo VARCHAR(50) NOT NULL,
    titulo TEXT NOT NULL,
    mensagem TEXT,
    lida BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_notificacoes_usuario ON notificacoes(usuario_id, lida, created_at DESC);

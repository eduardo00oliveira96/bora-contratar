-- ==============================
-- USUARIOS (perfis vinculados ao Supabase Auth)
-- ==============================
CREATE TABLE IF NOT EXISTS usuarios (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    auth_user_id uuid UNIQUE,
    nome text NOT NULL,
    email text NOT NULL,
    papel text NOT NULL CHECK (papel IN ('superadmin', 'admin', 'rh', 'gestor')),
    ativo boolean DEFAULT true,
    created_at timestamptz DEFAULT now()
);

-- ==============================
-- ALTERACOES NA TABELA VAGAS
-- ==============================
ALTER TABLE vagas ADD COLUMN IF NOT EXISTS criado_por uuid REFERENCES usuarios(id);
ALTER TABLE vagas ADD COLUMN IF NOT EXISTS gestor_owner_id uuid REFERENCES usuarios(id);
ALTER TABLE vagas ADD COLUMN IF NOT EXISTS status_vaga text DEFAULT 'rascunho'
    CHECK (status_vaga IN ('rascunho', 'solicitada', 'publicada', 'encerrada'));

-- ==============================
-- INDICES
-- ==============================
CREATE INDEX IF NOT EXISTS idx_usuarios_tenant ON usuarios(tenant_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_auth ON usuarios(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_vagas_status ON vagas(status_vaga);
CREATE INDEX IF NOT EXISTS idx_vagas_gestor ON vagas(gestor_owner_id);

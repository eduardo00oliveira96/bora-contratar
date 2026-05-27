CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================
-- TENANTS (empresas/organizações)
-- ==============================
CREATE TABLE IF NOT EXISTS tenants (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nome text NOT NULL,
    slug text UNIQUE NOT NULL,
    created_at timestamptz DEFAULT now()
);

-- ==============================
-- VAGAS (por tenant)
-- ==============================
CREATE TABLE IF NOT EXISTS vagas (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    titulo text NOT NULL,
    descricao text,
    local_trabalho text,
    tipo_contrato text,
    requisitos text,
    habilidades text,
    salario numeric,
    divulgar_salario boolean DEFAULT false,
    beneficios text,
    user_created text,
    ativo boolean DEFAULT true,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- ==============================
-- CANDIDATOS (perfil do candidato, por tenant)
-- ==============================
CREATE TABLE IF NOT EXISTS candidatos (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    nome text NOT NULL,
    cpf text,
    telefone text,
    email text,
    created_at timestamptz DEFAULT now(),
    UNIQUE(tenant_id, cpf)
);

-- ==============================
-- CANDIDATURAS (relaciona candidato a uma vaga)
-- ==============================
CREATE TABLE IF NOT EXISTS candidaturas (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    vaga_id uuid NOT NULL REFERENCES vagas(id) ON DELETE CASCADE,
    candidato_id uuid REFERENCES candidatos(id) ON DELETE SET NULL,
    status text DEFAULT 'Em análise',
    nota numeric,
    resumo text,
    analise_detalhada text,
    pontos_fortes text,
    gaps_atencao text,
    recomendacao text,
    tags text,
    link_curriculo text,
    etapa_entrevista text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- ==============================
-- ÍNDICES
-- ==============================
CREATE INDEX IF NOT EXISTS idx_vagas_tenant ON vagas(tenant_id);
CREATE INDEX IF NOT EXISTS idx_candidatos_tenant ON candidatos(tenant_id);
CREATE INDEX IF NOT EXISTS idx_candidaturas_tenant ON candidaturas(tenant_id);
CREATE INDEX IF NOT EXISTS idx_candidaturas_vaga ON candidaturas(vaga_id);
CREATE INDEX IF NOT EXISTS idx_candidaturas_candidato ON candidaturas(candidato_id);

-- ==============================
-- FICHAS TECNICAS (templates de cargo)
-- ==============================
CREATE TABLE IF NOT EXISTS fichas_tecnicas (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    titulo text NOT NULL,
    descricao text,
    local_trabalho text,
    tipo_contrato text,
    requisitos text,
    habilidades text,
    salario numeric,
    beneficios text,
    ativo boolean DEFAULT true,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fichas_tenant ON fichas_tecnicas(tenant_id);

-- ==============================
-- REFERENCIA NA TABELA VAGAS
-- ==============================
ALTER TABLE vagas ADD COLUMN IF NOT EXISTS ficha_tecnica_id uuid REFERENCES fichas_tecnicas(id);

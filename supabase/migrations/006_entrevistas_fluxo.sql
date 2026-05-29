-- ==============================
-- ETAPAS DE ENTREVISTA POR VAGA
-- ==============================
CREATE TABLE IF NOT EXISTS etapas_entrevista (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    vaga_id uuid NOT NULL REFERENCES vagas(id) ON DELETE CASCADE,
    titulo text NOT NULL,
    descricao text,
    ordem int NOT NULL,
    responsavel_papel text,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_etapas_vaga ON etapas_entrevista(vaga_id);
CREATE INDEX IF NOT EXISTS idx_etapas_ordem ON etapas_entrevista(vaga_id, ordem);

-- ==============================
-- PROGRESSO DO CANDIDATO NAS ETAPAS
-- ==============================
CREATE TABLE IF NOT EXISTS entrevistas_candidato (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    candidatura_id uuid NOT NULL REFERENCES candidaturas(id) ON DELETE CASCADE,
    etapa_id uuid NOT NULL REFERENCES etapas_entrevista(id) ON DELETE CASCADE,
    status text DEFAULT 'pendente'
        CHECK (status IN ('pendente', 'agendado', 'realizado', 'aprovado', 'reprovado')),
    feedback text,
    agendado_para timestamptz,
    realizado_em timestamptz,
    entrevistador_id uuid REFERENCES usuarios(id),
    created_at timestamptz DEFAULT now(),
    UNIQUE(candidatura_id, etapa_id)
);

CREATE INDEX IF NOT EXISTS idx_entrevistas_candidatura ON entrevistas_candidato(candidatura_id);

-- ==============================
-- PIPELINE NA FICHA TECNICA
-- ==============================
ALTER TABLE fichas_tecnicas ADD COLUMN IF NOT EXISTS pipeline_personalizado BOOLEAN DEFAULT false;

-- ==============================
-- CAMPOS NA VAGA
-- ==============================
ALTER TABLE vagas ADD COLUMN IF NOT EXISTS pipeline_tipo text DEFAULT 'manual'
    CHECK (pipeline_tipo IN ('manual', 'pre_definido'));
ALTER TABLE vagas ADD COLUMN IF NOT EXISTS candidatura_contratada_id uuid REFERENCES candidaturas(id);
ALTER TABLE vagas ADD COLUMN IF NOT EXISTS data_conclusao timestamptz;

-- ==============================
-- NOVOS STATUS DA VAGA
-- ==============================
ALTER TABLE vagas DROP CONSTRAINT IF EXISTS vagas_status_vaga_check;
ALTER TABLE vagas ADD CONSTRAINT vagas_status_vaga_check
    CHECK (status_vaga IN (
        'rascunho', 'solicitada', 'em_triagem', 'aguardando_aprovacao',
        'aprovada', 'aprovada_ressalvas', 'em_recrutamento',
        'publicada', 'em_entrevistas', 'concluida', 'encerrada'
    ));

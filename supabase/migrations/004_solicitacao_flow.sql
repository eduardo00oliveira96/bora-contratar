-- ==============================
-- NOVOS CAMPOS NA TABELA VAGAS
-- ==============================
ALTER TABLE vagas ADD COLUMN IF NOT EXISTS tipo_solicitacao text
    CHECK (tipo_solicitacao IN ('aumento_quadro', 'substituicao', 'temporario', 'estagio'));
ALTER TABLE vagas ADD COLUMN IF NOT EXISTS justificativa text;
ALTER TABLE vagas ADD COLUMN IF NOT EXISTS centro_custo text;
ALTER TABLE vagas ADD COLUMN IF NOT EXISTS previsao_inicio date;
ALTER TABLE vagas ADD COLUMN IF NOT EXISTS parecer_rh text
    CHECK (parecer_rh IN ('validada', 'ajustes', 'reprovada_rh'));
ALTER TABLE vagas ADD COLUMN IF NOT EXISTS observacoes_rh text;

-- ==============================
-- TABELA DE APROVACOES (multi-aprovador)
-- ==============================
CREATE TABLE IF NOT EXISTS aprovacoes_solicitacao (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    vaga_id uuid NOT NULL REFERENCES vagas(id) ON DELETE CASCADE,
    usuario_id uuid NOT NULL REFERENCES usuarios(id),
    ordem_aprovacao int DEFAULT 1,
    parecer text DEFAULT 'pendente'
        CHECK (parecer IN ('pendente', 'aprovado', 'aprovado_ressalvas', 'reprovado')),
    observacoes text,
    criado_em timestamptz DEFAULT now(),
    respondido_em timestamptz,
    UNIQUE(vaga_id, usuario_id)
);

-- ==============================
-- ATUALIZA PAPEL DO USUARIO
-- ==============================
ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS usuarios_papel_check;
ALTER TABLE usuarios ADD CONSTRAINT usuarios_papel_check
    CHECK (papel IN ('superadmin', 'admin', 'rh', 'gestor', 'aprovador'));

-- ==============================
-- ATUALIZA STATUS DA VAGA
-- ==============================
ALTER TABLE vagas DROP CONSTRAINT IF EXISTS vagas_status_vaga_check;
ALTER TABLE vagas ADD CONSTRAINT vagas_status_vaga_check
    CHECK (status_vaga IN (
        'rascunho', 'solicitada', 'em_triagem', 'aguardando_aprovacao',
        'aprovada', 'aprovada_ressalvas', 'em_recrutamento', 'publicada', 'encerrada'
    ));

-- ==============================
-- INDICES
-- ==============================
CREATE INDEX IF NOT EXISTS idx_aprovacoes_vaga ON aprovacoes_solicitacao(vaga_id);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_usuario ON aprovacoes_solicitacao(usuario_id);
CREATE INDEX IF NOT EXISTS idx_vagas_tipo_solicitacao ON vagas(tipo_solicitacao);

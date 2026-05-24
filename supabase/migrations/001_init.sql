-- extensão necessária para UUID
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- TABELA VAGAS


CREATE TABLE IF NOT EXISTS vagas (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo text NOT NULL,
    descricao text,
    local_trabalho text,
    contrato_trabalho text,
    requisitos text,
    habilidades text,
    salario numeric,
    divulgacao_salario boolean DEFAULT false,
    user_created text,
    ativo boolean DEFAULT true,
    created_at timestamp DEFAULT now()
);


-- TABELA CANDIDATOS


CREATE TABLE IF NOT EXISTS candidatos (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nome text NOT NULL,
    cpf text UNIQUE,
    telefone text,
    resumo text,
    email text,
    status text DEFAULT 'Em análise',
    nota numeric,
    analise_detalhada text,
    pontos_fortes text,
    gaps_atencao text,
    recomendacao text,
    tags text,
    link_curriculo text,
    created_at timestamp DEFAULT now()
);


-- TABELA BENEFICIOS


CREATE TABLE IF NOT EXISTS beneficios (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nome_beneficio text NOT NULL
);


-- TABELA VAGA_BENEFICIOS


CREATE TABLE IF NOT EXISTS vaga_beneficios (
    vaga_id uuid NOT NULL REFERENCES vagas(id) ON DELETE CASCADE,
    beneficio_id uuid NOT NULL REFERENCES beneficios(id) ON DELETE CASCADE,
    PRIMARY KEY (vaga_id, beneficio_id)
);


-- TABELA PROCESSO SELETIVO


CREATE TABLE IF NOT EXISTS processo_seletivo (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    vaga_id uuid REFERENCES vagas(id) ON DELETE CASCADE,
    candidato_id uuid REFERENCES candidatos(id) ON DELETE CASCADE,
    etapa_processo text,
    usuario_rh text,
    usuario_gestor text,
    created_at timestamp DEFAULT now()
);
CREATE TABLE beneficios (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_beneficios_tenant ON beneficios(tenant_id);

CREATE TABLE ficha_beneficios (
    ficha_id UUID NOT NULL REFERENCES fichas_tecnicas(id) ON DELETE CASCADE,
    beneficio_id UUID NOT NULL REFERENCES beneficios(id) ON DELETE CASCADE,
    PRIMARY KEY (ficha_id, beneficio_id)
);

INSERT INTO beneficios (tenant_id, nome)
SELECT t.id, v.nome
FROM tenants t
CROSS JOIN (
    VALUES
        ('Vale Refeição'),
        ('Vale Transporte'),
        ('Plano de Saúde'),
        ('Plano Odontológico'),
        ('Auxílio Home Office'),
        ('Gympass')
) AS v(nome);

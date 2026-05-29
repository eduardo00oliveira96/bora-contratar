-- ==============================
-- ADD TENANT_ID TO ENTREVISTAS_CANDIDATO
-- ==============================

-- 1. Add column nullable first
ALTER TABLE entrevistas_candidato ADD COLUMN tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE;

-- 2. Backfill via etapas_entrevista -> vagas -> tenant_id
UPDATE entrevistas_candidato ec
SET tenant_id = v.tenant_id
FROM etapas_entrevista ee
JOIN vagas v ON v.id = ee.vaga_id
WHERE ec.etapa_id = ee.id;

-- 3. Make NOT NULL after backfill
ALTER TABLE entrevistas_candidato ALTER COLUMN tenant_id SET NOT NULL;

-- 4. Index
CREATE INDEX IF NOT EXISTS idx_entrevistas_candidato_tenant ON entrevistas_candidato(tenant_id);

-- 5. Add to unique constraint if needed (candidatura_id, etapa_id) should be unique per tenant
--    Not adding cross-tenant uniqueness since UUIDs are globally unique

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE agencies (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    code TEXT
);

CREATE TABLE naics_codes (
    code TEXT PRIMARY KEY,
    description TEXT
);

CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name TEXT NOT NULL,
    uei TEXT,
    cage_code TEXT,
    naics_codes TEXT[],
    capability_embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE company_aliases (
    id SERIAL PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    alias_name TEXT NOT NULL,
    source TEXT
);

CREATE TABLE contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    award_id TEXT UNIQUE,
    company_id UUID REFERENCES companies(id),
    agency_id INTEGER REFERENCES agencies(id),
    naics_code TEXT REFERENCES naics_codes(code),
    obligation_amount NUMERIC,
    date_signed DATE,
    description TEXT,
    raw_payload JSONB
);

CREATE TABLE contract_capabilities (
    contract_id UUID REFERENCES contracts(id),
    capability TEXT NOT NULL,
    PRIMARY KEY (contract_id, capability)
);

CREATE TABLE staging_usaspending_awards (
    id SERIAL PRIMARY KEY,
    raw_payload JSONB NOT NULL,
    pulled_at TIMESTAMPTZ DEFAULT now(),
    processed BOOLEAN DEFAULT false
);

CREATE TABLE staging_sam_entities (
    id SERIAL PRIMARY KEY,
    raw_payload JSONB NOT NULL,
    pulled_at TIMESTAMPTZ DEFAULT now(),
    processed BOOLEAN DEFAULT false
);

CREATE INDEX idx_contracts_company ON contracts(company_id);
CREATE INDEX idx_contracts_naics ON contracts(naics_code);
CREATE INDEX idx_company_capability_embedding ON companies USING hnsw (capability_embedding vector_cosine_ops);

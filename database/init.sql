-- FarmaCompare Database Initialization & Seed Data

-- Insert default pharmacies
INSERT INTO pharmacies (name, slug, active, created_at, updated_at)
VALUES
    ('Araujo', 'araujo', true, NOW(), NOW()),
    ('Pague Menos', 'pague-menos', true, NOW(), NOW()),
    ('Drogaria Raia', 'raia', true, NOW(), NOW()),
    ('Drogaria Pacheco', 'pacheco', true, NOW(), NOW()),
    ('Drogasil', 'drogasil', true, NOW(), NOW())
ON CONFLICT (slug) DO NOTHING;

-- Insert initial popular search terms for discovery
INSERT INTO search_terms (term, priority, search_count, active, created_at, updated_at)
VALUES
    ('dipirona', 10, 0, true, NOW(), NOW()),
    ('paracetamol', 9, 0, true, NOW(), NOW()),
    ('ibuprofeno', 8, 0, true, NOW(), NOW()),
    ('omeprazol', 7, 0, true, NOW(), NOW()),
    ('loratadina', 6, 0, true, NOW(), NOW()),
    ('simeticona', 5, 0, true, NOW(), NOW()),
    ('vitamina c', 5, 0, true, NOW(), NOW()),
    ('protetor solar', 4, 0, true, NOW(), NOW()),
    ('shampoo', 3, 0, true, NOW(), NOW()),
    ('creme dental', 3, 0, true, NOW(), NOW()),
    ('fralda', 3, 0, true, NOW(), NOW()),
    ('desodorante', 3, 0, true, NOW(), NOW())
ON CONFLICT (term) DO NOTHING;

-- Neon PostgreSQL Schema for coins2025
-- Migration from Google BigQuery

-- Create catalog table
CREATE TABLE IF NOT EXISTS catalog (
    coin_type VARCHAR(10) NOT NULL,
    year INTEGER NOT NULL,
    country VARCHAR(100) NOT NULL,
    series VARCHAR(100) NOT NULL,
    value FLOAT NOT NULL,
    coin_id VARCHAR(100) NOT NULL PRIMARY KEY,
    image_url TEXT,
    feature TEXT,
    volume TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes on frequently queried columns
CREATE INDEX IF NOT EXISTS idx_catalog_year ON catalog(year DESC);
CREATE INDEX IF NOT EXISTS idx_catalog_country ON catalog(country);
CREATE INDEX IF NOT EXISTS idx_catalog_coin_type ON catalog(coin_type);
CREATE INDEX IF NOT EXISTS idx_catalog_series ON catalog(series);
CREATE INDEX IF NOT EXISTS idx_catalog_country_coin_type_year ON catalog(country, coin_type, year);

-- Create history table
CREATE TABLE IF NOT EXISTS history (
    id UUID NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    coin_id VARCHAR(100) NOT NULL,
    date TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT true,
    FOREIGN KEY (coin_id) REFERENCES catalog(coin_id) ON DELETE RESTRICT
);

-- Create indexes on history table
CREATE INDEX IF NOT EXISTS idx_history_coin_id ON history(coin_id);
CREATE INDEX IF NOT EXISTS idx_history_name ON history(name);
CREATE INDEX IF NOT EXISTS idx_history_name_coin_id ON history(name, coin_id);
CREATE INDEX IF NOT EXISTS idx_history_created_at ON history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_history_date ON history(date DESC);
CREATE INDEX IF NOT EXISTS idx_history_is_active ON history(is_active);
CREATE INDEX IF NOT EXISTS idx_history_name_coin_id_created_at ON history(name, coin_id, created_at DESC);

-- Create groups table
CREATE TABLE IF NOT EXISTS groups (
    id UUID NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
    group_key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes on groups table
CREATE INDEX IF NOT EXISTS idx_groups_group_key ON groups(group_key);
CREATE INDEX IF NOT EXISTS idx_groups_is_active ON groups(is_active);

-- Create group_users table
CREATE TABLE IF NOT EXISTS group_users (
    id UUID NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    alias VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
    UNIQUE(group_id, name)
);

-- Create indexes on group_users table
CREATE INDEX IF NOT EXISTS idx_group_users_group_id ON group_users(group_id);
CREATE INDEX IF NOT EXISTS idx_group_users_name ON group_users(name);
CREATE INDEX IF NOT EXISTS idx_group_users_group_id_is_active ON group_users(group_id, is_active);
CREATE INDEX IF NOT EXISTS idx_group_users_is_active ON group_users(is_active);

-- Add comments for clarity
COMMENT ON TABLE catalog IS 'Coin catalog with denomination and year information';
COMMENT ON TABLE history IS 'Ownership history tracking when users acquire or sell coins';
COMMENT ON TABLE groups IS 'User groups/collections for organizing shared coin collections';
COMMENT ON TABLE group_users IS 'Members of groups with their display aliases';

COMMENT ON COLUMN history.is_active IS 'true = coin is owned, false = coin was sold/removed';
COMMENT ON COLUMN groups.is_active IS 'true = active group, false = soft-deleted group';
COMMENT ON COLUMN group_users.is_active IS 'true = active member, false = removed from group';

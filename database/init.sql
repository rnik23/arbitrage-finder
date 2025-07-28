-- Database initialization script for arbitrage finder

-- Create tables for storing arbitrage data
CREATE TABLE IF NOT EXISTS arbitrage_runs (
    id SERIAL PRIMARY KEY,
    sport VARCHAR(50) NOT NULL,
    run_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    events_count INTEGER DEFAULT 0,
    arbitrages_found INTEGER DEFAULT 0,
    bookmakers_included TEXT[],
    game_status VARCHAR(20) DEFAULT 'all',
    api_requests_used INTEGER DEFAULT 0,
    api_requests_remaining INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES arbitrage_runs(id),
    event_id VARCHAR(100) NOT NULL,
    sport VARCHAR(50) NOT NULL,
    market_type VARCHAR(20) NOT NULL, -- h2h, totals, spreads
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,
    event_time TIMESTAMP WITH TIME ZONE,
    roi_percentage DECIMAL(5,2) NOT NULL,
    total_stake DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS arbitrage_stakes (
    id SERIAL PRIMARY KEY,
    arbitrage_id INTEGER REFERENCES arbitrage_opportunities(id),
    stake_type VARCHAR(20) NOT NULL, -- home, away, over, under, draw
    bookmaker VARCHAR(50) NOT NULL,
    price DECIMAL(8,3) NOT NULL,
    american_odds VARCHAR(10),
    stake_amount DECIMAL(10,2) NOT NULL,
    betting_link TEXT,
    point_spread DECIMAL(4,1), -- for totals/spreads
    outcome_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS odds_snapshots (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES arbitrage_runs(id),
    event_id VARCHAR(100) NOT NULL,
    sport VARCHAR(50) NOT NULL,
    bookmaker VARCHAR(50) NOT NULL,
    market_type VARCHAR(20) NOT NULL,
    outcome_name VARCHAR(100) NOT NULL,
    price DECIMAL(8,3) NOT NULL,
    snapshot_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_arbitrage_runs_sport_time ON arbitrage_runs(sport, run_timestamp);
CREATE INDEX idx_arbitrage_opportunities_sport_time ON arbitrage_opportunities(sport, event_time);
CREATE INDEX idx_arbitrage_stakes_bookmaker ON arbitrage_stakes(bookmaker);
CREATE INDEX idx_odds_snapshots_event_bookmaker ON odds_snapshots(event_id, bookmaker);

-- Create a view for easy arbitrage analysis
CREATE VIEW arbitrage_summary AS
SELECT 
    ar.sport,
    ar.run_timestamp,
    ao.event_id,
    ao.home_team,
    ao.away_team,
    ao.market_type,
    ao.roi_percentage,
    COUNT(ast.id) as stakes_count,
    SUM(ast.stake_amount) as total_stake,
    STRING_AGG(DISTINCT ast.bookmaker, ', ') as bookmakers_used
FROM arbitrage_runs ar
JOIN arbitrage_opportunities ao ON ar.id = ao.run_id
JOIN arbitrage_stakes ast ON ao.id = ast.arbitrage_id
GROUP BY ar.sport, ar.run_timestamp, ao.event_id, ao.home_team, ao.away_team, ao.market_type, ao.roi_percentage;

-- Insert initial data
INSERT INTO arbitrage_runs (sport, events_count, arbitrages_found, bookmakers_included) 
VALUES ('setup', 0, 0, ARRAY['Initial Setup']);

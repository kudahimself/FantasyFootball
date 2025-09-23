#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from django.db import connection

def create_missing_tables():
    cursor = connection.cursor()

    # Create player_matches table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS player_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_name VARCHAR(200) NOT NULL,
        season VARCHAR(20) NOT NULL,
        date DATE NOT NULL,
        competition VARCHAR(100) NOT NULL,
        round_info VARCHAR(100),
        opponent VARCHAR(100) NOT NULL,
        result VARCHAR(20) NOT NULL,
        position VARCHAR(50),
        minutes_played INTEGER DEFAULT 0,
        goals INTEGER DEFAULT 0,
        assists INTEGER DEFAULT 0,
        points INTEGER DEFAULT 0,
        elo_after_match REAL NOT NULL,
        saves INTEGER DEFAULT 0,
        goals_conceded INTEGER DEFAULT 0,
        clean_sheet BOOLEAN DEFAULT 0,
        created_at DATETIME,
        updated_at DATETIME
    );
    ''')

    # Create elo_calculations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS elo_calculations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_name VARCHAR(200) NOT NULL,
        week INTEGER NOT NULL,
        season VARCHAR(20) NOT NULL,
        elo REAL NOT NULL,
        previous_elo REAL,
        elo_change REAL DEFAULT 0.0,
        matches_played INTEGER DEFAULT 0,
        last_match_date DATE,
        created_at DATETIME,
        updated_at DATETIME
    );
    ''')

    # Create players table (if missing)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(200) NOT NULL,
        position VARCHAR(50) NOT NULL,
        elo REAL NOT NULL,
        cost REAL NOT NULL,
        week INTEGER NOT NULL,
        team VARCHAR(100),
        competition VARCHAR(100),
        created_at DATETIME,
        updated_at DATETIME
    );
    ''')

    # Create indexes for better performance
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_player_matches_name_date ON player_matches(player_name, date);',
        'CREATE INDEX IF NOT EXISTS idx_player_matches_name_season ON player_matches(player_name, season);',
        'CREATE INDEX IF NOT EXISTS idx_player_matches_date_comp ON player_matches(date, competition);',
        'CREATE INDEX IF NOT EXISTS idx_player_matches_name_elo ON player_matches(player_name, elo_after_match);',
    'CREATE INDEX IF NOT EXISTS idx_elo_calculations_name_week ON elo_calculations(player_name, week);',
    'CREATE INDEX IF NOT EXISTS idx_elo_calculations_week_season ON elo_calculations(week, season);',
    'CREATE INDEX IF NOT EXISTS idx_elo_calculations_elo ON elo_calculations(elo DESC);',
        'CREATE INDEX IF NOT EXISTS idx_players_name_week ON players(name, week);',
        'CREATE INDEX IF NOT EXISTS idx_players_elo ON players(elo DESC);',
        'CREATE INDEX IF NOT EXISTS idx_players_position ON players(position);'
    ]

    for index_sql in indexes:
        cursor.execute(index_sql)

    # Create unique constraints
    unique_constraints = [
        'CREATE UNIQUE INDEX IF NOT EXISTS idx_player_matches_unique ON player_matches(player_name, date, opponent);',
        'CREATE UNIQUE INDEX IF NOT EXISTS idx_elo_calculations_unique ON elo_calculations(player_name, week, season);',
        'CREATE UNIQUE INDEX IF NOT EXISTS idx_players_unique ON players(name, week);'
    ]

    for constraint_sql in unique_constraints:
        try:
            cursor.execute(constraint_sql)
        except Exception as e:
            print(f"Warning: Could not create constraint: {e}")

    connection.commit()
    print('✅ Database tables created successfully!')
    
    # Verify tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('player_matches', 'elo_calculations', 'players');")
    tables = cursor.fetchall()
    
    print(f"✅ Found {len(tables)} tables: {[table[0] for table in tables]}")
    
    # Check table schemas
    for table_name in ['player_matches', 'elo_calculations', 'players']:
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print(f"✅ Table '{table_name}' has {len(columns)} columns")

if __name__ == '__main__':
    create_missing_tables()
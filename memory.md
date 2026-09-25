# Database Migration Strategy

## Current Database Schema Version 1

The database at `/data/skybreak.db` has the following schema (Version 1):

### Tables

1. **settings**
   - `key` (TEXT, PRIMARY KEY)
   - `value` (TEXT)

2. **flights**
   - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `airport_icao` (TEXT)
   - `airport_name` (TEXT)
   - `destination_icao` (TEXT)
   - `destination_name` (TEXT)
   - `flight_direction` (TEXT)
   - `departure_time` (TEXT)
   - `arrival_time` (TEXT)
   - `duration_minutes` (INTEGER)
   - `flight_number` (TEXT)
   - `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

3. **airports** (in skybreak/airport.py)
   - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `code` (TEXT UNIQUE NOT NULL)
   - `name` (TEXT)
   - `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

### Migration History

- **Version 1** (current): Initial schema with `settings` and `flights` tables
  - Created by `init_db.py` in the root
  - Includes automatic cleanup of old `api_key` and `fetch_months` settings
  - Migrates `departure` column to `departure_time` if needed
  - Adds `airport_name` and `destination_name` columns to `flights` table

## Migration Strategy

### Core Principles

1. **Schema Versioning**: Each migration increments the schema version
2. **Atomic Migrations**: Each migration is a single, reversible operation
3. **Idempotent**: Migrations can be safely re-run
4. **Backward Compatible**: New columns are added with defaults, old columns kept

### Migration Steps

#### Migration 1 (Version 1) - Initial Schema
- Create `settings` table (key, value)
- Create `flights` table with all required columns
- Handle migration from `departure` to `departure_time` if needed
- Initialize `airports` table (via `add_airport` function)

#### Future Migrations (Version N+)
- Add new columns to existing tables
- Rename or reorganize tables as needed
- Preserve backward compatibility

### Implementation Plan

1. **Save Schema Version**: Store the current schema definition in the database metadata
2. **Apply Startup Migrations**: During container startup, run schema migrations to ensure the database matches the expected schema
3. **Automated Migration**: The `init_db()` functions in both `init_db.py` and `skybreak/airport.py` handle schema creation and migration

### Unused Tables/Columns

After reviewing the code:
- The `flights_new` table in `skybreak/airport.py` (line 16) appears to be a legacy table that should be removed
- The `airports` table in `skybreak/airport.py` (line 11) is actually used and should be kept
- All columns in the `flights` table appear to be actively used by the application

### Resulting Schema (Version 1)

The final schema for Version 1 is:

```sql
-- Table: settings
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- Table: flights
CREATE TABLE IF NOT EXISTS flights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    airport_icao TEXT,
    airport_name TEXT,
    destination_icao TEXT,
    destination_name TEXT,
    flight_direction TEXT,
    departure_time TEXT,
    arrival_time TEXT,
    duration_minutes INTEGER,
    flight_number TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: airports
CREATE TABLE IF NOT EXISTS airports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

All migrations should increment the version number (e.g., V2, V3) when new schema changes are introduced.

## DB Migration Strategy (Updated 2026-09-25)
- DB schema version saved in db_version table inside DB.
- Each schema change gets its own migration step increasing version.
- All steps applied at container startup via skybreak/db_migrate.py.
- Unused init scripts removed (init_db.py deleted); runtime uses db_migrate.apply_migrations().
- Schema v1: airports, settings, flights (used cols only), db_version.
- Never edit DB/container live — only code + build + redeploy.

# GitHub Auth Token
GITHUB_PERSONAL_ACCESS_TOKEN available for PR creation/merge via API.
Reference as GH_TOKEN=\$GITHUB_TOKEN when using gh CLI.

#!/usr/bin/env python3
"""
Database setup script for Wildlife Camera Trap Game.
Creates SQLite database with required tables and indexes.
"""

import sqlite3
import os
import sys

DATABASE_PATH = 'camera_trap_data.db'

def create_database():
    """Create database and all required tables."""

    # Remove existing database if it exists
    if os.path.exists(DATABASE_PATH):
        print(f"Removing existing database: {DATABASE_PATH}")
        os.remove(DATABASE_PATH)

    # Create new database connection
    print(f"Creating new database: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute('PRAGMA foreign_keys = ON')

    # Create taxa table
    print("Creating taxa table...")
    cursor.execute('''
        CREATE TABLE taxa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kingdom TEXT,
            phylum TEXT,
            subphylum TEXT,
            superclass TEXT,
            class TEXT,
            subclass TEXT,
            infraclass TEXT,
            superorder TEXT,
            order_ TEXT,
            suborder TEXT,
            infraorder TEXT,
            superfamily TEXT,
            family TEXT,
            subfamily TEXT,
            tribe TEXT,
            genus TEXT,
            subgenus TEXT,
            species TEXT,
            subspecies TEXT,
            variety TEXT,
            common_name TEXT,
            most_specific_level TEXT,
            most_specific_name TEXT
        )
    ''')

    # Create sequences table
    print("Creating sequences table...")
    cursor.execute('''
        CREATE TABLE sequences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sequence_id TEXT,
            taxon_id INTEGER,
            location_id TEXT,
            datetime TEXT,
            FOREIGN KEY (taxon_id) REFERENCES taxa (id),
            UNIQUE(sequence_id, taxon_id)
        )
    ''')

    # Create images table
    print("Creating images table...")
    cursor.execute('''
        CREATE TABLE images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_id TEXT UNIQUE,
            sequence_table_id INTEGER,
            frame_num INTEGER,
            url_gcp TEXT,
            url_aws TEXT,
            url_azure TEXT,
            FOREIGN KEY (sequence_table_id) REFERENCES sequences (id)
        )
    ''')

    # Create high_scores table
    print("Creating high_scores table...")
    cursor.execute('''
        CREATE TABLE high_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            game_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create indexes for performance
    print("Creating indexes...")

    # Indexes for taxa table
    cursor.execute('CREATE INDEX idx_taxa_names ON taxa(most_specific_name, common_name)')
    cursor.execute('CREATE INDEX idx_taxa_levels ON taxa(most_specific_level)')

    # Indexes for sequences table
    cursor.execute('CREATE INDEX idx_sequences_taxon ON sequences(taxon_id)')
    cursor.execute('CREATE INDEX idx_sequences_id ON sequences(sequence_id)')

    # Indexes for images table
    cursor.execute('CREATE INDEX idx_images_sequence ON images(sequence_table_id)')
    cursor.execute('CREATE INDEX idx_images_frame ON images(frame_num)')

    # Index for high scores
    cursor.execute('CREATE INDEX idx_high_scores_score ON high_scores(score DESC)')

    # Commit changes
    conn.commit()
    print("Database schema created successfully!")

    # Verify tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Created tables: {[table[0] for table in tables]}")

    conn.close()
    return True

def verify_database():
    """Verify database structure is correct."""

    if not os.path.exists(DATABASE_PATH):
        print(f"Error: Database {DATABASE_PATH} not found!")
        return False

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Check all required tables exist
    required_tables = ['taxa', 'sequences', 'images', 'high_scores']
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]

    missing_tables = [table for table in required_tables if table not in existing_tables]
    if missing_tables:
        print(f"Error: Missing tables: {missing_tables}")
        conn.close()
        return False

    # Check taxa table structure
    cursor.execute("PRAGMA table_info(taxa)")
    taxa_columns = [row[1] for row in cursor.fetchall()]
    required_taxa_columns = [
        'id', 'kingdom', 'phylum', 'subphylum', 'superclass', 'class', 'subclass',
        'infraclass', 'superorder', 'order_', 'suborder', 'infraorder', 'superfamily',
        'family', 'subfamily', 'tribe', 'genus', 'subgenus', 'species', 'subspecies',
        'variety', 'common_name', 'most_specific_level', 'most_specific_name'
    ]

    missing_columns = [col for col in required_taxa_columns if col not in taxa_columns]
    if missing_columns:
        print(f"Error: Taxa table missing columns: {missing_columns}")
        conn.close()
        return False

    print("Database structure verification passed!")
    conn.close()
    return True

def main():
    """Main function to set up database."""

    print("Wildlife Camera Trap Game - Database Setup")
    print("=" * 50)

    try:
        # Create database
        success = create_database()
        if not success:
            print("Failed to create database!")
            sys.exit(1)

        # Verify database
        success = verify_database()
        if not success:
            print("Database verification failed!")
            sys.exit(1)

        print("\nDatabase setup completed successfully!")
        print(f"Database location: {os.path.abspath(DATABASE_PATH)}")
        print("\nNext steps:")
        print("1. Run: python data_processor.py --csv-path /path/to/your/data.csv")
        print("2. Run: python app.py")

    except Exception as e:
        print(f"Error during database setup: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

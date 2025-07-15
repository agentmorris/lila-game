#!/usr/bin/env python3
"""
Database models and queries for Wildlife Camera Trap Game.
"""

import sqlite3
import random
import os
from typing import List, Dict, Optional, Tuple

# Support environment variable override for database path (useful for Docker)
DATABASE_PATH = os.getenv('DATABASE_PATH')

if not DATABASE_PATH:
    # Auto-detect database location
    possible_paths = [
        '/app/data/camera_trap_data.db',  # Docker volume mount
        'data/camera_trap_data.db',      # Local development with data dir
        'camera_trap_data.db'            # Local development, current dir
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            DATABASE_PATH = path
            print(f"DEBUG: Found database at: {DATABASE_PATH}")
            break
    
    if not DATABASE_PATH:
        # Default to Docker path (will be created if needed)
        DATABASE_PATH = '/app/data/camera_trap_data.db'
        print(f"DEBUG: No existing database found, using default: {DATABASE_PATH}")

print(f"DEBUG: Using database path: {DATABASE_PATH}")

def get_db_connection():
    """Get database connection with optimizations."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    conn.execute('PRAGMA cache_size = 10000')  # Increase cache size
    conn.execute('PRAGMA temp_store = memory')  # Use memory for temp storage
    return conn

class Taxa:
    """Model for taxa data."""
    
    @staticmethod
    def get_random_taxa(count: int) -> List[Dict]:
        """Get random taxa for a game (family level or lower only)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Define acceptable taxonomic levels (family and below)
        acceptable_levels = ['variety', 'subspecies', 'species', 'subgenus', 'genus', 'tribe', 'subfamily', 'family']
        level_placeholders = ','.join(['?'] * len(acceptable_levels))
        
        # Get random taxa that have sequences and are at family level or lower
        cursor.execute(f'''
            SELECT DISTINCT t.* FROM taxa t
            JOIN sequences s ON t.id = s.taxon_id
            WHERE t.most_specific_level IN ({level_placeholders})
            ORDER BY RANDOM()
            LIMIT ?
        ''', acceptable_levels + [count])
        
        taxa = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return taxa
    
    @staticmethod
    def get_taxon_by_id(taxon_id: int) -> Optional[Dict]:
        """Get a specific taxon by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM taxa WHERE id = ?', (taxon_id,))
        row = cursor.fetchone()
        
        conn.close()
        return dict(row) if row else None
    
    @staticmethod
    def search_taxa(query: str, limit: int = 20) -> List[Dict]:
        """Search taxa by name (scientific or common)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = f"%{query.lower()}%"
        
        # Search in most_specific_name and common_name
        cursor.execute('''
            SELECT id, most_specific_name, most_specific_level, common_name,
                   kingdom, phylum, class, order_, family, genus, species
            FROM taxa 
            WHERE (LOWER(most_specific_name) LIKE ? OR LOWER(common_name) LIKE ?)
              AND most_specific_name IS NOT NULL
            ORDER BY 
                CASE WHEN LOWER(most_specific_name) = LOWER(?) THEN 1
                     WHEN LOWER(common_name) = LOWER(?) THEN 2
                     WHEN LOWER(most_specific_name) LIKE ? THEN 3
                     WHEN LOWER(common_name) LIKE ? THEN 4
                     ELSE 5 END,
                most_specific_name
            LIMIT ?
        ''', (query, query, query.strip('%'), query.strip('%'), 
              f"{query.strip('%')}%", f"{query.strip('%')}%", limit))
        
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            # Add display name for UI
            display_name = result['most_specific_name']
            if result['common_name']:
                display_name += f" ({result['common_name']})"
            result['display_name'] = display_name
            results.append(result)
        
        conn.close()
        return results

class Sequences:
    """Model for sequence data."""
    
    @staticmethod
    def get_sequences_for_taxon(taxon_id: int, count: int = 4) -> List[Dict]:
        """Get random sequences for a specific taxon."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM sequences 
            WHERE taxon_id = ? 
            ORDER BY RANDOM() 
            LIMIT ?
        ''', (taxon_id, count))
        
        sequences = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return sequences
    
    @staticmethod
    def get_sequence_by_id(sequence_id: int) -> Optional[Dict]:
        """Get a specific sequence by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM sequences WHERE id = ?', (sequence_id,))
        row = cursor.fetchone()
        
        conn.close()
        return dict(row) if row else None

class Images:
    """Model for image data."""
    
    @staticmethod
    def get_images_for_sequences(sequence_ids: List[int], cloud_preference: str = 'gcp') -> List[Dict]:
        """Get images for given sequences (max 10 per sequence), ordered by sequence and frame."""
        if not sequence_ids:
            return []
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholders = ','.join(['?'] * len(sequence_ids))
        cursor.execute(f'''
            SELECT *
            FROM (
                SELECT i.*, s.sequence_id as original_sequence_id,
                       ROW_NUMBER() OVER (PARTITION BY i.sequence_table_id ORDER BY i.frame_num) as rn
                FROM images i
                JOIN sequences s ON i.sequence_table_id = s.id
                WHERE i.sequence_table_id IN ({placeholders})
            ) 
            WHERE rn <= 10
            ORDER BY sequence_table_id, frame_num
        ''', sequence_ids)
        
        images = []
        for row in cursor.fetchall():
            image = dict(row)
            
            # Select preferred URL
            if cloud_preference == 'aws' and image['url_aws']:
                image['url'] = image['url_aws']
            elif cloud_preference == 'azure' and image['url_azure']:
                image['url'] = image['url_azure']
            else:  # Default to GCP
                image['url'] = image['url_gcp']
            
            images.append(image)
        
        conn.close()
        return images

class HighScores:
    """Model for high scores."""
    
    @staticmethod
    def get_top_scores(limit: int = 10) -> List[Dict]:
        """Get top high scores."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT player_name, score, game_date
            FROM high_scores 
            ORDER BY score DESC, game_date ASC
            LIMIT ?
        ''', (limit,))
        
        scores = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return scores
    
    @staticmethod
    def add_score(player_name: str, score: int) -> bool:
        """Add a new high score and maintain top 10."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Insert new score
            cursor.execute('''
                INSERT INTO high_scores (player_name, score)
                VALUES (?, ?)
            ''', (player_name, score))
            
            # Keep only top 10 scores
            cursor.execute('''
                DELETE FROM high_scores 
                WHERE id NOT IN (
                    SELECT id FROM high_scores 
                    ORDER BY score DESC, game_date ASC 
                    LIMIT 10
                )
            ''')
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error adding high score: {e}")
            conn.rollback()
            return False
        
        finally:
            conn.close()
    
    @staticmethod
    def is_high_score(score: int) -> bool:
        """Check if a score qualifies for the high score list."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if we have less than 10 scores, or if this score is higher than the lowest
        cursor.execute('''
            SELECT COUNT(*) as count, MIN(score) as min_score
            FROM high_scores
        ''')
        
        row = cursor.fetchone()
        count = row['count']
        min_score = row['min_score'] if row['min_score'] is not None else 0
        
        conn.close()
        
        # Qualifies if less than 10 scores, or score is higher than minimum
        return count < 10 or score > min_score

class GameData:
    """Helper class for game-specific data operations."""
    
    @staticmethod
    def get_taxon_statistics() -> Dict:
        """Get database statistics for debugging."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Count taxa
        cursor.execute('SELECT COUNT(*) as count FROM taxa')
        stats['taxa_count'] = cursor.fetchone()['count']
        
        # Count sequences
        cursor.execute('SELECT COUNT(*) as count FROM sequences')
        stats['sequences_count'] = cursor.fetchone()['count']
        
        # Count images
        cursor.execute('SELECT COUNT(*) as count FROM images')
        stats['images_count'] = cursor.fetchone()['count']
        
        # Taxa by level
        cursor.execute('''
            SELECT most_specific_level, COUNT(*) as count 
            FROM taxa 
            WHERE most_specific_level IS NOT NULL
            GROUP BY most_specific_level
            ORDER BY count DESC
        ''')
        stats['taxa_by_level'] = dict(cursor.fetchall())
        
        # Sequences per taxon stats
        cursor.execute('''
            SELECT COUNT(s.id) as seq_count
            FROM taxa t
            LEFT JOIN sequences s ON t.id = s.taxon_id
            GROUP BY t.id
            HAVING seq_count > 0
        ''')
        seq_counts = [row['seq_count'] for row in cursor.fetchall()]
        if seq_counts:
            stats['sequences_per_taxon'] = {
                'min': min(seq_counts),
                'max': max(seq_counts),
                'avg': sum(seq_counts) / len(seq_counts)
            }
        
        conn.close()
        return stats
    
    @staticmethod
    def validate_database() -> Dict[str, bool]:
        """Validate database integrity."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        validation = {}
        
        try:
            # Check if we have taxa with sequences
            cursor.execute('''
                SELECT COUNT(*) as count FROM taxa t
                JOIN sequences s ON t.id = s.taxon_id
            ''')
            taxa_with_sequences = cursor.fetchone()['count']
            validation['has_playable_taxa'] = taxa_with_sequences > 0
            
            # Check if sequences have images
            cursor.execute('''
                SELECT COUNT(*) as count FROM sequences s
                JOIN images i ON s.id = i.sequence_table_id
            ''')
            sequences_with_images = cursor.fetchone()['count']
            validation['sequences_have_images'] = sequences_with_images > 0
            
            # Check for valid image URLs
            cursor.execute('''
                SELECT COUNT(*) as count FROM images
                WHERE url_gcp IS NOT NULL OR url_aws IS NOT NULL OR url_azure IS NOT NULL
            ''')
            images_with_urls = cursor.fetchone()['count']
            validation['images_have_urls'] = images_with_urls > 0
            
            # Check taxa have scientific names
            cursor.execute('''
                SELECT COUNT(*) as count FROM taxa
                WHERE most_specific_name IS NOT NULL AND most_specific_name != ''
            ''')
            taxa_with_names = cursor.fetchone()['count']
            validation['taxa_have_names'] = taxa_with_names > 0
            
        except Exception as e:
            print(f"Validation error: {e}")
            validation['database_accessible'] = False
        
        finally:
            conn.close()
        
        return validation
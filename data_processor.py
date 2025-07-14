#!/usr/bin/env python3
"""
Memory-optimized data processor for Wildlife Camera Trap Game.
Two-pass approach to handle large CSV files efficiently with robust null handling.
"""

import pandas as pd
import sqlite3
import sys
import os
import argparse
import time
from collections import defaultdict

DATABASE_PATH = 'camera_trap_data.db'

# Taxonomic columns in hierarchical order
TAXONOMY_COLUMNS = [
    'kingdom', 'phylum', 'subphylum', 'superclass', 'class', 'subclass',
    'infraclass', 'superorder', 'order', 'suborder', 'infraorder',
    'superfamily', 'family', 'subfamily', 'tribe', 'genus', 'subgenus',
    'species', 'subspecies', 'variety'
]

def safe_str(value):
    """Safely convert value to string, handling None/NaN values."""
    if value is None or pd.isna(value):
        return ''
    return str(value).strip()

def find_most_specific_level(row):
    """Find the most specific taxonomic level for a row."""
    for level in reversed(TAXONOMY_COLUMNS):
        value = safe_str(row.get(level, ''))
        if value and value.lower() not in ['', 'nan', 'none', 'null']:
            return level, value
    return None, None

def is_wildlife_row(row):
    """Check if a row contains wildlife data (non-empty taxonomy)."""
    for column in TAXONOMY_COLUMNS:
        value = safe_str(row.get(column, ''))
        if value and value.lower() not in ['', 'nan', 'none', 'null']:
            return True

    # Also check common_name
    common_name = safe_str(row.get('common_name', ''))
    if common_name and common_name.lower() not in ['', 'nan', 'none', 'null', 'empty']:
        return True

    return False

def create_taxon_key(row):
    """Create a unique key for a taxon based on taxonomy columns."""
    values = []
    for column in TAXONOMY_COLUMNS:
        value = safe_str(row.get(column, ''))
        if value and value.lower() not in ['', 'nan', 'none', 'null']:
            values.append(value)
        else:
            values.append('')

    # Include common name in the key
    common_name = safe_str(row.get('common_name', ''))
    if common_name and common_name.lower() not in ['', 'nan', 'none', 'null', 'empty']:
        values.append(common_name)
    else:
        values.append('')

    return tuple(values)

def get_csv_row_count(csv_path, debug_limit=None):
    """Get total row count for progress tracking."""
    print("Counting rows in CSV file...")
    start_time = time.time()

    try:
        row_count = 0
        with open(csv_path, 'r', encoding='utf-8') as f:
            next(f)  # Skip header
            for _ in f:
                row_count += 1
                if debug_limit and row_count >= debug_limit:
                    break
                if row_count % 1000000 == 0:
                    print(f"  Counted {row_count:,} rows so far...")

        elapsed = time.time() - start_time
        if debug_limit and row_count >= debug_limit:
            print(f"Debug mode: limiting to first {row_count:,} rows (counted in {elapsed:.1f} seconds)")
        else:
            print(f"Total rows: {row_count:,} (counted in {elapsed:.1f} seconds)")
        return row_count

    except Exception as e:
        print(f"Could not count rows efficiently: {e}")
        return None

def pass_1_extract_taxa(csv_path, debug_limit=None):
    """Pass 1: Extract unique taxa and insert into database."""

    print("\n" + "="*60)
    print("PASS 1: EXTRACTING UNIQUE TAXA")
    if debug_limit:
        print(f"DEBUG MODE: Processing first {debug_limit:,} rows only")
    print("="*60)

    # Get total row count for progress
    total_rows = get_csv_row_count(csv_path, debug_limit)

    print(f"\nProcessing CSV in chunks to extract unique taxa...")
    start_time = time.time()

    chunk_size = 1000  # Smaller chunks for memory efficiency
    taxa_dict = {}
    total_processed = 0
    wildlife_count = 0

    try:
        chunk_num = 0

        # Set up pandas read_csv parameters
        read_params = {
            'chunksize': chunk_size,
            'low_memory': False,
            'na_values': ['', 'NA', 'N/A', 'NULL', 'null', 'none', 'None', 'NaN', 'nan'],
            'keep_default_na': True
        }

        if debug_limit:
            read_params['nrows'] = debug_limit

        for chunk in pd.read_csv(csv_path, **read_params):
            chunk_num += 1
            chunk_start_time = time.time()

            # Process each row in chunk
            for _, row in chunk.iterrows():
                total_processed += 1

                if debug_limit and total_processed > debug_limit:
                    break

                try:
                    if is_wildlife_row(row):
                        wildlife_count += 1
                        taxon_key = create_taxon_key(row)

                        if taxon_key not in taxa_dict:
                            # Create taxon record
                            taxon = {}

                            # Copy taxonomy columns
                            for column in TAXONOMY_COLUMNS:
                                value = safe_str(row.get(column, ''))
                                if value and value.lower() not in ['', 'nan', 'none', 'null']:
                                    taxon[column] = value
                                else:
                                    taxon[column] = None

                            # Add common name
                            common_name = safe_str(row.get('common_name', ''))
                            if common_name and common_name.lower() not in ['', 'nan', 'none', 'null', 'empty']:
                                taxon['common_name'] = common_name
                            else:
                                taxon['common_name'] = None

                            # Find most specific level
                            most_specific_level, most_specific_name = find_most_specific_level(taxon)
                            taxon['most_specific_level'] = most_specific_level
                            taxon['most_specific_name'] = most_specific_name

                            taxa_dict[taxon_key] = taxon

                except Exception as e:
                    print(f"    Error processing row {total_processed}: {e}")
                    print(f"    Row data: {dict(row)}")
                    continue

            # Progress reporting
            chunk_time = time.time() - chunk_start_time
            if total_rows:
                percent = (total_processed / total_rows) * 100
                print(f"  Chunk {chunk_num:,}: {total_processed:,}/{total_rows:,} rows ({percent:.1f}%) - "
                      f"{wildlife_count:,} wildlife, {len(taxa_dict):,} unique taxa - "
                      f"{chunk_time:.1f}s")
            else:
                print(f"  Chunk {chunk_num:,}: {total_processed:,} rows - "
                      f"{wildlife_count:,} wildlife, {len(taxa_dict):,} unique taxa - "
                      f"{chunk_time:.1f}s")

            # Memory cleanup every 100 chunks
            if chunk_num % 100 == 0:
                print(f"    Memory cleanup checkpoint at chunk {chunk_num:,}")

            # Break if we've hit debug limit
            if debug_limit and total_processed >= debug_limit:
                break

    except Exception as e:
        print(f"Error during Pass 1: {e}")
        import traceback
        traceback.print_exc()
        return None, None

    elapsed = time.time() - start_time
    print(f"\nPass 1 complete: {total_processed:,} rows processed in {elapsed:.1f} seconds")
    print(f"Found {wildlife_count:,} wildlife rows with {len(taxa_dict):,} unique taxa")

    if len(taxa_dict) == 0:
        print("ERROR: No taxa found! Check your CSV format and data.")
        return None, None

    # Insert taxa into database
    print(f"\nInserting {len(taxa_dict):,} unique taxa into database...")
    taxa_id_map = insert_taxa_to_database(list(taxa_dict.values()))

    return taxa_id_map, taxa_dict

def insert_taxa_to_database(taxa_list):
    """Insert taxa into database and return mapping of taxon_key -> taxon_id."""

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    taxa_id_map = {}

    try:
        print("  Starting taxa insertion...")
        start_time = time.time()

        for i, taxon in enumerate(taxa_list):
            cursor.execute('''
                INSERT INTO taxa (
                    kingdom, phylum, subphylum, superclass, class, subclass,
                    infraclass, superorder, order_, suborder, infraorder,
                    superfamily, family, subfamily, tribe, genus, subgenus,
                    species, subspecies, variety, common_name,
                    most_specific_level, most_specific_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                taxon.get('kingdom'), taxon.get('phylum'), taxon.get('subphylum'),
                taxon.get('superclass'), taxon.get('class'), taxon.get('subclass'),
                taxon.get('infraclass'), taxon.get('superorder'), taxon.get('order'),
                taxon.get('suborder'), taxon.get('infraorder'), taxon.get('superfamily'),
                taxon.get('family'), taxon.get('subfamily'), taxon.get('tribe'),
                taxon.get('genus'), taxon.get('subgenus'), taxon.get('species'),
                taxon.get('subspecies'), taxon.get('variety'), taxon.get('common_name'),
                taxon.get('most_specific_level'), taxon.get('most_specific_name')
            ))

            taxon_id = cursor.lastrowid
            taxon_key = create_taxon_key(taxon)
            taxa_id_map[taxon_key] = taxon_id

            if (i + 1) % 500 == 0:
                print(f"    Inserted {i + 1:,}/{len(taxa_list):,} taxa...")
                conn.commit()  # Commit periodically

        conn.commit()
        elapsed = time.time() - start_time
        print(f"  Taxa insertion complete: {len(taxa_list):,} taxa in {elapsed:.1f} seconds")

    except Exception as e:
        print(f"Error inserting taxa: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

    return taxa_id_map

def pass_2_process_sequences(csv_path, taxa_id_map, taxa_dict, debug_limit=None):
    """Pass 2: Process sequences and images in batches."""

    print("\n" + "="*60)
    print("PASS 2: PROCESSING SEQUENCES AND IMAGES")
    if debug_limit:
        print(f"DEBUG MODE: Processing first {debug_limit:,} rows only")
    print("="*60)

    # Get total row count for progress
    total_rows = get_csv_row_count(csv_path, debug_limit)

    print(f"\nProcessing sequences in batches...")
    start_time = time.time()

    chunk_size = 1000
    sequence_batch_size = 5000  # Process sequences in batches

    current_batch = {}  # sequence_id -> list of rows
    total_processed = 0
    total_sequences_created = 0
    total_images_created = 0

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        chunk_num = 0

        # Set up pandas read_csv parameters
        read_params = {
            'chunksize': chunk_size,
            'low_memory': False,
            'na_values': ['', 'NA', 'N/A', 'NULL', 'null', 'none', 'None', 'NaN', 'nan'],
            'keep_default_na': True
        }

        if debug_limit:
            read_params['nrows'] = debug_limit

        for chunk in pd.read_csv(csv_path, **read_params):
            chunk_num += 1
            chunk_start_time = time.time()

            # Process each row in chunk
            for _, row in chunk.iterrows():
                total_processed += 1

                if debug_limit and total_processed > debug_limit:
                    break

                try:
                    if is_wildlife_row(row):
                        sequence_id = safe_str(row.get('sequence_id', ''))
                        if sequence_id:
                            if sequence_id not in current_batch:
                                current_batch[sequence_id] = []
                            current_batch[sequence_id].append(row)

                except Exception as e:
                    print(f"    Error processing row {total_processed}: {e}")
                    continue

            # Process batch if it's getting large
            if len(current_batch) >= sequence_batch_size:
                seq_created, img_created = process_sequence_batch(
                    current_batch, taxa_id_map, cursor
                )
                total_sequences_created += seq_created
                total_images_created += img_created
                current_batch = {}  # Clear batch
                conn.commit()
                print(f"    Batch processed: {total_sequences_created:,} sequences, {total_images_created:,} images")

            # Progress reporting
            chunk_time = time.time() - chunk_start_time
            if total_rows:
                percent = (total_processed / total_rows) * 100
                print(f"  Chunk {chunk_num:,}: {total_processed:,}/{total_rows:,} rows ({percent:.1f}%) - "
                      f"{len(current_batch):,} sequences in current batch - {chunk_time:.1f}s")
            else:
                print(f"  Chunk {chunk_num:,}: {total_processed:,} rows - "
                      f"{len(current_batch):,} sequences in current batch - {chunk_time:.1f}s")

            # Break if we've hit debug limit
            if debug_limit and total_processed >= debug_limit:
                break

        # Process final batch
        if current_batch:
            print(f"\nProcessing final batch of {len(current_batch):,} sequences...")
            seq_created, img_created = process_sequence_batch(
                current_batch, taxa_id_map, cursor
            )
            total_sequences_created += seq_created
            total_images_created += img_created
            conn.commit()

        elapsed = time.time() - start_time
        print(f"\nPass 2 complete: {total_processed:,} rows processed in {elapsed:.1f} seconds")
        print(f"Created {total_sequences_created:,} sequences and {total_images_created:,} images")

    except Exception as e:
        print(f"Error during Pass 2: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    finally:
        conn.close()

def process_sequence_batch(sequence_batch, taxa_id_map, cursor):
    """Process a batch of sequences and insert into database."""

    sequences_created = 0
    images_created = 0

    for sequence_id, rows in sequence_batch.items():
        try:
            # Group rows in this sequence by taxon
            taxa_in_sequence = defaultdict(list)

            for row in rows:
                taxon_key = create_taxon_key(row)
                taxa_in_sequence[taxon_key].append(row)

            # Create separate sequence records for each taxon
            for taxon_key, taxon_rows in taxa_in_sequence.items():
                taxon_id = taxa_id_map.get(taxon_key)
                if not taxon_id:
                    continue  # Skip if taxon not found

                # Use the first row for sequence metadata
                first_row = taxon_rows[0]

                # Insert sequence (ignore if already exists due to multi-chunk sequences)
                cursor.execute('''
                    INSERT OR IGNORE INTO sequences (sequence_id, taxon_id, location_id, datetime)
                    VALUES (?, ?, ?, ?)
                ''', (
                    sequence_id,  # Use original sequence_id
                    taxon_id,
                    safe_str(first_row.get('location_id', '')) or None,
                    safe_str(first_row.get('datetime', '')) or None
                ))

                if cursor.rowcount > 0:
                    # New sequence was created
                    sequence_table_id = cursor.lastrowid
                    sequences_created += 1
                else:
                    # Sequence already exists (from previous chunk), get its ID
                    cursor.execute('''
                        SELECT id FROM sequences WHERE sequence_id = ? AND taxon_id = ?
                    ''', (sequence_id, taxon_id))
                    sequence_table_id = cursor.fetchone()[0]

                # Insert images for this sequence
                sorted_images = sorted(taxon_rows, key=lambda x: int(safe_str(x.get('frame_num', '0')) or 0))
                for image_row in sorted_images:
                    # Use INSERT OR IGNORE to handle expected image duplicates gracefully
                    cursor.execute('''
                        INSERT OR IGNORE INTO images (
                            image_id, sequence_table_id, frame_num,
                            url_gcp, url_aws, url_azure
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        safe_str(image_row.get('image_id', '')),
                        sequence_table_id,
                        int(safe_str(image_row.get('frame_num', '0')) or 0),
                        safe_str(image_row.get('url_gcp', '')) or None,
                        safe_str(image_row.get('url_aws', '')) or None,
                        safe_str(image_row.get('url_azure', '')) or None
                    ))

                    # Note: cursor.rowcount will be 0 for ignored duplicates, 1 for new inserts
                    if cursor.rowcount > 0:
                        images_created += 1

        except Exception as e:
            print(f"    Error processing sequence {sequence_id}: {e}")
            continue

    return sequences_created, images_created

def print_final_summary():
    """Print final database statistics."""

    print("\n" + "="*60)
    print("FINAL DATABASE SUMMARY")
    print("="*60)

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Count records
        cursor.execute('SELECT COUNT(*) FROM taxa')
        taxa_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM sequences')
        sequences_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM images')
        images_count = cursor.fetchone()[0]

        print(f"Taxa: {taxa_count:,}")
        print(f"Sequences: {sequences_count:,}")
        print(f"Images: {images_count:,}")

        # Show database file size
        db_size = os.path.getsize(DATABASE_PATH)
        print(f"Database size: {db_size / (1024*1024):.1f} MB")

        # Sample taxa
        print(f"\nSample taxa:")
        cursor.execute('''
            SELECT most_specific_name, most_specific_level, common_name
            FROM taxa
            WHERE most_specific_name IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 5
        ''')
        for row in cursor.fetchall():
            name, level, common = row
            common_str = f" ({common})" if common else ""
            print(f"  {name} ({level}){common_str}")

        conn.close()

    except Exception as e:
        print(f"Error generating summary: {e}")

def main():
    """Main function."""

    parser = argparse.ArgumentParser(description='Process wildlife camera trap CSV data (memory-optimized)')
    parser.add_argument('--csv-path', required=True, help='Path to the CSV file')
    parser.add_argument('--debug', action='store_true', help='Debug mode: process only first 100k rows')
    parser.add_argument('--debug-rows', type=int, default=100000, help='Number of rows to process in debug mode (default: 100k)')
    args = parser.parse_args()

    print("Wildlife Camera Trap Game - Memory-Optimized Data Processor")
    print("=" * 70)
    print("Two-pass approach for efficient processing of large datasets")

    if args.debug:
        print(f"🐛 DEBUG MODE: Processing only first {args.debug_rows:,} rows")

    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        print(f"Error: Database {DATABASE_PATH} not found!")
        print("Run 'python db_setup.py' first to create the database.")
        sys.exit(1)

    # Check if CSV file exists
    if not os.path.exists(args.csv_path):
        print(f"Error: CSV file {args.csv_path} not found!")
        sys.exit(1)

    # Show file sizes
    csv_size = os.path.getsize(args.csv_path)
    print(f"\nInput CSV file: {csv_size / (1024*1024*1024):.1f} GB")

    debug_limit = args.debug_rows if args.debug else None
    overall_start_time = time.time()

    try:
        # Pass 1: Extract and insert taxa
        taxa_id_map, taxa_dict = pass_1_extract_taxa(args.csv_path, debug_limit)
        if not taxa_id_map:
            print("Pass 1 failed!")
            sys.exit(1)

        # Pass 2: Process sequences and images
        pass_2_process_sequences(args.csv_path, taxa_id_map, taxa_dict, debug_limit)

        # Final summary
        print_final_summary()

        total_elapsed = time.time() - overall_start_time
        print(f"\nTotal processing time: {total_elapsed / 60:.1f} minutes")

        if args.debug:
            print(f"\n🐛 DEBUG MODE COMPLETE")
            print(f"Processed {debug_limit:,} rows successfully")
            print("Run without --debug flag to process the full dataset")
        else:
            print("\nData processing completed successfully!")
            print("You can now run: python app.py")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

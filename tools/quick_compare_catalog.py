#!/usr/bin/env python3
"""
Quick catalog comparison utility - simplified version for quick checks.
"""

import csv
import sys
from pathlib import Path


def quick_compare_catalogs(file1_path: str, file2_path: str, key_columns: list = None):
    """
    Quick comparison of two catalog CSV files.
    
    Args:
        file1_path: Path to first CSV file
        file2_path: Path to second CSV file
        key_columns: List of columns to use for comparison (default: core coin data)
    """
    
    def load_csv_records(file_path):
        """Load CSV as list of dictionaries."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    
    def create_key(record, columns):
        """Create a comparison key from record."""
        if columns:
            return tuple(record.get(col, '') for col in columns)
        else:
            return tuple(record.values())
    
    def format_coin_info(record):
        """Format coin information for display."""
        country = record.get('country', 'N/A')
        year = record.get('year', 'N/A')
        coin_id = record.get('id', 'N/A')
        value = record.get('value', 'N/A')
        return f"{country} {year} - {coin_id} ({value}€)"
    
    print(f"Comparing {Path(file1_path).name} vs {Path(file2_path).name}")
    print("-" * 60)
    
    # Load files
    records1 = load_csv_records(file1_path)
    records2 = load_csv_records(file2_path)
    
    print(f"Records in file 1: {len(records1)}")
    print(f"Records in file 2: {len(records2)}")
    
    if not records1 or not records2:
        print("❌ One or both files are empty!")
        return
    
    # Get columns
    cols1 = list(records1[0].keys())
    cols2 = list(records2[0].keys())
    
    print(f"Columns in file 1: {cols1}")
    print(f"Columns in file 2: {cols2}")
    
    # Determine comparison columns
    if key_columns:
        compare_cols = key_columns
        print(f"Comparing using columns: {compare_cols}")
    else:
        # Default to core coin identification columns
        core_columns = ['type', 'year', 'country', 'series', 'value', 'id']
        compare_cols = [col for col in core_columns if col in cols1 and col in cols2]
        print(f"Comparing using core columns: {compare_cols}")
    
    # Create sets for comparison
    set1 = {create_key(record, compare_cols) for record in records1}
    set2 = {create_key(record, compare_cols) for record in records2}
    
    # Find differences
    only_in_1 = set1 - set2
    only_in_2 = set2 - set1
    common = set1 & set2
    
    print(f"\nCommon records: {len(common)}")
    print(f"Only in file 1: {len(only_in_1)}")
    print(f"Only in file 2: {len(only_in_2)}")
    
    if len(only_in_1) == 0 and len(only_in_2) == 0:
        print("\n✅ Files are identical!")
    else:
        print("\n❌ Files have differences!")
        
        if only_in_1:
            print(f"\nFirst 5 records only in {Path(file1_path).name}:")
            for i, record in enumerate(list(only_in_1)[:5]):
                record_dict = dict(zip(compare_cols, record))
                if 'id' in record_dict and 'country' in record_dict:
                    print(f"  {i+1}. {format_coin_info(record_dict)}")
                else:
                    print(f"  {i+1}. {record_dict}")
        
        if only_in_2:
            print(f"\nFirst 5 records only in {Path(file2_path).name}:")
            for i, record in enumerate(list(only_in_2)[:5]):
                record_dict = dict(zip(compare_cols, record))
                if 'id' in record_dict and 'country' in record_dict:
                    print(f"  {i+1}. {format_coin_info(record_dict)}")
                else:
                    print(f"  {i+1}. {record_dict}")


def analyze_catalog_quick_stats(file1_path: str, file2_path: str):
    """Quick statistical analysis of both files."""
    
    def get_stats(file_path):
        """Get quick stats from a catalog file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            records = list(csv.DictReader(f))
        
        if not records:
            return {}
        
        stats = {
            'total': len(records),
            'countries': len(set(r.get('country', '') for r in records)),
            'years': sorted(set(r.get('year', '') for r in records if r.get('year'))),
            'types': {}
        }
        
        # Count coin types
        for record in records:
            coin_type = record.get('type', 'Unknown')
            stats['types'][coin_type] = stats['types'].get(coin_type, 0) + 1
        
        return stats
    
    print("\n" + "="*60)
    print("QUICK CATALOG STATISTICS")
    print("="*60)
    
    stats1 = get_stats(file1_path)
    stats2 = get_stats(file2_path)
    
    print(f"\n{Path(file1_path).name}:")
    print(f"  - Total coins: {stats1.get('total', 0)}")
    print(f"  - Countries: {stats1.get('countries', 0)}")
    print(f"  - Year range: {stats1.get('years', ['N/A'])[0] if stats1.get('years') else 'N/A'} - {stats1.get('years', ['N/A'])[-1] if stats1.get('years') else 'N/A'}")
    print(f"  - Coin types: {stats1.get('types', {})}")
    
    print(f"\n{Path(file2_path).name}:")
    print(f"  - Total coins: {stats2.get('total', 0)}")
    print(f"  - Countries: {stats2.get('countries', 0)}")
    print(f"  - Year range: {stats2.get('years', ['N/A'])[0] if stats2.get('years') else 'N/A'} - {stats2.get('years', ['N/A'])[-1] if stats2.get('years') else 'N/A'}")
    print(f"  - Coin types: {stats2.get('types', {})}")


if __name__ == "__main__":
    # Default file paths
    file1 = "../data/coins_export.csv"
    file2 = "../data/catalog.csv"
    
    # Parse command line arguments
    if len(sys.argv) >= 3:
        file1 = sys.argv[1]
        file2 = sys.argv[2]
    
    # Check if files exist
    if not Path(file1).exists():
        print(f"Error: {file1} not found!")
        sys.exit(1)
    
    if not Path(file2).exists():
        print(f"Error: {file2} not found!")
        sys.exit(1)
    
    # Run comparison
    quick_compare_catalogs(file1, file2)
    
    # Compare just the coin IDs
    print("\n" + "="*60)
    print("COMPARISON OF COIN IDs ONLY")
    print("="*60)
    quick_compare_catalogs(file1, file2, key_columns=['id'])
    
    # Show quick statistics
    analyze_catalog_quick_stats(file1, file2)

#!/usr/bin/env python3
"""
Quick CSV comparison utility - simplified version for quick checks.
"""

import csv
import sys
from pathlib import Path


def quick_compare(file1_path: str, file2_path: str, key_columns: list = None):
    """
    Quick comparison of two CSV files.
    
    Args:
        file1_path: Path to first CSV file
        file2_path: Path to second CSV file
        key_columns: List of columns to use for comparison (default: all)
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
        compare_cols = list(set(cols1) & set(cols2))
        print(f"Comparing using common columns: {compare_cols}")
    
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
                print(f"  {i+1}. {record_dict}")
        
        if only_in_2:
            print(f"\nFirst 5 records only in {Path(file2_path).name}:")
            for i, record in enumerate(list(only_in_2)[:5]):
                record_dict = dict(zip(compare_cols, record))
                print(f"  {i+1}. {record_dict}")


if __name__ == "__main__":
    # Default file paths
    file1 = "../data/history_export.csv"
    file2 = "../data/history.csv"
    
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
    quick_compare(file1, file2)
    
    # Also compare without dates
    print("\n" + "="*60)
    print("COMPARISON WITHOUT DATES")
    print("="*60)
    quick_compare(file1, file2, key_columns=['name', 'id'])

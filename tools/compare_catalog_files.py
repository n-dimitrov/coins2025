#!/usr/bin/env python3
"""
Script to compare entries in coins_export.csv and catalog.csv files.
Handles different sorting and provides detailed comparison results.
"""

import csv
import pandas as pd
from typing import Set, Tuple, Dict, List
from pathlib import Path


def load_csv_as_set(file_path: str, relevant_columns: List[str]) -> Set[Tuple]:
    """
    Load CSV file and return a set of tuples containing only relevant columns.
    
    Args:
        file_path: Path to the CSV file
        relevant_columns: List of column names to include in comparison
        
    Returns:
        Set of tuples representing the records
    """
    records = set()
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Create tuple with only relevant columns
            record = tuple(row[col] for col in relevant_columns)
            records.add(record)
    return records


def compare_csv_files(file1_path: str, file2_path: str, relevant_columns: List[str]) -> Dict:
    """
    Compare two CSV files based on specified columns.
    
    Args:
        file1_path: Path to first CSV file
        file2_path: Path to second CSV file
        relevant_columns: List of column names to compare
        
    Returns:
        Dictionary containing comparison results
    """
    print(f"Loading {file1_path}...")
    records1 = load_csv_as_set(file1_path, relevant_columns)
    
    print(f"Loading {file2_path}...")
    records2 = load_csv_as_set(file2_path, relevant_columns)
    
    # Find differences
    only_in_file1 = records1 - records2
    only_in_file2 = records2 - records1
    common_records = records1 & records2
    
    return {
        'file1_total': len(records1),
        'file2_total': len(records2),
        'common_records': len(common_records),
        'only_in_file1': only_in_file1,
        'only_in_file2': only_in_file2,
        'files_identical': len(only_in_file1) == 0 and len(only_in_file2) == 0
    }


def print_comparison_results(results: Dict, file1_name: str, file2_name: str, columns: List[str]):
    """Print detailed comparison results."""
    print("\n" + "="*80)
    print("COMPARISON RESULTS")
    print("="*80)
    
    print(f"\nComparing columns: {', '.join(columns)}")
    print(f"\n{file1_name}: {results['file1_total']} records")
    print(f"{file2_name}: {results['file2_total']} records")
    print(f"Common records: {results['common_records']}")
    
    if results['files_identical']:
        print(f"\n✅ FILES ARE IDENTICAL (based on columns: {', '.join(columns)})")
    else:
        print(f"\n❌ FILES ARE DIFFERENT")
        
        if results['only_in_file1']:
            print(f"\nRecords only in {file1_name} ({len(results['only_in_file1'])} records):")
            for i, record in enumerate(sorted(results['only_in_file1']), 1):
                record_dict = dict(zip(columns, record))
                print(f"  {i}. {record_dict}")
                if i >= 10:  # Limit output for readability
                    remaining = len(results['only_in_file1']) - 10
                    if remaining > 0:
                        print(f"     ... and {remaining} more records")
                    break
        
        if results['only_in_file2']:
            print(f"\nRecords only in {file2_name} ({len(results['only_in_file2'])} records):")
            for i, record in enumerate(sorted(results['only_in_file2']), 1):
                record_dict = dict(zip(columns, record))
                print(f"  {i}. {record_dict}")
                if i >= 10:  # Limit output for readability
                    remaining = len(results['only_in_file2']) - 10
                    if remaining > 0:
                        print(f"     ... and {remaining} more records")
                    break


def analyze_catalog_differences(file1_path: str, file2_path: str):
    """
    Analyze differences in catalog structure between the two files.
    """
    print("\n" + "="*80)
    print("CATALOG STRUCTURE ANALYSIS")
    print("="*80)
    
    # Load both files as DataFrames
    df1 = pd.read_csv(file1_path)
    df2 = pd.read_csv(file2_path)
    
    print(f"\nColumns in {Path(file1_path).name}: {list(df1.columns)}")
    print(f"Columns in {Path(file2_path).name}: {list(df2.columns)}")
    
    # Analyze key statistics
    print(f"\nKey statistics for {Path(file1_path).name}:")
    print(f"  - Total records: {len(df1)}")
    print(f"  - Unique countries: {df1['country'].nunique()}")
    print(f"  - Unique series: {df1['series'].nunique()}")
    print(f"  - Year range: {df1['year'].min()} - {df1['year'].max()}")
    print(f"  - Coin types: {df1['type'].value_counts().to_dict()}")
    
    print(f"\nKey statistics for {Path(file2_path).name}:")
    print(f"  - Total records: {len(df2)}")
    print(f"  - Unique countries: {df2['country'].nunique()}")
    print(f"  - Unique series: {df2['series'].nunique()}")
    print(f"  - Year range: {df2['year'].min()} - {df2['year'].max()}")
    print(f"  - Coin types: {df2['type'].value_counts().to_dict()}")
    
    # Sample records
    print(f"\nSample records from {Path(file1_path).name}:")
    for i, (_, row) in enumerate(df1.head(3).iterrows()):
        print(f"  {i+1}. {row['country']} {row['year']} - {row['id']} ({row['value']}€)")
    
    print(f"\nSample records from {Path(file2_path).name}:")
    for i, (_, row) in enumerate(df2.head(3).iterrows()):
        print(f"  {i+1}. {row['country']} {row['year']} - {row['id']} ({row['value']}€)")


def main():
    """Main function to run the comparison."""
    # Define file paths
    base_path = Path(__file__).parent.parent / "data"
    coins_export_path = base_path / "coins_export.csv"
    catalog_path = base_path / "catalog.csv"
    
    # Check if files exist
    if not coins_export_path.exists():
        print(f"Error: {coins_export_path} not found!")
        return
    
    if not catalog_path.exists():
        print(f"Error: {catalog_path} not found!")
        return
    
    print("🔍 Comparing coins_export.csv and catalog.csv")
    print("="*80)
    
    # Analyze catalog structure first
    analyze_catalog_differences(str(coins_export_path), str(catalog_path))
    
    # Compare based on all columns
    all_columns = ['type', 'year', 'country', 'series', 'value', 'id', 'image', 'feature', 'volume']
    
    results = compare_csv_files(
        str(coins_export_path), 
        str(catalog_path), 
        all_columns
    )
    
    print_comparison_results(
        results, 
        "coins_export.csv", 
        "catalog.csv", 
        all_columns
    )
    
    # Additional analysis: Compare just coin identifiers (ignoring metadata like images)
    print("\n" + "="*80)
    print("COMPARISON OF COIN IDENTIFIERS ONLY")
    print("="*80)
    
    id_columns = ['type', 'year', 'country', 'series', 'value', 'id']
    id_results = compare_csv_files(
        str(coins_export_path), 
        str(catalog_path), 
        id_columns
    )
    
    print_comparison_results(
        id_results, 
        "coins_export.csv", 
        "catalog.csv", 
        id_columns
    )
    
    # Compare just the unique coin IDs
    print("\n" + "="*80)
    print("COMPARISON OF UNIQUE COIN IDs ONLY")
    print("="*80)
    
    id_only_results = compare_csv_files(
        str(coins_export_path), 
        str(catalog_path), 
        ['id']
    )
    
    print_comparison_results(
        id_only_results, 
        "coins_export.csv", 
        "catalog.csv", 
        ['id']
    )
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if results['files_identical']:
        print("✅ The files are completely identical (all fields match)")
    elif id_results['files_identical']:
        print("⚠️  The files contain the same coin data but metadata differs (images, features, volume)")
    elif id_only_results['files_identical']:
        print("⚠️  The files contain the same coins but coin details differ")
    else:
        print("❌ The files contain different coin collections")
        print(f"   - Records only in coins_export.csv: {len(results['only_in_file1'])}")
        print(f"   - Records only in catalog.csv: {len(results['only_in_file2'])}")


if __name__ == "__main__":
    main()

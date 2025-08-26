#!/usr/bin/env python3
"""
Script to compare entries in history_export.csv and history.csv files.
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


def analyze_date_differences(file1_path: str, file2_path: str):
    """
    Analyze differences in date formatting between the two files.
    """
    print("\n" + "="*80)
    print("DATE FORMAT ANALYSIS")
    print("="*80)
    
    # Load both files as DataFrames
    df1 = pd.read_csv(file1_path)
    df2 = pd.read_csv(file2_path)
    
    print(f"\nColumns in {Path(file1_path).name}: {list(df1.columns)}")
    print(f"Columns in {Path(file2_path).name}: {list(df2.columns)}")
    
    # Sample date formats
    print(f"\nSample dates from {Path(file1_path).name}:")
    for i, date in enumerate(df1['date'].head(3)):
        print(f"  {i+1}. {date}")
    
    print(f"\nSample dates from {Path(file2_path).name}:")
    for i, date in enumerate(df2['date'].head(3)):
        print(f"  {i+1}. {date}")
    
    # If history.csv has date_only column, show samples
    if 'date_only' in df2.columns:
        print(f"\nSample date_only values from {Path(file2_path).name}:")
        for i, date in enumerate(df2['date_only'].head(3)):
            print(f"  {i+1}. {date}")


def main():
    """Main function to run the comparison."""
    # Define file paths
    base_path = Path(__file__).parent.parent / "data"
    history_export_path = base_path / "history_export.csv"
    history_path = base_path / "history.csv"
    
    # Check if files exist
    if not history_export_path.exists():
        print(f"Error: {history_export_path} not found!")
        return
    
    if not history_path.exists():
        print(f"Error: {history_path} not found!")
        return
    
    print("🔍 Comparing history_export.csv and history.csv")
    print("="*80)
    
    # Analyze date formats first
    analyze_date_differences(str(history_export_path), str(history_path))
    
    # Compare based on name, id, and date columns (common to both files)
    relevant_columns = ['name', 'id', 'date']
    
    results = compare_csv_files(
        str(history_export_path), 
        str(history_path), 
        relevant_columns
    )
    
    print_comparison_results(
        results, 
        "history_export.csv", 
        "history.csv", 
        relevant_columns
    )
    
    # Additional analysis: Compare just name and id (ignoring dates)
    print("\n" + "="*80)
    print("COMPARISON WITHOUT DATES (name + id only)")
    print("="*80)
    
    name_id_columns = ['name', 'id']
    name_id_results = compare_csv_files(
        str(history_export_path), 
        str(history_path), 
        name_id_columns
    )
    
    print_comparison_results(
        name_id_results, 
        "history_export.csv", 
        "history.csv", 
        name_id_columns
    )
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if results['files_identical']:
        print("✅ The files contain identical records (including dates)")
    elif name_id_results['files_identical']:
        print("⚠️  The files contain the same name/id combinations but dates differ")
    else:
        print("❌ The files contain different records")
        print(f"   - Records only in history_export.csv: {len(results['only_in_file1'])}")
        print(f"   - Records only in history.csv: {len(results['only_in_file2'])}")


if __name__ == "__main__":
    main()

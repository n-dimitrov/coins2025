#!/usr/bin/env python3
"""
Enhanced script to compare catalog CSV files with additional features:
- Detailed statistics
- Export differences to CSV
- Support for custom column selection
- Catalog-specific analysis
"""

import csv
import pandas as pd
import argparse
from typing import Set, Tuple, Dict, List, Optional
from pathlib import Path
from collections import Counter
import sys


class CatalogComparator:
    """A class to handle catalog CSV file comparisons with various options."""
    
    def __init__(self, file1_path: str, file2_path: str):
        self.file1_path = Path(file1_path)
        self.file2_path = Path(file2_path)
        self.file1_name = self.file1_path.name
        self.file2_name = self.file2_path.name
        
        # Validate files exist
        if not self.file1_path.exists():
            raise FileNotFoundError(f"File not found: {self.file1_path}")
        if not self.file2_path.exists():
            raise FileNotFoundError(f"File not found: {self.file2_path}")
    
    def get_column_info(self) -> Dict:
        """Get column information from both files."""
        with open(self.file1_path, 'r', encoding='utf-8') as f:
            cols1 = next(csv.reader(f))
        
        with open(self.file2_path, 'r', encoding='utf-8') as f:
            cols2 = next(csv.reader(f))
        
        return {
            'file1_columns': cols1,
            'file2_columns': cols2,
            'common_columns': list(set(cols1) & set(cols2)),
            'file1_only_columns': list(set(cols1) - set(cols2)),
            'file2_only_columns': list(set(cols2) - set(cols1))
        }
    
    def load_records(self, file_path: Path, columns: List[str]) -> Set[Tuple]:
        """Load CSV records as a set of tuples."""
        records = set()
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    record = tuple(row[col] for col in columns)
                    records.add(record)
                except KeyError as e:
                    print(f"Warning: Column {e} not found in {file_path.name}")
                    return set()
        return records
    
    def compare_records(self, columns: List[str]) -> Dict:
        """Compare records based on specified columns."""
        print(f"Loading {self.file1_name}...")
        records1 = self.load_records(self.file1_path, columns)
        
        print(f"Loading {self.file2_name}...")
        records2 = self.load_records(self.file2_path, columns)
        
        if not records1 or not records2:
            return {}
        
        only_in_file1 = records1 - records2
        only_in_file2 = records2 - records1
        common_records = records1 & records2
        
        return {
            'file1_total': len(records1),
            'file2_total': len(records2),
            'common_records': len(common_records),
            'only_in_file1': only_in_file1,
            'only_in_file2': only_in_file2,
            'files_identical': len(only_in_file1) == 0 and len(only_in_file2) == 0,
            'columns_used': columns
        }
    
    def export_differences(self, results: Dict, output_dir: str = "catalog_comparison_output"):
        """Export differences to CSV files."""
        if results['files_identical']:
            print("No differences to export - files are identical!")
            return
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        columns = results['columns_used']
        
        # Export records only in file1
        if results['only_in_file1']:
            file1_only_path = output_path / f"only_in_{self.file1_path.stem}.csv"
            with open(file1_only_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for record in sorted(results['only_in_file1']):
                    writer.writerow(record)
            print(f"Records only in {self.file1_name} exported to: {file1_only_path}")
        
        # Export records only in file2
        if results['only_in_file2']:
            file2_only_path = output_path / f"only_in_{self.file2_path.stem}.csv"
            with open(file2_only_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for record in sorted(results['only_in_file2']):
                    writer.writerow(record)
            print(f"Records only in {self.file2_name} exported to: {file2_only_path}")
    
    def analyze_catalog_statistics(self, columns: List[str]) -> Dict:
        """Generate detailed statistics about the catalog files."""
        df1 = pd.read_csv(self.file1_path)
        df2 = pd.read_csv(self.file2_path)
        
        stats = {
            'file1': {
                'total_rows': len(df1),
                'columns': list(df1.columns),
                'memory_usage': df1.memory_usage(deep=True).sum(),
                'countries': df1['country'].nunique() if 'country' in df1.columns else 0,
                'years': f"{df1['year'].min()}-{df1['year'].max()}" if 'year' in df1.columns else 'N/A',
                'coin_types': df1['type'].value_counts().to_dict() if 'type' in df1.columns else {},
                'unique_series': df1['series'].nunique() if 'series' in df1.columns else 0
            },
            'file2': {
                'total_rows': len(df2),
                'columns': list(df2.columns),
                'memory_usage': df2.memory_usage(deep=True).sum(),
                'countries': df2['country'].nunique() if 'country' in df2.columns else 0,
                'years': f"{df2['year'].min()}-{df2['year'].max()}" if 'year' in df2.columns else 'N/A',
                'coin_types': df2['type'].value_counts().to_dict() if 'type' in df2.columns else {},
                'unique_series': df2['series'].nunique() if 'series' in df2.columns else 0
            }
        }
        
        return stats
    
    def print_detailed_results(self, results: Dict, show_samples: bool = True, max_samples: int = 10):
        """Print comprehensive comparison results."""
        print("\n" + "="*80)
        print("DETAILED CATALOG COMPARISON RESULTS")
        print("="*80)
        
        columns = results.get('columns_used', [])
        print(f"\nColumns compared: {', '.join(columns)}")
        print(f"{self.file1_name}: {results['file1_total']} records")
        print(f"{self.file2_name}: {results['file2_total']} records")
        print(f"Common records: {results['common_records']}")
        print(f"Records only in {self.file1_name}: {len(results['only_in_file1'])}")
        print(f"Records only in {self.file2_name}: {len(results['only_in_file2'])}")
        
        if results['files_identical']:
            print(f"\n✅ FILES ARE IDENTICAL")
        else:
            print(f"\n❌ FILES HAVE DIFFERENCES")
            
            if show_samples:
                self._print_sample_differences(results, columns, max_samples)
    
    def _print_sample_differences(self, results: Dict, columns: List[str], max_samples: int):
        """Print sample differences between files."""
        if results['only_in_file1']:
            print(f"\nSample records only in {self.file1_name}:")
            for i, record in enumerate(sorted(list(results['only_in_file1'])[:max_samples]), 1):
                record_dict = dict(zip(columns, record))
                # Format coin info nicely
                if 'id' in record_dict and 'country' in record_dict and 'value' in record_dict:
                    coin_info = f"{record_dict.get('country', 'N/A')} {record_dict.get('year', 'N/A')} - {record_dict.get('id', 'N/A')} ({record_dict.get('value', 'N/A')}€)"
                    print(f"  {i}. {coin_info}")
                else:
                    print(f"  {i}. {record_dict}")
            
            remaining = len(results['only_in_file1']) - max_samples
            if remaining > 0:
                print(f"     ... and {remaining} more records")
        
        if results['only_in_file2']:
            print(f"\nSample records only in {self.file2_name}:")
            for i, record in enumerate(sorted(list(results['only_in_file2'])[:max_samples]), 1):
                record_dict = dict(zip(columns, record))
                # Format coin info nicely
                if 'id' in record_dict and 'country' in record_dict and 'value' in record_dict:
                    coin_info = f"{record_dict.get('country', 'N/A')} {record_dict.get('year', 'N/A')} - {record_dict.get('id', 'N/A')} ({record_dict.get('value', 'N/A')}€)"
                    print(f"  {i}. {coin_info}")
                else:
                    print(f"  {i}. {record_dict}")
            
            remaining = len(results['only_in_file2']) - max_samples
            if remaining > 0:
                print(f"     ... and {remaining} more records")


def main():
    """Main function with command line argument support."""
    parser = argparse.ArgumentParser(description='Compare two catalog CSV files')
    parser.add_argument('file1', nargs='?', default='../data/coins_export.csv', 
                       help='Path to first CSV file')
    parser.add_argument('file2', nargs='?', default='../data/catalog.csv',
                       help='Path to second CSV file')
    parser.add_argument('--columns', '-c', nargs='+', 
                       help='Specific columns to compare (default: all common columns)')
    parser.add_argument('--core-only', action='store_true',
                       help='Compare only core coin data (type, year, country, series, value, id)')
    parser.add_argument('--ids-only', action='store_true',
                       help='Compare only coin IDs')
    parser.add_argument('--ignore-metadata', action='store_true',
                       help='Ignore metadata columns (image, feature, volume)')
    parser.add_argument('--export-differences', '-e', action='store_true',
                       help='Export differences to CSV files')
    parser.add_argument('--no-samples', action='store_true',
                       help='Don\'t show sample differences')
    parser.add_argument('--max-samples', type=int, default=10,
                       help='Maximum number of sample differences to show')
    
    args = parser.parse_args()
    
    try:
        # Initialize comparator
        comparator = CatalogComparator(args.file1, args.file2)
        
        print(f"🔍 Comparing {comparator.file1_name} and {comparator.file2_name}")
        print("="*80)
        
        # Get column information
        col_info = comparator.get_column_info()
        print(f"\nColumns in {comparator.file1_name}: {col_info['file1_columns']}")
        print(f"Columns in {comparator.file2_name}: {col_info['file2_columns']}")
        print(f"Common columns: {col_info['common_columns']}")
        
        if col_info['file1_only_columns']:
            print(f"Only in {comparator.file1_name}: {col_info['file1_only_columns']}")
        if col_info['file2_only_columns']:
            print(f"Only in {comparator.file2_name}: {col_info['file2_only_columns']}")
        
        # Determine columns to compare
        if args.columns:
            compare_columns = args.columns
        elif args.core_only:
            compare_columns = ['type', 'year', 'country', 'series', 'value', 'id']
        elif args.ids_only:
            compare_columns = ['id']
        elif args.ignore_metadata:
            compare_columns = [col for col in col_info['common_columns'] 
                             if col not in ['image', 'feature', 'volume']]
        else:
            compare_columns = col_info['common_columns']
        
        print(f"\nUsing columns for comparison: {compare_columns}")
        
        # Perform comparison
        results = comparator.compare_records(compare_columns)
        
        if results:
            # Print results
            comparator.print_detailed_results(
                results, 
                show_samples=not args.no_samples,
                max_samples=args.max_samples
            )
            
            # Export differences if requested
            if args.export_differences:
                comparator.export_differences(results)
            
            # Print statistics
            stats = comparator.analyze_catalog_statistics(compare_columns)
            print("\n" + "="*80)
            print("CATALOG STATISTICS")
            print("="*80)
            print(f"{comparator.file1_name}:")
            print(f"  - Total rows: {stats['file1']['total_rows']}")
            print(f"  - Countries: {stats['file1']['countries']}")
            print(f"  - Year range: {stats['file1']['years']}")
            print(f"  - Unique series: {stats['file1']['unique_series']}")
            print(f"  - Coin types: {stats['file1']['coin_types']}")
            print(f"  - Memory usage: {stats['file1']['memory_usage']} bytes")
            
            print(f"\n{comparator.file2_name}:")
            print(f"  - Total rows: {stats['file2']['total_rows']}")
            print(f"  - Countries: {stats['file2']['countries']}")
            print(f"  - Year range: {stats['file2']['years']}")
            print(f"  - Unique series: {stats['file2']['unique_series']}")
            print(f"  - Coin types: {stats['file2']['coin_types']}")
            print(f"  - Memory usage: {stats['file2']['memory_usage']} bytes")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

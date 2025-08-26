# CSV Comparison Scripts

This directory contains three scripts for comparing CSV files, specifically designed to compare `history_export.csv` and `history.csv` files, but can be used for any CSV comparison tasks.

## Scripts Overview

### 1. `compare_history_files.py` - Basic Comparison
A straightforward script that performs a comprehensive comparison of the two history files.

**Features:**
- Compares all common columns
- Analyzes date format differences
- Shows identical records count
- Provides summary of differences

**Usage:**
```bash
cd tools
python compare_history_files.py
```

### 2. `quick_compare.py` - Quick Utility
A fast and simple comparison tool for quick checks.

**Features:**
- Quick comparison with minimal output
- Supports custom file paths
- Shows first 5 differences
- Compares with and without dates

**Usage:**
```bash
# Default files (history_export.csv vs history.csv)
cd tools
python quick_compare.py

# Custom files
python quick_compare.py file1.csv file2.csv
```

### 3. `compare_history_advanced.py` - Advanced Analysis
A comprehensive tool with many options for detailed analysis.

**Features:**
- Command-line arguments support
- Export differences to CSV files
- Custom column selection
- Detailed statistics
- Memory usage analysis
- Configurable sample output

**Usage:**
```bash
# Basic comparison
cd tools
python compare_history_advanced.py

# Compare specific columns only
python compare_history_advanced.py --columns name id

# Ignore date columns
python compare_history_advanced.py --ignore-dates

# Export differences to CSV files
python compare_history_advanced.py --export-differences

# Compare custom files
python compare_history_advanced.py file1.csv file2.csv

# Limit sample output
python compare_history_advanced.py --max-samples 5

# No sample differences shown
python compare_history_advanced.py --no-samples
```

## File Structure Expected

The scripts expect the following file structure:
```
tools/                    # Comparison scripts location
└── CSV_COMPARISON_README.md
└── compare_history_files.py
└── compare_history_advanced.py
└── quick_compare.py
data/
├── history_export.csv    # First file to compare
└── history.csv          # Second file to compare
```

## Output Examples

### When Files Are Identical
```
✅ FILES ARE IDENTICAL (based on columns: name, id, date)
```

### When Files Have Differences
```
❌ FILES HAVE DIFFERENCES
Records only in history_export.csv: 5
Records only in history.csv: 3

Sample records only in history_export.csv:
  1. {'name': 'John', 'id': 'CC2024ESP-A-CC1-200', 'date': '2024-01-15 10:30:00'}
  2. {'name': 'Jane', 'id': 'RE2024FRA-A-RE1-100', 'date': '2024-02-20 14:45:00'}
```

## Column Analysis

The scripts automatically detect:
- Common columns between files
- Columns unique to each file
- Date format differences
- Missing values and duplicates

## Use Cases

1. **Data Validation**: Ensure exported data matches source data
2. **Migration Verification**: Confirm data integrity after migrations
3. **Backup Verification**: Check if backups contain all expected records
4. **Synchronization Checks**: Verify data sync between systems
5. **Quality Assurance**: Regular data quality checks

## Performance Notes

- **Memory Usage**: Scripts load entire files into memory. For very large files (>1GB), consider using chunk processing
- **Speed**: Quick comparison is fastest, advanced comparison provides most detail
- **Sorting**: All scripts handle different sorting automatically by using set operations

## Error Handling

Scripts will handle:
- Missing files (with clear error messages)
- Empty files
- Missing columns
- Different column orders
- Encoding issues (UTF-8 assumed)

## Requirements

```python
pandas>=1.3.0
```

Install with:
```bash
pip install pandas
```

## Examples of Real Usage

### Check if export matches current data
```bash
cd tools
python quick_compare.py
```

### Export all differences for analysis
```bash
cd tools
python compare_history_advanced.py --export-differences
```

### Compare only name and ID (ignore dates and other fields)
```bash
cd tools
python compare_history_advanced.py --columns name id
```

### Compare any two CSV files
```bash
cd tools
python quick_compare.py /path/to/file1.csv /path/to/file2.csv
```

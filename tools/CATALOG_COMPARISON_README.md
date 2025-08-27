# Catalog Comparison Scripts

This directory contains three scripts for comparing catalog CSV files, specifically designed to compare `coins_export.csv` and `catalog.csv` files, but can be used for any coin catalog comparison tasks.

## Scripts Overview

### 1. `compare_catalog_files.py` - Basic Catalog Comparison
A comprehensive script that performs detailed comparison of catalog files with coin-specific analysis.

**Features:**
- Compares all catalog columns
- Analyzes catalog structure (countries, years, coin types)
- Shows identical records count
- Multiple comparison levels (full, core data, IDs only)
- Catalog-specific statistics

**Usage:**
```bash
cd tools
python compare_catalog_files.py
```

### 2. `quick_compare_catalog.py` - Quick Catalog Utility
A fast and simple comparison tool for quick catalog checks.

**Features:**
- Quick comparison with coin-formatted output
- Supports custom file paths
- Shows first 5 differences with coin information
- Quick catalog statistics (countries, years, coin types)
- Core coin data focus

**Usage:**
```bash
# Default files (coins_export.csv vs catalog.csv)
cd tools
python quick_compare_catalog.py

# Custom files
python quick_compare_catalog.py file1.csv file2.csv
```

### 3. `compare_catalog_advanced.py` - Advanced Catalog Analysis
A comprehensive tool with many options for detailed catalog analysis.

**Features:**
- Command-line arguments support
- Export differences to CSV files
- Custom column selection
- Catalog-specific filtering options
- Detailed coin statistics
- Memory usage analysis
- Configurable sample output

**Usage:**
```bash
# Basic comparison
cd tools
python compare_catalog_advanced.py

# Compare only core coin data (ignore metadata)
python compare_catalog_advanced.py --core-only

# Compare only coin IDs
python compare_catalog_advanced.py --ids-only

# Ignore metadata columns
python compare_catalog_advanced.py --ignore-metadata

# Export differences to CSV files
python compare_catalog_advanced.py --export-differences

# Compare custom files
python compare_catalog_advanced.py file1.csv file2.csv

# Compare specific columns only
python compare_catalog_advanced.py --columns type year country id

# Limit sample output
python compare_catalog_advanced.py --max-samples 5

# No sample differences shown
python compare_catalog_advanced.py --no-samples
```

## Catalog File Structure Expected

The scripts expect the following file structure:
```
tools/                           # Comparison scripts location
└── compare_catalog_files.py
└── compare_catalog_advanced.py
└── quick_compare_catalog.py
data/
├── coins_export.csv            # First catalog file to compare
└── catalog.csv                 # Second catalog file to compare
```

## Catalog Column Structure

Expected columns in catalog files:
- **type**: Coin type (RE for regular, CC for commemorative)
- **year**: Year of issue
- **country**: Country code (e.g., BEL, DEU, FRA)
- **series**: Series identifier
- **value**: Coin value in euros (e.g., 2.0, 1.0, 0.5)
- **id**: Unique coin identifier
- **image**: URL to coin image (optional)
- **feature**: Special features (optional)
- **volume**: Coin volume information (optional)

## Output Examples

### When Catalogs Are Identical
```
✅ FILES ARE IDENTICAL (based on columns: type, year, country, series, value, id, image, feature, volume)

CATALOG STATISTICS
coins_export.csv:
  - Total coins: 831
  - Countries: 24
  - Year range: 1999-2024
  - Coin types: {'CC': 547, 'RE': 284}
```

### When Catalogs Have Differences
```
❌ FILES HAVE DIFFERENCES
Records only in coins_export.csv: 5
Records only in catalog.csv: 3

Sample records only in coins_export.csv:
  1. Germany 2024 - CC2024DEU-A-CC1-200 (2.0€)
  2. France 2024 - CC2024FRA-A-CC1-200 (2.0€)
```

## Comparison Modes

### 1. Full Comparison
Compares all columns including metadata (images, features, volume)
```bash
python compare_catalog_advanced.py
```

### 2. Core Data Only
Compares only essential coin identification data
```bash
python compare_catalog_advanced.py --core-only
```

### 3. IDs Only
Compares only the unique coin identifiers
```bash
python compare_catalog_advanced.py --ids-only
```

### 4. Ignore Metadata
Excludes optional columns from comparison
```bash
python compare_catalog_advanced.py --ignore-metadata
```

## Use Cases

1. **Catalog Validation**: Ensure exported catalogs match master catalogs
2. **Import Verification**: Confirm catalog imports are complete and accurate
3. **Synchronization Checks**: Verify catalog sync between different systems
4. **Quality Assurance**: Regular catalog data quality checks
5. **Migration Verification**: Confirm data integrity after catalog migrations
6. **Collection Comparison**: Compare different coin collections or catalog versions

## Catalog-Specific Analysis

The scripts provide specialized analysis for coin catalogs:

- **Country Coverage**: Number of unique countries represented
- **Year Range**: Temporal span of the coin collection
- **Coin Type Distribution**: Breakdown of regular vs commemorative coins
- **Series Analysis**: Number of unique coin series
- **Value Distribution**: Analysis of coin denominations

## Performance Notes

- **Memory Usage**: Scripts load entire catalogs into memory. For very large catalogs (>10,000 coins), consider using chunk processing
- **Speed**: Quick comparison is fastest, advanced comparison provides most detail
- **Sorting**: All scripts handle different sorting automatically using set operations

## Error Handling

Scripts will handle:
- Missing files (with clear error messages)
- Empty catalogs
- Missing columns
- Different column orders
- Encoding issues (UTF-8 assumed)
- Invalid coin data formats

## Requirements

```python
pandas>=1.3.0
```

Install with:
```bash
pip install pandas
```

## Examples of Real Usage

### Check if export matches current catalog
```bash
cd tools
python quick_compare_catalog.py
```

### Export all catalog differences for analysis
```bash
cd tools
python compare_catalog_advanced.py --export-differences
```

### Compare only coin identification data (ignore images and metadata)
```bash
cd tools
python compare_catalog_advanced.py --core-only
```

### Compare any two catalog files
```bash
cd tools
python quick_compare_catalog.py /path/to/catalog1.csv /path/to/catalog2.csv
```

### Check for missing coins between catalogs
```bash
cd tools
python compare_catalog_advanced.py --ids-only --export-differences
```

## Integration with Existing Tools

These catalog comparison scripts complement the existing history comparison tools:
- Use `compare_history_*.py` for transaction/ownership data
- Use `compare_catalog_*.py` for coin catalog data
- Both sets follow the same command-line interface patterns

# Adding New Coin Series to My EuroCoins 🪙

This comprehensive guide explains how to add new coin series to the My EuroCoins catalog. Whether you're adding a new commemorative series, regular circulation coins from a new country, or updating existing series with new releases, this guide covers all the necessary steps.

## 📋 Table of Contents

1. [Understanding Coin Series](#understanding-coin-series)
2. [Data Sources and Research](#data-sources-and-research)
3. [Series Identification and Naming](#series-identification-and-naming)
4. [Adding Data to the System](#adding-data-to-the-system)
5. [Frontend Integration](#frontend-integration)
6. [BigQuery Database Updates](#bigquery-database-updates)
7. [Testing and Validation](#testing-and-validation)
8. [Deployment Process](#deployment-process)

## 🎯 Understanding Coin Series

### Types of Coin Series

#### 1. **Regular Circulation Series (RE)**
- Standard denominations: 1¢, 2¢, 5¢, 10¢, 20¢, 50¢, €1, €2
- Each country has unique designs for each denomination
- Updated when countries change designs or join the eurozone
- Series code format: `{COUNTRY_CODE}-{SERIES_NUMBER}` (e.g., `DEU-01`, `ESP-02`)

#### 2. **Commemorative Series (CC)**
- Special €2 coins issued to commemorate events, anniversaries, or cultural heritage
- Can be multi-year series (e.g., German Bundesländer series spanning 16 years)
- Single commemorative releases for specific events
- Series code format: `CC-{YEAR}` or descriptive names for multi-year series

### Examples of Commemorative Series

#### Multi-Year Series:
- **German Federal States (Bundesländer)**: 2006-2023, featuring all 16 German states
- **Spanish UNESCO World Heritage Sites**: 2010-2014, featuring various Spanish heritage sites
- **Lithuanian Ethnographic Regions**: 2019-2022, featuring the 5 historical regions

#### Single Commemorative Releases:
- **Treaty of Rome Anniversary** (various countries, 2007)
- **European Monetary Union** (various countries, 2009)
- **COVID-19 Frontline Workers** (various countries, 2021)

## 🔍 Data Sources and Research

### Official Sources

#### 1. **European Central Bank (ECB)**
- **URL**: [www.ecb.europa.eu/euro/coins/](https://www.ecb.europa.eu/euro/coins/)
- **Contains**: Official announcements, coin specifications, high-quality images
- **Use for**: Verification of all data, official coin images

#### 2. **National Central Banks**
- Each eurozone country's central bank publishes coin information
- **Examples**:
  - Deutsche Bundesbank (Germany)
  - Banco de España (Spain)
  - Banque de France (France)

#### 3. **Automated Data Collection Tools**
The project includes specialized scraping tools for gathering data from ECB:

##### Commemorative Coins Scraper (`tools/scrape_cc_catalog.py`)
- **Purpose**: Automatically extracts commemorative coin data from ECB annual pages
- **Features**:
  - Selenium-based web scraping with Chrome browser
  - Handles multi-country commemorative releases (e.g., joint Euro area releases)
  - Extracts coin images, features, descriptions, and volume information
  - Supports carousel image galleries for multi-country releases
- **Usage**: Modify the `year` variable and `url` to scrape specific years

##### Regular Coins Scraper (`tools/scrape_re_catalog.py`)
- **Purpose**: Extracts regular circulation coin data for all eurozone countries
- **Features**:
  - Processes all 24 eurozone countries from predefined URL list
  - Extracts coin denominations, descriptions, and images
  - Handles multiple coin images per denomination
- **Usage**: Modify the `country` and `url` variables to scrape specific countries

### Research Checklist

Before adding a new series, research and document:

- [ ] **Official announcement** from ECB or national central bank
- [ ] **Release date** and circulation start date
- [ ] **Mintage numbers** (how many coins were produced)
- [ ] **Design description** and commemorated subject
- [ ] **Designer/Artist** information (optional)
- [ ] **Technical specifications** (weight, diameter, edge type)
- [ ] **High-quality coin image** URLs from official sources
- [ ] **Series classification** (single release vs. multi-year series)

## 🏷️ Series Identification and Naming

### Series Code Conventions

#### Regular Coins (RE)
```
Format: {COUNTRY_CODE}-{SERIES_NUMBER}
Examples:
- DEU-01  (Germany, first series)
- ESP-02  (Spain, second series)
- FRA-01  (France, first series)
```

#### Commemorative Coins (CC)
```
Single Release Format: CC-{YEAR}
Multi-Year Series: Descriptive name

Examples:
- CC-2023                    (Single commemorative 2023)
- Bundesländer-{STATE}       (German states series)
- UNESCO-Spain-{SITE}        (Spanish UNESCO series)
- Lithuanian-Regions-{REGION} (Lithuanian regions series)
```

### Country Codes (ISO 3166-1 Alpha-3)
```
AND - Andorra        DEU - Germany       LTU - Lithuania
AUT - Austria        GRC - Greece        LUX - Luxembourg
BEL - Belgium        IRL - Ireland       MLT - Malta
HRV - Croatia        ITA - Italy         MCO - Monaco
CYP - Cyprus         LVA - Latvia        NLD - Netherlands
EST - Estonia        LIE - Liechtenstein PRT - Portugal
FIN - Finland        SVK - Slovakia      SVN - Slovenia
FRA - France         ESP - Spain         VAT - Vatican
```

## 📊 Adding Data to the System

### Automated Data Collection Workflow

The project provides several automated tools to streamline the data collection and processing:

#### 1. **Web Scraping Tools**

##### Scraping Commemorative Coins
```bash
cd tools/

# Edit scrape_cc_catalog.py to set the target year
# Modify these lines:
year = "2024"  # Change to desired year
url = "https://www.ecb.europa.eu/euro/coins/comm/html/comm_" + year + ".en.html"

# Run the scraper
python scrape_cc_catalog.py

# Output: Creates tmp/cc_catalog.json with structured data
```

**Scraper Features:**
- Extracts coin country, feature, description, image URL, volume
- Handles multi-country commemorative releases with image carousels
- Automatically generates series codes (CC-YYYY format)
- Saves data in structured JSON format

##### Scraping Regular Coins
```bash
cd tools/

# Edit scrape_re_catalog.py to select country
# Modify these lines:
country = "Croatia"  # Change to desired country
url = urls[index]     # Select appropriate URL from the list

# Run the scraper
python scrape_re_catalog.py

# Output: Creates tmp/re_catalog.json with structured data
```

#### 2. **Data Generation Tools**

##### Generate Commemorative CSV
```bash
cd tools/

# Converts scraped JSON data to CSV format
python generate_cc_csv.py

# Input: tmp/cc_catalog.json
# Output: tmp/cc.csv with proper coin IDs and formatting
```

**Generation Features:**
- Converts country names to ISO 3166-1 Alpha-3 codes
- Generates unique coin IDs following project conventions
- Handles multi-country releases (Euro area countries)
- Creates proper series identifiers

##### Generate Regular CSV
```bash
cd tools/

# Converts scraped JSON data to CSV format
python generate_re_csv.py

# Input: tmp/re_catalog.json
# Output: tmp/re.csv with proper coin IDs and series mapping
```

**Generation Features:**
- Maps denominations to numeric values and codes
- Associates coins with proper series based on predefined mapping
- Generates chronologically accurate coin IDs

### 3. **Manual Data Entry**

#### Main Catalog File: `data/catalog.csv`

**CSV Structure:**
```csv
type,year,country,series,value,id,image,feature,volume
```

**Field Descriptions:**
- `type`: "RE" for regular, "CC" for commemorative
- `year`: Year of issue (YYYY)
- `country`: Full country name in English
- `series`: Series identifier (see naming conventions above)
- `value`: Denomination (0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 1.0, 2.0)
- `id`: Unique coin identifier (see ID conventions below)
- `image`: Full URL to official ECB coin image
- `feature`: Description/commemorated subject (for CC coins)
- `volume`: Mintage information (e.g., "30 million coins")

#### Example Entries:

**Regular Coin Series:**
```csv
RE,2023,Croatia,HRV-01,0.01,RE2023HRV-A-001-001,https://www.ecb.europa.eu/euro/coins/common/html/cr.jpg,,2 million coins
RE,2023,Croatia,HRV-01,0.02,RE2023HRV-A-001-002,https://www.ecb.europa.eu/euro/coins/common/html/cr.jpg,,2 million coins
```

**Commemorative Coin:**
```csv
CC,2023,Germany,Bundesländer-Hamburg,2.0,CC2023DEU-A-CC2-200,https://www.ecb.europa.eu/euro/coins/comm/html/comm_2023/hamburg.jpg,Bundeslander series – Hamburg,30 million coins
```

### 4. **Coin ID Convention**

#### Regular Coins
```
Format: {TYPE}{YEAR}{COUNTRY}-{MINT}-{SERIES}-{VALUE}
Example: RE2023HRV-A-001-200 
```

#### Commemorative Coins
```
Format: {TYPE}{YEAR}{COUNTRY}-{MINT}-{CC_NUMBER}-{VALUE}
Example: CC2023DEU-A-CC2-200
```

**Components:**
- `TYPE`: RE or CC
- `YEAR`: 4-digit year
- `COUNTRY`: 3-letter country code
- `MINT`: Usually "A" for standard mint
- `SERIES/CC_NUMBER`: Series identifier or CC number
- `VALUE`: Denomination in cents (001=1¢, 200=€2)

### 5. **JSON Data Files**

#### Commemorative Coins: `data/cc_catalog.json`
```json
{
  "CC2023DEU-A-CC2-200": {
    "coin_type": "CC",
    "year": 2023,
    "country": "Germany",
    "series": "Bundesländer-Hamburg",
    "value": 2.0,
    "coin_id": "CC2023DEU-A-CC2-200",
    "image_url": "https://www.ecb.europa.eu/euro/coins/comm/html/comm_2023/hamburg.jpg",
    "feature": "Bundeslander series – Hamburg",
    "volume": "30 million coins"
  }
}
```

#### Regular Coins: `data/re_catalog.json`
```json
{
  "RE2023HRV-A-001-001": {
    "coin_type": "RE",
    "year": 2023,
    "country": "Croatia",
    "series": "HRV-01",
    "value": 0.01,
    "coin_id": "RE2023HRV-A-001-001",
    "image_url": "https://www.ecb.europa.eu/euro/coins/common/html/cr.jpg",
    "feature": null,
    "volume": "2 million coins"
  }
}
```

## 🎨 Frontend Integration

### 1. Update JavaScript Labels

In `static/js/coins.js`, add labels for new commemorative series:

```javascript
class CoinCatalog {
    constructor() {
        // Static mapping for special commemorative series
        this.commemorativeLabels = {
            'CC-2023': '2023 Commemorative',
            'Bundesländer-Hamburg': 'Hamburg (Federal States series)',
            'UNESCO-Spain-Cordoba': 'Córdoba Historic Centre (UNESCO series)',
            // Add new series here
            'Lithuanian-Regions-Aukstaitija': 'Aukštaitija (Ethnographic Regions)',
            'Your-New-Series-Name': 'Display Name for Your Series'
        };

        // Static mapping for regular series
        this.regularLabels = {
            'DEU-01': 'Germany - First Series',
            'ESP-02': 'Spain - Second Series',
            // Add new regular series here
            'HRV-01': 'Croatia - First Series'
        };
    }
}
```

### 2. Update Filter Options

If adding a new commemorative series that should appear in filters:

```javascript
// In the generateFilters() method, add new series to commemorative options
const commemorativeOptions = [
    { value: '', text: 'All Commemoratives' },
    { value: 'CC-2023', text: '2023 Commemoratives' },
    { value: 'Bundesländer-Hamburg', text: 'German Federal States' },
    // Add your new series
    { value: 'Your-New-Series', text: 'Your Series Display Name' }
];
```

### 3. Country Flag Support

If adding coins from a new country, ensure the country flag is available:

1. **Add flag image** to `static/images/flags/` directory
2. **Name convention**: `{country_name_lowercase}.png` (e.g., `croatia.png`)
3. **Update JavaScript** flag mapping if necessary

## 🗄️ BigQuery Database Updates

### 1. Schema Verification

Ensure your BigQuery table has the correct schema:

```sql
CREATE TABLE `your-project.coins.catalog` (
  coin_type STRING,
  year INT64,
  country STRING,
  series STRING,
  value FLOAT64,
  coin_id STRING,
  image_url STRING,
  feature STRING,
  volume STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### 2. Data Import Methods

#### Method A: Using the Project's Import Tool (Recommended)

The project includes a comprehensive import tool at `tools/import_catalog.py`:

```bash
cd tools/

# Basic import (replaces existing data)
python import_catalog.py

# The tool automatically:
# - Authenticates with Google Cloud using service_account.json
# - Creates dataset and table if they don't exist
# - Validates and cleans data
# - Imports with proper schema and timestamps
# - Provides detailed logging and error handling
```

**Import Tool Features:**
- **Automatic Schema Creation**: Creates optimized BigQuery tables with proper data types
- **Data Validation**: Validates and cleans data before import (removes invalid years/values)
- **Performance Optimization**: Uses partitioning by `created_at` and clustering by `country`, `coin_type`, `year`
- **Error Handling**: Comprehensive error handling with detailed logging
- **Timestamp Management**: Automatically adds `created_at` and `updated_at` timestamps

**Configuration:**
The import tool uses these default settings (modify in `import_catalog.py` if needed):
```python
PROJECT_ID = "coins2025"
DATASET_ID = "db"
SERVICE_ACCOUNT_PATH = "service_account.json"
CSV_FILE_PATH = "data/catalog.csv"
```

#### Method B: Using Streamlit Interface

For interactive data management, use the streamlit catalog viewer:

```bash
cd streamlit/

# Install dependencies
pip install -r requirements.txt

# Run the interface
streamlit run catalog.py

# Features:
# - View catalog data from BigQuery
# - Filter and search coins
# - Verify data integrity
# - Monitor import status
```

#### Method C: Direct BigQuery Import (Manual)

For direct control over the import process:

```bash
# Upload CSV to BigQuery directly
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --replace \
  your-project:coins.catalog \
  data/catalog.csv \
  coin_type:STRING,year:INTEGER,country:STRING,series:STRING,value:FLOAT,coin_id:STRING,image_url:STRING,feature:STRING,volume:STRING
```

#### Method D: Using Python Script (Custom)

For custom import logic:

```python
from google.cloud import bigquery
import pandas as pd
from datetime import datetime

def upload_new_series(csv_file_path):
    client = bigquery.Client()
    table_id = "your-project.coins.catalog"
    
    # Read and prepare CSV
    df = pd.read_csv(csv_file_path)
    
    # Rename columns to match schema
    df = df.rename(columns={
        'type': 'coin_type',
        'id': 'coin_id',
        'image': 'image_url'
    })
    
    # Add timestamps
    current_timestamp = datetime.now()
    df['created_at'] = current_timestamp
    df['updated_at'] = current_timestamp
    
    # Configure load job
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # Replace all data
        autodetect=False,
        schema=[
            bigquery.SchemaField("coin_type", "STRING"),
            bigquery.SchemaField("year", "INTEGER"),
            bigquery.SchemaField("country", "STRING"),
            bigquery.SchemaField("series", "STRING"),
            bigquery.SchemaField("value", "FLOAT"),
            bigquery.SchemaField("coin_id", "STRING"),
            bigquery.SchemaField("image_url", "STRING"),
            bigquery.SchemaField("feature", "STRING"),
            bigquery.SchemaField("volume", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("updated_at", "TIMESTAMP")
        ]
    )
    
    # Load data
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for completion
    
    print(f"Loaded {job.output_rows} rows to {table_id}")

# Usage
upload_new_series("data/catalog.csv")
```

### 3. Data Validation Queries

After importing, run these queries to validate your data:

#### Basic Data Integrity Checks
```sql
-- Check total count
SELECT COUNT(*) as total_coins FROM `your-project.coins.catalog`;

-- Check data distribution
SELECT 
  coin_type,
  COUNT(*) as count,
  MIN(year) as earliest_year,
  MAX(year) as latest_year
FROM `your-project.coins.catalog`
GROUP BY coin_type
ORDER BY coin_type;

-- Check for duplicates
SELECT coin_id, COUNT(*) as count
FROM `your-project.coins.catalog`
GROUP BY coin_id
HAVING COUNT(*) > 1;
```

#### Series-Specific Validation
```sql
-- Check new series
SELECT 
  series, 
  country,
  COUNT(*) as coin_count,
  MIN(year) as first_year,
  MAX(year) as last_year,
  STRING_AGG(DISTINCT CAST(value AS STRING), ', ' ORDER BY value) as denominations
FROM `your-project.coins.catalog` 
WHERE series = 'Your-New-Series-Name'
GROUP BY series, country
ORDER BY country;

-- Validate commemorative coins
SELECT 
  country,
  year,
  feature,
  volume,
  image_url
FROM `your-project.coins.catalog`
WHERE coin_type = 'CC' 
  AND year = 2024  -- Replace with target year
ORDER BY country;
```

#### Performance and Quality Checks
```sql
-- Check image URL accessibility (sample)
SELECT 
  country,
  COUNT(*) as total_coins,
  COUNT(image_url) as coins_with_images,
  ROUND(COUNT(image_url) / COUNT(*) * 100, 2) as image_coverage_percent
FROM `your-project.coins.catalog`
GROUP BY country
ORDER BY image_coverage_percent DESC;

-- Check feature descriptions for commemorative coins
SELECT 
  country,
  year,
  series,
  CASE 
    WHEN feature IS NULL OR feature = '' THEN 'Missing'
    WHEN LENGTH(feature) < 10 THEN 'Too Short'
    ELSE 'Good'
  END as feature_quality
FROM `your-project.coins.catalog`
WHERE coin_type = 'CC'
  AND year >= 2020
ORDER BY year DESC, country;
```

### 4. Advanced BigQuery Configuration

#### Table Optimization
The import tool automatically configures tables for optimal performance:

```sql
-- Partitioning strategy (automatically applied)
CREATE TABLE `coins2025.db.catalog` (
  -- column definitions --
)
PARTITION BY DATE(created_at)
CLUSTER BY country, coin_type, year;
```

#### Backup and Versioning
```sql
-- Create backup before major updates
CREATE TABLE `coins2025.db.catalog_backup_YYYYMMDD` AS
SELECT * FROM `coins2025.db.catalog`;

-- Create versioned table for history tracking
CREATE TABLE `coins2025.db.catalog_history` AS
SELECT *, CURRENT_TIMESTAMP() as archived_at
FROM `coins2025.db.catalog`;
```

## 🧪 Testing and Validation

### 1. Local Testing

#### Start Development Server
```bash
# Activate virtual environment
source venv/bin/activate

# Start server
uvicorn app.main:app --reload --port 8000

# Test endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/coins?coin_type=CC&series=Your-New-Series
```

#### Frontend Testing Checklist

- [ ] **Search functionality**: Search for new series by name
- [ ] **Filter functionality**: Filter by new series in commemorative dropdown
- [ ] **Coin display**: Verify coin images and descriptions appear correctly
- [ ] **Country flags**: Check flag appears for new countries
- [ ] **Responsive design**: Test on mobile, tablet, and desktop
- [ ] **Performance**: Ensure page loads quickly with new data

### 2. Data Quality Checks

#### Automated Validation Script

Create `scripts/validate_data.py`:

```python
import pandas as pd
import requests
from urllib.parse import urlparse

def validate_catalog_data(csv_path):
    """Validate catalog data for common issues."""
    df = pd.read_csv(csv_path)
    errors = []
    
    # Check required fields
    required_fields = ['type', 'year', 'country', 'series', 'value', 'id', 'image']
    for field in required_fields:
        if field not in df.columns:
            errors.append(f"Missing required field: {field}")
        elif df[field].isnull().any():
            errors.append(f"Null values found in field: {field}")
    
    # Validate coin types
    valid_types = ['RE', 'CC']
    invalid_types = df[~df['type'].isin(valid_types)]['type'].unique()
    if len(invalid_types) > 0:
        errors.append(f"Invalid coin types: {invalid_types}")
    
    # Validate years
    current_year = 2025
    invalid_years = df[(df['year'] < 1999) | (df['year'] > current_year)]
    if len(invalid_years) > 0:
        errors.append(f"Invalid years found: {invalid_years['year'].unique()}")
    
    # Validate denominations
    valid_values = [0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 1.0, 2.0]
    invalid_values = df[~df['value'].isin(valid_values)]['value'].unique()
    if len(invalid_values) > 0:
        errors.append(f"Invalid denominations: {invalid_values}")
    
    # Check for duplicate IDs
    duplicate_ids = df[df['id'].duplicated()]['id'].unique()
    if len(duplicate_ids) > 0:
        errors.append(f"Duplicate coin IDs: {duplicate_ids}")
    
    # Validate image URLs (sample check)
    sample_images = df['image'].dropna().head(5)
    for url in sample_images:
        try:
            response = requests.head(url, timeout=10)
            if response.status_code != 200:
                errors.append(f"Image URL returns {response.status_code}: {url}")
        except Exception as e:
            errors.append(f"Cannot access image URL {url}: {str(e)}")
    
    return errors

# Run validation
errors = validate_catalog_data("../data/catalog.csv")
if errors:
    print("❌ Validation errors found:")
    for error in errors:
        print(f"  - {error}")
else:
    print("✅ All validation checks passed!")
```

### 3. API Testing

#### Test API Endpoints

```bash
# Test health check
curl http://localhost:8000/api/health

# Test coin listing with new series
curl "http://localhost:8000/api/coins?series=Your-New-Series&limit=10"

# Test search functionality
curl "http://localhost:8000/api/coins?search=Hamburg&coin_type=CC"

# Test statistics endpoint
curl http://localhost:8000/api/coins/stats

# Test filter options
curl http://localhost:8000/api/coins/filters
```

#### Expected Response Format

```json
{
  "coins": [
    {
      "coin_type": "CC",
      "year": 2023,
      "country": "Germany",
      "series": "Bundesländer-Hamburg",
      "value": 2.0,
      "coin_id": "CC2023DEU-A-CC2-200",
      "image_url": "https://www.ecb.europa.eu/euro/coins/comm/html/comm_2023/hamburg.jpg",
      "feature": "Bundeslander series – Hamburg",
      "volume": "30 million coins"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

## 🚀 Deployment Process

### 1. Pre-Deployment Checklist

- [ ] **Data validation** passed all checks
- [ ] **Local testing** completed successfully
- [ ] **BigQuery data** imported and verified
- [ ] **Frontend labels** updated for new series
- [ ] **Documentation** updated (this file, README, etc.)
- [ ] **Git commit** with descriptive message

### 2. Staging Deployment

```bash
# Create feature branch
git checkout -b feature/add-new-series-name

# Commit changes
git add .
git commit -m "feat: add [Series Name] commemorative series

- Add [X] new coins from [Country] [Series Name] series
- Update frontend labels and filters
- Import data to BigQuery
- Add validation tests"

# Push to GitHub
git push origin feature/add-new-series-name

# Create pull request for review
```

### 3. Production Deployment

#### Automated Deployment (Recommended)

1. **Merge to main branch** triggers automatic deployment via Cloud Build
2. **Monitor deployment** in Google Cloud Console
3. **Verify live site** at [myeurocoins.org](https://myeurocoins.org)

#### Manual Deployment

```bash
# Deploy to Google Cloud Run
gcloud builds submit --config cloudbuild.yaml

# Or use deployment script
chmod +x scripts/deploy_to_gcp.sh
./scripts/deploy_to_gcp.sh
```

### 4. Post-Deployment Verification

```bash
# Test production API
curl https://myeurocoins.org/api/health
curl "https://myeurocoins.org/api/coins?series=Your-New-Series"

# Check website functionality
open https://myeurocoins.org
```

## 📝 Example: Adding a Complete New Series

Let's walk through adding the "Austrian Provinces" commemorative series as a complete example using the automated tools:

### Step 1: Research and Data Collection
- **Official source**: Austrian National Bank announcement
- **Series details**: 9 coins, one for each Austrian province, 2024-2026
- **Design**: Each coin features a landmark from the respective province

### Step 2: Automated Data Extraction

#### Using the Commemorative Scraper
```bash
cd tools/

# Edit scrape_cc_catalog.py
# Change these variables:
year = "2024"
url = "https://www.ecb.europa.eu/euro/coins/comm/html/comm_2024.en.html"

# Run the scraper
python scrape_cc_catalog.py

# Output: tmp/cc_catalog.json with Austrian data
```

#### Generate CSV Data
```bash
# Convert JSON to CSV format
python generate_cc_csv.py

# Output: tmp/cc.csv with properly formatted coin data
```

### Step 3: Data Preparation

#### Review Generated Data
The scraper will extract data like:
```json
{
  "2024": {
    "Austria": [
      {
        "country": "Austria",
        "feature": "Austrian Provinces series – Tyrol",
        "description": "The coin depicts...",
        "image": "https://www.ecb.europa.eu/euro/coins/comm/html/comm_2024/austria_tyrol.jpg",
        "year": "2024",
        "volume": "1.2 million coins",
        "series": "CC-2024"
      }
    ]
  }
}
```

#### Merge with Main Catalog
```bash
# Copy generated data to main catalog
cat tmp/cc.csv >> data/catalog.csv

# Or manually merge specific entries after review
```

### Step 4: Update Frontend Labels

#### JavaScript Labels (`static/js/coins.js`):
```javascript
this.commemorativeLabels = {
    // ... existing labels
    'CC-2024': '2024 Commemorative Coins',
    'Austrian-Provinces-Tyrol': 'Tyrol (Austrian Provinces series)',
    'Austrian-Provinces-Salzburg': 'Salzburg (Austrian Provinces series)',
    // ... add all 9 provinces as data becomes available
};
```

### Step 5: Database Import

#### Using the Project's Import Tool
```bash
cd tools/

# Import all catalog data to BigQuery
python import_catalog.py

# The tool will:
# - Validate the data
# - Create/update BigQuery tables
# - Import with proper timestamps
# - Provide import summary
```

#### Verify Import
```sql
-- Check new Austrian coins
SELECT 
  country,
  series,
  feature,
  volume,
  image_url
FROM `coins2025.db.catalog`
WHERE country = 'Austria' 
  AND year = 2024
  AND coin_type = 'CC'
ORDER BY feature;
```

### Step 6: Test and Deploy

```bash
# Local testing
uvicorn app.main:app --reload
# Test at http://localhost:8000

# Search for "Austria" and verify new coins appear
# Test filtering by "2024 Commemoratives"

# Create pull request
git checkout -b feature/add-austrian-provinces-2024
git add data/catalog.csv static/js/coins.js
git commit -m "feat: add Austrian Provinces 2024 commemorative series

- Add Austrian province commemorative coins for 2024
- Update frontend labels for better UX
- Import data to BigQuery with automated tools
- Verify all coin images and metadata"

git push origin feature/add-austrian-provinces-2024
```

### Step 7: Automated Workflow Summary

The complete workflow using project tools:

```bash
# 1. Scrape data from ECB
cd tools/
python scrape_cc_catalog.py  # (after editing year/URL)

# 2. Generate proper CSV format
python generate_cc_csv.py

# 3. Review and merge data
cp tmp/cc.csv data/new_series_2024.csv
# Review data, then append to main catalog

# 4. Update frontend (manual)
# Edit static/js/coins.js to add new series labels

# 5. Import to BigQuery
python import_catalog.py

# 6. Test locally
cd ..
uvicorn app.main:app --reload

# 7. Deploy
git add . && git commit -m "feat: add new series"
git push origin main  # Triggers automatic deployment
```

This automated approach significantly reduces manual work and ensures data consistency across the project.

## 🆘 Troubleshooting

### Common Issues and Solutions

#### 1. **Image URLs Not Loading**
- **Symptom**: Coin images don't appear on the website
- **Solution**: Verify URLs are accessible and use HTTPS
- **Check**: ECB website structure may have changed

#### 2. **Series Not Appearing in Filters**
- **Symptom**: New commemorative series doesn't show in dropdown
- **Solution**: Add series to `commemorativeLabels` in `coins.js`
- **Check**: Clear browser cache after deployment

#### 3. **BigQuery Import Errors**
- **Symptom**: Data import fails or returns errors
- **Solution**: Validate CSV format, check column headers
- **Check**: Ensure no duplicate coin_id values

#### 4. **API Returning No Results**
- **Symptom**: API calls return empty results for new series
- **Solution**: Check BigQuery data was imported correctly
- **Debug**: Run validation queries in BigQuery console

#### 5. **Frontend JavaScript Errors**
- **Symptom**: Catalog page doesn't load or filter properly
- **Solution**: Check browser console for JavaScript errors
- **Debug**: Validate JSON syntax in updated files

### Debug Commands

```bash
# Check BigQuery data
bq query --use_legacy_sql=false 'SELECT * FROM `your-project.coins.catalog` WHERE series = "Your-Series" LIMIT 10'

# Test API locally
curl -v http://localhost:8000/api/coins?series=Your-Series

# Check application logs
gcloud logs read --service=myeurocoins --limit=50

# Validate CSV format
python -c "import pandas as pd; print(pd.read_csv('data/catalog.csv').head())"
```

## 📋 Final Checklist

Before considering your new series addition complete:

- [ ] **Research completed** with official sources verified
- [ ] **Data files updated** (CSV and JSON)
- [ ] **Coin IDs follow** established conventions
- [ ] **Image URLs tested** and accessible
- [ ] **Frontend labels added** for user-friendly display
- [ ] **BigQuery import successful** with validation queries passed
- [ ] **Local testing completed** including all functionality
- [ ] **API endpoints tested** with new data
- [ ] **Documentation updated** including this guide if needed
- [ ] **Git commit created** with descriptive message
- [ ] **Pull request submitted** for code review
- [ ] **Production deployment completed** and verified
- [ ] **Live website tested** with new series visible

## 🔗 Additional Resources

- [European Central Bank Coin Database](https://www.ecb.europa.eu/euro/coins/)
- [NumiWiki - Comprehensive Coin Database](https://numiwiki.com/)
- [Google BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Bootstrap Documentation](https://getbootstrap.com/)

---

**Need help?** Open an issue on [GitHub](https://github.com/n-dimitrov/coins2025/issues) or start a [discussion](https://github.com/n-dimitrov/coins2025/discussions).

*Last updated: August 2025*

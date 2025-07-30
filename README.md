# coins2025
**Euro Coins Collector Community 2025**

A collaborative Euro coins catalog and collection tracking system for coin collectors. Track who has found which coins, browse the complete Euro coin catalog, and manage your collector community's acquisitions.

## Features

- **📊 Complete Euro Coin Catalog**: Browse all Euro coins (regular and commemorative) with images
- **👥 Collector Community**: Track which collectors have found each coin
- **🔍 Advanced Filtering**: Filter by country, year, value, coin type, and collector
- **📱 Multiple Views**: Table, card, and gallery display modes
- **🏆 Collection Statistics**: See collection sizes and find rates across collectors
- **🔎 Search Functionality**: Search across countries, features, and series
- **☁️ Database-Driven**: All data stored in Google BigQuery for reliability and performance

## Architecture

### Data Storage
- **BigQuery Database**: Primary data source for both catalog and ownership data
- **Catalog Table** (`coins2025.db.catalog`): Complete Euro coin information
- **Ownership History** (`coins2025.db.ownership_history`): Collector acquisition records

### Application Components
- **Streamlit Web App** (`catalog.py`): Interactive catalog interface
- **Data Import Scripts**: 
  - `import_db.py`: Import coin catalog to BigQuery
  - `import_history.py`: Import collector ownership history
- **Web Scrapers** (in `tools/`): Collect coin data from various sources

## Setup

### Prerequisites
- Python 3.8+
- Google Cloud account with BigQuery enabled
- Service account with BigQuery permissions

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd coins2025
   ```

2. **Install dependencies**:
   ```bash
   ./setup.sh
   # or manually:
   pip install -r requirements.txt
   ```

3. **Configure Google Cloud**:
   - Place your `service_account.json` file in the project root
   - Ensure the service account has BigQuery Data Editor and Job User roles

4. **Import data to BigQuery**:
   ```bash
   # Import coin catalog
   python import_db.py
   
   # Import ownership history
   python import_history.py
   ```

5. **Run the application**:
   ```bash
   streamlit run catalog.py
   ```

## Usage

### Web Interface
The Streamlit app provides an intuitive interface to:
- Browse the complete Euro coin catalog
- Filter coins by multiple criteria
- View collector statistics and ownership information
- Search for specific coins or features

### Data Management
- **Adding New Coins**: Update the catalog CSV and re-run `import_db.py`
- **Recording New Finds**: Add entries to `data/history.csv` and re-run `import_history.py`
- **Viewing Statistics**: Use the web interface or query BigQuery directly

### Collector Features
- **Personal Collections**: Filter to see what coins each collector has found
- **Find Rates**: See how many collectors have found each coin type
- **Community Overview**: View collection statistics across all collectors

## Data Structure

### Catalog Data
- **Type**: Regular (RE) or Commemorative (CC)
- **Basic Info**: Year, country, series, denomination value
- **Images**: High-quality coin images from ECB
- **Details**: Special features, volumes, unique identifiers

### Ownership Data
- **Collector Name**: Who found the coin
- **Coin ID**: Reference to catalog entry
- **Date**: When the coin was acquired
- **Individual Ownership**: Each collector has their own copy of each coin type

## Technical Details

### Database Schema
```sql
-- Catalog table
CREATE TABLE `coins2025.db.catalog` (
  coin_type STRING,
  year INTEGER,
  country STRING,
  series STRING,
  value FLOAT,
  coin_id STRING,
  image_url STRING,
  feature STRING,
  volume STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Ownership history table
CREATE TABLE `coins2025.db.ownership_history` (
  name STRING,
  coin_id STRING,
  date TIMESTAMP,
  date_only DATE
);
```

### Performance Optimizations
- **BigQuery Caching**: Streamlit caches database queries for faster loading
- **Partitioning**: Tables partitioned for optimal query performance
- **Clustering**: Strategic clustering on frequently queried columns

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with your own BigQuery setup
5. Submit a pull request

## License

This project is for educational and personal use in coin collecting communities.

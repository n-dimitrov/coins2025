"""
Series label generation utilities for backend
Provides helper functions for generating series labels and metadata
"""

from typing import Dict, List, Optional, Tuple
import re


class SeriesAnalyzer:
    """Analyzes series data and provides metadata for label generation."""
    
    # Country code mappings
    COUNTRY_CODES = {
        'AND': 'Andorra',
        'AUT': 'Austria', 
        'BEL': 'Belgium',
        'CYP': 'Cyprus',
        'DEU': 'Germany',
        'ESP': 'Spain',
        'EST': 'Estonia',
        'FIN': 'Finland',
        'FRA': 'France',
        'GRC': 'Greece',
        'HRV': 'Croatia',
        'IRL': 'Ireland',
        'ITA': 'Italy',
        'LTU': 'Lithuania',
        'LUX': 'Luxembourg',
        'LVA': 'Latvia',
        'MCO': 'Monaco',
        'MLT': 'Malta',
        'NLD': 'Netherlands',
        'PRT': 'Portugal',
        'SMR': 'San Marino',
        'SVK': 'Slovakia',
        'SVN': 'Slovenia',
        'VAT': 'Vatican City'
    }
    
    # Commemorative suffixes
    COMMEMORATIVE_SUFFIXES = {
        'TOR': 'Treaty of Rome',
        'EMU': 'Economic and Monetary Union',
        'TYE': 'Ten Years of Euro',
        'EUF': 'European Flag',
        'ERA': 'Erasmus Programme'
    }

    @classmethod
    def analyze_series_from_coins(cls, coins_data: List[Dict]) -> Dict[str, Dict]:
        """
        Analyze coins data to generate series metadata.
        
        Args:
            coins_data: List of coin dictionaries with 'series', 'year', 'country' fields
            
        Returns:
            Dictionary mapping series codes to metadata
        """
        series_metadata = {}
        
        # Group coins by series
        series_groups = {}
        for coin in coins_data:
            series = coin.get('series')
            if not series:
                continue
                
            if series not in series_groups:
                series_groups[series] = []
            series_groups[series].append(coin)
        
        # Generate metadata for each series
        for series_code, coins in series_groups.items():
            series_metadata[series_code] = cls._analyze_single_series(series_code, coins)
        
        return series_metadata

    @classmethod
    def _analyze_single_series(cls, series_code: str, coins: List[Dict]) -> Dict:
        """Analyze a single series and generate metadata."""
        
        # Extract years
        years = [coin.get('year') for coin in coins if coin.get('year')]
        years = sorted(set(years))
        
        # Determine series type
        is_commemorative = series_code.startswith('CC-')
        
        metadata = {
            'series_code': series_code,
            'is_commemorative': is_commemorative,
            'years': years,
            'min_year': min(years) if years else None,
            'max_year': max(years) if years else None,
            'coin_count': len(coins),
            'countries': list(set(coin.get('country') for coin in coins if coin.get('country')))
        }
        
        # Add type-specific metadata
        if is_commemorative:
            metadata.update(cls._analyze_commemorative_series(series_code))
        else:
            metadata.update(cls._analyze_regular_series(series_code, coins))
        
        return metadata

    @classmethod
    def _analyze_commemorative_series(cls, series_code: str) -> Dict:
        """Analyze commemorative series."""
        parts = series_code.split('-')
        
        metadata = {
            'base_year': None,
            'suffix': None,
            'suffix_description': None
        }
        
        if len(parts) >= 2:
            try:
                metadata['base_year'] = int(parts[1])
            except ValueError:
                pass
        
        if len(parts) >= 3:
            suffix = parts[2]
            metadata['suffix'] = suffix
            metadata['suffix_description'] = cls.COMMEMORATIVE_SUFFIXES.get(suffix, suffix)
        
        return metadata

    @classmethod
    def _analyze_regular_series(cls, series_code: str, coins: List[Dict]) -> Dict:
        """Analyze regular series."""
        parts = series_code.split('-')
        
        metadata = {
            'country_code': None,
            'country_name': None,
            'series_number': None
        }
        
        if len(parts) >= 2:
            country_code = parts[0]
            series_number = parts[1]
            
            metadata['country_code'] = country_code
            metadata['country_name'] = cls.COUNTRY_CODES.get(country_code, country_code)
            metadata['series_number'] = series_number
        
        return metadata

    @classmethod
    def generate_enhanced_filter_options(cls, coins_data: List[Dict]) -> Dict:
        """
        Generate enhanced filter options with metadata.
        
        Args:
            coins_data: List of coin dictionaries
            
        Returns:
            Enhanced filter options with metadata
        """
        # Get unique commemoratives
        commemoratives = list(set(
            coin['series'] for coin in coins_data 
            if coin.get('series', '').startswith('CC-')
        ))
        
        # Analyze series
        series_metadata = cls.analyze_series_from_coins(coins_data)
        
        # Generate commemorative options with metadata
        commemorative_options = []
        for series in sorted(commemoratives, key=lambda x: (
            -series_metadata.get(x, {}).get('base_year', 0),  # Sort by year desc
            x  # Then by series code
        )):
            metadata = series_metadata.get(series, {})
            commemorative_options.append({
                'code': series,
                'label': cls._generate_commemorative_label(metadata),
                'year': metadata.get('base_year'),
                'suffix': metadata.get('suffix'),
                'description': metadata.get('suffix_description')
            })
        
        return {
            'commemoratives': commemorative_options,
            'series_metadata': series_metadata
        }

    @classmethod
    def _generate_commemorative_label(cls, metadata: Dict) -> str:
        """Generate a label for commemorative series."""
        base_year = metadata.get('base_year')
        suffix_desc = metadata.get('suffix_description')
        
        if not base_year:
            return metadata.get('series_code', '')
        
        if suffix_desc and suffix_desc != metadata.get('suffix'):
            return f"{base_year} {suffix_desc}"
        
        return str(base_year)


def get_series_label_data() -> Dict:
    """
    Get all the data needed for client-side series label generation.
    This can be called from an API endpoint to provide the frontend with
    the necessary mapping data.
    """
    return {
        'country_codes': SeriesAnalyzer.COUNTRY_CODES,
        'commemorative_suffixes': SeriesAnalyzer.COMMEMORATIVE_SUFFIXES
    }

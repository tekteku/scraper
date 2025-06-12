import os
import re
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PropertyDataProcessor")

# Folders configuration
RAW_DATA_FOLDER = "real_estate_data/raw"
CLEAN_DATA_FOLDER = "real_estate_data/clean"
REPORTS_FOLDER = "real_estate_data/reports"

# Create output folders if they don't exist
for folder in [RAW_DATA_FOLDER, CLEAN_DATA_FOLDER, REPORTS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Generate timestamp for this session
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# Tunisia governorates and major cities for data normalization
TUNISIA_LOCATIONS = {
    # Governorates
    "tunis": "Tunis",
    "ariana": "Ariana",
    "ben arous": "Ben Arous",
    "manouba": "Manouba",
    "nabeul": "Nabeul",
    "zaghouan": "Zaghouan",
    "bizerte": "Bizerte",
    "beja": "Béja",
    "jendouba": "Jendouba",
    "kef": "Le Kef",
    "siliana": "Siliana",
    "sousse": "Sousse",
    "monastir": "Monastir",
    "mahdia": "Mahdia",
    "sfax": "Sfax",
    "kairouan": "Kairouan",
    "kasserine": "Kasserine",
    "sidi bouzid": "Sidi Bouzid",
    "gabes": "Gabès",
    "medenine": "Médenine",
    "tataouine": "Tataouine",
    "gafsa": "Gafsa",
    "tozeur": "Tozeur",
    "kebili": "Kébili",
    
    # Major cities and suburbs
    "la marsa": "La Marsa (Tunis)",
    "carthage": "Carthage (Tunis)",
    "sidi bou said": "Sidi Bou Saïd (Tunis)",
    "gammarth": "Gammarth (Tunis)",
    "la goulette": "La Goulette (Tunis)",
    "hammamet": "Hammamet (Nabeul)",
    "marsa": "La Marsa (Tunis)",
    "les berges du lac": "Les Berges du Lac (Tunis)",
    "lac": "Les Berges du Lac (Tunis)",
    "ain zaghouan": "Ain Zaghouan (Tunis)",
    "el menzah": "El Menzah (Tunis)",
    "manar": "El Manar (Tunis)",
    "menzah": "El Menzah (Tunis)",
    "ennasr": "Ennasr (Ariana)",
    "el ghazela": "El Ghazela (Ariana)",
    "ghazela": "El Ghazela (Ariana)",
    "jardins de carthage": "Jardins de Carthage (Tunis)",
    "soukra": "Soukra (Ariana)",
    "borj cedria": "Borj Cédria (Ben Arous)",
    "rades": "Radès (Ben Arous)",
    "ezzahra": "Ezzahra (Ben Arous)",
    "hammam lif": "Hammam Lif (Ben Arous)",
    "hammam-lif": "Hammam Lif (Ben Arous)",
    "megrine": "Mégrine (Ben Arous)",
    "mourouj": "El Mourouj (Ben Arous)",
    "nouvelle medina": "Nouvelle Médina (Ben Arous)",
    "ghazela": "El Ghazela (Ariana)",
    "aouina": "Aouina (Tunis)",
}

def normalize_location(location):
    """Normalize location names in Tunisia"""
    if not location or location == "Unknown" or pd.isna(location):
        return "Unknown"
    
    location = str(location).lower().strip()
    
    # First check if the exact location is in our mapping
    if location in TUNISIA_LOCATIONS:
        return TUNISIA_LOCATIONS[location]
    
    # Check if location contains any of our known locations
    for key, value in TUNISIA_LOCATIONS.items():
        if key in location:
            return value
    
    # If not found, return the title-cased version
    return location.title()

def clean_and_normalize_data(raw_file_path):
    """Process, clean and normalize raw property data"""
    logger.info(f"Starting data cleaning process for: {raw_file_path}")
    
    try:
        # Read the raw data
        df = pd.read_csv(raw_file_path)
        original_count = len(df)
        logger.info(f"Loaded {original_count} records from raw data file")
        
        # Store raw values before cleaning
        if 'raw_price' not in df.columns:
            df['raw_price'] = df['price']
        if 'raw_area' not in df.columns:
            df['raw_area'] = df['area']
        
        # ===== Price Normalization =====
        # Convert price to numeric, handling various formats
        df['price'] = df['price'].astype(str).apply(
            lambda x: re.sub(r'[^\d.]', '', x.replace(',', '.')) if x and pd.notna(x) else ''
        )
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        
        # ===== Area Normalization =====
        # Convert area to numeric, handling various formats
        df['area'] = df['area'].astype(str).apply(
            lambda x: re.sub(r'[^\d.]', '', x.replace(',', '.')) if x and pd.notna(x) else ''
        )
        df['area'] = pd.to_numeric(df['area'], errors='coerce')
        
        # ===== Location Normalization =====
        # Standardize location names
        df['location'] = df['location'].apply(normalize_location)
        
        # Add a region column based on location
        if 'region' not in df.columns:
            df['region'] = df['location'].apply(normalize_location)
        
        # ===== Property Type Standardization =====
        # Map property types to standard categories
        property_type_map = {
            'appartement': 'Appartement',
            'apartment': 'Appartement',
            'villa': 'Villa',
            'maison': 'Maison',
            'house': 'Maison',
            'studio': 'Studio',
            'duplex': 'Duplex',
            'bureau': 'Bureau',
            'office': 'Bureau',
            'local': 'Local Commercial',
            'commercial': 'Local Commercial',
            'terrain': 'Terrain',
            'land': 'Terrain',
        }
        
        def standardize_property_type(prop_type):
            if pd.isna(prop_type) or not prop_type:
                return 'Autre'
            
            prop_type = str(prop_type).lower().strip()
            for key, value in property_type_map.items():
                if key in prop_type:
                    return value
            return 'Autre'
        
        df['property_type'] = df['property_type'].apply(standardize_property_type)
        
        # ===== Clean Features =====
        # Standardize and clean features
        df['features'] = df['features'].fillna('')
        df['features'] = df['features'].apply(
            lambda x: ', '.join([item.strip() for item in str(x).split('\n') if item.strip()])
        )
        
        # ===== Handle Bedrooms/Bathrooms =====
        # Convert to numeric
        for col in ['bedrooms', 'bathrooms']:
            df[col] = df[col].apply(
                lambda x: re.sub(r'[^\d]', '', str(x)) if x and pd.notna(x) else ''
            )
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # ===== Remove Duplicates =====
        # Check for duplicates based on title, price, and location
        df_no_duplicates = df.drop_duplicates(subset=['title', 'price', 'location', 'area'])
        duplicate_count = original_count - len(df_no_duplicates)
        logger.info(f"Removed {duplicate_count} duplicate records")
        
        # ===== Outlier Detection =====
        # Detect and flag outliers in price and area
        def flag_outliers(df, column):
            # Only consider non-NA values
            values = df[column].dropna()
            
            if len(values) < 5:  # Need at least a few data points
                df[f'{column}_outlier'] = False
                return df
                
            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1
            
            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)
            
            # Flag outliers
            df[f'{column}_outlier'] = ((df[column] < lower_bound) | (df[column] > upper_bound))
            
            # Log statistics
            outlier_count = df[f'{column}_outlier'].sum()
            logger.info(f"Detected {outlier_count} outliers in {column}")
            logger.info(f"{column} bounds: [{lower_bound}, {upper_bound}], median: {values.median()}")
            
            return df
        
        # Flag outliers for price and area
        df_no_duplicates = flag_outliers(df_no_duplicates, 'price')
        df_no_duplicates = flag_outliers(df_no_duplicates, 'area')
        
        # ===== Handle Missing Critical Data =====
        # Create version with critical fields
        df_clean = df_no_duplicates.copy()
        
        # Drop records with both price and location missing
        df_filtered = df_clean.dropna(subset=['price', 'location'], how='all')
        missing_count = len(df_clean) - len(df_filtered)
        logger.info(f"Removed {missing_count} records with critical fields missing")
        
        # Create two versions of the final dataset
        # 1. With outliers included but flagged
        df_with_outliers = df_filtered.copy()
        
        # 2. With outliers removed
        df_no_outliers = df_filtered[
            (~df_filtered['price_outlier'] | df_filtered['price'].isna()) &
            (~df_filtered['area_outlier'] | df_filtered['area'].isna())
        ].copy()
        
        outliers_removed = len(df_filtered) - len(df_no_outliers)
        logger.info(f"Set aside {outliers_removed} outlier records in separate dataset")
        
        # ===== Generate Statistics =====
        # Calculate statistics for reporting
        stats = {
            "original_count": original_count,
            "duplicate_count": duplicate_count,
            "missing_data_count": missing_count,
            "outliers_count": outliers_removed,
            "final_count_with_outliers": len(df_with_outliers),
            "final_count_no_outliers": len(df_no_outliers),
            "price_statistics": {
                "min": df_filtered['price'].min(),
                "max": df_filtered['price'].max(),
                "mean": df_filtered['price'].mean(),
                "median": df_filtered['price'].median(),
                "std": df_filtered['price'].std()
            },
            "area_statistics": {
                "min": df_filtered['area'].min(),
                "max": df_filtered['area'].max(),
                "mean": df_filtered['area'].mean(),
                "median": df_filtered['area'].median(),
                "std": df_filtered['area'].std()
            },
            "sources": df_filtered['source_site'].value_counts().to_dict(),
            "property_types": df_filtered['property_type'].value_counts().to_dict(),
            "regions": df_filtered['region'].value_counts().to_dict()
        }
        
        return df_with_outliers, df_no_outliers, stats
    
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        return None, None, {"error": str(e)}

def process_raw_data_file(raw_file_path):
    """Process a raw data file and save cleaned versions"""
    logger.info(f"Processing file: {raw_file_path}")
    
    # Extract base name without extension
    base_name = os.path.basename(raw_file_path)
    name_without_ext = os.path.splitext(base_name)[0]
    
    # Process the data
    df_with_outliers, df_no_outliers, stats = clean_and_normalize_data(raw_file_path)
    
    if df_with_outliers is None:
        logger.error(f"Failed to process {raw_file_path}")
        return
    
    # Save statistics
    stats_file = os.path.join(REPORTS_FOLDER, f"{name_without_ext}_stats.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        # Convert numpy values to native Python types for JSON serialization
        stats_dict = {}
        for k, v in stats.items():
            if isinstance(v, dict):
                stats_dict[k] = {kk: float(vv) if isinstance(vv, np.number) else vv 
                                for kk, vv in v.items()}
            else:
                stats_dict[k] = float(v) if isinstance(v, np.number) else v
        json.dump(stats_dict, f, indent=4, ensure_ascii=False)
    
    # Save cleaned data with outliers
    clean_with_outliers_csv = os.path.join(CLEAN_DATA_FOLDER, f"{name_without_ext}_clean_with_outliers.csv")
    df_with_outliers.to_csv(clean_with_outliers_csv, index=False, encoding='utf-8')
    
    # Save cleaned data without outliers
    clean_no_outliers_csv = os.path.join(CLEAN_DATA_FOLDER, f"{name_without_ext}_clean_no_outliers.csv")
    df_no_outliers.to_csv(clean_no_outliers_csv, index=False, encoding='utf-8')
    
    logger.info(f"Saved cleaned data to:")
    logger.info(f"  - With outliers: {clean_with_outliers_csv} ({len(df_with_outliers)} records)")
    logger.info(f"  - Without outliers: {clean_no_outliers_csv} ({len(df_no_outliers)} records)")
    logger.info(f"  - Statistics: {stats_file}")
    
    return {
        "file_with_outliers": clean_with_outliers_csv,
        "file_no_outliers": clean_no_outliers_csv,
        "stats_file": stats_file,
        "count_with_outliers": len(df_with_outliers),
        "count_no_outliers": len(df_no_outliers)
    }

def generate_summary_report(processed_files):
    """Generate a summary report of all processed files"""
    logger.info("Generating summary report...")
    
    report = {
        "timestamp": TIMESTAMP,
        "processed_files": len(processed_files),
        "total_properties_with_outliers": sum(f['count_with_outliers'] for f in processed_files),
        "total_properties_no_outliers": sum(f['count_no_outliers'] for f in processed_files),
        "files": processed_files
    }
    
    # Save the report
    report_file = os.path.join(REPORTS_FOLDER, f"summary_report_{TIMESTAMP}.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Summary report saved to: {report_file}")
    
    return report

def combine_all_clean_data():
    """Combine all cleaned data files into a single master dataset"""
    logger.info("Combining all cleaned datasets...")
    
    # Find all cleaned files with outliers
    with_outliers_files = [f for f in os.listdir(CLEAN_DATA_FOLDER) if f.endswith('_clean_with_outliers.csv')]
    no_outliers_files = [f for f in os.listdir(CLEAN_DATA_FOLDER) if f.endswith('_clean_no_outliers.csv')]
    
    # Combine with outliers files
    if with_outliers_files:
        dfs_with_outliers = []
        for file in with_outliers_files:
            file_path = os.path.join(CLEAN_DATA_FOLDER, file)
            df = pd.read_csv(file_path)
            dfs_with_outliers.append(df)
        
        combined_with_outliers = pd.concat(dfs_with_outliers, ignore_index=True)
        combined_with_outliers = combined_with_outliers.drop_duplicates(subset=['title', 'price', 'location', 'area'])
        
        # Save combined file
        combined_with_outliers_file = os.path.join(CLEAN_DATA_FOLDER, f"all_properties_combined_with_outliers_{TIMESTAMP}.csv")
        combined_with_outliers.to_csv(combined_with_outliers_file, index=False, encoding='utf-8')
        logger.info(f"Combined {len(with_outliers_files)} files with outliers -> {len(combined_with_outliers)} total unique properties")
    
    # Combine no outliers files
    if no_outliers_files:
        dfs_no_outliers = []
        for file in no_outliers_files:
            file_path = os.path.join(CLEAN_DATA_FOLDER, file)
            df = pd.read_csv(file_path)
            dfs_no_outliers.append(df)
        
        combined_no_outliers = pd.concat(dfs_no_outliers, ignore_index=True)
        combined_no_outliers = combined_no_outliers.drop_duplicates(subset=['title', 'price', 'location', 'area'])
        
        # Save combined file
        combined_no_outliers_file = os.path.join(CLEAN_DATA_FOLDER, f"all_properties_combined_no_outliers_{TIMESTAMP}.csv")
        combined_no_outliers.to_csv(combined_no_outliers_file, index=False, encoding='utf-8')
        logger.info(f"Combined {len(no_outliers_files)} files without outliers -> {len(combined_no_outliers)} total unique properties")
    
    return {
        "combined_with_outliers": combined_with_outliers_file if with_outliers_files else None,
        "combined_no_outliers": combined_no_outliers_file if no_outliers_files else None,
        "count_with_outliers": len(combined_with_outliers) if with_outliers_files else 0,
        "count_no_outliers": len(combined_no_outliers) if no_outliers_files else 0
    }

def main():
    """Main function to process all raw data files"""
    logger.info(f"Starting data processing at {TIMESTAMP}")
    
    # Find all raw data files
    raw_files = []
    for file in os.listdir(RAW_DATA_FOLDER):
        if file.endswith('.csv') and 'raw' in file:
            raw_files.append(os.path.join(RAW_DATA_FOLDER, file))
    
    if not raw_files:
        logger.warning("No raw data files found in directory.")
        return
    
    logger.info(f"Found {len(raw_files)} raw data files to process")
    
    # Process each file
    processed_files = []
    for raw_file in raw_files:
        result = process_raw_data_file(raw_file)
        if result:
            processed_files.append(result)
    
    # Generate summary report
    report = generate_summary_report(processed_files)
    
    # Combine all cleaned data
    combined_result = combine_all_clean_data()
    
    logger.info(f"\nData processing complete!")
    logger.info(f"Processed {len(processed_files)} raw data files")
    logger.info(f"Total properties with outliers: {report['total_properties_with_outliers']}")
    logger.info(f"Total properties without outliers: {report['total_properties_no_outliers']}")
    
    if combined_result['combined_with_outliers']:
        logger.info(f"Combined dataset with outliers: {combined_result['count_with_outliers']} properties")
    
    if combined_result['combined_no_outliers']:
        logger.info(f"Combined dataset without outliers: {combined_result['count_no_outliers']} properties")

if __name__ == "__main__":
    main()

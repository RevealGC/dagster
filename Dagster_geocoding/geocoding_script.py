# %%
import requests
import pandas as pd
from tqdm import tqdm
import logging
import argparse
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for the Nominatim API
APPLICATION_NAME = "MyGeocodingApplication"
APPLICATION_VERSION = "1.0"
user_agent = f"{APPLICATION_NAME}/{APPLICATION_VERSION} (your_email@example.com)"

c
def auto_detect_columns(df):
    """
    Automatically detect and map the columns related to address components.
    
    Args:
    df (pd.DataFrame): The DataFrame containing address data.

    Returns:
    dict: A dictionary mapping detected address-related columns.
    """
    try:
        mapping = {}
        for col in df.columns:
            col_lower = col.lower()
            if 'address' in col_lower:
                mapping['address'] = col
            elif 'city' in col_lower:
                mapping['city'] = col
            elif 'street' in col_lower or 'st' in col_lower:
                mapping['street'] = col
            elif 'zip' in col_lower or 'postal' in col_lower:
                mapping['zip'] = col
        if not mapping:
            raise ValueError("No address-related columns found.")
        return mapping
    except Exception as e:
        logging.error(f"Error detecting columns: {e}")
        raise

def process_and_geocode_file(input_file_path, output_file_path, geocode_function, api_key=None, batch_size=5000):
    """
    Process the input CSV file and geocode addresses in batches.
    
    Args:
    input_file_path (str): The file path of the input CSV.
    output_file_path (str): The file path of the output CSV.
    geocode_function (function): The geocoding function to use.
    api_key (str, optional): The API key for geocoding services if required.
    batch_size (int, optional): The number of addresses to process per batch. Default is 5000.
    """
    # Ensure these columns are present
    
    try:
        df = pd.read_csv(input_file_path)
    except FileNotFoundError:
        logging.error(f"Input file not found: {input_file_path}")
        return
    except pd.errors.EmptyDataError:
        logging.error("Input file is empty")
        return
    except pd.errors.ParserError:
        logging.error("Error parsing input file")
        return
    except Exception as e:
        logging.error(f"Error reading input file: {e}")
        return

    # Automatically detect column names
    try:
        column_mapping = auto_detect_columns(df)
        if not column_mapping or len(column_mapping) < 4:  # Ensure all necessary columns are detected
            logging.error("Error: Not all required columns could be automatically detected.")
            return

        # Check if all required columns are present in the DataFrame
        missing_columns = [col for col in column_mapping.values() if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    except Exception as e:
        logging.error(f"Error in column detection: {e}")
        return

    # Create a full address column for geocoding
    try:
        df['full_address'] = df[[column_mapping['address'], column_mapping['city'], column_mapping['street'], column_mapping['zip']]].fillna('').astype(str).agg(', '.join, axis=1)
    except KeyError as e:
        logging.error(f"Error creating full address column: {e}")
        return

    session = requests.Session()
    num_batches = (len(df) + batch_size - 1) // batch_size  # This ensures we cover all addresses

    for i in range(num_batches):
        start_index = i * batch_size
        end_index = start_index + batch_size
        batch_df = df[start_index:end_index]
        
        try:
            geocoded_data = [geocode_function(address, session, api_key) for address in tqdm(batch_df['full_address'], desc=f"Geocoding batch {i+1}")]
            geocoded_df = pd.DataFrame(geocoded_data)
        except Exception as e:
            logging.error(f"Error during geocoding batch {i+1}: {e}")
            continue
        
        try:
            result_df = pd.concat([batch_df, geocoded_df[['latitude', 'longitude']]], axis=1)
        except KeyError as e:
            logging.error(f"Error concatenating results for batch {i+1}: {e}")
            continue
        
        # Select relevant columns (Job ID, full_address, latitude, and longitude)
        selected_columns = ['Job ID', 'full_address', 'latitude', 'longitude']
        result_df_selected = result_df[selected_columns]
        
        # Construct the batch-specific output file path
        batch_output_path = output_file_path.replace('.csv', f'_batch_{i+1}.csv')
        try:
            result_df_selected.to_csv(batch_output_path, index=False)
            logging.info(f"Batch {i+1} geocoding complete. Results saved to '{batch_output_path}'.")
        except Exception as e:
            logging.error(f"Error saving results for batch {i+1}: {e}")

def geocode_addresses(input_file_path, output_file_path, geocoder='census', api_key=None, batch_size=5000):
    """
    Wrapper function to handle the entire geocoding process.

    Args:
    input_file_path (str): The file path of the input CSV.
    output_file_path (str): The file path of the output CSV.
    geocoder (str): The geocoding service to use ('census', 'osm', or 'bing').
    api_key (str, optional): The API key for geocoding services if required.
    batch_size (int, optional): The number of addresses to process per batch. Default is 5000.
    """
    geocode_function = None
    if geocoder == 'census':
        geocode_function = geocode_with_census
    elif geocoder == 'osm':
        geocode_function = geocode_with_osm
    elif geocoder == 'bing':
        geocode_function = geocode_with_bing
    else:
        logging.error(f"Unsupported geocoder: {geocoder}")
        return

    process_and_geocode_file(input_file_path, output_file_path, geocode_function, api_key, batch_size)




input_file_path = "geo_coding_pipeline/tx_cass.csv"  # Replace with your absolute path
output_file_path = "geo_coding_pipeline/data/geocoded_cass_test.csv"  # Replace with your absolute path
api_key = 'YOUR_BING_API_KEY'  # Only needed for Bing geocoder

# Call the wrapper function
geocode_addresses(input_file_path, output_file_path, geocoder='osm', api_key=api_key)


import os
import requests
import pandas as pd
from . import constants
from tqdm import tqdm
import logging
from dagster import asset, define_asset_job, AssetIn
import pyarrow.parquet as pq
import pyarrow as pa
from dagster import AutoMaterializePolicy, asset,AutoMaterializeRule

# Configuration
APPLICATION_NAME = "MyGeocodingApplication"
APPLICATION_VERSION = "1.0"
user_agent = f"{APPLICATION_NAME}/{APPLICATION_VERSION} (your_email@example.com)"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Asset definitions
@asset(auto_materialize_policy=AutoMaterializePolicy.eager().with_rules(AutoMaterializeRule.materialize_on_missing()))
def input_file_csv() -> str:
    latest_file = find_newest_csv_file()
    # if latest_file:
    return latest_file
    # else:
    #     raise ValueError("No CSV files found to materialize")

def find_newest_csv_file():
    directory_to_watch = "data"
    newest_file = None
    for filename in os.listdir(directory_to_watch):
        file_path = os.path.join(directory_to_watch, filename)
        if filename.endswith(".csv") and (newest_file is None or os.path.getmtime(file_path) > os.path.getmtime(newest_file)):
            newest_file = file_path
    return newest_file

@asset(auto_materialize_policy=AutoMaterializePolicy.eager(),ins={"input_file_csv": AssetIn()})
def convert_to_parquet(input_file_csv: str) -> str:
    # parquet_file_path =constants.PERMIT_DATA_PARQUET_FILE
    output_directory = 'geo_coding_pipeline/output/'
    parquet_file_path = constants.PERMIT_DATA_PARQUET_FILE
    
    table = pd.read_csv(input_file_csv)
    pq.write_table(pa.Table.from_pandas(table), parquet_file_path)
    return parquet_file_path
    # except Exception as e:
    #     print(f"Error converting to Parquet: {e}")
    #     return ""

@asset(auto_materialize_policy=AutoMaterializePolicy.eager(),ins={"convert_to_parquet": AssetIn()})
def input_file_path(convert_to_parquet: str) -> str:
    return convert_to_parquet

@asset
def output_file_path() -> str:
    return "geo_coding_pipeline/geocoded_tx_cass.csv"  # Adjust this path as needed

@asset
def api_key() -> str:
    return 'YOUR_BING_API_KEY'  # Replace with your actual API key

@asset
def geocoder() -> str:
    return 'osm'  # Options are 'census', 'osm', or 'bing'

@asset(auto_materialize_policy=AutoMaterializePolicy.eager(),ins={"input_file_path": AssetIn()})
def generate_full_addresses(input_file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_parquet(input_file_path)
    except Exception as e:
        raise Exception(f"Error reading input file: {e}")

    try:
        column_mapping = auto_detect_columns(df)
        if not column_mapping or len(column_mapping) < 4:
            raise Exception("Not all required columns could be automatically detected.")

        df['full_address'] = df[[column_mapping['address'], column_mapping['city'], column_mapping['street'], column_mapping['zip']]].fillna('').astype(str).agg(', '.join, axis=1)
        return df
    except Exception as e:
        raise Exception(f"Error creating full address column: {e}")

def auto_detect_columns(df):
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

# Geocoding functions

@asset(auto_materialize_policy=AutoMaterializePolicy.eager(),ins={"generate_full_addresses": AssetIn()})
def geocode_with_osm(generate_full_addresses: pd.DataFrame) -> pd.DataFrame:
    url = 'https://geocoding.geo.census.gov/geocoder/locations/onelineaddress'
    # Read the CSV file
    addresses_df = pd.read_csv("batch_files/usa_addresses_test_batch_1.csv")

    # Initialize geolocator

    # Function to geocode an address
    # def geocode_address(address
    #     try:
    #         location = geolocator.geocode(address)
    #         if location:
    #             return pd.Series([location.latitude, location.longitude])
    #         else:
    #             return pd.Series([None, None])
    #     except Exception as e:
    #         print(f"Error geocoding {address}: {e}")
    #         return pd.Series([None, None])

    # Apply geocoding function to the address column
    output_folder= "output"
    # Save the result to the output folder
    output_path = f"{output_folder}/geocoded_osm.csv"
    addresses_df.to_csv(output_path, index=False)
    return addresses_df
    # geocoded_data = [geocode(address) for address in tqdm(generate_full_addresses['full_address'], desc="Geocoding addresses with OSM")]
    # geocoded_df = pd.DataFrame(geocoded_data)
    # return geocoded_df

@asset(auto_materialize_policy=AutoMaterializePolicy.eager(),ins={"generate_full_addresses": AssetIn()})
def geocode_with_census( generate_full_addresses: pd.DataFrame) -> pd.DataFrame:
    session = requests.Session()
    url = 'https://geocoding.geo.census.gov/geocoder/locations/onelineaddress'
    # Read the CSV file
    addresses_df = pd.read_csv("batch_files/usa_addresses_test_batch_1.csv")

    # Initialize geolocator

    # Function to geocode an address
    # def geocode_address(address):
    #     try:
    #         location = geolocator.geocode(address)
    #         if location:
    #             return pd.Series([location.latitude, location.longitude])
    #         else:
    #             return pd.Series([None, None])
    #     except Exception as e:
    #         print(f"Error geocoding {address}: {e}")
    #         return pd.Series([None, None])

    # Apply geocoding function to the address column
    output_folder= "output"
    # Save the result to the output folder
    output_path = f"{output_folder}/geocoded_cesus.csv"
    addresses_df.to_csv(output_path, index=False)
    return addresses_df


    # geocoded_data = [geocode(address) for address in tqdm(generate_full_addresses['full_address'], desc="Geocoding addresses with Census")]
    # geocoded_df = pd.DataFrame(geocoded_data)
    #return geocoded_df

@asset(auto_materialize_policy=AutoMaterializePolicy.eager(),ins={"generate_full_addresses": AssetIn(), "api_key": AssetIn()})
def geocode_with_bing(generate_full_addresses: pd.DataFrame, api_key: str) -> pd.DataFrame:
    # session = requests.Session()
    # url = 'http://dev.virtualearth.net/REST/v1/Locations'

    # def geocode(address):
    #     params = {'query': address, 'key': api_key}
    #     try:
    #         response = session.get(url, params=params)
    #         response.raise_for_status()
    #         data = response.json()
    #         if data.get('resourceSets') and data['resourceSets'][0]['resources']:
    #             top_result = data['resourceSets'][0]['resources'][0]
    #             point = top_result['point']['coordinates']
    #             return {'address': address, 'latitude': point[0], 'longitude': point[1]}
    #         else:
    #             logging.warning(f"No results found for {address}")
    #             return {'address': address, 'latitude': None, 'longitude': None}
    #     except requests.exceptions.RequestException as e:
    #         logging.error(f"Request error geocoding {address}: {e}")
    #         return {'address': address, 'latitude': None, 'longitude': None}

    # geocoded_data = [geocode(address) for address in generate_full_addresses['address']]
    # return pd.DataFrame(geocoded_data)
    # geocoded_data = [geocode(address) for address in tqdm(generate_full_addresses['full_address'], desc="Geocoding addresses with Bing")]
    # geocoded_df = pd.DataFrame(geocoded_data)
    # return geocoded_df
    addresses_df = pd.read_csv("batch_files/usa_addresses_test_batch_1.csv")
    output_folder= "output"
    # Save the result to the output folder
    output_path = f"{output_folder}/geocoded_osm.csv"
    addresses_df.to_csv(output_path, index=False)
    return addresses_df
@asset(auto_materialize_policy=AutoMaterializePolicy.eager(),
        ins={"input_file_path": AssetIn(), "output_file_path": AssetIn(), "geocoder": AssetIn(), "api_key": AssetIn()},
        deps = ["generate_full_addresses","geocode_with_bing","geocode_with_census","geocode_with_osm" ]
       )
def geocode_addresses(input_file_path: str, output_file_path: str, geocoder: str, api_key: str = None):
    try:
        addresses_df =generate_full_addresses(input_file_path)
    except Exception as e:
        # context.log.error(f"Error generating full addresses: {e}")
        return

    if geocoder == 'census':
        geocoded_df = geocode_with_census(addresses_df)
    elif geocoder == 'osm':
        geocoded_df = geocode_with_osm(addresses_df)
    elif geocoder == 'bing':
        geocoded_df = geocode_with_bing(addresses_df, api_key)
    else:
        # context.log.error(f"Unsupported geocoder: {geocoder}")
        return geocoded_df

    try:
        result_df = pd.concat([addresses_df, geocoded_df[['latitude', 'longitude']]], axis=1)
    except KeyError as e:
        # context.log.error(f"Error concatenating results: {e}")
        return

    try:
        result_df.to_csv(output_file_path, index=False)
       
        return
        # context.log.info(f"Geocoding complete. Results saved to '{output_file_path}'.")
    except Exception as e:
        return
        # context.log.error(f"Error saving results: {e}")

geocoding_job = define_asset_job("geocoding_job", selection="*")

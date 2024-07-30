# input_file_path = "../data/tx_cass.csv"
# output_file_path = "../data/geocoded_cass_test.csv"
# api_key = 'YOUR_BING_API_KEY'  # Only needed for Bing geocoder

#     # Call the wrapper function
# geocode_addresses(input_file_path, output_file_path, geocoder='osm', api_key=api_key)

from dagster import execute_pipeline
from geo_coding_pipeline.Dagster_geocoding import definitions

if __name__ == "__main__":
    execute_pipeline(definitions)
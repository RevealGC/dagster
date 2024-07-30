import os
from dagster import Definitions, repository, sensor, RunRequest, SkipReason, define_asset_job, AssetSelection,DefaultSensorStatus
from . import assets

# Define the assets
all_assets = [
    assets.input_file_csv,
    assets.input_file_path,
    assets.convert_to_parquet,
    assets.output_file_path,
    assets.api_key,
    assets.geocoder,
    assets.generate_full_addresses,
    assets.geocode_with_osm,
    assets.geocode_with_census,
    assets.geocode_with_bing,
    assets.geocode_addresses
]
input_csv_materialization_job = define_asset_job(
    name="input_csv_materialization_job",
    selection=AssetSelection.keys("input_file_csv"),  
)

# Define the job to run the convert_to_parquet asset
convert_to_parquet_job = define_asset_job(
    name="convert_to_parquet_job",
    selection=AssetSelection.keys("convert_to_parquet"),
)

# In-memory set to track seen files (non-persistent)
global seen_files
seen_files = set()
# Sensor definition to monitor the directory for new files
@sensor(job=convert_to_parquet_job,default_status=DefaultSensorStatus.RUNNING, minimum_interval_seconds=15)
def new_file_sensor(context):
    directory_to_watch = "data"

    # Check for new files in the directory
    new_files_found = False
    for filename in os.listdir(directory_to_watch):
        file_path = os.path.join(directory_to_watch, filename)
        if filename.endswith(".csv") and file_path not in seen_files:
            # New file detected
            seen_files.add(file_path)
            new_files_found = True
            yield RunRequest(
                run_key=file_path, 
                tags={"filename": file_path}
            )

    if not new_files_found:
        yield SkipReason("No new files found.")
        
# Combine the definitions
defs = Definitions(
    assets=all_assets,
    jobs=[input_csv_materialization_job,convert_to_parquet_job],
    sensors=[new_file_sensor]
)

@repository
def deploy_docker_repository():
    return defs 
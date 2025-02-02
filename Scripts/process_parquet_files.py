import os
import pandas as pd
from datetime import timedelta
import duckdb

# Directory paths
input_dir = "."
output_dir = "../processed_data"
os.makedirs(output_dir, exist_ok=True)

# Define time ranges in HH:MM:SS format
pre_market_start = timedelta(hours=4)  # 04:00:00
pre_market_end = timedelta(hours=9, minutes=30)  # 09:30:00
post_market_start = timedelta(hours=16)  # 16:00:00
post_market_end = timedelta(hours=20)  # 20:00:00

# Filter function
def filter_time_range(df, time_col, start, end):
    return df[(df[time_col] >= start) & (df[time_col] <= end)]

# Process each Parquet file
for file in sorted(os.listdir(input_dir)):
    if file.endswith(".parquet") and file.startswith("ctm"):
        print(f"Processing {file}...")
        
        # Read the Parquet file
        file_path = os.path.join(input_dir, file)
        
        # Query the Parquet file using DuckDB
        query = f"SELECT * FROM '{file_path}'"
        df = duckdb.query(query).to_df()
        print(df.head())

        # Check if TIME_M column exists
        if 'TIME_M' not in df.columns:
            print(f"Skipping {file}: 'TIME_M' column not found.\nThese are the columns: {df.columns}")
            continued = input("Press 'y' to continue processing other files, or any other key to stop: ")
            if continued.lower() == 'y':
                continue  # Skip the current file and proceed to the next
            else:
                print("Stopping the script.")
                break  # Exit the loop and stop processing  

        # Convert TIME_M from seconds to timedelta
        df['TIME_M'] = pd.to_timedelta(df['TIME_M'], unit='s')

        # Filter pre-market and post-market trades
        pre_market_data = filter_time_range(df, "TIME_M", pre_market_start, pre_market_end)
        post_market_data = filter_time_range(df, "TIME_M", post_market_start, post_market_end)

        # Save filtered data
        pre_market_output = os.path.join(output_dir, f"pre_market_{file}")
        post_market_output = os.path.join(output_dir, f"post_market_{file}")
        pre_market_data.to_parquet(pre_market_output, index=False)
        post_market_data.to_parquet(post_market_output, index=False)

        print(f"Saved pre-market and post-market data for {file}")

print("Processing complete!")

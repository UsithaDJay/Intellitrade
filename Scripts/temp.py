import os
import pandas as pd
from datetime import timedelta
import duckdb

# Define selected tickers
SELECTED_TICKERS = {
    "AAPL", "AMZN", "JNJ", "SQ", "TWLO", "VOO", "JPM", "T", "DIS", "MSFT", "AYX",
    "CRM", "SHOP", "VTI", "V", "GOOG", "BA", "BRK", "KO", "MA", "ABBV", "BABA", "BAC"
}

# Define time ranges
PRE_MARKET_START = timedelta(hours=4)  # 04:00:00
PRE_MARKET_END = timedelta(hours=9, minutes=30)  # 09:30:00
POST_MARKET_START = timedelta(hours=16)  # 16:00:00
POST_MARKET_END = timedelta(hours=20)  # 20:00:00

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Script location: savindu/dataset
INPUT_BASE_DIR = os.path.join(BASE_DIR, "dataset")
OUTPUT_BASE_DIR = os.path.join(BASE_DIR, "processed_data")

# Ensure output directory exists
os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

# Function to filter data based on time range
def filter_time_range(df, time_col, start, end, session_label):
    filtered_df = df[(df[time_col] >= start) & (df[time_col] <= end)].copy()
    filtered_df["MARKET_SESSION"] = session_label
    return filtered_df

# Process each month directory
# for month_dir in sorted(os.listdir(INPUT_BASE_DIR)):
for month_dir in sorted(['201901']):
    month_path = os.path.join(INPUT_BASE_DIR, month_dir)

    if not os.path.isdir(month_path):  # Skip non-directory files
        print(f"Skipping {month_dir}: Not a directory.")
        continue

    print(f"Processing month: {month_dir}...")

    # Ensure month directory exists in output
    output_month_dir = os.path.join(OUTPUT_BASE_DIR, month_dir)
    os.makedirs(output_month_dir, exist_ok=True)

    # Process each Parquet file in the month directory
    for file in sorted(os.listdir(month_path)):
        if not file.endswith(".parquet") or not file.startswith("ctm"):
            continue  # Skip non-trade message files

        print(f"Processing {file}...")

        # Read the Parquet file using DuckDB
        file_path = os.path.join(month_path, file)
        query = f"SELECT * FROM '{file_path}'"
        df = duckdb.query(query).to_df()

        # Ensure TIME_M column exists
        if "TIME_M" not in df.columns:
            print(f"Skipping {file}: 'TIME_M' column not found.\nColumns: {df.columns}")
            user_input = input("Press 'y' to continue processing other files, or any other key to stop: ")
            if user_input.lower() == 'y':
                continue
            else:
                print("Stopping the script.")
                break  # Exit processing

        # Convert TIME_M from seconds to timedelta
        df["TIME_M"] = pd.to_timedelta(df["TIME_M"], unit="s")

        # Filter for selected tickers
        df = df[df["SYM_ROOT"].isin(SELECTED_TICKERS)]

        # Extract pre-market and post-market trades
        pre_market_data = filter_time_range(df, "TIME_M", PRE_MARKET_START, PRE_MARKET_END, "PRE_MARKET")
        post_market_data = filter_time_range(df, "TIME_M", POST_MARKET_START, POST_MARKET_END, "POST_MARKET")

        # Combine both datasets
        final_df = pd.concat([pre_market_data, post_market_data])

        # Sort by SYM_ROOT and TIME_M
        final_df = final_df.sort_values(by=["SYM_ROOT", "TIME_M"])

        # Save to Parquet
        output_file = os.path.join(output_month_dir, f"filtered_{file}")
        final_df.to_parquet(output_file, index=False)

        print(f"Saved: {output_file}")

print("Processing complete!")

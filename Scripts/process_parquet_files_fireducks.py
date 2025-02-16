import os
import fireducks.pandas as pd  # Using FireDucks for acceleration
import duckdb
from datetime import timedelta

# Directory paths
input_dir = "/RAID/algotrade/sapumal"
output_dir = os.path.join(os.getcwd(), "processed_data")  # Output in the script's location
os.makedirs(output_dir, exist_ok=True)

# Define Pre-Market & Post-Market Time Ranges
pre_market_start, pre_market_end = timedelta(hours=4), timedelta(hours=9, minutes=30)
post_market_start, post_market_end = timedelta(hours=16), timedelta(hours=20)

# Selected Tickers
selected_tickers = {
    "AAPL", "AMZN", "JNJ", "SQ", "TWLO", "VOO", "JPM", "T", "DIS", "MSFT",
    "AYX", "CRM", "SHOP", "VTI", "V", "GOOG", "BA", "BRK", "KO", "MA", "ABBV", "BABA", "BAC"
}

# Skip Already Processed Directories
skip_dirs = {f"xep_m2019{month:02d}" for month in range(1, 13)} # Skipping xep_m201901 - xep_m201912
skip_dirs.update({"xep_m201902_ctm"}) # skip xep_m201902_ctm dir
skip_dirs.update({f"xep_m2020{month:02d}" for month in range(1, 3)}) # Skipping xep_m202001 - xep_m202002

# Function to Filter Time Ranges
def filter_time_range(df, time_col, start, end):
    return df[(df[time_col] >= start - timedelta(minutes=1)) & (df[time_col] <= end + timedelta(minutes=1))]

# Process Each Month Directory
for month_dir in sorted(os.listdir(input_dir)):
    month_path = os.path.join(input_dir, month_dir)

    # Skip Non-Data Directories
    if month_dir in skip_dirs or not month_dir.startswith("xep_m"):
        print(f"Skipping {month_dir}: Already processed or not a data directory.")
        continue

    if not os.path.isdir(month_path):
        print(f"Skipping {month_dir}: Not a directory.")
        continue

    print(f"Processing month: {month_dir}...")

    # Ensure Output Directory for Month Exists
    output_month_dir = os.path.join(output_dir, month_dir.split('_')[1])
    os.makedirs(output_month_dir, exist_ok=True)

    # Process Each Parquet File
    for file in sorted(os.listdir(month_path)):
        if file.endswith(".parquet") and file.startswith("ctm"):
            print(f"[INFO] Processing {file}...")

            # Read Parquet File Using DuckDB
            file_path = os.path.join(month_path, file)
            query = f"SELECT * FROM '{file_path}'"
            df = duckdb.query(query).to_df()

            # Convert SYM_ROOT from ByteArray to String
            df["SYM_ROOT"] = df["SYM_ROOT"].apply(lambda x: x.decode("utf-8") if isinstance(x, (bytes, bytearray)) else str(x))

            # Log Sample Rows
            print(f"[DEBUG] Sample rows from {file}:\n{df.head()}")

            # Ensure Required Columns Exist
            if 'TIME_M' not in df.columns or 'SYM_ROOT' not in df.columns:
                print(f"[ERROR] Skipping {file}: Missing required columns.")
                continue

            # Normalize TIME_M Scale
            max_time = df["TIME_M"].max()
            if max_time > 1e12: df["TIME_M"] = df["TIME_M"] / 1e9
            elif max_time > 1e9: df["TIME_M"] = df["TIME_M"] / 1e6
            elif max_time > 1e6: df["TIME_M"] = df["TIME_M"] / 1e3

            # Convert TIME_M to timedelta
            df["TIME_M"] = pd.to_timedelta(df["TIME_M"], unit="s")

            # Filter Only Selected Tickers
            df = df[df["SYM_ROOT"].isin(selected_tickers)]
            if df.empty:
                print(f"[WARNING] No matching tickers found in {file}. Skipping.")
                continue

            # Filter Pre-Market & Post-Market Data
            pre_market_data = filter_time_range(df, "TIME_M", pre_market_start, pre_market_end).copy()
            post_market_data = filter_time_range(df, "TIME_M", post_market_start, post_market_end).copy()

            # Add Market Session Column
            pre_market_data.loc[:, "Market_Session"] = "Pre-Market"
            post_market_data.loc[:, "Market_Session"] = "Post-Market"

            # Merge Data
            combined_data = pd.concat([pre_market_data, post_market_data])

            if combined_data.empty:
                print(f"[WARNING] No pre-market or post-market data found in {file}. Skipping.")
                continue

            # Save Processed Data with FireDucks Acceleration
            output_path = os.path.join(output_month_dir, f"filtered_{file}")
            combined_data.to_parquet(output_path, index=False)

            print(f"[INFO] Processed and saved: {output_path}")

print("[INFO] Processing complete!")

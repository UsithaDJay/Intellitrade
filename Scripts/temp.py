import os
import pandas as pd
from datetime import timedelta
import duckdb

# Directory paths
base_dir = os.path.dirname(os.path.abspath(__file__))  # Script location
input_dir = os.path.dirname('/RAID/algotrade/sapumal')  # Input directory
output_dir = os.path.join(base_dir, "processed_data")  # Output directory
os.makedirs(output_dir, exist_ok=True)

# Define pre-market and post-market time ranges
pre_market_start = timedelta(hours=4)  # 04:00:00
pre_market_end = timedelta(hours=9, minutes=30)  # 09:30:00
post_market_start = timedelta(hours=16)  # 16:00:00
post_market_end = timedelta(hours=20)  # 20:00:00

# Tickers of interest
selected_tickers = {
    "AAPL", "AMZN", "JNJ", "SQ", "TWLO", "VOO", "JPM", "T", "DIS", "MSFT",
    "AYX", "CRM", "SHOP", "VTI", "V", "GOOG", "BA", "BRK", "KO", "MA", "ABBV", "BABA", "BAC"
}

# Function to filter time range
def filter_time_range(df, time_col, start, end):
    return df[(df[time_col] >= start - timedelta(minutes=1)) & (df[time_col] <= end + timedelta(minutes=1))]

# **Process only directories >= `xep_201909`**
for month_dir in sorted(os.listdir(input_dir)):
    if not month_dir.startswith("xep_"):  # Ensure it follows the correct format
        print(f"Skipping {month_dir}: Not a valid data directory.")
        continue
    
    # Extract YYYYMM from `xep_YYYYMM`
    try:
        month_number = int(month_dir.split("_")[1])  # Extract YYYYMM
    except (IndexError, ValueError):
        print(f"Skipping {month_dir}: Incorrect directory format.")
        continue

    # Skip directories before `xep_201909`
    if month_number < 201909:
        print(f"Skipping {month_dir}: Already processed.")
        continue

    month_path = os.path.join(input_dir, month_dir)
    
    if not os.path.isdir(month_path):  # Skip non-directory files
        print(f"Skipping {month_dir}: Not a directory.")
        continue

    print(f"Processing month: {month_dir}...")

    # Output directory for this month
    output_month_dir = os.path.join(output_dir, month_dir.split('_')[1])  # Extract YYYYMM
    os.makedirs(output_month_dir, exist_ok=True)

    # Process each Parquet file
    for file in sorted(os.listdir(month_path)):
        if file.endswith(".parquet") and file.startswith("ctm"):
            print(f"[INFO] Processing {file}...")

            file_path = os.path.join(month_path, file)

            # Query the Parquet file using DuckDB
            query = f"SELECT * FROM '{file_path}'"
            df = duckdb.query(query).to_df()

            # Convert SYM_ROOT bytearray to string
            df["SYM_ROOT"] = df["SYM_ROOT"].apply(lambda x: x.decode("utf-8") if isinstance(x, (bytes, bytearray)) else str(x))

            # Check if TIME_M column exists
            if 'TIME_M' not in df.columns:
                print(f"[ERROR] Skipping {file}: 'TIME_M' column not found.\nColumns: {df.columns}")
                continue

            # Check if SYM_ROOT column exists
            if 'SYM_ROOT' not in df.columns:
                print(f"[ERROR] Skipping {file}: 'SYM_ROOT' column not found.\nColumns: {df.columns}")
                continue

            # Normalize TIME_M column scale
            max_time = df["TIME_M"].max()
            if max_time > 1e12:  # Nanoseconds
                df["TIME_M"] = df["TIME_M"] / 1e9
            elif max_time > 1e9:  # Microseconds
                df["TIME_M"] = df["TIME_M"] / 1e6
            elif max_time > 1e6:  # Milliseconds
                df["TIME_M"] = df["TIME_M"] / 1e3

            # Convert TIME_M from seconds to timedelta
            df["TIME_M"] = pd.to_timedelta(df["TIME_M"], unit="s")

            # Filter only the selected tickers
            df = df[df["SYM_ROOT"].isin(selected_tickers)]

            # Skip file if no matching tickers
            if df.empty:
                print(f"[WARNING] No matching tickers found in {file}. Skipping.")
                continue

            # Filter pre-market and post-market trades
            pre_market_data = filter_time_range(df, "TIME_M", pre_market_start, pre_market_end)
            post_market_data = filter_time_range(df, "TIME_M", post_market_start, post_market_end)

            # Fix SettingWithCopyWarning by making a copy
            pre_market_data = pre_market_data.copy()
            post_market_data = post_market_data.copy()

            # Add session labels
            pre_market_data.loc[:, "Market_Session"] = "Pre-Market"
            post_market_data.loc[:, "Market_Session"] = "Post-Market"
            combined_data = pd.concat([pre_market_data, post_market_data])

            # Skip file if no pre/post market data
            if combined_data.empty:
                print(f"[WARNING] No pre-market or post-market data found in {file}. Skipping.")
                continue

            # Save processed data
            output_path = os.path.join(output_month_dir, f"filtered_{file}")
            combined_data.to_parquet(output_path, index=False)

            print(f"[INFO] Processed and saved: {output_path}")

print("[INFO] Processing complete!")

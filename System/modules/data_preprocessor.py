import pandas as pd
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()

def preprocess_data(data):
    data = data.copy()
    feature_columns = []
    
    data[feature_columns] = scaler.fit_transform(data[feature_columns])
    
    return data, scaler



#######
def calculate_range_change_metrics(df):
    # Sort by SYM_ROOT and DATE to preserve time order for percent change calculation
    df = df.sort_values(by=['DATE'])

    # Range-based change as a percentage of the minimum value
    df['pre_market_range_change'] = ((df['pre_market_price_max'] - df['pre_market_price_min'])
                                     / df['pre_market_price_min']) * 100
    df['prev_post_market_range_change'] = ((df['post_market_price_max'].shift(1) - df['post_market_price_min'].shift(1))
                                      / df['post_market_price_min'].shift(1)) * 100

    # Spread relative to the mean as a percentage (to measure volatility)
    df['pre_market_spread'] = ((df['pre_market_price_max'] - df['pre_market_price_min']) / df['pre_market_price_mean'])*100
    df['prev_post_market_spread'] = ((df['post_market_price_max'].shift(1) - df['post_market_price_min'].shift(1)) / df['post_market_price_mean'].shift(1))*100

    return df


# Function to calculate percentage increment
def calculate_percentage_increment(df, col, window):
    df = df.sort_values(by="DATE")
    df[f"{col}_avg_{window}"] = df[col].rolling(window=window, min_periods=window).mean().shift(1)

    df[f"{col}_avg_{window}_increment"] = ((df[col] - df[f"{col}_avg_{window}"]) / df[f"{col}_avg_{window}"]) * 100

    return df


def calculate_precentage_increment_for_price(df):
  df = calculate_percentage_increment(df, 'pre_market_price_mean',1)
  df = calculate_percentage_increment(df, 'pre_market_price_mean',3)
  df = calculate_percentage_increment(df, 'pre_market_price_mean',5)

  df = calculate_percentage_increment(df, 'pre_market_price_std',1)
  df = calculate_percentage_increment(df, 'pre_market_price_std',3)

  df = calculate_percentage_increment(df, 'PREV_post_market_price_mean',1)
  df = calculate_percentage_increment(df, 'PREV_post_market_price_mean',3)
  df = calculate_percentage_increment(df, 'PREV_post_market_price_mean',5)

  df = calculate_percentage_increment(df, 'PREV_post_market_price_std',1)
  df = calculate_percentage_increment(df, 'PREV_post_market_price_std',3)

  return df


def calculate_percentage_increment_for_pre_post(df):
  # Apply the function for pre-market
  df = calculate_percentage_increment(df, "pre_market_volume", 3)
  df = calculate_percentage_increment(df, "pre_market_volume", 5)
  df = calculate_percentage_increment(df, "pre_market_volume", 9)
  df = calculate_percentage_increment(df, "pre_market_volume", 12)

  # Apply the function for post-market volumes
  df = calculate_percentage_increment(df, "PREV_post_market_volume", 3)
  df = calculate_percentage_increment(df, "PREV_post_market_volume", 5)
  df = calculate_percentage_increment(df, "PREV_post_market_volume", 9)
  df = calculate_percentage_increment(df, "PREV_post_market_volume", 12)
  return df


def calculate_the_percentage_increment_open_close(df):
  df = calculate_percentage_increment(df, 'PREV_OPEN',3)
  df = calculate_percentage_increment(df, 'PREV_OPEN',5)

  df = calculate_percentage_increment(df, 'PREV_CLOSE',3)
  df = calculate_percentage_increment(df, 'PREV_CLOSE',5)

  df = calculate_percentage_increment(df, 'PREV_HIGH',3)
  df = calculate_percentage_increment(df, 'PREV_CLOSE',3)

  return df


# def retrieve_the_Labels(df, buy_sell_threshold):

#   # Define labels based on percentiles
#   df["label"] = "Neutral"  # Default label

#   percentile_values = [buy_percentile, sell_percentile]
#   percentile_values_all = {p: df["average_increment_per_day"].quantile(p) for p in percentile_values}

#   # Clamp the buy percentile between min and max
#   buy_val = percentile_values_all[buy_percentile]
#   if buy_val > buy_sell_threshold['max_dif']:
#       buy_val = buy_sell_threshold['max_dif']
#   elif buy_val < buy_sell_threshold['min_dif']:
#       buy_val = buy_sell_threshold['min_dif']
#   percentile_values_all[buy_percentile] = buy_val

#   # Clamp the sell percentile between -max and -min
#   sell_val = percentile_values_all[sell_percentile]
#   if sell_val < -buy_sell_threshold['max_dif']:
#       sell_val = -buy_sell_threshold['max_dif']
#   elif sell_val > -buy_sell_threshold['min_dif']:
#       sell_val = -buy_sell_threshold['min_dif']
#   percentile_values_all[sell_percentile] = sell_val

#   df.loc[df["average_increment_per_day"] >= percentile_values_all[buy_percentile], "label"] = "Buy"
#   df.loc[df["average_increment_per_day"] <= percentile_values_all[sell_percentile], "label"] = "Sell"

#   return df, percentile_values_all


# def create_the_labels(df, test_df, buy_sell_threshold = {'max_dif':1.5,'min_dif':0.5}):
#   df['average_increment_per_day'] = (df['CLOSE'] - df['OPEN'])*100/df['OPEN']
#   test_df['average_increment_per_day'] = (test_df['CLOSE'] - test_df['OPEN'])*100/test_df['OPEN']

#   df, percentile_values_all = retrieve_the_Labels(df,buy_sell_threshold)
#   test_df, percentile_values_all = retrieve_the_Labels(test_df,buy_sell_threshold)

#   return df, test_df

def preprocess_for_ml(df, categorical_columns, boolean_columns=[]):
    """
    Preprocess the DataFrame for ML by:
    - One-hot encoding categorical columns.
    - Converting boolean columns to numerical (0/1).

    Args:
        df (pd.DataFrame): The dataset to preprocess.
        categorical_columns (list): List of categorical column names to one-hot encode.
        boolean_columns (list): List of boolean column names to convert to numerical.

    Returns:
        pd.DataFrame: The preprocessed DataFrame.
    """
    # One-hot encode categorical columns
    df = pd.get_dummies(df, columns=categorical_columns, drop_first=False)

    # Convert boolean columns to integers (0/1)
    for col in boolean_columns:
        if df[col].dtype == 'bool':
            df[col] = df[col].astype(int)

    return df
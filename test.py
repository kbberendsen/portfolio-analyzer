import pandas as pd
import os

# Load monthly and daily data
df = pd.read_parquet(os.path.join('output', 'portfolio_monthly.parquet'))
daily_df = pd.read_parquet(os.path.join('output', 'portfolio_performance_daily.parquet'))

print(df.head())
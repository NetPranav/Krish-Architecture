import pandas as pd
import glob

files = glob.glob('data/raw/*.csv')
for f in files:
    if 'Government.csv' in f:
        continue
    print(f"\n--- File: {f} ---")
    try:
        # Read a chunk first
        df = pd.read_csv(f, on_bad_lines='skip', low_memory=False)
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"First row: {df.iloc[0].to_dict() if not df.empty else 'Empty'}")
    except Exception as e:
        print(f"Error reading {f}: {e}")

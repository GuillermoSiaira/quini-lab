import numpy as np
import pandas as pd
from google.cloud import bigquery
import time
import os

PROJECT_ID = "quini6-opt-7626"
DATASET_ID = "quini6_data"
TABLE_ID = "quini_montecarlo"

def generate_montecarlo(n_draws=100000):
    print(f"Generating {n_draws} Monte Carlo simulated draws...")
    
    # Pre-allocate array for speed
    # We draw 6 numbers from 00 to 45 (total 46 numbers)
    all_draws = []
    
    start = time.time()
    for _ in range(n_draws):
        # random.choice without replacement
        draw = np.sort(np.random.choice(46, 6, replace=False))
        all_draws.append(draw)
        
    df = pd.DataFrame(all_draws, columns=['N1', 'N2', 'N3', 'N4', 'N5', 'N6'])
    df['sorteo_id'] = range(1, n_draws + 1)
    
    print(f"Generation completed in {time.time() - start:.2f} seconds.")
    return df

def upload_to_bigquery(df):
    print("Uploading to BigQuery...")
    client = bigquery.Client(project=PROJECT_ID)
    
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE", # Replace data if exists
    )
    
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()  # Wait for the job to complete
    
    table = client.get_table(table_ref)
    print(f"Loaded {table.num_rows} rows and {len(table.schema)} columns to {table_ref}")

if __name__ == '__main__':
    # Generamos 100,000 para no agotar cuota ni tiempo
    df = generate_montecarlo(100000)
    upload_to_bigquery(df)

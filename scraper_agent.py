import requests
from bs4 import BeautifulSoup
import pandas as pd
from google.cloud import bigquery
import datetime
import re

PROJECT_ID = "quini6-opt-7626"
DATASET_ID = "quini6_data"
TABLE_ID = "quini_empirical"

def scrape_quini6_results():
    print("Scraping REAL Quini 6 empirical data from quiniya.com.ar...")
    url = "https://quiniya.com.ar/sorteos/"
    response = requests.get(url)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    
    if not table:
        raise ValueError("Could not find the historical table on the page.")
        
    tbody = table.find('tbody')
    rows = tbody.find_all('tr')
    
    draws = []
    
    # Parse each row
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 6:
            continue
            
        date_str = cols[0].text.strip()
        try:
            # Example: 24/5/2026
            dt = datetime.datetime.strptime(date_str, "%d/%m/%Y")
        except:
            dt = datetime.datetime.now()
            
        # El sorteo de quini suele ser 21:15 hs
        dt = dt.replace(hour=21, minute=15, second=0)
        
        # Extract sorteo_id from the link href (e.g., /sorteos/3376)
        sorteo_id = 0
        a_tag = cols[5].find('a')
        if a_tag and 'href' in a_tag.attrs:
            match = re.search(r'/sorteos/(\d+)', a_tag['href'])
            if match:
                sorteo_id = int(match.group(1))
                
        # Helper to parse 6 numbers string "05 08 10 12 28 34"
        def parse_numbers(num_str):
            nums = num_str.strip().split()
            if len(nums) >= 6:
                return [int(n) for n in nums[:6]]
            return None
            
        variantes = {
            'Tradicional': cols[1].text,
            'Segunda': cols[2].text,
            'Revancha': cols[3].text,
            'SiempreSale': cols[4].text
        }
        
        for var_name, var_nums_str in variantes.items():
            nums = parse_numbers(var_nums_str)
            if nums:
                draws.append({
                    'N1': nums[0],
                    'N2': nums[1],
                    'N3': nums[2],
                    'N4': nums[3],
                    'N5': nums[4],
                    'N6': nums[5],
                    'sorteo_id': sorteo_id,
                    'timestamp': dt,
                    'variante': var_name
                })
                
    df = pd.DataFrame(draws)
    print(f"Successfully scraped {len(df)} real draws/variants.")
    return df

def upload_to_bigquery(df):
    print("Uploading REAL Empirical data to BigQuery...")
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()
    
    table = client.get_table(table_ref)
    print(f"Loaded {table.num_rows} empirical rows to {table_ref}")

if __name__ == '__main__':
    df = scrape_quini6_results()
    upload_to_bigquery(df)

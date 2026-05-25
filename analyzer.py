import pandas as pd
from google.cloud import bigquery
import itertools

PROJECT_ID = "quini6-opt-7626"
DATASET_ID = "quini6_data"

def get_frequencies(client, table_id):
    query = f"""
    WITH unnested_draws AS (
      SELECT N1 as N FROM `{PROJECT_ID}.{DATASET_ID}.{table_id}` UNION ALL
      SELECT N2 as N FROM `{PROJECT_ID}.{DATASET_ID}.{table_id}` UNION ALL
      SELECT N3 as N FROM `{PROJECT_ID}.{DATASET_ID}.{table_id}` UNION ALL
      SELECT N4 as N FROM `{PROJECT_ID}.{DATASET_ID}.{table_id}` UNION ALL
      SELECT N5 as N FROM `{PROJECT_ID}.{DATASET_ID}.{table_id}` UNION ALL
      SELECT N6 as N FROM `{PROJECT_ID}.{DATASET_ID}.{table_id}`
    )
    SELECT N as number, COUNT(*) as frequency
    FROM unnested_draws
    GROUP BY N
    ORDER BY N
    """
    return client.query(query).to_dataframe()

def generate_optimized_tickets(pool, num_tickets=7):
    all_combinations = list(itertools.combinations(pool, 6))
    valid_combinations = all_combinations # Sin filtros estructurales, solo varianza pura
    
    if len(valid_combinations) < num_tickets:
        return valid_combinations

    # Algoritmo codicioso para maximizar la cobertura de tripletes (pares de 3)
    all_triplets = list(itertools.combinations(pool, 3))
    best_tickets = []
    uncovered_triplets = set(all_triplets)
    candidates = valid_combinations.copy()
    
    for _ in range(num_tickets):
        best_combo = None
        max_covered = -1
        
        for combo in candidates:
            combo_triplets = set(itertools.combinations(combo, 3))
            new_covered = len(combo_triplets.intersection(uncovered_triplets))
            
            if new_covered > max_covered:
                max_covered = new_covered
                best_combo = combo
                
        if best_combo:
            best_tickets.append(best_combo)
            candidates.remove(best_combo)
            covered_by_best = set(itertools.combinations(best_combo, 3))
            uncovered_triplets = uncovered_triplets - covered_by_best
            
    return best_tickets

def analyze():
    print("Iniciando Agente Analizador (ERC 8004)...")
    client = bigquery.Client(project=PROJECT_ID)
    
    print("Obteniendo distribución de Monte Carlo (Teórica)...")
    df_mc = get_frequencies(client, "quini_montecarlo")
    total_mc_balls = df_mc['frequency'].sum()
    df_mc['prob_teorica'] = df_mc['frequency'] / total_mc_balls
    
    print("Obteniendo distribución Empírica (Real/Scraping)...")
    df_emp = get_frequencies(client, "quini_empirical")
    total_emp_balls = df_emp['frequency'].sum()
    df_emp['prob_empirica'] = df_emp['frequency'] / total_emp_balls
    
    # Cruzando bases de datos
    df_merged = pd.merge(df_mc, df_emp, on='number', suffixes=('_mc', '_emp'))
    
    # Calculando desviación (Anomalía)
    df_merged['desviacion'] = df_merged['prob_empirica'] - df_merged['prob_teorica']
    
    # Queremos explotar la varianza, así que buscamos los números con mayor desviación positiva (los que están saliendo anormalmente más de la cuenta)
    df_merged = df_merged.sort_values(by='desviacion', ascending=False)
    
    print("\n--- TOP 9 NÚMEROS ANÓMALOS DETECTADOS ---")
    print(df_merged.head(9)[['number', 'prob_teorica', 'prob_empirica', 'desviacion']])
    
    top_9_pool = df_merged.head(9)['number'].tolist()
    
    print(f"\nGenerando {7} boletas usando el Pool Anómalo: {top_9_pool}")
    boletas = generate_optimized_tickets(top_9_pool, num_tickets=7)
    
    print("\n================ TUS BOLETAS A JUGAR ================")
    for i, t in enumerate(boletas, 1):
        formatted_ticket = [f"{int(n):02d}" for n in sorted(t)]
        print(f"Boleta {i}: {' - '.join(formatted_ticket)}")
    print("=====================================================")

if __name__ == '__main__':
    analyze()

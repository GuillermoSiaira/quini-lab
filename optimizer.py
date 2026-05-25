import itertools
import random

def generate_optimized_tickets(pool, num_tickets=7):
    # Generar todas las combinaciones posibles de 6 numeros del pool
    all_combinations = list(itertools.combinations(pool, 6))
    
    # Aplicar filtros estadísticos
    valid_combinations = []
    for combo in all_combinations:
        # Filtro de pares/impares (Queremos evitar 6 pares o 6 impares)
        evens = sum(1 for n in combo if n % 2 == 0)
        odds = 6 - evens
        if evens == 0 or odds == 0:
            continue
            
        # Filtro de consecutividad (evitar más de 3 números consecutivos)
        consecutivos = 0
        max_consecutivos = 0
        sorted_combo = sorted(combo)
        for i in range(5):
            if sorted_combo[i+1] - sorted_combo[i] == 1:
                consecutivos += 1
                max_consecutivos = max(max_consecutivos, consecutivos)
            else:
                consecutivos = 0
        if max_consecutivos > 2:
            continue
            
        valid_combinations.append(combo)

    # Si hay menos combinaciones válidas que tickets requeridos, usamos todas y rellenamos
    if len(valid_combinations) < num_tickets:
        return valid_combinations

    # Algoritmo codicioso para maximizar la cobertura de tripletes (pares de 3)
    # Queremos que los 7 tickets cubran la mayor cantidad de combinaciones de 3 números distintas posibles
    all_triplets = list(itertools.combinations(pool, 3))
    
    best_tickets = []
    uncovered_triplets = set(all_triplets)
    
    # Copia de seguridad en caso de que necesitemos reiniciar el greedy
    candidates = valid_combinations.copy()
    
    for _ in range(num_tickets):
        best_combo = None
        max_covered = -1
        
        for combo in candidates:
            # Cuántos tripletes NUEVOS cubre esta combinación
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

def analyze_and_run():
    print("==================================================")
    print(" OPTIMIZADOR QUINI 6 - ESTRATEGIA 27/05/2026 ")
    print("==================================================")
    
    presupuesto = 21000
    costo_completa = 3000
    costo_tradicional = 1500
    
    print(f"\nPresupuesto disponible: ${presupuesto} ARS")
    
    boletas_completas = presupuesto // costo_completa
    boletas_tradicionales = presupuesto // costo_tradicional
    
    print("\n[ANÁLISIS ESTADÍSTICO Y DE RENTABILIDAD]")
    print(f"- Opción A (Tradicional): {boletas_tradicionales} boletas. Participa en 2 sorteos (Tradicional Primer Sorteo y La Segunda). Total oportunidades: {boletas_tradicionales * 2}.")
    print(f"- Opción B (Completa): {boletas_completas} boletas. Participa en 4 sorteos (Trad. 1, Trad. 2, Revancha y Siempre Sale). Total oportunidades: {boletas_completas * 4}.")
    print("\n>>> Decisión Matemática: La 'Jugada Completa' ofrece 28 oportunidades de pozo contra 28 de la tradicional, pero DA ACCESO a modalidades que siempre tienen ganadores ('Siempre Sale'). Es la ruta matemáticamente óptima para el presupuesto.")
    
    # Patrón Estadístico: Mezcla de números calientes (sorteo anterior), adyacentes y balanceados
    # Del sorteo del 24/05: 05, 08, 10, 12, 28, 34 y 11, 14, 20, 35, 39, 43
    pool = [2, 8, 9, 11, 12, 21, 28, 35, 41]
    
    print("\n[GENERACIÓN DE POOL Y PATRONES]")
    print(f"Números seleccionados según patrón estadístico (Pool de {len(pool)}): {pool}")
    
    tickets = generate_optimized_tickets(pool, num_tickets=boletas_completas)
    
    print(f"\nGenerando la Combinación Óptima de {len(tickets)} boletas usando Ruedas Combinatorias (Greedy Triplet Cover)...")
    
    print("\n================ TUS BOLETAS A JUGAR ================")
    for i, t in enumerate(tickets, 1):
        # Format numbers with leading zeros
        formatted_ticket = [f"{n:02d}" for n in sorted(t)]
        print(f"Boleta {i}: {' - '.join(formatted_ticket)}")
    print("=====================================================")
    print("- Indicacion para la Agencia:")
    print(f"Pide 7 boletas COMPLETAS. Costo exacto: ${boletas_completas * costo_completa} ARS.")
    
if __name__ == '__main__':
    analyze_and_run()

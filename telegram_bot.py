import os
import itertools
from dotenv import load_dotenv
from google.cloud import bigquery
from google import genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PROJECT_ID = "quini6-opt-7626"
DATASET_ID = "quini6_data"

bq_client = bigquery.Client(project=PROJECT_ID)
ai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="us-central1")

def generate_optimized_tickets(pool, num_tickets):
    all_combinations = list(itertools.combinations(pool, 6))
    if len(all_combinations) < num_tickets:
        return all_combinations

    all_triplets = list(itertools.combinations(pool, 3))
    best_tickets = []
    uncovered_triplets = set(all_triplets)
    candidates = all_combinations.copy()
    
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

def get_last_draws(variante=None):
    where_clause = f"WHERE variante = '{variante}'" if variante else ""
    query = f"""
    SELECT N1, N2, N3, N4, N5, N6, sorteo_id, timestamp, variante
    FROM `{PROJECT_ID}.{DATASET_ID}.quini_empirical`
    {where_clause}
    ORDER BY timestamp DESC
    LIMIT 4
    """
    df = bq_client.query(query).to_dataframe()
    return df

def get_bq_stats(variante=None):
    where_clause = ""
    divisor_emp = 624.0 if variante else 2496.0
    
    if variante:
        where_clause = f"WHERE variante = '{variante}'"

    query = f"""
    WITH mc AS (
        SELECT N as number, COUNT(*) as freq_mc
        FROM (
            SELECT N1 as N FROM `{PROJECT_ID}.{DATASET_ID}.quini_montecarlo` UNION ALL
            SELECT N2 as N FROM `{PROJECT_ID}.{DATASET_ID}.quini_montecarlo` UNION ALL
            SELECT N3 as N FROM `{PROJECT_ID}.{DATASET_ID}.quini_montecarlo` UNION ALL
            SELECT N4 as N FROM `{PROJECT_ID}.{DATASET_ID}.quini_montecarlo` UNION ALL
            SELECT N5 as N FROM `{PROJECT_ID}.{DATASET_ID}.quini_montecarlo` UNION ALL
            SELECT N6 as N FROM `{PROJECT_ID}.{DATASET_ID}.quini_montecarlo`
        ) GROUP BY N
    ),
    emp AS (
        SELECT N as number, COUNT(*) as freq_emp
        FROM (
            SELECT N1 as N FROM `{PROJECT_ID}.{DATASET_ID}.quini_empirical` {where_clause} UNION ALL
            SELECT N2 as N FROM `{PROJECT_ID}.{DATASET_ID}.quini_empirical` {where_clause} UNION ALL
            SELECT N3 as N FROM `{PROJECT_ID}.{DATASET_ID}.quini_empirical` {where_clause} UNION ALL
            SELECT N4 as N FROM `{PROJECT_ID}.{DATASET_ID}.quini_empirical` {where_clause} UNION ALL
            SELECT N5 as N FROM `{PROJECT_ID}.{DATASET_ID}.quini_empirical` {where_clause} UNION ALL
            SELECT N6 as N FROM `{PROJECT_ID}.{DATASET_ID}.quini_empirical` {where_clause}
        ) GROUP BY N
    )
    SELECT 
        mc.number, 
        mc.freq_mc, 
        emp.freq_emp,
        (emp.freq_emp / {divisor_emp}) as prob_empirica,
        (mc.freq_mc / 600000.0) as prob_teorica
    FROM mc
    JOIN emp ON mc.number = emp.number
    """
    df = bq_client.query(query).to_dataframe()
    df['desviacion'] = df['prob_empirica'] - df['prob_teorica']
    
    calientes = df.sort_values(by='desviacion', ascending=False).head(9)
    rezagados = df.sort_values(by='desviacion', ascending=True).head(9)
    return calientes, rezagados

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("🎟️ Boletas Tradicional", callback_data="btn_tradicional"),
            InlineKeyboardButton("🎟️ Boletas Revancha", callback_data="btn_revancha")
        ],
        [
            InlineKeyboardButton("📊 Ver Último Sorteo", callback_data="btn_ultimo"),
            InlineKeyboardButton("🧠 ¿Cómo funciona?", callback_data="btn_explicar")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "¡Hola! Soy tu Agente Analizador del Quini 6 (ERC 8004) operando con DATOS REALES.\n\n"
        "¿En qué te puedo ayudar hoy? Puedes escribir tu consulta o usar estos botones:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    simulated_text = ""
    
    if data == "btn_tradicional":
        simulated_text = "Dame boletas para la modalidad Tradicional"
    elif data == "btn_revancha":
        simulated_text = "Dame boletas para la modalidad Revancha"
    elif data == "btn_ultimo":
        simulated_text = "Dame los resultados del último sorteo"
    elif data == "btn_explicar":
        simulated_text = "Explícame cómo funciona tu algoritmo de cálculo de números y las desviaciones"
        
    await process_request(query.message, simulated_text, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    await process_request(update.message, user_text, context)

async def process_request(message, user_text, context) -> None:
    user_text_lower = user_text.lower()
    
    variante = None
    var_context = "Todas las variantes (Global)"
    if "tradicional" in user_text_lower: 
        variante = "Tradicional"
        var_context = "Solo Tradicional"
    elif "segunda" in user_text_lower: 
        variante = "Segunda"
        var_context = "Solo Segunda"
    elif "revancha" in user_text_lower: 
        variante = "Revancha"
        var_context = "Solo Revancha"
    elif "siempre" in user_text_lower or "sale" in user_text_lower: 
        variante = "SiempreSale"
        var_context = "Solo Siempre Sale"

    processing_msg = await message.reply_text(f"🧠 Consultando BigQuery ({var_context})...")
    
    try:
        calientes, rezagados = get_bq_stats(variante)
        ultimos_sorteos = get_last_draws(variante)
        
        presupuesto = 21000 # default
        costo_boleta = 3000
        num_boletas = presupuesto // costo_boleta
        
        import re
        dinero_match = re.search(r'\$?(\d{2,5})', user_text_lower)
        if dinero_match:
            presupuesto = int(dinero_match.group(1))
            num_boletas = max(1, presupuesto // costo_boleta)
            
        pool_caliente = calientes['number'].tolist()
        boletas_calculadas = generate_optimized_tickets(pool_caliente, num_boletas)
        
        boletas_str = ""
        for i, t in enumerate(boletas_calculadas, 1):
            boletas_str += f"Boleta {i}: {' - '.join([f'{int(n):02d}' for n in sorted(t)])}\n"
            
        ultimos_sorteos_str = ultimos_sorteos.to_string(index=False)
            
        data_context = f"""
        Contexto Estadístico (BigQuery DATOS REALES):
        Filtro de Variante: {var_context}
        Números Calientes (mayor desviación positiva): {calientes[['number', 'desviacion']].to_dict('records')}
        Números Rezagados (mayor desviación negativa): {rezagados[['number', 'desviacion']].to_dict('records')}
        
        ÚLTIMOS SORTEOS REALES EXTRAÍDOS DE LA BASE DE DATOS:
        {ultimos_sorteos_str}
        
        PRE-CÁLCULO MATEMÁTICO STRICTO:
        El costo oficial actual de una boleta completa del Quini 6 es de $3000 ARS.
        El usuario ha mencionado o se asume un presupuesto de ${presupuesto} ARS.
        Por lo tanto, puede comprar exactamente {num_boletas} boletas completas.
        El algoritmo Python ya calculó las boletas óptimas usando los números calientes de la modalidad requerida. SON ESTAS:
        {boletas_str}
        
        Pregunta del usuario: "{user_text}"
        
        INSTRUCCIONES CRÍTICAS (NO ROMPER):
        1. Eres el Agente QuiniLab. NO inventes combinaciones de boletas ni hagas cálculos matemáticos de combinatoria por tu cuenta.
        2. Si el usuario pide los resultados del último sorteo, DÁSELOS basándote en la tabla de "ÚLTIMOS SORTEOS REALES" de arriba. Menciona la variante, el ID del sorteo y los números.
        3. Si el usuario pide boletas o menciona un presupuesto, DEBES darle ÚNICAMENTE las boletas que aparecen en la sección "PRE-CÁLCULO MATEMÁTICO STRICTO" de arriba. Cópialas tal cual.
        4. Aclara en qué variante te estás basando ({var_context}).
        5. Siempre aclara que la boleta cuesta $3000 ARS.
        6. Sé amable y conversacional, pero riguroso con los datos.
        """
        
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=data_context,
        )
        await processing_msg.edit_text(response.text)
        
    except Exception as e:
        await processing_msg.edit_text(f"Error interno: {str(e)}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()

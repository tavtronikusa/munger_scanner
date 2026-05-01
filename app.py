import streamlit as st
import yfinance as yf
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Munger Rule Scanner", layout="wide")

st.title("🛡️ Munger's 13 Rules Investment Scanner")
st.write("Analizador de acciones basado en la disciplina de Charlie Munger.")
st.markdown("---")

# --- SECCIÓN DE ENTRADA DE DATOS ---
col_tick, col_man, col_val = st.columns([1, 1, 1])

with col_tick:
    ticker_input = st.text_input("1. Ticker (ej: MSFT, GOOGL):", "MSFT").upper()

with col_man:
    st.write("2. ¿Usar valor de Simply Wall St?")
    usar_manual = st.checkbox("Activar ajuste manual", value=False)

with col_val:
    valor_estimado = st.number_input("3. Valor Intrínseco ($):", min_value=0.0, value=100.0, help="Introduce el Fair Value que encontraste en Simply Wall St u otra fuente.")

st.markdown("---")

if st.button("🚀 Ejecutar Análisis Completo"):
    with st.spinner(f'Analizando datos de {ticker_input}...'):
        try:
            stock = yf.Ticker(ticker_input)
            info = stock.info
            
            # --- RESUMEN DE ACTIVIDAD ---
            st.subheader(f"🏢 Empresa: {info.get('longName', ticker_input)}")
            resumen = info.get('longBusinessSummary', "No hay descripción disponible.")
            with st.expander("Haz clic aquí para leer qué hace esta empresa"):
                st.write(resumen)

            # --- EXTRACCIÓN DE MÉTRICAS (Basado en las 13 reglas) ---
            gm = info.get('grossMargins', 0)
            om = info.get('operatingMargins', 0)
            nm = info.get('profitMargins', 0)
            roe = info.get('returnOnEquity', 0)
            eps_growth = info.get('earningsGrowth', 0)
            de = info.get('debtToEquity', 500) / 100
            cr = info.get('currentRatio', 0)
            cash = info.get('totalCash', 0)
            debt = info.get('totalDebt', 1)
            cvd = cash / debt
            price = info.get('currentPrice', 1)

            # --- LÓGICA DEL MARGEN DE SEGURIDAD ---
            if usar_manual:
                mos = (valor_estimado - price) / valor_estimado if valor_estimado > 0 else 0
                fuente_mos = "Manual (Simply Wall St / Análisis propio)"
            else:
                target = info.get('targetMeanPrice', price)
                mos = (target - price) / target if target > 0 else 0
                fuente_mos = "Estimación promedio de analistas (Yahoo Finance)"

            # --- CÁLCULO DE PUNTUACIÓN Munger (100 pts) ---
            score = 0
            # Rentabilidad (35 pts)
            if gm >= 0.40: score += 8
            if om >= 0.20: score += 8
            if nm >= 0.15: score += 7
            if eps_growth >= 0.10: score += 6
            if roe >= 0.15: score += 6
            # Salud Financiera (25 pts)
            if de <= 0.5: score += 8
            if cr >= 1.5: score += 7
            if cvd >= 1.0: score += 10
            # Margen de Seguridad (40 pts) - La regla de oro
            if mos >= 0.30: score += 40 
            elif mos >= 0.15: score += 20

            # --- RESULTADOS VISUALES ---
            st.markdown("### 📊 Resultado del Diagnóstico")
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.metric(label="Puntuación Total", value=f"{score} / 100")
                if score >= 80:
                    st.success("✅ CALIDAD EXTREMA: Un negocio 'Mungeriano' de manual.")
                elif score >= 60:
                    st.warning("⚠️ CALIDAD ACEPTABLE: Buen negocio, pero revisa el precio o la deuda.")
                else:
                    st.error("❌ NO PASA EL FILTRO: Riesgo alto o valoración excesiva.")
                
                st.info(f"**Valoración basada en:**\n{fuente_mos}")

            with c2:
                # Tabla comparativa de reglas
                data = {
                    "Regla de Munger": ["Margen Bruto", "ROE", "Deuda/Patrimonio", "Caja vs Deuda", "Margen de Seguridad"],
                    "Estado Actual": [f"{gm*100:.1f}%", f"{roe*100:.1f}%", f"{de:.2f}", f"{cvd:.2f}", f"{mos*100:.1f}%"],
                    "Meta Ideal": ["> 40%", "> 15%", "< 0.5", "> 1.0", ">= 30%"]
                }
                st.table(pd.DataFrame(data))

        except Exception as e:
            st.error(f"Hubo un problema al obtener los datos. Asegúrate de que el ticker '{ticker_input}' sea correcto.")
            st.info("Nota: Algunas empresas internacionales o muy pequeñas pueden no tener todos los datos públicos disponibles.")

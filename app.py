import streamlit as st
import yfinance as yf
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Munger Rule Scanner", layout="wide")

# --- BARRA LATERAL PARA AJUSTES MANUALES (SIMPLY WALL ST) ---
st.sidebar.header("🎯 Ajustes de Valoración")
st.sidebar.write("Usa los datos de Simply Wall St o tu propio análisis para mayor precisión.")

usar_manual = st.sidebar.checkbox("Usar Valor Intrínseco Manual")
valor_estimado = st.sidebar.number_input("Valor Intrínseco Estimado ($)", min_value=0.0, value=100.0)

st.title("🛡️ Munger's 13 Rules Investment Scanner")
st.markdown("---")

# Entrada del Ticker
ticker_input = st.text_input("Introduce el Ticker oficial (ej: MSFT, GOOGL, V):", "MSFT").upper()

if st.button("Ejecutar Análisis"):
    with st.spinner(f'Analizando {ticker_input}...'):
        try:
            stock = yf.Ticker(ticker_input)
            info = stock.info
            
            # --- RESUMEN DE ACTIVIDAD ---
            st.subheader(f"Acerca de {info.get('longName', ticker_input)}")
            resumen = info.get('longBusinessSummary', "No hay descripción disponible.")
            with st.expander("Leer resumen de la empresa"):
                st.write(resumen)

            # --- EXTRACCIÓN DE MÉTRICAS ---
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
                fuente_mos = "Manual (User/SimplyWallSt)"
            else:
                target = info.get('targetMeanPrice', price)
                mos = (target - price) / target if target > 0 else 0
                fuente_mos = "Analistas (Yahoo Finance)"

            # --- CÁLCULO DE PUNTUACIÓN (100 pts) ---
            score = 0
            if gm >= 0.40: score += 8
            if om >= 0.20: score += 8
            if nm >= 0.15: score += 7
            if eps_growth >= 0.10: score += 6
            if roe >= 0.15: score += 6
            if de <= 0.5: score += 8
            if cr >= 1.5: score += 7
            if cvd >= 1.0: score += 10
            
            # Ponderación fuerte al Margen de Seguridad
            if mos >= 0.30: score += 40 
            elif mos >= 0.15: score += 20

            # --- RESULTADOS ---
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric(label="Munger Score", value=f"{score} / 100")
                st.write(f"**Fuente de valoración:** {fuente_mos}")
                if score >= 80: st.success("CALIDAD EXTREMA")
                elif score >= 60: st.warning("CALIDAD MEDIA")
                else: st.error("NO CUMPLE FILTROS")

            with col2:
                data = {
                    "Métrica": ["Gross Margin", "ROE", "Debt/Equity", "Cash vs Debt", "Margen Seguridad"],
                    "Valor Actual": [f"{gm*100:.1f}%", f"{roe*100:.1f}%", f"{de:.2f}", f"{cvd:.2f}", f"{mos*100:.1f}%"],
                    "Meta Munger": ["> 40%", "> 15%", "< 0.5", "> 1.0", ">= 30%"]
                }
                st.table(pd.DataFrame(data))

        except Exception as e:
            st.error(f"Error técnico: {e}")

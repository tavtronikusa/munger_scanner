import streamlit as st
import yfinance as yf
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Munger Rule Scanner", layout="wide")

st.title("🛡️ Munger's 13 Rules Investment Scanner")
st.markdown("---")

# Entrada del Ticker
ticker_input = st.text_input("Introduce el Ticker oficial (ej: MSFT, GOOGL, V, CRM):", "MSFT").upper()

if st.button("Ejecutar Análisis"):
    with st.spinner(f'Analizando {ticker_input} bajo los criterios de Munger...'):
        try:
            # Extracción de datos
            stock = yf.Ticker(ticker_input)
            info = stock.info
            financials = stock.financials
            cashflow = stock.cashflow

            # --- NUEVA SECCIÓN: RESUMEN DE ACTIVIDAD ---
            st.subheader(f"Acerca de {info.get('longName', ticker_input)}")
            resumen = info.get('longBusinessSummary', "No hay un resumen disponible para este ticker.")
            
            # Mostramos solo las primeras 500 caracteres con un botón para leer más
            with st.expander("Ver descripción completa de la empresa"):
                st.write(resumen)
            st.markdown("---")
            
            # 1. INCOME STATEMENT (35 pts)
            gm = info.get('grossMargins', 0)
            om = info.get('operatingMargins', 0)
            nm = info.get('profitMargins', 0)
            roe = info.get('returnOnEquity', 0)
            # Estimación simple de crecimiento de EPS (último año)
            eps_growth = info.get('earningsGrowth', 0)

            # 2. BALANCE SHEET (35 pts)
            de = info.get('debtToEquity', 500) / 100 # Default alto si no hay dato
            cr = info.get('currentRatio', 0)
            cash = info.get('totalCash', 0)
            debt = info.get('totalDebt', 1)
            cvd = cash / debt
            # Dilución de acciones (cambio en acciones en circulación)
            sh_out = info.get('sharesOutstanding', 1)
            
            # 3. VALORACIÓN / MARGEN DE SEGURIDAD (30 pts)
            price = info.get('currentPrice', 1)
            target = info.get('targetMeanPrice', price)
            mos = (target - price) / target if target > 0 else 0

            # --- LÓGICA DE PUNTUACIÓN PONDERADA ---
            score = 0
            # Reglas de Ingresos
            if gm >= 0.40: score += 8
            if om >= 0.20: score += 8
            if nm >= 0.15: score += 7
            if eps_growth >= 0.10: score += 6
            if roe >= 0.15: score += 6

            # Reglas de Balance
            if de <= 0.5: score += 8
            if cr >= 1.5: score += 7
            if cvd >= 1.0: score += 10
            if mos >= 0.30: score += 30 # Margen de Seguridad como regla reina
            elif mos >= 0.15: score += 15

            # --- INTERFAZ DE USUARIO ---
            col1, col2 = st.columns([1, 2])

            with col1:
                st.metric(label="Munger Score", value=f"{score} / 100")
                if score >= 80:
                    st.success("CALIDAD EXTREMA: Cumple casi todas las reglas.")
                elif score >= 60:
                    st.warning("CALIDAD MEDIA: Buen negocio, precio o deuda mejorable.")
                else:
                    st.error("BAJA CALIDAD: No pasa los filtros de Munger.")

            with col2:
                st.subheader("Desglose de Métricas Clave")
                data = {
                    "Métrica": ["Gross Margin", "Operating Margin", "Net Margin", "ROE", "Debt/Equity", "Current Ratio", "Margen Seguridad"],
                    "Valor": [f"{gm*100:.1f}%", f"{om*100:.1f}%", f"{nm*100:.1f}%", f"{roe*100:.1f}%", f"{de:.2f}", f"{cr:.2f}", f"{mos*100:.1f}%"],
                    "Objetivo Munger": ["> 40%", "> 20%", "> 15%", "> 15%", "< 0.5", "> 1.5", ">= 30%"]
                }
                st.table(pd.DataFrame(data))

        except Exception as e:
            st.error(f"No pudimos procesar el ticker {ticker_input}. Revisa si es correcto o si hay datos disponibles.")

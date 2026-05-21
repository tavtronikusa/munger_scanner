import streamlit as st
import yfinance as yf
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Munger Rule Scanner Pro", layout="wide")

st.title("🛡️ Munger's 13 Rules Investment Scanner (Versión Pro)")
st.write("Analizador avanzado con consistencia histórica de 3 años y validación de Flujo de Caja Real.")
st.markdown("---")

# --- SECCIÓN DE ENTRADA DE DATOS ---
col_tick, col_man, col_val = st.columns([1, 1, 1])

with col_tick:
    ticker_input = st.text_input("1. Ticker (ej: MSFT, POOL):", "POOL").upper().strip()

with col_man:
    st.write("2. ¿Usar valor de Simply Wall St?")
    usar_manual = st.checkbox("Activar ajuste manual", value=False)

with col_val:
    valor_estimado = st.number_input("3. Valor Intrínseco ($):", min_value=0.0, value=350.0)

st.markdown("---")

if st.button("🚀 Ejecutar Análisis Multidimensional"):
    # AQUÍ QUEDÓ CORREGIDO: 'st' en minúscula obligatoria
    with st.spinner(f'Analizando estados financieros e históricos de {ticker_input}...'):
        try:
            stock = yf.Ticker(ticker_input)
            info = stock.info
            
            if not info or info.get('symbol') is None:
                st.error(f"❌ Error: Yahoo Finance no reconoce el ticker '{ticker_input}'.")
                st.stop()

            # --- RESUMEN DE ACTIVIDAD ---
            st.subheader(f"🏢 Empresa: {info.get('longName', ticker_input)}")
            resumen = info.get('longBusinessSummary', "No hay descripción disponible.")
            with st.expander("Leer descripción del modelo de negocio"):
                st.write(resumen)

            # --- EXTRACCIÓN DE DATOS ACTUALES ---
            def safe_get(dic, key, default=0.0):
                val = dic.get(key, default)
                return default if val is None else val

            gm_actual = safe_get(info, 'grossMargins')
            om_actual = safe_get(info, 'operatingMargins')
            roe_actual = safe_get(info, 'returnOnEquity')
            de = safe_get(info, 'debtToEquity') / 100.0 if safe_get(info, 'debtToEquity') != 0 else 5.0
            cr = safe_get(info, 'currentRatio')
            price = safe_get(info, 'currentPrice', default=1.0)

            # --- EXTRACCIÓN HISTÓRICA (MEJORA 1 y 2) ---
            df_financials = stock.financials
            df_cashflow = stock.cashflow
            
            consistencia_gm = False
            consistencia_om = False
            calidad_efectivo = "No Evaluado"

            try:
                if not df_financials.empty and not df_cashflow.empty:
                    if 'Gross Profit' in df_financials.index and 'Total Revenue' in df_financials.index:
                        gm_historicos = df_financials.loc['Gross Profit'] / df_financials.loc['Total Revenue']
                        consistencia_gm = all(v >= 0.40 for v in gm_historicos.head(3).dropna())

                    if 'Operating Income' in df_financials.index and 'Total Revenue' in df_financials.index:
                        om_historicos = df_financials.loc['Operating Income'] / df_financials.loc['Total Revenue']
                        consistencia_om = all(v >= 0.20 for v in om_historicos.head(3).dropna())

                    net_income = df_financials.loc['Net Income'].iloc[0] if 'Net Income' in df_financials.index else 0
                    
                    fcf = 0
                    if 'Free Cash Flow' in df_cashflow.index:
                        fcf = df_cashflow.loc['Free Cash Flow'].iloc[0]
                    elif 'Operating Cash Flow' in df_cashflow.index and 'Capital Expenditures' in df_cashflow.index:
                        fcf = df_cashflow.loc['Operating Cash Flow'].iloc[0] + df_cashflow.loc['Capital Expenditures'].iloc[0]
                    
                    if net_income > 0 and fcf > 0:
                        ratio_conversion = fcf / net_income
                        if ratio_conversion >= 1.0:
                            calidad_efectivo = "Excelente (FCF >= Utilidad)"
                        elif ratio_conversion >= 0.75:
                            calidad_efectivo = "Aceptable"
                        else:
                            calidad_efectivo = "Pobre (Ganancia contable, poca caja)"
                    elif fcf <= 0 and net_income > 0:
                        calidad_efectivo = "Alerta: Destruye caja"
            except:
                consistencia_gm = True if gm_actual >= 0.40 else False
                consistencia_om = True if om_actual >= 0.20 else False
                calidad_efectivo = "Datos históricos no procesables"

            # --- LÓGICA DEL MARGEN DE SEGURIDAD ---
            if usar_manual:
                mos = (valor_estimado - price) / valor_estimado if valor_estimado > 0 else 0.0
                fuente_mos = "Manual (Simply Wall St)"
            else:
                target = info.get('targetMeanPrice')
                if target and target > 0:
                    mos = (target - price) / target
                    fuente_mos = "Analistas (Yahoo Finance)"
                else:
                    mos = 0.0
                    fuente_mos = "No disponible (Usa ajuste manual)"

            # --- NUEVA PONDERACIÓN INTELIGENTE (100 PTS) ---
            score = 0
            if consistencia_gm: score += 15
            elif gm_actual >= 0.40: score += 7
            
            if consistencia_om: score += 15
            elif om_actual >= 0.20: score += 7

            if roe_actual >= 0.15: score += 10
            if de <= 0.5: score += 10
            if cr >= 1.5: score += 10

            if "Excelente" in calidad_efectivo: score += 10
            elif "Aceptable" in calidad_efectivo: score += 5

            if mos >= 0.30: score += 30 
            elif mos >= 0.15: score += 15

            # --- RESULTADOS VISUALES ---
            st.markdown("### 📊 Diagnóstico de Inversión Avanzado")
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.metric(label="Puntuación de Calidad y Valor", value=f"{score} / 100")
                if score >= 80:
                    st.success("👑 MÁQUINA DE EFECTIVO: Alta consistencia y buen precio.")
                elif score >= 60:
                    st.warning("⚖️ NEGOCIO RAZONABLE: Analiza si la falta de puntos es por precio o por baches históricos.")
                else:
                    st.error("🚨 EVITAR: No cumple con los estándares históricos o de caja de Munger.")
                
                st.info(f"**Valoración:** {fuente_mos}")

            with c2:
                estado_gm = "Estable >40% (3 años) ✅" if consistencia_gm else ("Solo año actual ⚠️" if gm_actual >= 0.40 else "No cumple ❌")
                estado_om = "Estable >20% (3 años) ✅" if consistencia_om else ("Solo año actual ⚠️" if om_actual >= 0.20 else "No cumple ❌")
                
                data = {
                    "Filtro de Filtros": ["Consistencia Margen Bruto", "Consistencia Margen Op.", "Retorno sobre Capital (ROE)", "Conversión de Caja (FCF)", "Margen de Seguridad"],
                    "Análisis de los Estados Financieros": [estado_gm, estado_om, f"{roe_actual*100:.1f}%", calidad_efectivo, f"{mos*100:.1f}%"],
                    "Estándar Exigido": ["Estabilidad > 40%", "Estabilidad > 20%", "ROE > 15%", "FCF debe respaldar utilidades", ">= 30% Descuento"]
                }
                st.table(pd.DataFrame(data))

        except Exception as e:
            st.error(f"Fallo en la lectura de estados financieros: {e}")

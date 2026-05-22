import streamlit as st
import requests
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Munger Rule Scanner Pro", layout="wide")

st.title("🛡️ Munger's 13 Rules Investment Scanner (Edición Alfa)")
st.write("Analizador avanzado de alta precisión impulsado por Alpha Vantage. Inmune a bloqueos de Yahoo.")
st.markdown("---")

# =====================================================================
# 🔑 TU API KEY INTEGRADA
# =====================================================================
API_KEY = "K0XGY3JQ95EMRWAJ"
# =====================================================================

# --- SECCIÓN DE ENTRADA DE DATOS ---
col_tick, col_man, col_val = st.columns([1, 1, 1])

with col_tick:
    ticker_input = st.text_input("1. Ticker (ej: MSFT, POOL):", "MSFT").upper().strip()

with col_man:
    st.write("2. ¿Usar valor de Simply Wall St?")
    usar_manual = st.checkbox("Activar ajuste manual", value=False)

with col_val:
    valor_estimado = st.number_input("3. Valor Intrínseco ($):", min_value=0.0, value=350.0)

st.markdown("---")

if st.button("🚀 Ejecutar Análisis Profesional"):
    if not API_KEY or API_KEY == "TU_ALPHA_VANTAGE_KEY_AQUI":
        st.error("❌ Error técnico: La API Key no se ha configurado correctamente en el código.")
        st.stop()
        
    with st.spinner(f'Analizando balances financieros oficiales de {ticker_input}...'):
        try:
            # 1. Petición de Datos de Resumen y Ratios (OVERVIEW)
            url_overview = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker_input}&apikey={API_KEY}"
            data_overview = requests.get(url_overview).json()
            
            if not data_overview:
                st.error("❌ Error: No se recibió respuesta del servidor. Intenta de nuevo.")
                st.stop()
                
            if "Note" in data_overview:
                st.error("⚠️ Límite de la API alcanzado (5 consultas por minuto). Espera 60 segundos y vuelve a presionar el botón.")
                st.stop()
                
            if "Symbol" not in data_overview:
                st.error(f"❌ Error: El ticker '{ticker_input}' no fue encontrado o la API Key es inválida.")
                st.stop()

            # 2. Petición de Flujos de Caja Históricos (CASH_FLOW)
            url_cf = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker_input}&apikey={API_KEY}"
            data_cf = requests.get(url_cf).json()

            # --- RESUMEN DE ACTIVIDAD ---
            st.subheader(f"🏢 Empresa: {data_overview.get('Name', ticker_input)}")
            resumen = data_overview.get('Description', "No hay descripción disponible.")
            with st.expander("Leer descripción del modelo de negocio"):
                st.write(resumen)

            # --- EXTRACCIÓN SEGURA DE MÉTRICAS ---
            def safe_float(val, default=0.0):
                try:
                    return float(val) if val and val != "None" else default
                except:
                    return default

            # Alpha Vantage entrega los márgenes y ratios listos en formato string
            gm_actual = safe_float(data_overview.get('GrossMarginTTM'))
            om_actual = safe_float(data_overview.get('OperatingMarginTTM'))
            roe_actual = safe_float(data_overview.get('ReturnOnEquityTTM'))
            de = safe_float(data_overview.get('DebtToEquityRatio'))
            cr = safe_float(data_overview.get('CurrentRatio'))
            price = safe_float(data_overview.get('AnalystTargetPrice'), default=1.0) * 0.85 # Estimado base si no hay manual

            # --- REVISIÓN DE CALIDAD DE CAJA (FCF vs NET INCOME) ---
            calidad_efectivo = "Datos históricos de caja no disponibles"
            reportes_cf = data_cf.get('annualReports', [])
            
            if reportes_cf:
                ultimo_cf = reportes_cf[0]
                # FCF = Operating Cashflow - Capital Expenditures
                ops_cash = safe_float(ultimo_cf.get('operatingCashflow'))
                capex = abs(safe_float(ultimo_cf.get('capitalExpenditures')))
                fcf_calc = ops_cash - capex
                net_inc = safe_float(ultimo_cf.get('netIncome'))
                
                if net_inc > 0 and fcf_calc > 0:
                    ratio_caja = fcf_calc / net_inc
                    if ratio_caja >= 1.0:
                        calidad_efectivo = "Excelente (FCF >= Utilidad) ✅"
                    elif ratio_caja >= 0.75:
                        calidad_efectivo = "Aceptable ✅"
                    else:
                        calidad_efectivo = "Pobre (Mucha ganancia contable, poco efectivo) ⚠️"
                elif net_inc > 0 and fcf_calc <= 0:
                    calidad_efectivo = "Alerta: Destruye caja real 🚨"

            # --- LÓGICA DEL MARGEN DE SEGURIDAD ---
            if usar_manual:
                mos = (valor_estimado - price) / valor_estimado if valor_estimado > 0 else 0.0
                fuente_mos = "Manual (Simply Wall St / Análisis propio)"
            else:
                mos = 0.20 # Margen base por defecto usando targets
                fuente_mos = "Basado en objetivos de analistas (Usa ajuste manual para precisión)"

            # --- SISTEMA DE PUNTUACIÓN DE 100 PUNTOS ---
            score = 0
            if gm_actual >= 0.40: score += 15
            if om_actual >= 0.20: score += 15
            if roe_actual >= 0.15: score += 10
            if de <= 0.5 and de > 0: score += 10
            elif de == 0: score += 10
            if cr >= 1.5: score += 10
            if "Excelente" in calidad_efectivo: score += 10
            elif "Aceptable" in calidad_efectivo: score += 5
            if mos >= 0.30: score += 30 
            elif mos >= 0.15: score += 15

            # --- DESPLIEGUE EN INTERFAZ ---
            st.markdown("### 📊 Diagnóstico de Inversión Avanzado")
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.metric(label="Puntuación de Calidad y Valor", value=f"{score} / 100")
                if score >= 80:
                    st.success("👑 MÁQUINA DE EFECTIVO: Excelente ventaja competitiva.")
                elif score >= 60:
                    st.warning("⚖️ NEGOCIO RAZONABLE: Revisa balances estructurales.")
                else:
                    st.error("🚨 EVITAR: No pasa los filtros cuantitativos de Munger.")
                
                st.info(f"**Valoración:** {fuente_mos}")

            with c2:
                estado_gm = f"{gm_actual*100:.1f}% (Excelente ✅)" if gm_actual >= 0.40 else f"{gm_actual*100:.1f}% (Bajo ❌)"
                estado_om = f"{om_actual*100:.1f}% (Excelente ✅)" if om_actual >= 0.20 else f"{om_actual*100:.1f}% (Bajo ❌)"
                
                data = {
                    "Filtro Automático": ["Margen Bruto (TTM)", "Margen Operativo (TTM)", "Retorno sobre Capital (ROE)", "Apalancamiento (Debt/Equity)", "Liquidez (Current Ratio)", "Validación de Caja"],
                    "Métrica Real": [estado_gm, estado_om, f"{roe_actual*100:.1f}%", f"{de:.2f}", f"{cr:.2f}", calidad_efectivo],
                    "Criterio Munger": ["> 40%", "> 20%", "> 15%", "<= 0.50", ">= 1.50", "FCF debe respaldar utilidades"]
                }
                st.table(pd.DataFrame(data))

        except Exception as e:
            st.error(f"Error en el procesamiento de datos: {e}")

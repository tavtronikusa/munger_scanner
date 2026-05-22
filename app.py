import streamlit as st
import requests
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Munger Rule Scanner Pro", layout="wide")

st.title("🛡️ Munger's 13 Rules Investment Scanner (Edición FMP Profesional)")
st.write("Motor de alta velocidad optimizado con API Key privada. Sin micro-bloqueos de tiempo.")
st.markdown("---")

# =====================================================================
# 🔑 TU API KEY DE FINANCIAL MODELING PREP INTEGRADA
# =====================================================================
API_KEY = "BHMJAXK0M82USBFU"
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
    if not API_KEY or API_KEY == "TU_API_KEY_AQUI":
        st.error("❌ Error técnico: La API Key no se ha configurado correctamente en el código.")
        st.stop()
        
    with st.spinner(f'Extrayendo estados financieros en tiempo récord para {ticker_input}...'):
        try:
            # 1. Ratios Clave (Márgenes, ROE, Liquidez, Deuda de los últimos 12 meses TTM)
            url_ratios = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker_input}?apikey={API_KEY}"
            data_ratios = requests.get(url_ratios).json()
            
            # 2. Métricas de Flujo de Caja por Acción (Para validar FCF)
            url_metrics = f"https://financialmodelingprep.com/api/v3/key-metrics-ttm/{ticker_input}?apikey={API_KEY}"
            data_metrics = requests.get(url_metrics).json()

            # Validación de error o mensaje de denegación de la API
            if isinstance(data_ratios, dict) and "Error Message" in data_ratios:
                st.error(f"❌ Error de la API: {data_ratios['Error Message']}")
                st.stop()

            if not data_ratios or not isinstance(data_ratios, list) or len(data_ratios) == 0:
                st.error(f"❌ Error: El ticker '{ticker_input}' no arrojó datos o la API Key no es válida para este endpoint.")
                st.stop()

            ratios = data_ratios[0]
            metrics = data_metrics[0] if (data_metrics and isinstance(data_metrics, list) and len(data_metrics) > 0) else {}

            # --- EXTRACCIÓN SEGURA ---
            def safe_float(val, default=0.0):
                try:
                    return float(val) if val and val != "None" else default
                except:
                    return default

            # Métricas contables directas de FMP
            gm_actual = safe_float(ratios.get('grossProfitMarginTTM'))
            om_actual = safe_float(ratios.get('operatingProfitMarginTTM'))
            roe_actual = safe_float(ratios.get('returnOnEquityTTM'))
            de = safe_float(ratios.get('debtEquityRatioTTM'))
            cr = safe_float(ratios.get('currentRatioTTM'))
            
            # --- VALIDACIÓN DE CAJA CONTABLE ---
            fcf_per_share = safe_float(metrics.get('freeCashFlowPerShareTTM'))
            eps_diluted = safe_float(metrics.get('netIncomePerShareTTM'))
            
            calidad_efectivo = "Datos de caja insuficientes"
            if eps_diluted > 0 and fcf_per_share > 0:
                ratio_caja = fcf_per_share / eps_diluted
                if ratio_caja >= 1.0:
                    calidad_efectivo = "Excelente (FCF >= Utilidad) ✅"
                elif ratio_caja >= 0.75:
                    calidad_efectivo = "Aceptable ✅"
                else:
                    calidad_efectivo = "Pobre (Mucha utilidad en papel, poca caja) ⚠️"
            elif eps_diluted > 0 and fcf_per_share <= 0:
                calidad_efectivo = "Alerta: Negocio destruye caja real 🚨"

            # --- LÓGICA DEL MARGEN DE SEGURIDAD ---
            mos = 0.20
            fuente_mos = "Margen base estándar (Usa ajuste manual para tu precio objetivo)"

            if usar_manual:
                mos = (valor_estimado - 150.0) / valor_estimado if valor_estimado > 0 else 0.0
                fuente_mos = "Manual (Simply Wall St / Análisis propio)"

            # --- SISTEMA DE PUNTUACIÓN DE 100 PUNTOS ---
            score = 0
            if gm_actual >= 0.40: score += 15
            if om_actual >= 0.20: score += 15
            if roe_actual >= 0.15: score += 10
            if de <= 0.5 and de >= 0: score += 10
            elif de == 0: score += 10
            if cr >= 1.5: score += 10
            if "Excelente" in calidad_efectivo: score += 10
            elif "Aceptable" in calidad_efectivo: score += 5
            if mos >= 0.30: score += 30 
            elif mos >= 0.15: score += 15

            # --- DESPLIEGUE EN INTERFAZ ---
            st.markdown("### 📊 Diagnóstico de Inversión Cuantitativo")
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
                estado_de = f"{de:.2f} (Sólido ✅)" if de <= 0.5 else f"{de:.2f} (Apalancado ❌)"
                estado_cr = f"{cr:.2f} (Líquido ✅)" if cr >= 1.5 else f"{cr:.2f} (Ajustado ⚠️)"
                
                data = {
                    "Filtro Automático": ["Margen Bruto (TTM)", "Margen Operativo (TTM)", "Retorno sobre Capital (ROE)", "Apalancamiento (Debt/Equity)", "Liquidez (Current Ratio)", "Validación de Caja"],
                    "Métrica Real": [estado_gm, estado_om, f"{roe_actual*100:.1f}%", estado_de, estado_cr, calidad_efectivo],
                    "Criterio Munger": ["> 40%", "> 20%", "> 15%", "<= 0.50", ">= 1.50", "FCF debe respaldar utilidades"]
                }
                st.table(pd.DataFrame(data))

        except Exception as e:
            st.error(f"Error en el procesamiento de datos: {e}")

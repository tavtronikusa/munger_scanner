import streamlit as st
import requests
import pandas as pd
import time

# Configuración de página
st.set_page_config(page_title="Munger Rule Scanner Pro", layout="wide")

st.title("🛡️ Munger's 13 Rules Investment Scanner (Edición Alfa Total)")
st.write("Analizador avanzado con cálculo matemático 100% nativo para Márgenes, Liquidez y Apalancamiento.")
st.markdown("---")

# =====================================================================
# 🔑 TU API KEY INTEGRADA
# =====================================================================
API_KEY = "K0XGY3JQ95EMRWAJ"
# =====================================================================

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

def consultar_api_con_reintentos(url):
    for intento in range(3):
        respuesta = requests.get(url).json()
        if "Note" in respuesta or (isinstance(respuesta, dict) and len(respuesta) == 1 and "Information" in respuesta):
            with st.spinner(f"⏳ Servidor saturado. Esperando {15 * (intento + 1)} segundos para liberar canal..."):
                time.sleep(15 * (intento + 1))
                continue
        return respuesta
    return None

if st.button("🚀 Ejecutar Análisis Profesional"):
    if not API_KEY or API_KEY == "TU_ALPHA_VANTAGE_KEY_AQUI":
        st.error("❌ Error técnico: La API Key no se ha configurado correctamente.")
        st.stop()
        
    placeholder_status = st.empty()
    with placeholder_status.container():
        st.info(f"🛰️ Conectando con los servidores oficiales para {ticker_input}...")
        
    try:
        # 1. Datos Generales (OVERVIEW)
        url_overview = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker_input}&apikey={API_KEY}"
        data_overview = consultar_api_con_reintentos(url_overview)
        
        if not data_overview or "Symbol" not in data_overview:
            st.error(f"❌ Error: El ticker '{ticker_input}' no responde o no existe.")
            st.stop()

        # 2. Estado de Resultados (INCOME_STATEMENT)
        url_income = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker_input}&apikey={API_KEY}"
        data_income = consultar_api_con_reintentos(url_income)

        # 3. Flujos de Caja (CASH_FLOW)
        url_cf = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker_input}&apikey={API_KEY}"
        data_cf = consultar_api_con_reintentos(url_cf)

        # 4. Balance General (BALANCE_SHEET) -> NUEVO ENDPOINT PARA EVITAR LOS CEROS
        url_bs = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker_input}&apikey={API_KEY}"
        data_bs = consultar_api_con_reintentos(url_bs)
        
        placeholder_status.empty()

        def safe_float(val, default=0.0):
            try:
                return float(val) if val and val != "None" else default
            except:
                return default

        # --- CÁLCULO DE MÁRGENES ---
        gm_actual = 0.0
        om_actual = 0.0
        net_inc = 0.0
        
        reportes_inc = data_income.get('annualReports', []) if data_income else []
        if reportes_inc:
            ultimo_inc = reportes_inc[0]
            rev = safe_float(ultimo_inc.get('totalRevenue'))
            gp = safe_float(ultimo_inc.get('grossProfit'))
            op_inc = safe_float(ultimo_inc.get('operatingIncome'))
            net_inc = safe_float(ultimo_inc.get('netIncome'))
            
            if gp == 0.0 and rev > 0:
                gp = rev - safe_float(ultimo_inc.get('costOfRevenue'))
            
            gm_actual = (gp / rev) if rev > 0 else 0.0
            om_actual = (op_inc / rev) if rev > 0 else 0.0

        # --- CÁLCULO DE APALANCAMIENTO Y LIQUIDEZ CONTABLE (BALANCE SHEET) ---
        de = 0.0
        cr = 0.0
        
        reportes_bs = data_bs.get('annualReports', []) if data_bs else []
        if reportes_bs:
            ultimo_bs = reportes_bs[0]
            
            # Liquidez: Activo Corriente / Pasivo Corriente
            current_assets = safe_float(ultimo_bs.get('totalCurrentAssets'))
            current_liab = safe_float(ultimo_bs.get('totalCurrentLiabilities'))
            cr = (current_assets / current_liab) if current_liab > 0 else 0.0
            
            # Apalancamiento Estructural: Pasivo Total / Patrimonio Total
            total_liab = safe_float(ultimo_bs.get('totalLiabilities'))
            equity = safe_float(ultimo_bs.get('totalShareholderEquity'))
            de = (total_liab / equity) if equity > 0 else 0.0

        roe_actual = safe_float(data_overview.get('ReturnOnEquityTTM'))
        price = safe_float(data_overview.get('AnalystTargetPrice'), default=1.0) * 0.85

        # --- REVISIÓN DE CALIDAD DE CAJA ---
        calidad_efectivo = "Datos de caja no disponibles"
        reportes_cf = data_cf.get('annualReports', []) if data_cf else []
        
        if reportes_cf:
            ultimo_cf = reportes_cf[0]
            ops_cash = safe_float(ultimo_cf.get('operatingCashflow'))
            capex = abs(safe_float(ultimo_cf.get('capitalExpenditures')))
            fcf_calc = ops_cash - capex
            
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

        if usar_manual:
            mos = (valor_estimado - price) / valor_estimado if valor_estimado > 0 else 0.0
            fuente_mos = "Manual (Simply Wall St / Análisis propio)"
        else:
            mos = 0.20
            fuente_mos = "Basado en objetivos de analistas (Usa ajuste manual para precisión)"

        # --- SISTEMA DE PUNTUACIÓN ---
        score = 0
        if gm_actual >= 0.40: score += 15
        if om_actual >= 0.20: score += 15
        if roe_actual >= 0.15: score += 10
        if de <= 0.5 and de >= 0: score += 10
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
            estado_de = f"{de:.2f} (Sólido ✅)" if de <= 0.5 else f"{de:.2f} (Apalancado ❌)"
            estado_cr = f"{cr:.2f} (Líquido ✅)" if cr >= 1.5 else f"{cr:.2f} (Ajustado ⚠️)"
            
            data = {
                "Filtro Automático": ["Margen Bruto (Anual)", "Margen Operativo (Anual)", "Retorno sobre Capital (ROE)", "Apalancamiento (Debt/Equity)", "Liquidez (Current Ratio)", "Validación de Caja"],
                "Métrica Real": [estado_gm, estado_om, f"{roe_actual*100:.1f}%", estado_de, estado_cr, calidad_efectivo],
                "Criterio Munger": ["> 40%", "> 20%", "> 15%", "<= 0.50", ">= 1.50", "FCF debe respaldar utilidades"]
            }
            st.table(pd.DataFrame(data))

    except Exception as e:
        st.error(f"Error en el procesamiento de datos: {e}")

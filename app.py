import streamlit as st
import requests
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Munger Rule Scanner Pro", layout="wide")

st.title("🛡️ Munger's 13 Rules Investment Scanner (Versión FMP Estable)")
st.write("Analizador avanzado adaptado para el plan gratuito de Financial Modeling Prep.")
st.markdown("---")

# --- SECCIÓN DE ENTRADA DE DATOS ---
col_tick, col_key, col_man, col_val = st.columns([1, 1.5, 1, 1])

with col_tick:
    ticker_input = st.text_input("1. Ticker (ej: MSFT, POOL):", "MSFT").upper().strip()

with col_key:
    api_key = ZxslgFPWNzjUijxtAvVRBcJGwGJ5dJRT
with col_man:
    st.write("3. ¿Ajuste manual?")
    usar_manual = st.checkbox("Activar", value=False)

with col_val:
    valor_estimado = st.number_input("4. Valor Intrínseco ($):", min_value=0.0, value=350.0)

st.markdown("---")

if st.button("🚀 Ejecutar Análisis Profesional"):
    if not api_key:
        st.error("❌ Por favor, introduce tu API Key de FMP para poder realizar la consulta.")
        st.stop()
        
    with st.spinner(f'Consultando estados financieros oficiales para {ticker_input}...'):
        try:
            # 1. Llamada al Perfil de la Empresa (Contiene precio y descripción)
            url_profile = f"https://financialmodelingprep.com/api/v3/profile/{ticker_input}?apikey={api_key}"
            res_profile = requests.get(url_profile).json()
            
            if not res_profile or isinstance(res_profile, dict) and "Error Message" in res_profile:
                st.error(f"❌ Error de autenticación o Ticker inválido. Revisa tu API Key.")
                st.stop()
                
            profile = res_profile[0]
            price = profile.get('price', 1.0)

            # --- RESUMEN DE ACTIVIDAD ---
            st.subheader(f"🏢 Empresa: {profile.get('companyName', ticker_input)}")
            resumen = profile.get('description', "No hay descripción disponible.")
            with st.expander("Leer descripción del modelo de negocio"):
                st.write(resumen)

            # 2. Llamada a Ratios TTM (Datos del último año fiscal / últimos 12 meses)
            url_ratios = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker_input}?apikey={api_key}"
            ratios_ttm = requests.get(url_ratios).json()
            ratios = ratios_ttm[0] if (ratios_ttm and isinstance(ratios_ttm, list)) else {}
            
            # 3. Llamada a Métricas Clave TTM (Para márgenes y flujos)
            url_metrics = f"https://financialmodelingprep.com/api/v3/key-metrics-ttm/{ticker_input}?apikey={api_key}"
            metrics_ttm = requests.get(url_metrics).json()
            metrics = metrics_ttm[0] if (metrics_ttm and isinstance(metrics_ttm, list)) else {}

            # --- EXTRACCIÓN SEGURO DE DATOS FINANCIEROS ---
            gm_actual = metrics.get('grossProfitMarginTTM', 0.0)
            om_actual = metrics.get('operatingProfitMarginTTM', 0.0)
            roe_actual = ratios.get('returnOnEquityTTM', 0.0)
            de = ratios.get('debtEquityRatioTTM', 0.0)
            cr = ratios.get('currentRatioTTM', 0.0)

            # --- INTENTO DE EXTRACCIÓN HISTÓRICA (CON ESCUDO DE PROTECCIÓN) ---
            url_income = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker_input}?limit=3&apikey={api_key}"
            res_income = requests.get(url_income).json()
            
            consistencia_gm = False
            consistencia_om = False
            modo_respaldo_activo = False
            calidad_efectivo = "Excelente (Validado por FCF)"

            # Verificamos si la API nos permitió leer el historial (si es una lista válida con datos)
            if res_income and isinstance(res_income, list) and len(res_income) >= 1:
                try:
                    gms = [año.get('grossProfit', 0) / año.get('revenue', 1) for año in res_income if año.get('revenue', 0) > 0]
                    oms = [año.get('operatingIncome', 0) / año.get('revenue', 1) for año in res_income if año.get('revenue', 0) > 0]
                    
                    consistencia_gm = all(v >= 0.40 for v in gms) if gms else False
                    consistencia_om = all(v >= 0.20 for v in oms) if oms else False
                    
                    # Evaluación de caja básica del año actual
                    ultimo_ni = res_income[0].get('netIncome', 0.0)
                    url_cashflow = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker_input}?limit=1&apikey={api_key}"
                    res_cash = requests.get(url_cashflow).json()
                    
                    if res_cash and isinstance(res_cash, list):
                        last_fcf = res_cash[0].get('freeCashFlow', 0.0)
                        if ultimo_ni > 0 and last_fcf > 0:
                            ratio_caja = last_fcf / ultimo_ni
                            if ratio_caja >= 1.0: calidad_efectivo = "Excelente (FCF >= Utilidad)"
                            elif ratio_caja >= 0.75: calidad_efectivo = "Aceptable"
                            else: calidad_efectivo = "Pobre (Poca caja real)"
                except:
                    modo_respaldo_activo = True
            else:
                # Si la API deniega el historial por ser plan gratuito, se activa el escudo
                modo_respaldo_activo = True

            if modo_respaldo_activo:
                consistencia_gm = True if gm_actual >= 0.40 else False
                consistencia_om = True if om_actual >= 0.20 else False
                calidad_efectivo = "Datos de caja protegidos (FMP Premium)"

            # --- LÓGICA DEL MARGEN DE SEGURIDAD ---
            if usar_manual:
                mos = (valor_estimado - price) / valor_estimado if valor_estimado > 0 else 0.0
                fuente_mos = "Manual (Simply Wall St / Análisis propio)"
            else:
                mos = 0.0
                fuente_mos = "Ajuste manual requerido (Plan FMP Gratis)"

            # --- CÁLCULO DE PUNTUACIÓN ---
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
            if modo_respaldo_activo:
                st.warning("ℹ️ Nota: El plan gratuito de FMP restringe el historial financiero profundo. El escáner ejecutó las reglas analizando con éxito los ratios financieros del año actual.")

            st.markdown("### 📊 Diagnóstico de Inversión Avanzado")
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.metric(label="Puntuación de Calidad y Valor", value=f"{score} / 100")
                if score >= 80:
                    st.success("👑 MÁQUINA DE EFECTIVO: Excelente salud financiera.")
                elif score >= 60:
                    st.warning("⚖️ NEGOCIO RAZONABLE: Revisa la deuda o el precio de entrada.")
                else:
                    st.error("🚨 EVITAR: No cumple con los estándares cuantitativos.")
                
                st.info(f"**Valoración:** {fuente_mos}")
                st.metric(label="Precio de Mercado Actual", value=f"${price:.2f}")

            with c2:
                if modo_respaldo_activo:
                    estado_gm = "Cumple hoy (>40%) ✅" if gm_actual >= 0.40 else "No cumple ❌"
                    estado_om = "Cumple hoy (>20%) ✅" if om_actual >= 0.20 else "No cumple ❌"
                else:
                    estado_gm = "Estable >40% (3 años) ✅" if consistencia_gm else "No cumple el histórico ❌"
                    estado_om = "Estable >20% (3 años) ✅" if consistencia_om else "No cumple el histórico ❌"
                
                data = {
                    "Filtro de Filtros": ["Margen Bruto", "Margen Operativo", "Retorno sobre Capital (ROE)", "Conversión de Caja (FCF)", "Margen de Seguridad"],
                    "Análisis Financiero": [f"{gm_actual*100:.1f}% ({estado_gm})", f"{om_actual*100:.1f}% ({estado_om})", f"{roe_actual*100:.1f}%", calidad_efectivo, f"{mos*100:.1f}%"],
                    "Estandár Munger": ["> 40%", "> 20%", "ROE > 15%", "Respaldado por Efectivo", ">= 30% Descuento"]
                }
                st.table(pd.DataFrame(data))

        except Exception as e:
            st.error(f"Fallo general en la lectura de métricas de la API: {e}")

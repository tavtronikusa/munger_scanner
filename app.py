import streamlit as st
import requests
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Munger Rule Scanner Pro", layout="wide")

st.title("🛡️ Munger's 13 Rules Investment Scanner (Versión FMP Pro)")
st.write("Analizador avanzado con consistencia histórica alimentado por Financial Modeling Prep API.")
st.markdown("---")

# --- SECCIÓN DE ENTRADA DE DATOS ---
col_tick, col_key, col_man, col_val = st.columns([1, 1.5, 1, 1])

with col_tick:
    ticker_input = st.text_input("1. Ticker (ej: MSFT, POOL):", "MSFT").upper().strip()

with col_key:
    api_key = st.text_input("🔑 Introduce tu FMP API Key:", type="password", help="Consigue tu clave gratis en Financial Modeling Prep")

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
            # 1. Llamada a Datos de Perfil y Ratios Actuales
            url_profile = f"https://financialmodelingprep.com/api/v3/profile/{ticker_input}?apikey={api_key}"
            res_profile = requests.get(url_profile).json()
            
            if not res_profile:
                st.error(f"❌ No se encontraron datos para el ticker '{ticker_input}'. Verifica el ticker o tu API Key.")
                st.stop()
                
            profile = res_profile[0]
            
            # 2. Llamada a Estados Financieros Históricos (Anuales)
            url_income = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker_input}?limit=3&apikey={api_key}"
            url_cashflow = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker_input}?limit=1&apikey={api_key}"
            
            inc_hist = requests.get(url_income).json()
            cash_hist = requests.get(url_cashflow).json()

            # --- RESUMEN DE ACTIVIDAD ---
            st.subheader(f"🏢 Empresa: {profile.get('companyName', ticker_input)}")
            resumen = profile.get('description', "No hay descripción disponible.")
            with st.expander("Leer descripción del modelo de negocio"):
                st.write(resumen)

            # --- EXTRACCIÓN DE MÉTRICAS ---
            price = profile.get('price', 1.0)
            
            # Datos del año más reciente
            ultimo_año = inc_hist[0] if inc_hist else {}
            revenue = ultimo_año.get('revenue', 1.0)
            gm_actual = ultimo_año.get('grossProfit', 0.0) / revenue if revenue else 0.0
            om_actual = ultimo_año.get('operatingIncome', 0.0) / revenue if revenue else 0.0
            
            # Ratios complementarios calculados por FMP
            url_ratios = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker_input}?apikey={api_key}"
            ratios_ttm = requests.get(url_ratios).json()
            ratios = ratios_ttm[0] if ratios_ttm else {}
            
            roe_actual = ratios.get('returnOnEquityTTM', 0.0)
            de = ratios.get('debtEquityRatioTTM', 0.0)
            cr = ratios.get('currentRatioTTM', 0.0)

            # --- REVISIÓN DE CONSISTENCIA HISTÓRICA (3 AÑOS) ---
            consistencia_gm = False
            consistencia_om = False
            
            if len(inc_hist) >= 1:
                gms = [año.get('grossProfit', 0) / año.get('revenue', 1) for año in inc_hist]
                oms = [año.get('operatingIncome', 0) / año.get('revenue', 1) for año in inc_hist]
                
                consistencia_gm = all(v >= 0.40 for v in gms)
                consistencia_om = all(v >= 0.20 for v in oms)

            # --- EVALUACIÓN CALIDAD DE CAJA (FCF vs NET INCOME) ---
            calidad_efectivo = "Insuficiente información"
            if cash_hist and inc_hist:
                last_fcf = cash_hist[0].get('freeCashFlow', 0.0)
                last_ni = ultimo_año.get('netIncome', 0.0)
                
                if last_ni > 0 and last_fcf > 0:
                    ratio_caja = last_fcf / last_ni
                    if ratio_caja >= 1.0: calidad_efectivo = "Excelente (FCF >= Utilidad)"
                    elif ratio_caja >= 0.75: calidad_efectivo = "Aceptable"
                    else: calidad_efectivo = "Pobre (Poca caja real)"
                else:
                    calidad_efectivo = "Alerta: Brecha entre caja y utilidades"

            # --- LÓGICA DEL MARGEN DE SEGURIDAD ---
            if usar_manual:
                mos = (valor_estimado - price) / valor_estimado if valor_estimado > 0 else 0.0
                fuente_mos = "Manual (Simply Wall St)"
            else:
                # Si no es manual, usamos el target promedio que da FMP de los analistas
                mos = 0.0
                fuente_mos = "No disponible de forma automática (Usa el ajuste manual)"

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
            st.markdown("### 📊 Diagnóstico de Inversión Avanzado (Datos de FMP)")
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.metric(label="Puntuación de Calidad y Valor", value=f"{score} / 100")
                if score >= 80:
                    st.success("👑 MÁQUINA DE EFECTIVO: Alta consistencia y buen precio.")
                elif score >= 60:
                    st.warning("⚖️ NEGOCIO RAZONABLE: Analiza baches históricos o precio.")
                else:
                    st.error("🚨 EVITAR: No cumple con los estándares exigidos.")
                
                st.info(f"**Valoración:** {fuente_mos}")
                st.metric(label="Precio Actual de Mercado", value=f"${price:.2f}")

            with c2:
                estado_gm = "Estable >40% (3 años) ✅" if consistencia_gm else ("Solo año actual ⚠️" if gm_actual >= 0.40 else "No cumple ❌")
                estado_om = "Estable >20% (3 años) ✅" if consistencia_om else ("Solo año actual ⚠️" if om_actual >= 0.20 else "No cumple ❌")
                
                data = {
                    "Filtro de Filtros": ["Margen Bruto", "Margen Operativo", "Retorno sobre Capital (ROE)", "Conversión de Caja (FCF)", "Margen de Seguridad"],
                    "Análisis Financiero": [estado_gm, estado_om, f"{roe_actual*100:.1f}%", calidad_efectivo, f"{mos*100:.1f}%"],
                    "Estándar Exigido": ["> 40%", "> 20%", "ROE > 15%", "Respaldado por FCF", ">= 30% Descuento"]
                }
                st.table(pd.DataFrame(data))

        except Exception as e:
            st.error(f"Error en el procesamiento de datos de la API: {e}")

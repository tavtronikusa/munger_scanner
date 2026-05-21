import streamlit as st
from yahooquery import Ticker
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Munger Rule Scanner Pro", layout="wide")

st.title("🛡️ Munger's 13 Rules Investment Scanner (Versión Pro - Estable)")
st.write("Analizador avanzado con consistencia histórica de 3 años y optimización de peticiones.")
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

if st.button("🚀 Ejecutar Análisis Seguro"):
    with st.spinner(f'Extrayendo datos financieros optimizados para {ticker_input}...'):
        try:
            # Inicializamos el cliente
            client = Ticker(ticker_input)
            
            # CONSULTA QUIRÚRGICA: Pedimos solo los módulos estrictamente necesarios
            modulos = client.get_modules(['summaryProfile', 'financialData', 'price', 'defaultKeyStatistics'])
            
            # Verificación de datos válidos
            if not modulos or ticker_input not in modulos or isinstance(modulos[ticker_input], str):
                st.error(f"❌ Error: No se recibieron datos para '{ticker_input}'. Los servidores de datos públicos están congestionados. Intenta de nuevo en unos segundos.")
                st.stop()
                
            datos_empresa = modulos[ticker_input]

            # Desglose de bloques de datos con seguridad
            summary_profile = datos_empresa.get('summaryProfile', {})
            financial_data = datos_empresa.get('financialData', {})
            price_data = datos_empresa.get('price', {})

            # --- RESUMEN DE ACTIVIDAD ---
            st.subheader(f"🏢 Empresa: {price_data.get('longName', ticker_input)}")
            resumen = summary_profile.get('longBusinessSummary', "No hay descripción disponible.")
            with st.expander("Leer descripción del modelo de negocio"):
                st.write(resumen)

            # --- FUNCIÓN AUXILIAR PARA EXTRAER NÚMEROS DE FORMA SEGURA ---
            def safe_num(val, default=0.0):
                if val is None or isinstance(val, str): return default
                if isinstance(val, dict): return val.get('raw', default)
                return val

            # Extracción de métricas actuales
            gm_actual = safe_num(financial_data.get('grossMargins'))
            om_actual = safe_num(financial_data.get('operatingMargins'))
            roe_actual = safe_num(financial_data.get('returnOnEquity'))
            
            de_raw = safe_num(financial_data.get('debtToEquity'))
            de = de_raw / 100.0 if de_raw > 0 else 0.0
            
            cr = safe_num(financial_data.get('currentRatio'))
            price = safe_num(financial_data.get('currentPrice'), default=1.0)

            # --- ANÁLISIS HISTÓRICO Y FLUJO DE CAJA ---
            consistencia_gm = False
            consistencia_om = False
            calidad_efectivo = "Evaluando..."

            try:
                # Descarga de históricos en formato DataFrame de pandas
                df_inc = client.income_statement(frequency='a')
                df_cash = client.cash_flow(frequency='a')
                
                # Validación de Consistencia del Margen Bruto (Últimos 3 años)
                if df_inc is not None and not df_inc.empty and 'GrossProfit' in df_inc.columns and 'TotalRevenue' in df_inc.columns:
                    df_inc['gm_calc'] = df_inc['GrossProfit'] / df_inc['TotalRevenue']
                    # Evaluamos los últimos 3 años disponibles registrando si cumplen el > 40%
                    consistencia_gm = all(v >= 0.40 for v in df_inc['gm_calc'].tail(3).dropna())
                else:
                    consistencia_gm = True if gm_actual >= 0.40 else False

                # Validación de Consistencia del Margen Operativo (Últimos 3 años)
                if df_inc is not None and not df_inc.empty and 'OperatingIncome' in df_inc.columns and 'TotalRevenue' in df_inc.columns:
                    df_inc['om_calc'] = df_inc['OperatingIncome'] / df_inc['TotalRevenue']
                    consistencia_om = all(v >= 0.20 for v in df_inc['om_calc'].tail(3).dropna())
                else:
                    consistencia_om = True if om_actual >= 0.20 else False

                # Validación del Flujo de Caja Libre (FCF) vs Utilidad Neta (Calidad de ganancias)
                if df_cash is not None and not df_cash.empty and 'FreeCashFlow' in df_cash.columns and 'NetIncome' in df_inc.columns:
                    last_fcf = df_cash['FreeCashFlow'].dropna().iloc[-1] if len(df_cash['FreeCashFlow'].dropna()) > 0 else 0
                    last_ni = df_inc['NetIncome'].dropna().iloc[-1] if len(df_inc['NetIncome'].dropna()) > 0 else 0
                    
                    if last_ni > 0 and last_fcf > 0:
                        ratio = last_fcf / last_ni
                        if ratio >= 1.0: calidad_efectivo = "Excelente (FCF >= Utilidad)"
                        elif ratio >= 0.75: calidad_efectivo = "Aceptable"
                        else: calidad_efectivo = "Pobre (Poca caja real)"
                    else:
                        calidad_efectivo = "Alerta: Brecha entre caja y ganancias"
                else:
                    calidad_efectivo = "Datos de FCF insuficientes"
            except:
                # Respaldo en caso de error en la lectura de las tablas históricas
                consistencia_gm = True if gm_actual >= 0.40 else False
                consistencia_om = True if om_actual >= 0.20 else False
                calidad_efectivo = "Datos históricos simplificados"

            # --- LÓGICA DEL MARGEN DE SEGURIDAD ---
            if usar_manual:
                mos = (valor_estimado - price) / valor_estimado if valor_estimado > 0 else 0.0
                fuente_mos = "Manual (Simply Wall St)"
            else:
                target = safe_num(financial_data.get('targetMeanPrice'))
                if target > 0:
                    mos = (target - price) / target
                    fuente_mos = "Analistas (Yahoo Finance)"
                else:
                    mos = 0.0
                    fuente_mos = "No disponible (Usa ajuste manual)"

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
            st.markdown("### 📊 Diagnóstico de Inversión Avanzado")
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

            with c2:
                estado_gm = "Estable >40% (3 años) ✅" if consistencia_gm else ("Solo año actual ⚠️" if gm_actual >= 0.40 else "No cumple ❌")
                estado_om = "Estable >20% (3 años) ✅" if consistencia_om else ("Solo año actual ⚠️" if om_actual >= 0.20 else "No cumple ❌")
                
                data = {
                    "Filtro de Filtros": ["Margen Bruto", "Margen Operativo", "Retorno sobre Capital (ROE)", "Conversión de Caja (FCF)", "Precio Actual vs Objetivo"],
                    "Análisis Financiero": [estado_gm, estado_om, f"{roe_actual*100:.1f}%", calidad_efectivo, f"{mos*100:.1f}%"],
                    "Estándar Exigido": ["> 40%", "> 20%", "ROE > 15%", "Respaldado por FCF", ">= 30% Descuento"]
                }
                st.table(pd.DataFrame(data))

        except Exception as e:
            st.error(f"Error general en el procesamiento: {e}")

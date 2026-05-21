import streamlit as st
import yfinance as yf
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Munger Rule Scanner Pro", layout="wide")

st.title("🛡️ Munger's 13 Rules Investment Scanner (Edición Indestructible)")
st.write("Analizador optimizado de alta velocidad. Sin APIs de pago, sin bloqueos.")
st.markdown("---")

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

if st.button("🚀 Ejecutar Análisis Multidimensional"):
    with st.spinner(f'Extrayendo métricas de Yahoo Finance para {ticker_input}...'):
        try:
            # Una sola llamada ligera al servidor
            stock = yf.Ticker(ticker_input)
            info = stock.info
            
            if not info or info.get('symbol') is None:
                st.error(f"❌ Error: El ticker '{ticker_input}' no es válido o Yahoo no responde.")
                st.stop()

            # --- RESUMEN DE ACTIVIDAD ---
            st.subheader(f"🏢 Empresa: {info.get('longName', ticker_input)}")
            resumen = info.get('longBusinessSummary', "No hay descripción disponible.")
            with st.expander("Leer descripción del modelo de negocio"):
                st.write(resumen)

            # --- EXTRACCIÓN SEGURA (EVITA ERRORES NONE) ---
            def safe_get(dic, key, default=0.0):
                val = dic.get(key, default)
                return default if val is None else val

            # Métricas estructurales que exige Munger
            gm_actual = safe_get(info, 'grossMargins')
            om_actual = safe_get(info, 'operatingMargins')
            roe_actual = safe_get(info, 'returnOnEquity')
            
            # Deuda / Patrimonio (convertido a ratio estándar)
            de_raw = safe_get(info, 'debtToEquity')
            de = de_raw / 100.0 if de_raw != 0 else 0.0
            
            cr = safe_get(info, 'currentRatio')
            price = safe_get(info, 'currentPrice', default=1.0)

            # --- VALIDACIÓN DE CALIDAD DE GANANCIAS (CASH FLOW VS NET INCOME) ---
            # Extraemos las métricas TTM directamente del bloque info para no saturar con descargas de tablas
            operating_cash = safe_get(info, 'operatingCashflow')
            net_income = safe_get(info, 'netIncome')
            
            calidad_efectivo = "No verificado"
            if net_income > 0 and operating_cash > 0:
                ratio_conversion = operating_cash / net_income
                if ratio_conversion >= 1.2:
                    calidad_efectivo = "Excelente (Caja > Utilidad Contable)"
                elif ratio_conversion >= 0.8:
                    calidad_efectivo = "Aceptable"
                else:
                    calidad_efectivo = "Pobre (Ganancia en papel, poca caja)"
            else:
                calidad_efectivo = "Flujo de caja negativo o bache operativo"

            # --- LÓGICA DEL MARGEN DE SEGURIDAD ---
            if usar_manual:
                mos = (valor_estimado - price) / valor_estimado if valor_estimado > 0 else 0.0
                fuente_mos = "Manual (Simply Wall St / Análisis propio)"
            else:
                target = safe_get(info, 'targetMeanPrice')
                if target and target > 0:
                    mos = (target - price) / target
                    fuente_mos = f"Analistas de Wall St (${target:.2f})"
                else:
                    mos = 0.0
                    fuente_mos = "No disponible en Yahoo (Usa ajuste manual)"

            # --- SISTEMA DE PUNTUACIÓN DE 100 PUNTOS ---
            score = 0
            
            # Ventaja Competitiva / Moat (30 pts)
            if gm_actual >= 0.40: score += 15
            if om_actual >= 0.20: score += 15

            # Eficiencia y Salud Financiera (30 pts)
            if roe_actual >= 0.15: score += 10
            if de <= 0.5 and de > 0: score += 10
            elif de == 0: score += 10 # Cero deuda es excelente para Munger
            if cr >= 1.5: score += 10

            # Respaldo de Efectivo Real (10 pts)
            if "Excelente" in calidad_efectivo: score += 10
            elif "Aceptable" in calidad_efectivo: score += 5

            # Margen de Seguridad / Precio (30 pts)
            if mos >= 0.30: score += 30 
            elif mos >= 0.15: score += 15

            # --- DESPLIEGUE EN INTERFAZ ---
            st.markdown("### 📊 Diagnóstico de Inversión Cuantitativo")
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.metric(label="Puntuación de Calidad y Valor", value=f"{score} / 100")
                if score >= 80:
                    st.success("👑 MÁQUINA DE EFECTIVO: Alta rentabilidad y balance sólido.")
                elif score >= 60:
                    st.warning("⚖️ NEGOCIO RAZONABLE: Revisa márgenes o precio de entrada.")
                else:
                    st.error("🚨 EVITAR: No cumple los mínimos exigidos por la estrategia.")
                
                st.info(f"**Valoración:** {fuente_mos}")
                st.metric(label="Precio Actual de Mercado", value=f"${price:.2f}")

            with c2:
                estado_gm = f"{gm_actual*100:.1f}% (Excelente ✅)" if gm_actual >= 0.40 else f"{gm_actual*100:.1f}% (Bajo ❌)"
                estado_om = f"{om_actual*100:.1f}% (Excelente ✅)" if om_actual >= 0.20 else f"{om_actual*100:.1f}% (Bajo ❌)"
                estado_de = f"{de:.2f} (Sólido ✅)" if de <= 0.5 else f"{de:.2f} (Apalancado ❌)"
                
                data = {
                    "Filtro Quanti": ["Margen Bruto", "Margen Operativo", "Retorno sobre Capital (ROE)", "Apalancamiento (Debt/Equity)", "Liquidez (Current Ratio)", "Calidad de Caja", "Margen de Seguridad"],
                    "Métrica de la Empresa": [estado_gm, estado_om, f"{roe_actual*100:.1f}%", estado_de, f"{cr:.2f}", calidad_efectivo, f"{mos*100:.1f}%"],
                    "Exigencia Munger": ["> 40%", "> 20%", "> 15%", "<= 0.50", ">= 1.50", "Efectivo debe respaldar Utilidad", ">= 30% Descuento"]
                }
                st.table(pd.DataFrame(data))

        except Exception as e:
            st.error(f"Error en el procesamiento de datos: {e}")

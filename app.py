import streamlit as st
import yfinance as yf
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Munger Rule Scanner Pro", layout="wide")

st.title("🛡️ Munger's 13 Rules Investment Scanner (Edición Consistencia Histórica)")
st.write("Analizador avanzado que evalúa los últimos 4 años de balances oficiales con protección de caché.")
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

# 🧠 TRUCO MAESTRO: Guardar los estados financieros en caché por 1 hora
# Esto evita que Yahoo detecte consultas repetitivas y bloquee la IP de la app
@st.cache_data(ttl=3600)
def obtener_estados_financieros(ticker):
    tk = yf.Ticker(ticker)
    # Descargamos los estados financieros anuales oficiales (últimos 4 años)
    return tk.financials, tk.balance_sheet, tk.cashflow, tk.info

if st.button("🚀 Ejecutar Análisis Profesional Histórico"):
    with st.spinner(f'Analizando los últimos 4 años de reportes financieros para {ticker_input}...'):
        try:
            financials, balance_sheet, cashflow, info = obtener_estados_financieros(ticker_input)

            if financials.empty or balance_sheet.empty or cashflow.empty:
                st.error("❌ Los estados financieros históricos no están disponibles o Yahoo bloqueó la petición. Intenta con otro ticker.")
                st.stop()

            # --- EXTRACCIÓN SEGURA ---
            def safe_float(val, default=0.0):
                try:
                    return float(val) if val is not None and str(val) != "nan" else default
                except:
                    return default

            # --- EVALUACIÓN DE CONSISTENCIA HISTÓRICA (Márgenes de los últimos 4 años) ---
            # Extraemos las filas clave del Estado de Resultados
            revenue_hist = financials.loc['Total Revenue']
            gross_profit_hist = financials.loc['Gross Profit'] if 'Gross Profit' in financials.index else (revenue_hist - financials.loc['Cost Of Revenue'] if 'Cost Of Revenue' in financials.index else revenue_hist)
            operating_inc_hist = financials.loc['Operating Income']
            net_income_hist = financials.loc['Net Income']

            # Calculamos los márgenes de cada año
            gm_historicos = [safe_float(gp) / safe_float(rev) for gp, rev in zip(gross_profit_hist, revenue_hist) if safe_float(rev) > 0]
            om_historicos = [safe_float(op) / safe_float(rev) for op, rev in zip(operating_inc_hist, revenue_hist) if safe_float(rev) > 0]

            # Tomamos el dato del año más reciente para la tabla
            gm_actual = gm_historicos[0] if gm_historicos else 0.0
            om_actual = om_historicos[0] if om_historicos else 0.0

            # Veredicto de Consistencia: Munger quiere que TODOS los años cumplan el mínimo
            consistencia_gm = all(m >= 0.40 for m in gm_historicos)
            consistencia_om = all(m >= 0.20 for m in om_historicos)

            # --- FILTROS DE BALANCE GENERAL (Último Año) ---
            roe_actual = safe_float(info.get('returnOnEquity'))
            cr = safe_float(info.get('currentRatio'))
            de = (safe_float(balance_sheet.loc['Total Liabilities Net Minority Interest'][0]) / safe_float(balance_sheet.loc['Total Stockholders Equity'][0])) if 'Total Liabilities Net Minority Interest' in balance_sheet.index and 'Total Stockholders Equity' in balance_sheet.index else safe_float(info.get('debtToEquity'))/100.0

            # --- VALIDACIÓN HISTÓRICA DE CAJA (FCF vs Utilidad Neta) ---
            ops_cash_hist = cashflow.loc['Operating Cash Flow']
            capex_hist = abs(cashflow.loc['Capital Expenditure']) if 'Capital Expenditure' in cashflow.index else 0.0
            fcf_historico = [safe_float(ops) - safe_float(cap) for ops, cap in zip(ops_cash_hist, capex_hist)]
            
            # Verificamos si en los últimos años el FCF ha respaldado consistentemente a la utilidad neta
            caja_solida_años = 0
            for fcf, net in zip(fcf_historico, net_income_hist):
                if safe_float(net) > 0 and fcf / safe_float(net) >= 0.75:
                    caja_solida_años += 1

            if caja_solida_años == len(net_income_hist):
                calidad_efectivo = f"Consistencia Excelente ✅ (4/4 años generando caja real)"
            elif caja_solida_años >= 2:
                calidad_efectivo = f"Aceptable ⚠️ ({caja_solida_años}/4 años estables)"
            else:
                calidad_efectivo = "Pobre 🚨 (El negocio infla utilidades contables pero no ve el efectivo)"

            # --- MARGEN DE SEGURIDAD ---
            precio_actual = safe_float(info.get('currentPrice', info.get('previousClose', 1.0)))
            if usar_manual:
                mos = (valor_estimado - precio_actual) / valor_estimado if valor_estimado > 0 else 0.0
                fuente_mos = f"Manual vs Mercado (Precio Actual: ${precio_actual:.2f})"
            else:
                target = safe_float(info.get('targetMedianPrice', precio_actual))
                mos = (target - precio_actual) / target if target > 0 else 0.0
                fuente_mos = f"Consenso Analistas (Target: ${target:.2f} vs Actual: ${precio_actual:.2f})"

            # --- SISTEMA DE PUNTUACIÓN (Castiga si no hay consistencia pasada) ---
            score = 0
            if consistencia_gm: score += 20
            elif gm_actual >= 0.40: score += 10 # Puntos parciales si hoy cumple pero el pasado fue inestable
            
            if consistencia_om: score += 20
            elif om_actual >= 0.20: score += 10
            
            if roe_actual >= 0.15: score += 10
            if de <= 0.5 and de >= 0: score += 10
            if cr >= 1.5: score += 10
            if "Excelente" in calidad_efectivo: score += 10
            elif "Aceptable" in calidad_efectivo: score += 5
            if mos >= 0.20: score += 10

            # --- INTERFAZ ---
            st.markdown("### 📊 Diagnóstico de Inversión Fundamental")
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.metric(label="Puntuación de Consistencia Estructural", value=f"{score} / 100")
                if score >= 80:
                    st.success("👑 MÁQUINA DE EFECTIVO MUNGERIANA: Ventaja competitiva histórica probada.")
                elif score >= 60:
                    st.warning("⚖️ NEGOCIO RAZONABLE: Fluctúa en el tiempo o tiene deuda.")
                else:
                    st.error("🚨 EVITAR: Negocio inconsistente o trampa de valor.")
                st.info(f"**Valoración:** {fuente_mos}\n\n**Margen de Seguridad Real:** {mos*100:.1f}%")

            with c2:
                estado_gm = f"{gm_actual*100:.1f}% (Estable en el tiempo ✅)" if consistencia_gm else f"{gm_actual*100:.1f}% (Inconsistente en el pasado ⚠️)"
                estado_om = f"{om_actual*100:.1f}% (Estable en el tiempo ✅)" if consistencia_om else f"{om_actual*100:.1f}% (Inconsistente en el pasado ⚠️)"
                estado_de = f"{de:.2f} (Sólido ✅)" if de <= 0.5 else f"{de:.2f} (Apalancado ❌)"
                estado_cr = f"{cr:.2f} (Líquido ✅)" if cr >= 1.5 else f"{cr:.2f} (Ajustado ⚠️)"
                
                data = {
                    "Filtro Cuantitativo": ["Margen Bruto (Histórico)", "Margen Operativo (Histórico)", "Retorno sobre Capital (ROE)", "Apalancamiento (Debt/Equity)", "Liquidez (Current Ratio)", "Validación de Caja"],
                    "Métrica Real": [estado_gm, estado_om, f"{roe_actual*100:.1f}%", estado_de, estado_cr, calidad_efectivo],
                    "Criterio Munger": ["Siempre > 40% (4 años)", "Siempre > 20% (4 años)", "> 15% actual", "<= 0.50", ">= 1.50", "FCF debe respaldar utilidades siempre"]
                }
                st.table(pd.DataFrame(data))

        except Exception as e:
            st.error(f"Error en la extracción histórica: {e}. Es probable que Yahoo esté limitando las tablas en este momento.")

#!/usr/bin/env python3
"""
DASHBOARD WEB - Sistema de Monitoreo Climático Lima (LOCAL)
Framework: Streamlit + Folium
Datos: Archivos locales (no S3)
"""
import streamlit as st
import json
import os
import glob
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from datetime import datetime
import time

# Configuración de página
st.set_page_config(
    page_title="Clima Lima - Dashboard",
    page_icon="🌤️",
    layout="wide"
)

# Configuración de auto-refresh
REFRESH_INTERVAL = 30  # segundos

# Inicializar session state para control de refresh
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()
if 'refresh_counter' not in st.session_state:
    st.session_state.refresh_counter = 0

# Rutas de datos
BATCH_DIR = '../data/batch'
ALERTS_DIR = '../data/alerts'
PREDICTIONS_DIR = '../data/predictions'

# Coordenadas de las zonas
ZONAS_COORDS = {
    'Lima Centro': {'lat': -12.046, 'lon': -77.043},
    'Lima Norte': {'lat': -11.961, 'lon': -77.060},
    'Lima Sur': {'lat': -12.196, 'lon': -76.973},
    'Lima Este': {'lat': -12.046, 'lon': -76.933},
    'Callao': {'lat': -12.056, 'lon': -77.118},
    'Miraflores': {'lat': -12.119, 'lon': -77.028}
}

def cargar_ultimo_batch():
    """Carga el archivo batch más reciente"""
    if not os.path.exists(BATCH_DIR):
        return None

    archivos = glob.glob(os.path.join(BATCH_DIR, 'stats_*.json'))
    if not archivos:
        return None

    # Obtener el más reciente
    archivo_reciente = max(archivos, key=os.path.getmtime)

    with open(archivo_reciente, 'r') as f:
        return json.load(f)

def cargar_alertas():
    """Carga resumen de alertas"""
    alert_file = os.path.join(ALERTS_DIR, 'summary.json')
    if os.path.exists(alert_file):
        with open(alert_file, 'r') as f:
            return json.load(f)
    return None

def cargar_predicciones():
    """Carga predicciones consolidadas por zona"""
    pred_file = os.path.join(PREDICTIONS_DIR, 'predicciones_por_zona.json')
    if os.path.exists(pred_file):
        with open(pred_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def crear_mapa(datos_batch):
    """Crea mapa interactivo de Lima"""
    if not datos_batch:
        return None

    # Centrar mapa en Lima
    m = folium.Map(
        location=[-12.046, -77.043],
        zoom_start=11,
        tiles='OpenStreetMap'
    )

    # Agregar marcadores
    for zona, coords in ZONAS_COORDS.items():
        if zona in datos_batch:
            stats = datos_batch[zona]
            temp = stats['temp_avg']

            # Color según temperatura
            if temp < 16:
                color = 'blue'
            elif temp < 22:
                color = 'green'
            elif temp < 28:
                color = 'orange'
            else:
                color = 'red'

            popup_html = f"""
            <div style="font-family: Arial; font-size: 12px;">
                <h4>{zona}</h4>
                <b>Temperatura promedio:</b> {temp:.1f}°C<br>
                <b>Mínima:</b> {stats['temp_min']:.1f}°C<br>
                <b>Máxima:</b> {stats['temp_max']:.1f}°C<br>
                <b>Humedad promedio:</b> {stats.get('humedad_avg', 0):.0f}%<br>
                <b>Registros:</b> {stats['registros']}
            </div>
            """

            folium.CircleMarker(
                location=[coords['lat'], coords['lon']],
                radius=15,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{zona}: {temp:.1f}°C",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7
            ).add_to(m)

    return m

def main():
    # Calcular tiempo desde último refresh
    tiempo_transcurrido = int(time.time() - st.session_state.last_refresh)
    tiempo_restante = max(0, REFRESH_INTERVAL - tiempo_transcurrido)

    # Título principal con indicador de auto-refresh
    col_titulo, col_refresh = st.columns([3, 1])

    with col_titulo:
        st.title("🌤️ Sistema de Monitoreo Climático - Lima (LOCAL)")

    with col_refresh:
        st.write("")  # Espaciado
        ultima_actualizacion = datetime.fromtimestamp(st.session_state.last_refresh).strftime("%H:%M:%S")
        st.info(f"🔄 Última actualización: {ultima_actualizacion}")
        st.caption(f"Próxima actualización en: {tiempo_restante}s")

        if st.button("🔄 Refrescar Ahora", use_container_width=True):
            st.session_state.last_refresh = time.time()
            st.session_state.refresh_counter += 1
            st.rerun()

    st.markdown("---")

    # Cargar datos
    datos_batch = cargar_ultimo_batch()
    alertas = cargar_alertas()
    predicciones = cargar_predicciones()

    if not datos_batch:
        st.warning("⚠️ No hay datos disponibles. Asegúrate de que los consumers estén corriendo.")
        st.info("Ejecuta: `python consumers/consumer_batch.py`")
        return

    # Sidebar
    with st.sidebar:
        st.header("📊 Panel de Control")
        st.markdown("---")

        # Total zonas
        st.metric("Zonas Monitoreadas", len(datos_batch))

        st.markdown("---")
        st.subheader("🗺️ Zonas")
        for zona in datos_batch.keys():
            st.write(f"✓ {zona}")

    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Mapa", "📈 Gráficos", "🕐 Registros", "⚠️ Alertas"])

    # TAB 1: MAPA
    with tab1:
        st.header("Mapa Interactivo de Lima")

        mapa = crear_mapa(datos_batch)
        if mapa:
            st_folium(mapa, width=1200, height=600)

        # Tabla de datos actuales
        st.subheader("📋 Datos Actuales por Zona")

        zonas_data = []
        for zona, stats in datos_batch.items():
            zonas_data.append({
                'Zona': zona,
                'Temp Promedio': f"{stats['temp_avg']:.1f}°C",
                'Temp Mínima': f"{stats['temp_min']:.1f}°C",
                'Temp Máxima': f"{stats['temp_max']:.1f}°C",
                'Registros': stats['registros']
            })

        if zonas_data:
            df = pd.DataFrame(zonas_data)
            st.dataframe(df, use_container_width=True)

    # TAB 2: GRÁFICOS
    with tab2:
        st.header("Gráficos de Datos")

        # Gráfico de temperaturas
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🌡️ Temperaturas Promedio")

            zonas = list(datos_batch.keys())
            temps = [datos_batch[z]['temp_avg'] for z in zonas]

            fig_temp = go.Figure(data=[
                go.Bar(
                    x=zonas,
                    y=temps,
                    marker_color='indianred',
                    text=[f"{t:.1f}°C" for t in temps],
                    textposition='outside'
                )
            ])
            fig_temp.update_layout(
                yaxis_title="Temperatura (°C)",
                height=400
            )
            st.plotly_chart(fig_temp, use_container_width=True)

        with col2:
            st.subheader("📊 Rango de Temperaturas")

            fig_range = go.Figure()

            for zona in zonas:
                stats = datos_batch[zona]
                fig_range.add_trace(go.Scatter(
                    x=[zona, zona, zona],
                    y=[stats['temp_min'], stats['temp_avg'], stats['temp_max']],
                    mode='markers+lines',
                    name=zona,
                    marker=dict(size=[8, 12, 8])
                ))

            fig_range.update_layout(
                yaxis_title="Temperatura (°C)",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig_range, use_container_width=True)

    # TAB 3: REGISTROS CON TIMESTAMPS
    with tab3:
        st.header("🕐 Registros Detallados con Timestamps")

        # Selector de zona
        zona_seleccionada = st.selectbox(
            "Selecciona una zona:",
            list(datos_batch.keys())
        )

        if zona_seleccionada and 'registros_detalle' in datos_batch[zona_seleccionada]:
            registros = datos_batch[zona_seleccionada]['registros_detalle']

            st.subheader(f"Registros de {zona_seleccionada}")
            st.caption(f"Total: {len(registros)} registros en este batch")

            # Convertir a DataFrame para mejor visualización
            df_registros = pd.DataFrame(registros)

            # Formatear timestamp para mejor lectura
            if not df_registros.empty and 'timestamp' in df_registros.columns:
                df_registros['hora'] = pd.to_datetime(df_registros['timestamp']).dt.strftime('%H:%M:%S')
                df_registros['fecha'] = pd.to_datetime(df_registros['timestamp']).dt.strftime('%Y-%m-%d')

                # Reordenar columnas
                columnas = ['fecha', 'hora', 'temperatura', 'humedad', 'viento', 'presion']
                df_display = df_registros[columnas].copy()

                # Renombrar columnas
                df_display.columns = ['Fecha', 'Hora', 'Temp (°C)', 'Humedad (%)', 'Viento (km/h)', 'Presión (hPa)']

                # Mostrar tabla
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    height=400
                )

                # Gráfico de temperatura en el tiempo
                st.subheader("📈 Evolución de Temperatura")
                fig_timeline = go.Figure()
                fig_timeline.add_trace(go.Scatter(
                    x=df_registros['hora'],
                    y=df_registros['temperatura'],
                    mode='lines+markers',
                    name='Temperatura',
                    line=dict(color='red', width=2),
                    marker=dict(size=6)
                ))
                fig_timeline.update_layout(
                    xaxis_title="Hora",
                    yaxis_title="Temperatura (°C)",
                    height=300,
                    showlegend=False
                )
                st.plotly_chart(fig_timeline, use_container_width=True)

        else:
            st.warning("No hay registros detallados disponibles. Reinicia el consumer_batch para generar nuevos datos.")
            st.info("Los registros con timestamps se guardarán en los próximos batches.")

    # TAB 4: PREDICCIONES Y ALERTAS
    with tab4:
        st.header("🔮 Predicciones Climáticas por Zona")

        # Mostrar predicciones consolidadas
        if predicciones:
            for zona in sorted(predicciones.keys()):
                pred_zona = predicciones[zona]
                preds = pred_zona['predicciones']
                datos_act = pred_zona['datos_actuales']

                # Crear card expandible para cada zona
                with st.expander(f"📍 {zona}", expanded=True):
                    # Timestamp
                    timestamp_dt = datetime.fromisoformat(pred_zona['timestamp'])
                    st.caption(f"Última actualización: {timestamp_dt.strftime('%H:%M:%S')}")

                    # Mostrar probabilidades con barras de progreso
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("### ☀️ Soleado")
                        st.progress(preds['probabilidad_sol'] / 100)
                        st.metric("Probabilidad", f"{preds['probabilidad_sol']:.1f}%")

                    with col2:
                        st.markdown("### ☁️ Nublado")
                        st.progress(preds['probabilidad_nublado'] / 100)
                        st.metric("Probabilidad", f"{preds['probabilidad_nublado']:.1f}%")

                    with col3:
                        st.markdown("### 🌧️ Lluvia")
                        st.progress(preds['probabilidad_lluvia'] / 100)
                        st.metric("Probabilidad", f"{preds['probabilidad_lluvia']:.1f}%")

                    # Clasificación general
                    st.markdown("---")

                    # Emoji según clasificación
                    emojis_clasif = {
                        'Soleado': '☀️',
                        'Mayormente soleado': '🌤️',
                        'Parcialmente nublado': '⛅',
                        'Nublado': '☁️',
                        'Llovizna': '🌦️',
                        'Lluvioso': '🌧️',
                        'Tormenta': '⛈️'
                    }
                    emoji_clasif = emojis_clasif.get(preds['clasificacion'], '🌡️')

                    col_clasif, col_conf = st.columns([2, 1])
                    with col_clasif:
                        st.success(f"{emoji_clasif} **{preds['clasificacion']}**")
                    with col_conf:
                        st.info(f"Confianza: {preds['confianza']:.1f}%")

                    # Datos actuales
                    st.markdown("#### 📊 Condiciones Actuales")
                    col_datos1, col_datos2, col_datos3, col_datos4 = st.columns(4)

                    col_datos1.metric("🌡️ Temperatura", f"{datos_act['temperatura']:.1f}°C")
                    col_datos2.metric("💧 Humedad", f"{datos_act['humedad']:.0f}%")
                    col_datos3.metric("💨 Viento", f"{datos_act['viento']:.1f} km/h")
                    col_datos4.metric("🔽 Presión", f"{datos_act['presion']:.1f} hPa")

            st.markdown("---")

        else:
            st.info("⏳ Esperando predicciones... Asegúrate de que consumer_predicciones_consolidadas.py esté corriendo.")

        # Alertas antiguas (si existen)
        st.header("⚠️ Historial de Alertas")

        if alertas and alertas.get('total', 0) > 0:
            st.metric("Total Alertas Generadas", alertas['total'])

            st.subheader("Últimas Alertas")

            for alerta in reversed(alertas['alertas'][-10:]):
                with st.expander(f"🔴 {alerta['zona']} - {alerta['timestamp'][:19]}"):
                    st.write(f"**Alertas generadas:** {len(alerta['alertas'])}")

                    for a in alerta['alertas']:
                        st.write(f"🔴 **{a['tipo']}**: {a['valor']}")

                    st.write("**Datos en ese momento:**")
                    datos = alerta['datos']
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Temperatura", f"{datos['temperatura']:.1f}°C")
                    col2.metric("Humedad", f"{datos['humedad']:.0f}%")
                    col3.metric("Viento", f"{datos['viento']:.1f} km/h")
        else:
            st.info("No hay alertas generadas aún")

    # Footer
    st.markdown("---")
    st.caption("Sistema de Monitoreo Climático - Lima | Datos en tiempo real desde Kafka (local)")

    # Auto-refresh: recargar página automáticamente cada 30 segundos
    if tiempo_transcurrido >= REFRESH_INTERVAL:
        st.session_state.last_refresh = time.time()
        st.session_state.refresh_counter += 1
        time.sleep(0.1)  # Pequeña pausa para que se vea el cambio
        st.rerun()

if __name__ == "__main__":
    main()

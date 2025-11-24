# Sistema de Monitoreo Climático en Tiempo Real - Lima

Sistema de procesamiento de datos climáticos en tiempo real utilizando Apache Kafka, con predicción meteorológica basada en reglas y visualización web interactiva.

## 📋 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Componentes de Kafka](#componentes-de-kafka)
- [Tecnologías Utilizadas](#tecnologías-utilizadas)
- [Prerequisitos](#prerequisitos)
- [Instalación](#instalación)
- [Ejecución del Sistema](#ejecución-del-sistema)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Flujo de Datos](#flujo-de-datos)
- [Modelos de Predicción](#modelos-de-predicción)
- [Dashboard Web](#dashboard-web)
- [Ejemplos de Uso](#ejemplos-de-uso)

---

## 🎯 Descripción General

Sistema distribuido de procesamiento de datos climáticos que monitorea 6 zonas de Lima en tiempo real, procesa información meteorológica, genera predicciones simples del clima y visualiza los resultados en un dashboard web interactivo.

**Características principales:**
- ✅ Generación de datos climáticos sintéticos cada 10 segundos
- ✅ Procesamiento y limpieza de datos en tiempo real
- ✅ Almacenamiento por lotes (batch processing)
- ✅ Sistema de alertas para condiciones climáticas extremas
- ✅ 3 modelos de predicción meteorológica basados en reglas
- ✅ Dashboard web con actualización automática cada 30 segundos
- ✅ Registros con timestamps para análisis temporal

**Zonas monitoreadas:**
1. Lima Centro
2. Lima Norte
3. Lima Sur
4. Lima Este
5. Callao
6. Miraflores

---

## 🏗️ Arquitectura del Sistema

\`\`\`
┌─────────────────────────────────────────────────────────────────────┐
│                         FUENTE DE DATOS                              │
│                   Open-Meteo API (Datos reales)                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          PRODUCERS (2)                               │
├─────────────────────────────────────────────────────────────────────┤
│  Producer Realtime  ──────────►  Topic: weather-raw                 │
│       (6 zonas cada 10s)                                             │
│                                         │                            │
│  Producer Cleaning  ◄───────────────────┘                           │
│       (Validación)  ──────────►  Topic: weather-clean               │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      KAFKA BROKER (1)                                │
│                    localhost:9092                                    │
├─────────────────────────────────────────────────────────────────────┤
│  Topics (4):                                                         │
│    • weather-raw      (datos crudos)                                │
│    • weather-clean    (datos validados)                             │
│    • weather-alerts   (alertas generadas)                           │
│    • weather-stats    (estadísticas procesadas)                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        CONSUMERS (6)                                 │
├─────────────────────────────────────────────────────────────────────┤
│  1. Consumer Batch             ──► data/batch/*.json                │
│     (Procesamiento por lotes, 72 mensajes cada ~2 min)              │
│                                                                      │
│  2. Consumer Alerts            ──► data/alerts/*.json               │
│     (Monitoreo de umbrales)                                         │
│                                                                      │
│  3. Predictor Lluvia          ──► data/predictions/lluvia*.json     │
│     (Modelo de probabilidad de lluvia)                              │
│                                                                      │
│  4. Predictor Sol             ──► data/predictions/sol*.json        │
│     (Modelo de probabilidad de sol)                                 │
│                                                                      │
│  5. Clasificador Clima        ──► data/predictions/clasif*.json     │
│     (Clasificación general: soleado/nublado/lluvioso)               │
│                                                                      │
│  6. Consolidador Predicciones ──► data/predictions/                 │
│     (Consolida las 3 predicciones por zona)  predicciones_por_zona  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DASHBOARD WEB                                   │
│                   Streamlit (localhost:8501)                         │
├─────────────────────────────────────────────────────────────────────┤
│  • Mapa interactivo de Lima                                         │
│  • Gráficos de temperaturas                                         │
│  • Tabla de registros con timestamps                                │
│  • Predicciones climáticas por zona con emojis                      │
│  • Auto-refresh cada 30 segundos                                    │
└─────────────────────────────────────────────────────────────────────┘
\`\`\`

---

## 📊 Componentes de Kafka

### Brokers
- **Cantidad:** 1 broker
- **Puerto:** 9092
- **Host:** localhost

### Zookeeper
- **Puerto:** 2181
- **Uso:** Coordinación del cluster Kafka

### Topics (4 topics)

| Topic | Particiones | Replication Factor | Descripción |
|-------|-------------|-------------------|-------------|
| \`weather-raw\` | 1 | 1 | Datos crudos del producer realtime |
| \`weather-clean\` | 1 | 1 | Datos validados y limpios |
| \`weather-alerts\` | 1 | 1 | Alertas de condiciones extremas |
| \`weather-stats\` | 1 | 1 | Estadísticas procesadas |

### Producers (2 producers)

| Producer | Topic Destino | Frecuencia | Descripción |
|----------|--------------|-----------|-------------|
| \`producer_realtime.py\` | \`weather-raw\` | 10 segundos | Genera datos de 6 zonas con API real |
| \`producer_cleaning.py\` | \`weather-clean\` | En tiempo real | Valida y limpia datos del topic raw |

**Mensajes generados por ciclo:** 6 (uno por zona)
**Mensajes por minuto:** ~36 mensajes
**Mensajes por hora:** ~2,160 mensajes

### Consumers (6 consumers)

| Consumer | Group ID | Topic Consumido | Descripción |
|----------|----------|----------------|-------------|
| \`consumer_batch.py\` | \`batch-processor\` | \`weather-clean\` | Procesa lotes de 72 mensajes (~2 min) |
| \`consumer_alerts.py\` | \`alerts-monitor\` | \`weather-clean\` | Detecta condiciones extremas |
| \`consumer_predictor_lluvia.py\` | \`predictor-lluvia\` | \`weather-clean\` | Predice probabilidad de lluvia |
| \`consumer_predictor_sol.py\` | \`predictor-sol\` | \`weather-clean\` | Predice probabilidad de sol |
| \`consumer_clasificador_clima.py\` | \`clasificador-clima\` | \`weather-clean\` | Clasifica clima general |
| \`consumer_predicciones_consolidadas.py\` | \`predicciones-consolidadas\` | \`weather-clean\` | Consolida predicciones por zona |


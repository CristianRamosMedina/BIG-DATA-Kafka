# Sistema de Monitoreo Climático en Tiempo Real - Lima

Sistema distribuido de procesamiento de datos climáticos utilizando Apache Kafka con 3 brokers, deployeado en AWS EC2. Monitorea 6 zonas de Lima en tiempo real, procesa datos meteorológicos y visualiza resultados en dashboard web.

## Tabla de Contenidos

- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Componentes de Kafka](#componentes-de-kafka)
- [Fuente de Datos](#fuente-de-datos)
- [Ejemplos de Datos](#ejemplos-de-datos)
- [Deployment en AWS EC2](#deployment-en-aws-ec2)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Instalación Local](#instalación-local)

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FUENTE DE DATOS                              │
│                   Open-Meteo API (Datos reales)                      │
│                   Coordenadas de 6 zonas de Lima                     │
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
│                  KAFKA CLUSTER (3 Brokers)                           │
│              localhost:9092, 9093, 9094                              │
├─────────────────────────────────────────────────────────────────────┤
│  Topics (4):                                                         │
│    • weather-raw      (datos crudos de la API)                      │
│    • weather-clean    (datos validados)                             │
│    • weather-alerts   (alertas de condiciones extremas)             │
│    • weather-stats    (estadísticas procesadas)                     │
│                                                                      │
│  Zookeeper: localhost:2181                                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        CONSUMERS (6)                                 │
├─────────────────────────────────────────────────────────────────────┤
│  1. Consumer Batch             ──► data/batch/*.json                │
│     Group ID: batch-processor                                        │
│     (Procesamiento por lotes, 72 mensajes cada ~2 min)              │
│                                                                      │
│  2. Consumer Alerts            ──► data/alerts/*.json               │
│     Group ID: alerts-monitor                                         │
│     (Monitoreo de umbrales de temperatura y viento)                 │
│                                                                      │
│  3. Predictor Lluvia          ──► data/predictions/lluvia*.json     │
│     Group ID: predictor-lluvia                                       │
│     (Modelo de probabilidad de lluvia basado en humedad)            │
│                                                                      │
│  4. Predictor Sol             ──► data/predictions/sol*.json        │
│     Group ID: predictor-sol                                          │
│     (Modelo de probabilidad de sol basado en temperatura)           │
│                                                                      │
│  5. Clasificador Clima        ──► data/predictions/clasif*.json     │
│     Group ID: clasificador-clima                                     │
│     (Clasificación: soleado/nublado/lluvioso)                       │
│                                                                      │
│  6. Consolidador Predicciones ──► data/predictions/consolidado.json │
│     Group ID: predicciones-consolidadas                              │
│     (Consolida las 3 predicciones por zona)                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DASHBOARD WEB                                   │
│                   Streamlit (puerto 8501)                            │
├─────────────────────────────────────────────────────────────────────┤
│  • Mapa interactivo con Folium                                      │
│  • Gráficos de temperaturas con Plotly                              │
│  • Tabla de registros con timestamps                                │
│  • Predicciones climáticas por zona                                 │
│  • Auto-refresh cada 30 segundos                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Componentes de Kafka

### Brokers

Cluster Kafka distribuido con 3 brokers:

| Broker | Puerto | Host Local | Host EC2 |
|--------|--------|------------|----------|
| Broker 1 | 9092 | localhost | 54.146.168.205 |
| Broker 2 | 9093 | localhost | 54.146.168.205 |
| Broker 3 | 9094 | localhost | 54.146.168.205 |

### Zookeeper

- **Puerto**: 2181
- **Función**: Coordinación del cluster Kafka
- **Host**: localhost / 54.146.168.205

### Topics

| Topic | Particiones | Replication Factor | Descripción |
|-------|-------------|-------------------|-------------|
| `weather-raw` | 1 | 1 | Datos crudos del producer realtime |
| `weather-clean` | 1 | 1 | Datos validados y limpios |
| `weather-alerts` | 1 | 1 | Alertas de condiciones extremas |
| `weather-stats` | 1 | 1 | Estadísticas procesadas |

### Producers

| Producer | Topic Destino | Frecuencia | Descripción |
|----------|--------------|-----------|-------------|
| `producer_realtime.py` | `weather-raw` | 10 segundos | Obtiene datos de 6 zonas de Lima desde Open-Meteo API |
| `producer_cleaning.py` | `weather-clean` | Tiempo real | Consume de weather-raw, valida y limpia datos |

**Volumen de datos:**
- Mensajes por ciclo: 6 (uno por zona)
- Mensajes por minuto: 36
- Mensajes por hora: 2,160

### Consumers

| Consumer | Group ID | Topic Consumido | Descripción |
|----------|----------|----------------|-------------|
| `consumer_batch.py` | `batch-processor` | `weather-clean` | Procesa lotes de 72 mensajes (~2 min) |
| `consumer_alerts.py` | `alerts-monitor` | `weather-clean` | Detecta temp >30°C o viento >50 km/h |
| `consumer_predictor_lluvia.py` | `predictor-lluvia` | `weather-clean` | Predice probabilidad de lluvia |
| `consumer_predictor_sol.py` | `predictor-sol` | `weather-clean` | Predice probabilidad de sol |
| `consumer_clasificador_clima.py` | `clasificador-clima` | `weather-clean` | Clasifica clima general |
| `consumer_predicciones_consolidadas.py` | `predicciones-consolidadas` | `weather-clean` | Consolida predicciones |

---

## Fuente de Datos

**API**: Open-Meteo Weather Forecast API
**URL**: `https://api.open-meteo.com/v1/forecast`

### Zonas Monitoreadas

| Zona | Latitud | Longitud | Características |
|------|---------|----------|-----------------|
| Lima Centro | -12.046374 | -77.042793 | Centro histórico |
| Lima Norte | -11.889233 | -77.064896 | Zona norte costera |
| Lima Sur | -12.193806 | -76.986817 | Zona sur |
| Lima Este | -12.035000 | -76.870000 | Valle del Rímac |
| Callao | -12.056457 | -77.118784 | Puerto principal |
| Miraflores | -12.121097 | -77.029084 | Distrito turístico |

### Variables Capturadas

- **Temperatura**: Grados Celsius
- **Humedad**: Porcentaje (0-100)
- **Velocidad del viento**: km/h
- **Timestamp**: ISO 8601 format

---

## Ejemplos de Datos

### Topic: weather-raw

Datos crudos publicados por producer_realtime.py:

```json
{
  "zona": "Lima Centro",
  "temperatura": 18.5,
  "humedad": 89,
  "viento": 12.3,
  "timestamp": "2024-11-24T15:43:22"
}
```

### Topic: weather-clean

Datos validados por producer_cleaning.py:

```json
{
  "zona": "Miraflores",
  "temperatura": 18.0,
  "humedad": 91,
  "viento": 14.9,
  "timestamp": "2024-11-24T15:43:24",
  "validado": true
}
```

### Consumer Batch: data/batch/stats_*.json

Estadísticas procesadas cada 2 minutos (72 mensajes):

```json
{
  "Lima Centro": {
    "temp_avg": 18.4,
    "temp_min": 17.6,
    "temp_max": 18.9,
    "humedad_avg": 91.4,
    "viento_avg": 13.4,
    "registros": 12
  },
  "Lima Norte": {
    "temp_avg": 17.7,
    "temp_min": 17.2,
    "temp_max": 18.2,
    "humedad_avg": 90.8,
    "viento_avg": 15.0,
    "registros": 12
  }
}
```

### Consumer Alerts: data/alerts/alert_*.json

Alertas generadas por condiciones extremas:

```json
{
  "zona": "Lima Este",
  "tipo": "TEMPERATURA_ALTA",
  "valor": 31.2,
  "umbral": 30,
  "timestamp": "2024-11-24T14:30:15",
  "mensaje": "Temperatura excede umbral de 30°C"
}
```

### Predictor Lluvia: data/predictions/lluvia_*.json

```json
{
  "zona": "Lima Centro",
  "probabilidad_lluvia": 75,
  "humedad": 95,
  "categoria": "Alta probabilidad",
  "timestamp": "2024-11-24T15:44:00"
}
```

### Predictor Sol: data/predictions/sol_*.json

```json
{
  "zona": "Miraflores",
  "probabilidad_sol": 60,
  "temperatura": 22.5,
  "categoria": "Moderado",
  "timestamp": "2024-11-24T15:44:02"
}
```

### Clasificador: data/predictions/clasif_*.json

```json
{
  "zona": "Callao",
  "clasificacion": "NUBLADO",
  "temperatura": 18.0,
  "humedad": 88,
  "timestamp": "2024-11-24T15:44:05"
}
```

---

## Deployment en AWS EC2

### Información del Servidor

- **Tipo de Instancia**: t3.xlarge
- **ID de Instancia**: i-0bedfca959961bb9c
- **IP Pública**: 54.146.168.205 (cambia al reiniciar)
- **Sistema Operativo**: Amazon Linux 2
- **Región**: us-east-1
- **vCPU**: 4
- **RAM**: 16 GB
- **Storage**: 30 GB EBS gp2

### Dashboard Público

```
http://54.146.168.205:8501
```

El dashboard se actualiza automáticamente cada 30 segundos.

### Iniciar el Sistema en EC2

```bash
# 1. Iniciar Docker daemon
sudo systemctl start docker

# 2. Navegar al directorio del proyecto
cd ~/kafka-clima

# 3. Iniciar cluster Kafka (3 brokers) y Zookeeper
docker-compose up -d

# 4. Esperar 90 segundos para que Kafka esté listo
sleep 90

# 5. Iniciar Producer Realtime
cd ~/kafka-clima/producers
nohup python3 producer_realtime.py > /tmp/producer_realtime.log 2>&1 &

# 6. Iniciar Producer Cleaning
nohup python3 producer_cleaning.py > /tmp/producer_cleaning.log 2>&1 &

# 7. Iniciar Consumer Batch
cd ~/kafka-clima/consumers
nohup python3 consumer_batch.py > /tmp/consumer_batch.log 2>&1 &

# 8. Iniciar Dashboard Streamlit
cd ~/kafka-clima/dashboard
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > /tmp/streamlit.log 2>&1 &

# 9. Verificar procesos corriendo
ps aux | grep python | grep -v grep
docker ps | grep kafka
```

### Detener el Sistema en EC2

```bash
# Detener Dashboard
pkill -f streamlit

# Detener Consumers
pkill -f consumer_batch.py

# Detener Producers
pkill -f producer_realtime.py
pkill -f producer_cleaning.py

# Detener Kafka cluster
cd ~/kafka-clima
docker-compose down
```

### Ver Logs en Tiempo Real

```bash
# Producer Realtime
tail -f /tmp/producer_realtime.log

# Producer Cleaning
tail -f /tmp/producer_cleaning.log

# Consumer Batch
tail -f /tmp/consumer_batch.log

# Dashboard
tail -f /tmp/streamlit.log

# Logs de Kafka brokers
docker logs -f kafka-clima-1
docker logs -f kafka-clima-2
docker logs -f kafka-clima-3
```

### Conectarse a EC2

**Opción 1: EC2 Instance Connect (sin archivo .pem)**

1. Ir a https://console.aws.amazon.com/ec2
2. Seleccionar instancia i-0bedfca959961bb9c
3. Click en "Connect" → "EC2 Instance Connect"
4. Click en "Connect"

**Opción 2: SSH con archivo .pem**

```bash
ssh -i tu-clave.pem ec2-user@54.146.168.205
```

### Gestión de Costos

```bash
# Detener instancia EC2 (apagar sin eliminar)
aws ec2 stop-instances --instance-ids i-0bedfca959961bb9c

# Iniciar instancia EC2
aws ec2 start-instances --instance-ids i-0bedfca959961bb9c

# Obtener nueva IP pública después de iniciar
aws ec2 describe-instances --instance-ids i-0bedfca959961bb9c \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
```

**Costos estimados:**
- EC2 t3.xlarge running: $0.1664/hora (~$4/día)
- EC2 stopped: $0.10/día (solo EBS)
- S3 Storage: $0.01/mes (datos mínimos)

---

## Estructura del Proyecto

```
kafka-clima-lima-local/
├── producers/
│   ├── producer_realtime.py      # Obtiene datos de Open-Meteo API
│   └── producer_cleaning.py      # Valida y limpia datos
├── consumers/
│   ├── consumer_batch.py         # Procesamiento por lotes
│   ├── consumer_alerts.py        # Sistema de alertas
│   ├── consumer_predictor_lluvia.py
│   ├── consumer_predictor_sol.py
│   ├── consumer_clasificador_clima.py
│   └── consumer_predicciones_consolidadas.py
├── dashboard/
│   └── app.py                    # Dashboard Streamlit
├── data/
│   ├── batch/                    # Estadísticas procesadas
│   ├── alerts/                   # Alertas generadas
│   └── predictions/              # Predicciones climáticas
├── docker-compose.yml            # Kafka cluster (3 brokers)
└── README.md
```

---

## Instalación Local

### Prerequisitos

- Python 3.7+
- Docker y Docker Compose
- 8 GB RAM mínimo
- Puertos 2181, 9092, 9093, 9094, 8501 disponibles

### Pasos de Instalación

1. Clonar el repositorio:
```bash
git clone <URL_DEL_REPOSITORIO>
cd kafka-clima-lima-local
```

2. Instalar dependencias de Python:
```bash
pip install kafka-python requests streamlit folium plotly pandas
```

3. Iniciar Kafka cluster:
```bash
docker-compose up -d
sleep 90  # Esperar a que Kafka esté listo
```

4. Verificar que los 3 brokers estén corriendo:
```bash
docker ps | grep kafka
```

Deberías ver:
- kafka-clima-1 (puerto 9092)
- kafka-clima-2 (puerto 9093)
- kafka-clima-3 (puerto 9094)
- zookeeper (puerto 2181)

5. En terminales separadas, iniciar componentes:

Terminal 1 - Producer Realtime:
```bash
cd producers
python producer_realtime.py
```

Terminal 2 - Producer Cleaning:
```bash
cd producers
python producer_cleaning.py
```

Terminal 3 - Consumer Batch:
```bash
cd consumers
python consumer_batch.py
```

Terminal 4 - Dashboard:
```bash
cd dashboard
streamlit run app.py
```

6. Acceder al dashboard:
```
http://localhost:8501
```

### Detener Sistema Local

```bash
# Ctrl+C en cada terminal de Python

# Detener Kafka
docker-compose down
```

---

## Tecnologías Utilizadas

- **Apache Kafka**: Streaming de datos en tiempo real
- **Zookeeper**: Coordinación de brokers
- **Python 3**: Lenguaje de programación
- **kafka-python**: Cliente Kafka para Python
- **Streamlit**: Framework para dashboard web
- **Folium**: Mapas interactivos
- **Plotly**: Gráficos interactivos
- **Docker**: Contenedores para Kafka
- **AWS EC2**: Servidor en la nube
- **Open-Meteo API**: Fuente de datos climáticos

---

## Contacto y Deployment

**Dashboard en producción**: http://54.146.168.205:8501

**Nota**: La IP pública cambia cada vez que se reinicia la instancia EC2. Usar el comando de AWS CLI para obtener la IP actual.

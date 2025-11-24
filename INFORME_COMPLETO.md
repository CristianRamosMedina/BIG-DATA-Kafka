# INFORME COMPLETO - KAFKA CLIMA LIMA (LOCAL)

## UBICACION DEL PROYECTO
```
C:\Users\Cris\Desktop\kafka-clima-lima-local\
```

## ESTADO ACTUAL (EN VIVO)

### Servicios Corriendo:
1. **Kafka + Zookeeper** (Docker containers)
   - Container Kafka: `kafka-clima`
   - Container Zookeeper: `zookeeper-clima`
   - Puerto Kafka: `localhost:9092`
   - Puerto Zookeeper: `2181`

2. **Producer Realtime** (Python)
   - Generando datos cada 10 segundos
   - 6 zonas de Lima
   - Topic: `weather-raw`

3. **Producer Cleaning** (Python)
   - Validando y limpiando datos
   - Topic input: `weather-raw`
   - Topic output: `weather-clean`

4. **Consumer Batch** (Python)
   - Procesando batches de 72 mensajes (~2 minutos)
   - Guardando en: `data/batch/stats_YYYYMMDD_HHMMSS.json`

5. **Consumer Alerts** (Python)
   - Monitoreando umbrales de temperatura/humedad/viento
   - Sin alertas actualmente (clima normal)

6. **Dashboard Streamlit** (Python)
   - URL Local: **http://localhost:8501**
   - URL Red: http://192.168.1.36:8501
   - Mostrando mapa interactivo + graficos

## ESTRUCTURA DEL PROYECTO
```
kafka-clima-lima-local/
├── docker-compose.yml          # Kafka + Zookeeper
├── producers/
│   ├── producer_realtime.py    # Genera datos cada 10s
│   └── producer_cleaning.py    # Limpieza de datos
├── consumers/
│   ├── consumer_batch.py       # Procesa por lotes
│   └── consumer_alerts.py      # Sistema de alertas
├── dashboard/
│   └── app.py                  # Dashboard Streamlit
├── data/
│   ├── batch/                  # JSONs con estadisticas
│   └── alerts/                 # JSONs con alertas
└── README.md                   # Instrucciones de uso
```

## DATOS GENERADOS
- **Archivos batch**: 7+ archivos JSON en `data/batch/`
- **Mensajes procesados**: 150+ mensajes validados
- **Ciclos completados**: 19+ ciclos de generacion
- **Batches guardados**: 3+ batches completos

## COMANDOS PARA VERIFICAR QUE ESTA CORRIENDO

### 1. Verificar Docker Containers
```bash
docker ps
```
Debes ver: `kafka-clima` y `zookeeper-clima`

### 2. Verificar archivos generados
```bash
dir "C:\Users\Cris\Desktop\kafka-clima-lima-local\data\batch"
```

### 3. Ver procesos Python corriendo
```bash
tasklist | findstr python
```

## COMANDOS PARA REINICIAR (SI ES NECESARIO)

### Si TODO se apago:

#### 1. Iniciar Kafka
```bash
cd "C:\Users\Cris\Desktop\kafka-clima-lima-local"
docker-compose up -d
```
Esperar 30 segundos.

#### 2. Iniciar Producers (2 terminales separadas)
Terminal 1:
```bash
cd "C:\Users\Cris\Desktop\kafka-clima-lima-local\producers"
python producer_realtime.py
```

Terminal 2:
```bash
cd "C:\Users\Cris\Desktop\kafka-clima-lima-local\producers"
python producer_cleaning.py
```

#### 3. Iniciar Consumers (2 terminales separadas)
Terminal 3:
```bash
cd "C:\Users\Cris\Desktop\kafka-clima-lima-local\consumers"
python consumer_batch.py
```

Terminal 4:
```bash
cd "C:\Users\Cris\Desktop\kafka-clima-lima-local\consumers"
python consumer_alerts.py
```

#### 4. Iniciar Dashboard
Terminal 5:
```bash
cd "C:\Users\Cris\Desktop\kafka-clima-lima-local\dashboard"
python -m streamlit run app.py
```

Dashboard estara en: **http://localhost:8501**

## COMANDOS PARA DETENER TODO

### Detener procesos Python
Presiona Ctrl+C en cada terminal donde corre un proceso Python.

### Detener Kafka
```bash
cd "C:\Users\Cris\Desktop\kafka-clima-lima-local"
docker-compose down
```

## KAFKA TOPICS EN USO
1. `weather-raw` - Datos crudos del producer realtime
2. `weather-clean` - Datos validados del producer cleaning
3. `weather-alerts` - Alertas generadas
4. `weather-stats` - Estadisticas procesadas

## ZONAS MONITOREADAS
1. Lima Centro (-12.046, -77.043)
2. Lima Norte (-11.961, -77.060)
3. Lima Sur (-12.196, -76.973)
4. Lima Este (-12.046, -76.933)
5. Callao (-12.056, -77.118)
6. Miraflores (-12.119, -77.028)

## DEPENDENCIAS INSTALADAS
- kafka-python
- requests
- streamlit
- streamlit-folium
- folium
- plotly
- pandas

## NOTAS IMPORTANTES
- El producer realtime genera datos cada 10 segundos
- Los batches se completan cada ~2 minutos (72 mensajes)
- Los datos vienen de Open-Meteo API con variacion aleatoria
- Sin costos AWS - todo local con Docker
- Dashboard actualiza datos del ultimo batch guardado

## PROBLEMA ACTUAL
El usuario menciona que "no veo el tiempo real" en el frontend.
Posible causa: El dashboard lee archivos estaticos del ultimo batch, no consume directamente de Kafka en tiempo real.
Para ver datos en "tiempo real", el dashboard necesita refrescarse manualmente o implementar auto-refresh.

## PROXIMOS PASOS RECOMENDADOS
1. Agregar auto-refresh al dashboard cada 30-60 segundos
2. O cambiar dashboard para consumir directamente de Kafka
3. Verificar que los datos se estan generando correctamente

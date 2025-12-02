#!/usr/bin/env python3
"""
PRODUCER REAL-TIME - Datos climáticos Lima
Genera datos cada 10 segundos con variación realista
"""
import requests
import json
import time
import random
from kafka import KafkaProducer
from datetime import datetime

KAFKA_BROKERS = ['localhost:9092', 'localhost:9093', 'localhost:9094']
TOPIC = 'weather-raw'
INTERVALO = 10  # s

ZONAS_LIMA = {
    'Lima Centro': {'lat': -12.046, 'lon': -77.043},
    'Lima Norte': {'lat': -11.961, 'lon': -77.060},
    'Lima Sur': {'lat': -12.196, 'lon': -76.973},
    'Lima Este': {'lat': -12.046, 'lon': -76.933},
    'Callao': {'lat': -12.056, 'lon': -77.118},
    'Miraflores': {'lat': -12.119, 'lon': -77.028}
}

def get_weather_data(zona, lat, lon):
    """Obtiene datos climáticos de Open-Meteo API"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m,pressure_msl",
        "timezone": "America/Lima"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Variación realista (API actualiza cada 15 min, simulamos cambios)
        temp_base = data['current']['temperature_2m']
        hum_base = data['current']['relative_humidity_2m']
        wind_base = data['current']['wind_speed_10m']
        pres_base = data['current']['pressure_msl']

        return {
            'zona': zona,
            'timestamp': datetime.now().isoformat(),
            'coordenadas': {'lat': lat, 'lon': lon},
            'datos': {
                'temperatura': round(temp_base + random.uniform(-0.8, 0.8), 1),
                'humedad': max(0, min(100, hum_base + random.randint(-3, 3))),
                'precipitacion': max(0, data['current']['precipitation'] + random.uniform(-0.1, 0.2)),
                'codigo_clima': data['current']['weather_code'],
                'viento': round(max(0, wind_base + random.uniform(-2, 2)), 1),
                'direccion_viento': data['current']['wind_direction_10m'],
                'presion': round(pres_base + random.uniform(-1.5, 1.5), 1)
            }
        }
    except Exception as e:
        print(f"Error obteniendo datos para {zona}: {e}")
        return None

def main():
    print("=" * 70)
    print("PRODUCER REAL-TIME - KAFKA CLIMA LIMA")
    print("=" * 70)
    print(f"Conectando a Kafka Cluster: {', '.join(KAFKA_BROKERS)}")

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None,
        acks='all'
    )

    print(f"Generando datos cada {INTERVALO} segundos...")
    print(f"Zonas: {', '.join(ZONAS_LIMA.keys())}")
    print("Presiona Ctrl+C para detener")
    print("=" * 70)

    contador = 0

    try:
        while True:
            print(f"\n[CICLO {contador + 1}] {datetime.now().strftime('%H:%M:%S')}")

            for zona, info in ZONAS_LIMA.items():
                mensaje = get_weather_data(zona, info['lat'], info['lon'])
                if mensaje:
                    producer.send(TOPIC, key=zona, value=mensaje)
                    print(f"  {zona:15s} - Temp: {mensaje['datos']['temperatura']:5.1f}C | "
                          f"Hum: {mensaje['datos']['humedad']:3.0f}% | "
                          f"Viento: {mensaje['datos']['viento']:4.1f} km/h")

            producer.flush()
            contador += 1
            time.sleep(INTERVALO)

    except KeyboardInterrupt:
        print(f"\n\n{'=' * 70}")
        print(f"Producer detenido. Total ciclos: {contador}")
        print(f"Total mensajes enviados: {contador * len(ZONAS_LIMA)}")
        print("=" * 70)
    finally:
        producer.close()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
PRODUCER 2: HISTORICO
Carga datos historicos de los ultimos 30 dias para analisis
Topic destino: weather-historical
"""

import requests
import json
import time
from kafka import KafkaProducer
from datetime import datetime, timedelta
import sys

# Configuracion Kafka
KAFKA_BROKER = 'localhost:9092'
TOPIC = 'weather-historical'

# 6 Zonas de Lima
ZONAS_LIMA = {
    'Lima Centro': {'lat': -12.046, 'lon': -77.043},
    'Lima Norte': {'lat': -11.961, 'lon': -77.060},
    'Lima Sur': {'lat': -12.196, 'lon': -76.973},
    'Lima Este': {'lat': -12.046, 'lon': -76.933},
    'Callao': {'lat': -12.056, 'lon': -77.118},
    'Miraflores': {'lat': -12.119, 'lon': -77.028}
}

# Configuracion de carga historica
DIAS_HISTORICO = 30  # Ultimos 30 dias
BATCH_SIZE = 50  # Enviar en lotes de 50 mensajes


def get_historical_data(zona, lat, lon, fecha_inicio, fecha_fin):
    """
    Obtiene datos historicos de Open-Meteo API
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": fecha_inicio,
        "end_date": fecha_fin,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m,pressure_msl",
        "timezone": "America/Lima"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        mensajes = []

        # Procesar datos horarios
        if 'hourly' in data:
            hourly = data['hourly']
            timestamps = hourly['time']

            for i in range(len(timestamps)):
                mensaje = {
                    'zona': zona,
                    'timestamp': timestamps[i],
                    'coordenadas': {
                        'lat': lat,
                        'lon': lon
                    },
                    'datos': {
                        'temperatura': hourly['temperature_2m'][i],
                        'humedad': hourly['relative_humidity_2m'][i],
                        'precipitacion': hourly['precipitation'][i],
                        'codigo_clima': hourly['weather_code'][i],
                        'viento': hourly['wind_speed_10m'][i],
                        'direccion_viento': hourly['wind_direction_10m'][i],
                        'presion': hourly['pressure_msl'][i]
                    },
                    'metadata': {
                        'fuente': 'Open-Meteo API Historical',
                        'tipo': 'historical'
                    }
                }
                mensajes.append(mensaje)

        return mensajes

    except requests.exceptions.RequestException as e:
        print(f"Error obteniendo datos historicos para {zona}: {e}")
        return []
    except KeyError as e:
        print(f"Error en formato de datos historicos para {zona}: {e}")
        return []


def main():
    print("=" * 80)
    print("PRODUCER 2: HISTORICO - Carga de Datos Historicos")
    print("=" * 80)
    print(f"Topic: {TOPIC}")
    print(f"Broker: {KAFKA_BROKER}")
    print(f"Zonas: {len(ZONAS_LIMA)}")
    print(f"Periodo: Ultimos {DIAS_HISTORICO} dias")
    print(f"Batch size: {BATCH_SIZE} mensajes")
    print("=" * 80)

    # Calcular fechas
    fecha_fin = datetime.now().date()
    fecha_inicio = fecha_fin - timedelta(days=DIAS_HISTORICO)

    print(f"\nFecha inicio: {fecha_inicio}")
    print(f"Fecha fin: {fecha_fin}")
    print(f"Total de dias: {DIAS_HISTORICO}")
    print(f"Estimado: {DIAS_HISTORICO * 24 * len(ZONAS_LIMA)} registros ({DIAS_HISTORICO} dias × 24 horas × {len(ZONAS_LIMA)} zonas)")
    print("\n" + "=" * 80)

    # Crear producer Kafka
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
            batch_size=16384,  # Batch mas grande para carga historica
            linger_ms=100  # Esperar 100ms para acumular mensajes
        )
        print("Producer Kafka conectado exitosamente")
    except Exception as e:
        print(f"Error conectando a Kafka: {e}")
        print("Asegurate de que Kafka este corriendo en localhost:9092")
        sys.exit(1)

    print("\nIniciando carga historica...\n")

    total_enviados = 0
    total_errores = 0

    try:
        for zona, info in ZONAS_LIMA.items():
            print(f"\n[{zona}] Obteniendo datos...")
            print("-" * 80)

            # Obtener datos historicos
            mensajes = get_historical_data(
                zona,
                info['lat'],
                info['lon'],
                str(fecha_inicio),
                str(fecha_fin)
            )

            if not mensajes:
                print(f"  No se obtuvieron datos para {zona}")
                total_errores += 1
                continue

            print(f"  Datos obtenidos: {len(mensajes)} registros")
            print(f"  Enviando a Kafka en lotes de {BATCH_SIZE}...")

            # Enviar en batches
            enviados = 0
            for i, mensaje in enumerate(mensajes):
                try:
                    producer.send(
                        TOPIC,
                        key=zona,
                        value=mensaje
                    )
                    enviados += 1

                    # Mostrar progreso cada BATCH_SIZE mensajes
                    if (i + 1) % BATCH_SIZE == 0:
                        producer.flush()
                        print(f"    Progreso: {i + 1}/{len(mensajes)} mensajes enviados")

                except Exception as e:
                    print(f"    Error enviando mensaje {i + 1}: {e}")
                    total_errores += 1

            # Flush final para esta zona
            producer.flush()

            print(f"  Completado: {enviados}/{len(mensajes)} mensajes enviados para {zona}")
            total_enviados += enviados

            # Pequeno delay entre zonas
            time.sleep(1)

        print("\n" + "=" * 80)
        print("CARGA HISTORICA COMPLETADA")
        print("=" * 80)
        print(f"Total zonas procesadas: {len(ZONAS_LIMA)}")
        print(f"Total mensajes enviados: {total_enviados}")
        print(f"Total errores: {total_errores}")
        print(f"Tasa de exito: {(total_enviados / (total_enviados + total_errores) * 100):.1f}%" if total_enviados + total_errores > 0 else "N/A")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\nCarga interrumpida por usuario")
        print(f"Mensajes enviados hasta el momento: {total_enviados}")

    except Exception as e:
        print(f"\nError durante la carga: {e}")

    finally:
        producer.close()
        print("\nProducer cerrado correctamente")


if __name__ == "__main__":
    # Confirmar antes de ejecutar
    print("\nEste script cargara aproximadamente", DIAS_HISTORICO * 24 * len(ZONAS_LIMA), "registros historicos")
    respuesta = input("Deseas continuar? (s/n): ")

    if respuesta.lower() == 's':
        main()
    else:
        print("Carga cancelada")

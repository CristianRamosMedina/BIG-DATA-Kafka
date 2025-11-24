#!/usr/bin/env python3
"""
CONSUMER BATCH - Procesamiento por lotes
Guarda estadísticas cada 2 minutos en archivos locales
"""
import json
import os
from kafka import KafkaConsumer
from datetime import datetime
from collections import defaultdict

KAFKA_BROKER = 'localhost:9092'
TOPIC = 'weather-clean'
GROUP_ID = 'batch-processor'
BATCH_SIZE = 72  # Mini-batch cada 2 minutos (12 ciclos × 6 zonas)
OUTPUT_DIR = '../data/batch'

buffer = []
stats = defaultdict(lambda: {'temps': [], 'humedades': [], 'vientos': []})

def save_batch():
    """Guarda estadísticas del batch en archivo JSON"""
    if not buffer:
        return

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Calcular estadísticas
    resultado = {}
    for zona, data in stats.items():
        if data['temps']:
            resultado[zona] = {
                'temp_avg': round(sum(data['temps']) / len(data['temps']), 1),
                'temp_min': round(min(data['temps']), 1),
                'temp_max': round(max(data['temps']), 1),
                'humedad_avg': round(sum(data['humedades']) / len(data['humedades']), 1),
                'viento_avg': round(sum(data['vientos']) / len(data['vientos']), 1),
                'registros': len(data['temps'])
            }

    # Agrupar registros individuales por zona
    registros_por_zona = defaultdict(list)
    for registro in buffer:
        zona = registro['zona']
        registros_por_zona[zona].append({
            'timestamp': registro.get('timestamp', ''),
            'temperatura': registro['datos']['temperatura'],
            'humedad': registro['datos']['humedad'],
            'viento': registro['datos']['viento'],
            'presion': registro['datos'].get('presion', 0)
        })

    # Agregar registros individuales a cada zona
    for zona in resultado.keys():
        resultado[zona]['registros_detalle'] = sorted(
            registros_por_zona[zona],
            key=lambda x: x['timestamp']
        )

    # Guardar stats en archivo
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, f'stats_{timestamp}.json')

    with open(output_file, 'w') as f:
        json.dump(resultado, f, indent=2)

    print(f"\n{'='*70}")
    print(f"BATCH guardado: {output_file}")
    print(f"Registros: {len(buffer)}")
    print(f"{'='*70}")

    for zona, stat in resultado.items():
        print(f"{zona:15s} | Avg: {stat['temp_avg']:5.1f}°C | "
              f"Min: {stat['temp_min']:5.1f}°C | Max: {stat['temp_max']:5.1f}°C")

    print(f"{'='*70}\n")

    buffer.clear()
    stats.clear()

def main():
    print("=" * 70)
    print("CONSUMER BATCH - PROCESAMIENTO POR LOTES")
    print("=" * 70)
    print(f"Tamaño batch: {BATCH_SIZE} mensajes (~2 minutos)")
    print("Presiona Ctrl+C para detener")
    print("=" * 70)

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        group_id=GROUP_ID,
        auto_offset_reset='earliest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=30000
    )

    try:
        for message in consumer:
            data = message.value
            buffer.append(data)

            zona = data['zona']
            stats[zona]['temps'].append(data['datos']['temperatura'])
            stats[zona]['humedades'].append(data['datos']['humedad'])
            stats[zona]['vientos'].append(data['datos']['viento'])

            print(f"[BATCH] {zona:15s} | Buffer: {len(buffer)}/{BATCH_SIZE}")

            if len(buffer) >= BATCH_SIZE:
                save_batch()

    except KeyboardInterrupt:
        print(f"\n\n{'=' * 70}")
        print("Batch processor detenido")
        if buffer:
            print(f"Guardando último batch ({len(buffer)} registros)...")
            save_batch()
        print("=" * 70)
    finally:
        if buffer:
            save_batch()
        consumer.close()

if __name__ == "__main__":
    main()

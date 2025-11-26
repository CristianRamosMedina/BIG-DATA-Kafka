#!/usr/bin/env python3
"""
CONSUMER BATCH (HDFS VERSION)
Acumula datos cada hora y guarda en HDFS
Topic: weather-clean
Output: HDFS /kafka-clima/batch/
"""

import json
import csv
import os
from kafka import KafkaConsumer
from datetime import datetime
from collections import defaultdict
import time
from hdfs import InsecureClient
from io import StringIO

# Configuración
KAFKA_BROKER = 'localhost:9092'
TOPIC = 'weather-clean'
GROUP_ID = 'batch-processor-hdfs'
BATCH_INTERVAL = 3600  # 1 hora
HDFS_URL = 'http://localhost:9870'
HDFS_USER = 'ec2-user'
HDFS_BASE_PATH = '/kafka-clima/batch'

class HDFSBatchProcessor:
    """
    Procesador batch que guarda en HDFS
    """

    def __init__(self, hdfs_client, hdfs_path):
        self.buffer = []
        self.stats = defaultdict(lambda: {
            'temps': [],
            'humedades': [],
            'vientos': [],
            'precipitaciones': []
        })
        self.hdfs_client = hdfs_client
        self.hdfs_path = hdfs_path

        # Crear directorio en HDFS
        try:
            self.hdfs_client.makedirs(hdfs_path)
            print(f"✅ Directorio HDFS creado: {hdfs_path}")
        except Exception as e:
            print(f"ℹ️  Directorio HDFS ya existe o error: {e}")

    def add_message(self, mensaje):
        """Agrega mensaje al buffer"""
        self.buffer.append(mensaje)
        zona = mensaje['zona']

        datos = mensaje['datos']
        self.stats[zona]['temps'].append(datos['temperatura'])
        self.stats[zona]['humedades'].append(datos['humedad'])
        self.stats[zona]['vientos'].append(datos['viento'])
        self.stats[zona]['precipitaciones'].append(datos['precipitacion'])

    def calculate_stats(self):
        """Calcula estadísticas del batch"""
        resultado = {}

        for zona, data in self.stats.items():
            if data['temps']:
                resultado[zona] = {
                    'temperatura': {
                        'promedio': sum(data['temps']) / len(data['temps']),
                        'min': min(data['temps']),
                        'max': max(data['temps']),
                        'registros': len(data['temps'])
                    },
                    'humedad': {
                        'promedio': sum(data['humedades']) / len(data['humedades']),
                        'min': min(data['humedades']),
                        'max': max(data['humedades'])
                    },
                    'viento': {
                        'promedio': sum(data['vientos']) / len(data['vientos']),
                        'max': max(data['vientos'])
                    },
                    'precipitacion': {
                        'total': sum(data['precipitaciones']),
                        'max': max(data['precipitaciones'])
                    }
                }

        return resultado

    def save_batch_to_hdfs(self):
        """Guarda el batch en HDFS"""
        if not self.buffer:
            print("Buffer vacío, no se guarda nada")
            return

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # Crear CSV en memoria
        csv_buffer = StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=[
            'timestamp', 'zona', 'temperatura', 'humedad',
            'precipitacion', 'viento', 'direccion_viento', 'presion', 'codigo_clima'
        ])
        writer.writeheader()

        for msg in self.buffer:
            writer.writerow({
                'timestamp': msg['timestamp'],
                'zona': msg['zona'],
                'temperatura': msg['datos']['temperatura'],
                'humedad': msg['datos']['humedad'],
                'precipitacion': msg['datos']['precipitacion'],
                'viento': msg['datos']['viento'],
                'direccion_viento': msg['datos'].get('direccion_viento', 0),
                'presion': msg['datos']['presion'],
                'codigo_clima': msg['datos'].get('codigo_clima', 0)
            })

        # Guardar CSV en HDFS
        csv_filename = f"{self.hdfs_path}/batch_{timestamp}.csv"
        try:
            self.hdfs_client.write(csv_filename, csv_buffer.getvalue(), encoding='utf-8')
            print(f"\n{'=' * 80}")
            print(f"✅ BATCH GUARDADO EN HDFS: {csv_filename}")
            print(f"📊 Total registros: {len(self.buffer)}")
            print(f"{'=' * 80}")
        except Exception as e:
            print(f"❌ Error guardando en HDFS: {e}")
            return

        # Calcular y mostrar estadísticas
        stats = self.calculate_stats()

        for zona, stat in stats.items():
            print(f"\n{zona}:")
            print(f"  Temperatura: {stat['temperatura']['promedio']:.1f}°C "
                  f"(min: {stat['temperatura']['min']:.1f}, "
                  f"max: {stat['temperatura']['max']:.1f})")
            print(f"  Humedad: {stat['humedad']['promedio']:.1f}% "
                  f"(min: {stat['humedad']['min']:.0f}, "
                  f"max: {stat['humedad']['max']:.0f})")
            print(f"  Viento: {stat['viento']['promedio']:.1f} km/h "
                  f"(max: {stat['viento']['max']:.1f})")
            print(f"  Precipitación total: {stat['precipitacion']['total']:.1f} mm")
            print(f"  Registros: {stat['temperatura']['registros']}")

        print(f"\n{'=' * 80}\n")

        # Guardar estadísticas en HDFS (JSON)
        stats_filename = f"{self.hdfs_path}/stats_{timestamp}.json"
        try:
            self.hdfs_client.write(stats_filename, json.dumps(stats, indent=2), encoding='utf-8')
            print(f"✅ Estadísticas guardadas en HDFS: {stats_filename}\n")
        except Exception as e:
            print(f"❌ Error guardando estadísticas: {e}")

        # Limpiar buffer
        self.buffer = []
        self.stats = defaultdict(lambda: {
            'temps': [],
            'humedades': [],
            'vientos': [],
            'precipitaciones': []
        })


def main():
    print("=" * 80)
    print("CONSUMER BATCH (HDFS VERSION)")
    print("=" * 80)
    print(f"Topic: {TOPIC}")
    print(f"Group ID: {GROUP_ID}")
    print(f"Batch interval: {BATCH_INTERVAL} segundos ({BATCH_INTERVAL/60:.1f} minutos)")
    print(f"HDFS URL: {HDFS_URL}")
    print(f"HDFS Path: {HDFS_BASE_PATH}")
    print("=" * 80)

    # Conectar a HDFS
    try:
        hdfs_client = InsecureClient(HDFS_URL, user=HDFS_USER)
        print("✅ Conectado a HDFS")
    except Exception as e:
        print(f"❌ Error conectando a HDFS: {e}")
        print("Asegúrate de que HDFS esté corriendo en localhost:9870")
        return

    # Crear consumer Kafka
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        group_id=GROUP_ID,
        auto_offset_reset='latest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    processor = HDFSBatchProcessor(hdfs_client, HDFS_BASE_PATH)
    last_save = datetime.now()

    print(f"\n✅ Consumer iniciado. Esperando mensajes...\n")

    try:
        for message in consumer:
            data = message.value
            processor.add_message(data)

            zona = data['zona']
            temp = data['datos']['temperatura']

            print(f"[HDFS-BATCH] {zona:15s} | Temp: {temp:5.1f}°C | "
                  f"Buffer: {len(processor.buffer):3d} mensajes | "
                  f"Próximo guardado en: {BATCH_INTERVAL - (datetime.now() - last_save).seconds:4d}s")

            # Guardar batch cada BATCH_INTERVAL segundos
            if (datetime.now() - last_save).seconds >= BATCH_INTERVAL:
                processor.save_batch_to_hdfs()
                last_save = datetime.now()

    except KeyboardInterrupt:
        print("\n\nDeteniendo consumer...")
        if processor.buffer:
            print("Guardando datos pendientes en HDFS...")
            processor.save_batch_to_hdfs()

    finally:
        consumer.close()
        print("Consumer cerrado correctamente")
        print("=" * 80)


if __name__ == "__main__":
    main()

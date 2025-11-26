#!/usr/bin/env python3
"""
CONSUMER 5: AGREGACION
Calcula estadisticas agregadas por zona con ventanas temporales
Topic input: weather-clean
Topic output: weather-stats
"""

import json
import os
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics

# Configuracion
KAFKA_BROKER = 'localhost:9092'
TOPIC_INPUT = 'weather-clean'
TOPIC_OUTPUT = 'weather-stats'
GROUP_ID = 'aggregation-processor'
OUTPUT_DIR = '../data/aggregation'

# Ventanas temporales (en minutos)
VENTANAS = {
    '1h': 60,
    '6h': 360,
    '24h': 1440
}


class AggregationProcessor:
    """
    Procesador de agregaciones con ventanas temporales
    """

    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.ventanas = defaultdict(lambda: defaultdict(lambda: {
            'datos': deque(),
            'timestamps': deque()
        }))
        self.contador_mensajes = 0

        os.makedirs(output_dir, exist_ok=True)

    def agregar_dato(self, mensaje):
        """
        Agrega dato a las ventanas temporales
        """
        zona = mensaje['zona']
        timestamp = datetime.fromisoformat(mensaje['timestamp'].replace('Z', '+00:00'))
        datos = mensaje['datos']

        # Agregar a cada ventana
        for ventana_nombre in VENTANAS.keys():
            self.ventanas[ventana_nombre][zona]['datos'].append(datos)
            self.ventanas[ventana_nombre][zona]['timestamps'].append(timestamp)

        self.contador_mensajes += 1

    def limpiar_ventanas(self):
        """
        Elimina datos fuera de las ventanas temporales
        """
        ahora = datetime.now()

        for ventana_nombre, ventana_minutos in VENTANAS.items():
            limite = ahora - timedelta(minutes=ventana_minutos)

            for zona in self.ventanas[ventana_nombre].keys():
                datos = self.ventanas[ventana_nombre][zona]['datos']
                timestamps = self.ventanas[ventana_nombre][zona]['timestamps']

                # Eliminar datos antiguos
                while timestamps and timestamps[0] < limite:
                    timestamps.popleft()
                    datos.popleft()

    def calcular_estadisticas(self, zona, ventana_nombre):
        """
        Calcula estadisticas para una zona y ventana
        """
        datos_ventana = self.ventanas[ventana_nombre][zona]['datos']

        if not datos_ventana:
            return None

        # Extraer valores
        temps = [d['temperatura'] for d in datos_ventana]
        hums = [d['humedad'] for d in datos_ventana]
        vientos = [d['viento'] for d in datos_ventana]
        precips = [d['precipitacion'] for d in datos_ventana]

        estadisticas = {
            'zona': zona,
            'ventana': ventana_nombre,
            'periodo_minutos': VENTANAS[ventana_nombre],
            'registros': len(datos_ventana),
            'timestamp_calculo': datetime.now().isoformat(),
            'temperatura': {
                'min': round(min(temps), 1),
                'max': round(max(temps), 1),
                'avg': round(statistics.mean(temps), 1),
                'std': round(statistics.stdev(temps), 2) if len(temps) > 1 else 0
            },
            'humedad': {
                'min': round(min(hums), 0),
                'max': round(max(hums), 0),
                'avg': round(statistics.mean(hums), 1)
            },
            'viento': {
                'min': round(min(vientos), 1),
                'max': round(max(vientos), 1),
                'avg': round(statistics.mean(vientos), 1)
            },
            'precipitacion': {
                'total': round(sum(precips), 1),
                'max': round(max(precips), 1)
            }
        }

        return estadisticas

    def procesar_agregacion(self):
        """
        Procesa agregaciones para todas las zonas y ventanas
        """
        self.limpiar_ventanas()

        todas_stats = {}

        for ventana_nombre in VENTANAS.keys():
            todas_stats[ventana_nombre] = {}

            for zona in self.ventanas[ventana_nombre].keys():
                stats = self.calcular_estadisticas(zona, ventana_nombre)
                if stats:
                    todas_stats[ventana_nombre][zona] = stats

        return todas_stats

    def mostrar_estadisticas(self, todas_stats):
        """
        Muestra estadisticas en consola
        """
        print(f"\n{'=' * 80}")
        print(f"ESTADISTICAS AGREGADAS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 80}")
        print(f"Total mensajes procesados: {self.contador_mensajes}")
        print(f"{'=' * 80}")

        for ventana_nombre in ['1h', '6h', '24h']:
            if ventana_nombre not in todas_stats:
                continue

            print(f"\n--- VENTANA: {ventana_nombre} ({VENTANAS[ventana_nombre]} minutos) ---")

            for zona, stats in todas_stats[ventana_nombre].items():
                print(f"\n{zona}:")
                print(f"  Registros: {stats['registros']}")
                print(f"  Temperatura: {stats['temperatura']['avg']:.1f}°C "
                      f"(min: {stats['temperatura']['min']:.1f}, "
                      f"max: {stats['temperatura']['max']:.1f}, "
                      f"std: {stats['temperatura']['std']:.2f})")
                print(f"  Humedad: {stats['humedad']['avg']:.1f}% "
                      f"(min: {stats['humedad']['min']:.0f}, "
                      f"max: {stats['humedad']['max']:.0f})")
                print(f"  Viento: {stats['viento']['avg']:.1f} km/h "
                      f"(max: {stats['viento']['max']:.1f})")
                print(f"  Precipitacion total: {stats['precipitacion']['total']:.1f} mm")

        print(f"\n{'=' * 80}\n")

    def guardar_estadisticas(self, todas_stats):
        """
        Guarda estadisticas en JSON y envia a Kafka
        """
        # Guardar en archivo
        filename = os.path.join(self.output_dir, 'stats_current.json')

        with open(filename, 'w') as f:
            json.dump(todas_stats, f, indent=2)

        return todas_stats


def main():
    print("=" * 80)
    print("CONSUMER 5: AGREGACION Y ESTADISTICAS")
    print("=" * 80)
    print(f"Topic input: {TOPIC_INPUT}")
    print(f"Topic output: {TOPIC_OUTPUT}")
    print(f"Group ID: {GROUP_ID}")
    print(f"\nVentanas temporales:")
    for nombre, minutos in VENTANAS.items():
        print(f"  - {nombre}: {minutos} minutos ({minutos/60:.1f} horas)")
    print("=" * 80)

    # Crear consumer
    consumer = KafkaConsumer(
        TOPIC_INPUT,
        bootstrap_servers=[KAFKA_BROKER],
        group_id=GROUP_ID,
        auto_offset_reset='latest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    # Crear producer para stats
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None
    )

    processor = AggregationProcessor(OUTPUT_DIR)

    print("\nProcesador de agregacion iniciado...\n")

    contador_display = 0

    try:
        for message in consumer:
            data = message.value

            # Agregar dato a ventanas
            processor.agregar_dato(data)

            zona = data['zona']
            temp = data['datos']['temperatura']

            print(f"[AGG] {zona:15s} | Temp: {temp:5.1f}°C | "
                  f"Total procesados: {processor.contador_mensajes:4d}")

            contador_display += 1

            # Calcular y mostrar estadisticas cada 10 mensajes
            if contador_display % 10 == 0:
                todas_stats = processor.procesar_agregacion()
                processor.mostrar_estadisticas(todas_stats)
                processor.guardar_estadisticas(todas_stats)

                # Enviar a topic de stats
                for ventana_nombre, zonas_stats in todas_stats.items():
                    for zona, stats in zonas_stats.items():
                        producer.send(TOPIC_OUTPUT, key=zona, value=stats)

                producer.flush()

    except KeyboardInterrupt:
        print("\n\nDeteniendo consumer...")
        todas_stats = processor.procesar_agregacion()
        processor.mostrar_estadisticas(todas_stats)
        processor.guardar_estadisticas(todas_stats)

    finally:
        consumer.close()
        producer.close()
        print("Consumer cerrado correctamente")


if __name__ == "__main__":
    main()

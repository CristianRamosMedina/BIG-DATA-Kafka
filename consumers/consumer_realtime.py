#!/usr/bin/env python3
"""
CONSUMER 2: REAL-TIME PROCESSING
Procesa datos al instante y mantiene estado actualizado
Topic: weather-clean
Output: JSON en /data/realtime/current.json
"""

import json
import os
from kafka import KafkaConsumer
from datetime import datetime
from collections import deque

# Configuracion
KAFKA_BROKER = 'localhost:9092'
TOPIC = 'weather-clean'
GROUP_ID = 'realtime-processor'
MAX_HISTORY = 10  # Ultimas N lecturas por zona
OUTPUT_DIR = '../data/realtime'


class RealtimeProcessor:
    """
    Procesador en tiempo real
    """

    def __init__(self, output_dir):
        self.history = {}
        self.output_dir = output_dir
        self.total_messages = 0

        # Crear directorio
        os.makedirs(output_dir, exist_ok=True)

    def process_message(self, mensaje):
        """
        Procesa mensaje en tiempo real
        """
        zona = mensaje['zona']

        # Mantener historial limitado
        if zona not in self.history:
            self.history[zona] = deque(maxlen=MAX_HISTORY)

        self.history[zona].append({
            'timestamp': mensaje['timestamp'],
            'temperatura': mensaje['datos']['temperatura'],
            'humedad': mensaje['datos']['humedad'],
            'viento': mensaje['datos']['viento'],
            'precipitacion': mensaje['datos']['precipitacion'],
            'presion': mensaje['datos']['presion']
        })

        self.total_messages += 1

    def get_current_state(self):
        """
        Obtiene estado actual de todas las zonas
        """
        state = {}

        for zona, lecturas in self.history.items():
            if lecturas:
                ultima = lecturas[-1]

                # Calcular tendencia si hay historial
                tendencia = "→"
                if len(lecturas) >= 2:
                    diff = lecturas[-1]['temperatura'] - lecturas[-2]['temperatura']
                    if diff > 0.1:
                        tendencia = f"↑ +{diff:.1f}°C"
                    elif diff < -0.1:
                        tendencia = f"↓ {diff:.1f}°C"

                state[zona] = {
                    'actual': {
                        'temperatura': ultima['temperatura'],
                        'humedad': ultima['humedad'],
                        'viento': ultima['viento'],
                        'precipitacion': ultima['precipitacion'],
                        'presion': ultima['presion']
                    },
                    'timestamp': ultima['timestamp'],
                    'tendencia': tendencia,
                    'historial_size': len(lecturas)
                }

        return state

    def save_state(self):
        """
        Guarda estado actual en JSON
        """
        state = {
            'timestamp_update': datetime.now().isoformat(),
            'total_messages': self.total_messages,
            'zonas': self.get_current_state()
        }

        filename = os.path.join(self.output_dir, 'current.json')

        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)

    def display_current(self):
        """
        Muestra estado actual en consola
        """
        os.system('cls' if os.name == 'nt' else 'clear')

        print("=" * 80)
        print("CONSUMER 2: REAL-TIME DASHBOARD")
        print("=" * 80)
        print(f"Actualizacion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total mensajes procesados: {self.total_messages}")
        print("=" * 80)

        state = self.get_current_state()

        for zona, data in state.items():
            actual = data['actual']
            print(f"\n{zona}:")
            print(f"  Temperatura:    {actual['temperatura']:6.1f}°C  {data['tendencia']}")
            print(f"  Humedad:        {actual['humedad']:6.0f}%")
            print(f"  Viento:         {actual['viento']:6.1f} km/h")
            print(f"  Precipitacion:  {actual['precipitacion']:6.1f} mm")
            print(f"  Presion:        {actual['presion']:6.1f} hPa")
            print(f"  Ultima act:     {data['timestamp'][-8:]}")
            print(f"  Historial:      {data['historial_size']} registros")

        print("\n" + "=" * 80)
        print("Esperando nuevos mensajes... (Ctrl+C para salir)")
        print("=" * 80)


def main():
    print("Iniciando CONSUMER 2: REAL-TIME...")

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        group_id=GROUP_ID,
        auto_offset_reset='latest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    processor = RealtimeProcessor(OUTPUT_DIR)

    print("Consumer iniciado\n")

    try:
        for message in consumer:
            data = message.value
            processor.process_message(data)
            processor.save_state()
            processor.display_current()

    except KeyboardInterrupt:
        print("\n\nDeteniendo consumer...")

    finally:
        processor.save_state()
        consumer.close()
        print("Consumer cerrado correctamente")


if __name__ == "__main__":
    main()

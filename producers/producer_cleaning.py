#!/usr/bin/env python3
"""
PRODUCER CLEANING - Validación y limpieza de datos
Consumer-Producer híbrido
"""
import json
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime

KAFKA_BROKER = 'localhost:9092'
TOPIC_INPUT = 'weather-raw'
TOPIC_OUTPUT = 'weather-clean'
GROUP_ID = 'cleaning-processor'

def main():
    print("=" * 70)
    print("PRODUCER CLEANING - VALIDACIÓN DE DATOS")
    print("=" * 70)

    consumer = KafkaConsumer(
        TOPIC_INPUT,
        bootstrap_servers=[KAFKA_BROKER],
        group_id=GROUP_ID,
        auto_offset_reset='latest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=30000  # Termina si no hay mensajes por 30s
    )

    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None,
        acks='all'
    )

    print("Esperando mensajes para limpiar...")
    print("Presiona Ctrl+C para detener")
    print("=" * 70)

    contador_ok = 0
    contador_rechazado = 0

    try:
        for message in consumer:
            mensaje = message.value

            # Validar datos básicos
            if 'datos' in mensaje and 'zona' in mensaje:
                datos = mensaje['datos']

                # Validar rangos
                temp_ok = -10 <= datos.get('temperatura', 0) <= 45
                hum_ok = 0 <= datos.get('humedad', 0) <= 100

                if temp_ok and hum_ok:
                    # Agregar metadata de limpieza
                    mensaje['metadata'] = mensaje.get('metadata', {})
                    mensaje['metadata']['limpieza'] = {
                        'validado': True,
                        'timestamp': datetime.now().isoformat()
                    }

                    # Enviar a topic limpio
                    producer.send(TOPIC_OUTPUT, key=mensaje['zona'], value=mensaje)
                    contador_ok += 1
                    print(f"[OK] {mensaje['zona']:15s} | Temp: {datos['temperatura']:5.1f}°C | Total: {contador_ok}")
                else:
                    contador_rechazado += 1
                    print(f"[X] {mensaje.get('zona', 'unknown'):15s} | Datos fuera de rango (rechazado)")

    except KeyboardInterrupt:
        print(f"\n\n{'=' * 70}")
        print(f"Limpieza detenida")
        print(f"Mensajes validados: {contador_ok}")
        print(f"Mensajes rechazados: {contador_rechazado}")
        print("=" * 70)
    finally:
        producer.close()
        consumer.close()

if __name__ == "__main__":
    main()

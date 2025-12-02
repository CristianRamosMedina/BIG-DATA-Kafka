#!/usr/bin/env python3
"""
CONSUMER ALERTS - Sistema de alertas climáticas
Detecta anomalías y guarda en archivos locales
"""
import json
import os
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime
 
KAFKA_BROKERS = ['localhost:9092', 'localhost:9093', 'localhost:9094']
TOPIC_INPUT = 'weather-clean'
TOPIC_OUTPUT = 'weather-alerts'
GROUP_ID = 'alert-processor'
OUTPUT_DIR = '../data/alerts'

UMBRALES = {
    'temperatura_alta': 30,
    'temperatura_baja': 12,
    'humedad_alta': 95,
    'viento_fuerte': 40
}

alertas_generadas = []

def main():
    print("=" * 70)
    print("CONSUMER ALERTS - SISTEMA DE ALERTAS")
    print("=" * 70)
    print("Umbrales:")
    print(f"  Temperatura alta: > {UMBRALES['temperatura_alta']}°C")
    print(f"  Temperatura baja: < {UMBRALES['temperatura_baja']}°C")
    print(f"  Humedad alta: > {UMBRALES['humedad_alta']}%")
    print(f"  Viento fuerte: > {UMBRALES['viento_fuerte']} km/h")
    print("=" * 70)

    consumer = KafkaConsumer(
        TOPIC_INPUT,
        bootstrap_servers=KAFKA_BROKERS,
        group_id=GROUP_ID,
        auto_offset_reset='earliest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=30000
    )

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None
    )

    try:
        for message in consumer:
            data = message.value
            zona = data['zona']
            datos = data['datos']
            alertas = []

            if datos['temperatura'] > UMBRALES['temperatura_alta']:
                alertas.append({'tipo': 'CALOR_EXTREMO', 'valor': datos['temperatura']})
            if datos['temperatura'] < UMBRALES['temperatura_baja']:
                alertas.append({'tipo': 'FRIO_EXTREMO', 'valor': datos['temperatura']})
            if datos['humedad'] > UMBRALES['humedad_alta']:
                alertas.append({'tipo': 'HUMEDAD_ALTA', 'valor': datos['humedad']})
            if datos['viento'] > UMBRALES['viento_fuerte']:
                alertas.append({'tipo': 'VIENTO_FUERTE', 'valor': datos['viento']})

            if alertas:
                alerta = {
                    'timestamp': datetime.now().isoformat(),
                    'zona': zona,
                    'alertas': alertas,
                    'datos': datos
                }
                alertas_generadas.append(alerta)
                producer.send(TOPIC_OUTPUT, key=zona, value=alerta)
                print(f"[ALERT] {zona:15s} | {len(alertas)} alertas: {[a['tipo'] for a in alertas]}")
            else:
                print(f"[OK] {zona:15s} | {datos['temperatura']:5.1f}°C - Sin alertas")

    except KeyboardInterrupt:
        print(f"\n\n{'=' * 70}")
        print(f"Alerts processor detenido")
        print(f"Total alertas generadas: {len(alertas_generadas)}")
        print("=" * 70)
    finally:
        # Guardar resumen
        if alertas_generadas:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            output_file = os.path.join(OUTPUT_DIR, 'summary.json')

            with open(output_file, 'w') as f:
                json.dump({
                    'total': len(alertas_generadas),
                    'alertas': alertas_generadas
                }, f, indent=2)

            print(f"Resumen guardado: {output_file}")

        consumer.close()
        producer.close()

if __name__ == "__main__":
    main()

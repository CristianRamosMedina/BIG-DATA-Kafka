#!/usr/bin/env python3
"""
CONSUMER - PREDICTOR DE LLUVIA (Modelo Simple)
Predice probabilidad de lluvia basado en:
- Humedad alta (>80%)
- Presión baja (<1010 hPa)
- Precipitación actual
"""
import json
import os
from kafka import KafkaConsumer
from datetime import datetime

KAFKA_BROKER = 'localhost:9092'
TOPIC = 'weather-clean'
GROUP_ID = 'predictor-lluvia'
OUTPUT_DIR = '../data/predictions'

def predecir_lluvia(datos):
    """Modelo simple de predicción de lluvia"""
    temp = datos['temperatura']
    humedad = datos['humedad']
    precipitacion = datos['precipitacion']
    presion = datos['presion']

    # Probabilidad base
    prob_lluvia = 0.0

    # Regla 1: Ya está lloviendo
    if precipitacion > 0.1:
        prob_lluvia = 90.0

    # Regla 2: Condiciones favorables para lluvia
    elif humedad > 85 and presion < 1010:
        prob_lluvia = 70.0
    elif humedad > 80 and presion < 1012:
        prob_lluvia = 50.0
    elif humedad > 75:
        prob_lluvia = 30.0
    elif humedad > 70:
        prob_lluvia = 15.0
    else:
        prob_lluvia = 5.0

    # Clasificación
    if prob_lluvia >= 70:
        clasificacion = "Alta probabilidad de lluvia"
    elif prob_lluvia >= 40:
        clasificacion = "Probabilidad moderada de lluvia"
    elif prob_lluvia >= 20:
        clasificacion = "Baja probabilidad de lluvia"
    else:
        clasificacion = "No se espera lluvia"

    return {
        'probabilidad': round(prob_lluvia, 1),
        'clasificacion': clasificacion,
        'factores': {
            'humedad': humedad,
            'presion': presion,
            'precipitacion_actual': precipitacion
        }
    }

def guardar_prediccion(zona, timestamp, datos, prediccion):
    """Guarda predicción en archivo JSON"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    archivo = os.path.join(OUTPUT_DIR, 'lluvia_predictions.json')

    registro = {
        'zona': zona,
        'timestamp': timestamp,
        'datos': datos,
        'prediccion': prediccion
    }

    # Leer predicciones existentes
    predicciones = []
    if os.path.exists(archivo):
        with open(archivo, 'r') as f:
            predicciones = json.load(f)

    # Agregar nueva predicción
    predicciones.append(registro)

    # Mantener solo las últimas 100 predicciones
    if len(predicciones) > 100:
        predicciones = predicciones[-100:]

    # Guardar
    with open(archivo, 'w') as f:
        json.dump(predicciones, f, indent=2)

def main():
    print("=" * 70)
    print("PREDICTOR DE LLUVIA - Modelo Simple")
    print("=" * 70)
    print("Consumiendo datos de:", TOPIC)
    print("Presiona Ctrl+C para detener")
    print("=" * 70)

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        group_id=GROUP_ID,
        auto_offset_reset='latest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    try:
        for message in consumer:
            data = message.value
            zona = data['zona']
            timestamp = data['timestamp']
            datos = data['datos']

            # Hacer predicción
            prediccion = predecir_lluvia(datos)

            # Guardar
            guardar_prediccion(zona, timestamp, datos, prediccion)

            # Mostrar
            prob = prediccion['probabilidad']
            clasif = prediccion['clasificacion']

            # Indicador simple en lugar de emoji
            indicador = "[ALTA]" if prob >= 70 else "[MED]" if prob >= 40 else "[BAJA]"

            print(f"{indicador} {zona:15s} | Prob: {prob:5.1f}% | {clasif}")

    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("Predictor de lluvia detenido")
        print("=" * 70)
    finally:
        consumer.close()

if __name__ == "__main__":
    main()

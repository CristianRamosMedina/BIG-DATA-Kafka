#!/usr/bin/env python3
"""
CONSUMER - PREDICTOR DE DÍA SOLEADO (Modelo Simple)
Predice día soleado basado en:
- Humedad baja (<60%)
- Presión alta (>1013 hPa)
- Sin precipitación
- Temperatura agradable
"""
import json
import os
from kafka import KafkaConsumer
from datetime import datetime

KAFKA_BROKERS = ['localhost:9092', 'localhost:9093', 'localhost:9094']
TOPIC = 'weather-clean'
GROUP_ID = 'predictor-sol'
OUTPUT_DIR = '../data/predictions'

def predecir_sol(datos):
    """Modelo simple de predicción de día soleado"""
    temp = datos['temperatura']
    humedad = datos['humedad']
    precipitacion = datos['precipitacion']
    presion = datos['presion']
    viento = datos['viento']

    # Probabilidad base
    prob_sol = 0.0

    # Regla 1: Sin precipitación
    if precipitacion > 0:
        prob_sol = 0.0
        clasificacion = "No soleado - Hay precipitación"
    else:
        # Regla 2: Condiciones ideales para sol
        if humedad < 50 and presion > 1015:
            prob_sol = 90.0
        elif humedad < 60 and presion > 1013:
            prob_sol = 75.0
        elif humedad < 70 and presion > 1012:
            prob_sol = 55.0
        elif humedad < 75:
            prob_sol = 35.0
        else:
            prob_sol = 10.0

        # Ajustar por viento (viento moderado puede despejar nubes)
        if 10 < viento < 20:
            prob_sol += 5.0

        # Clasificación
        if prob_sol >= 75:
            clasificacion = "Día muy soleado"
        elif prob_sol >= 50:
            clasificacion = "Parcialmente soleado"
        elif prob_sol >= 30:
            clasificacion = "Poco sol, algo nublado"
        else:
            clasificacion = "Mayormente nublado"

    return {
        'probabilidad': round(min(prob_sol, 100), 1),
        'clasificacion': clasificacion,
        'factores': {
            'humedad': humedad,
            'presion': presion,
            'precipitacion': precipitacion,
            'viento': viento
        }
    }

def guardar_prediccion(zona, timestamp, datos, prediccion):
    """Guarda predicción en archivo JSON"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    archivo = os.path.join(OUTPUT_DIR, 'sol_predictions.json')

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
    print("PREDICTOR DE SOL - Modelo Simple")
    print("=" * 70)
    print("Consumiendo datos de:", TOPIC)
    print("Presiona Ctrl+C para detener")
    print("=" * 70)

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKERS,
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
            prediccion = predecir_sol(datos)

            # Guardar
            guardar_prediccion(zona, timestamp, datos, prediccion)

            # Mostrar
            prob = prediccion['probabilidad']
            clasif = prediccion['clasificacion']

            # Indicador simple en lugar de emoji
            indicador = "[SOL]" if prob >= 75 else "[PCIAL]" if prob >= 50 else "[NUBLADO]"

            print(f"{indicador} {zona:15s} | Prob: {prob:5.1f}% | {clasif}")

    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("Predictor de sol detenido")
        print("=" * 70)
    finally:
        consumer.close()

if __name__ == "__main__":
    main()

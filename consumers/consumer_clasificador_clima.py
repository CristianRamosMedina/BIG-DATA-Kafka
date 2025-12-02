#!/usr/bin/env python3
"""
CONSUMER - CLASIFICADOR GENERAL DE CLIMA (Modelo Simple)
Clasifica el clima en categorías:
- Soleado
- Parcialmente nublado
- Nublado
- Lluvioso
- Tormenta
"""
import json
import os
from kafka import KafkaConsumer
from datetime import datetime
 
KAFKA_BROKERS = ['localhost:9092', 'localhost:9093', 'localhost:9094']
TOPIC = 'weather-clean'
GROUP_ID = 'clasificador-clima'
OUTPUT_DIR = '../data/predictions'

def clasificar_clima(datos):
    """Modelo simple de clasificación de clima"""
    temp = datos['temperatura']
    humedad = datos['humedad']
    precipitacion = datos['precipitacion']
    presion = datos['presion']
    viento = datos['viento']

    # Variables de decisión
    clasificacion = ""
    confianza = 0.0
    detalles = []

    # Árbol de decisión simple
    if precipitacion > 5.0:
        clasificacion = "Tormenta"
        confianza = 95.0
        detalles.append("Precipitación muy alta")

        if viento > 30:
            detalles.append("Vientos fuertes")
            confianza = 98.0

    elif precipitacion > 0.5:
        clasificacion = "Lluvioso"
        confianza = 90.0
        detalles.append("Lluvia activa")

    elif precipitacion > 0.1:
        clasificacion = "Llovizna"
        confianza = 85.0
        detalles.append("Lluvia ligera")

    elif humedad > 85:
        clasificacion = "Nublado"
        confianza = 75.0
        detalles.append("Alta humedad")

        if presion < 1010:
            detalles.append("Presión baja - posible lluvia próxima")
            confianza = 80.0

    elif humedad > 70:
        clasificacion = "Parcialmente nublado"
        confianza = 70.0
        detalles.append("Humedad moderada")

        if presion > 1015:
            detalles.append("Presión alta - puede despejar")
            clasificacion = "Mayormente soleado"

    else:
        clasificacion = "Soleado"
        confianza = 85.0
        detalles.append("Baja humedad")

        if presion > 1015:
            detalles.append("Excelentes condiciones")
            confianza = 92.0

    # Información adicional sobre temperatura
    if temp < 15:
        detalles.append("Frío")
    elif temp > 25:
        detalles.append("Cálido")
    else:
        detalles.append("Temperatura agradable")

    # Información sobre viento
    if viento > 25:
        detalles.append("Viento fuerte")
    elif viento > 15:
        detalles.append("Viento moderado")

    return {
        'clasificacion': clasificacion,
        'confianza': round(confianza, 1),
        'detalles': detalles,
        'condiciones': {
            'temperatura': temp,
            'humedad': humedad,
            'precipitacion': precipitacion,
            'presion': presion,
            'viento': viento
        }
    }

def guardar_prediccion(zona, timestamp, datos, prediccion):
    """Guarda predicción en archivo JSON"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    archivo = os.path.join(OUTPUT_DIR, 'clasificacion_predictions.json')

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
    print("CLASIFICADOR DE CLIMA - Modelo Simple")
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

            # Hacer clasificación
            prediccion = clasificar_clima(datos)

            # Guardar
            guardar_prediccion(zona, timestamp, datos, prediccion)

            # Mostrar
            clasif = prediccion['clasificacion']
            conf = prediccion['confianza']
            detalles_str = ", ".join(prediccion['detalles'][:2])

            # Indicador simple
            print(f"[CLIMA] {zona:15s} | {clasif:20s} | Conf: {conf:5.1f}% | {detalles_str}")

    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("Clasificador de clima detenido")
        print("=" * 70)
    finally:
        consumer.close()

if __name__ == "__main__":
    main()

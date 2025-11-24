#!/usr/bin/env python3
"""
CONSUMER - PREDICCIONES CONSOLIDADAS POR ZONA
Consolida las 3 predicciones (lluvia, sol, clasificación) en un solo archivo
para mostrar en el dashboard
"""
import json
import os
from kafka import KafkaConsumer
from datetime import datetime
from collections import defaultdict

KAFKA_BROKER = 'localhost:9092'
TOPIC = 'weather-clean'
GROUP_ID = 'predicciones-consolidadas'
OUTPUT_DIR = '../data/predictions'

# Buffer para agrupar predicciones por zona
buffer_zonas = defaultdict(lambda: {
    'timestamp': None,
    'datos': {},
    'predicciones': {}
})

def calcular_probabilidad_lluvia(datos):
    """Calcula probabilidad de lluvia"""
    humedad = datos['humedad']
    precipitacion = datos['precipitacion']
    presion = datos['presion']

    if precipitacion > 0.1:
        return 90.0
    elif humedad > 85 and presion < 1010:
        return 70.0
    elif humedad > 80 and presion < 1012:
        return 50.0
    elif humedad > 75:
        return 30.0
    elif humedad > 70:
        return 15.0
    else:
        return 5.0

def calcular_probabilidad_sol(datos):
    """Calcula probabilidad de sol"""
    humedad = datos['humedad']
    precipitacion = datos['precipitacion']
    presion = datos['presion']
    viento = datos['viento']

    if precipitacion > 0:
        return 0.0

    prob_sol = 0.0
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

    # Ajuste por viento
    if 10 < viento < 20:
        prob_sol += 5.0

    return min(prob_sol, 100)

def calcular_probabilidad_nublado(datos):
    """Calcula probabilidad de nublado (lo que no es sol ni lluvia)"""
    humedad = datos['humedad']
    precipitacion = datos['precipitacion']

    if precipitacion > 0.1:
        return 10.0  # Si llueve, poco nublado
    elif humedad > 85:
        return 85.0
    elif humedad > 75:
        return 70.0
    elif humedad > 65:
        return 50.0
    elif humedad > 55:
        return 30.0
    else:
        return 15.0

def clasificar_clima(datos):
    """Clasificación general del clima"""
    temp = datos['temperatura']
    humedad = datos['humedad']
    precipitacion = datos['precipitacion']
    presion = datos['presion']
    viento = datos['viento']

    if precipitacion > 5.0:
        return "Tormenta", 95.0
    elif precipitacion > 0.5:
        return "Lluvioso", 90.0
    elif precipitacion > 0.1:
        return "Llovizna", 85.0
    elif humedad > 85:
        return "Nublado", 75.0
    elif humedad > 70:
        return "Parcialmente nublado", 70.0
    else:
        return "Soleado", 85.0

def guardar_predicciones_consolidadas():
    """Guarda todas las predicciones consolidadas por zona"""
    if not buffer_zonas:
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    archivo = os.path.join(OUTPUT_DIR, 'predicciones_por_zona.json')

    # Preparar datos para guardar
    predicciones = {}

    for zona, info in buffer_zonas.items():
        if info['timestamp']:
            predicciones[zona] = {
                'timestamp': info['timestamp'],
                'datos_actuales': info['datos'],
                'predicciones': {
                    'probabilidad_lluvia': info['predicciones'].get('lluvia', 0),
                    'probabilidad_sol': info['predicciones'].get('sol', 0),
                    'probabilidad_nublado': info['predicciones'].get('nublado', 0),
                    'clasificacion': info['predicciones'].get('clasificacion', 'Desconocido'),
                    'confianza': info['predicciones'].get('confianza', 0)
                }
            }

    # Guardar
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(predicciones, f, indent=2, ensure_ascii=False)

def main():
    print("=" * 70)
    print("PREDICCIONES CONSOLIDADAS POR ZONA")
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

    contador_mensajes = 0

    try:
        for message in consumer:
            data = message.value
            zona = data['zona']
            timestamp = data['timestamp']
            datos = data['datos']

            # Calcular las 3 probabilidades
            prob_lluvia = calcular_probabilidad_lluvia(datos)
            prob_sol = calcular_probabilidad_sol(datos)
            prob_nublado = calcular_probabilidad_nublado(datos)
            clasificacion, confianza = clasificar_clima(datos)

            # Actualizar buffer de la zona
            buffer_zonas[zona]['timestamp'] = timestamp
            buffer_zonas[zona]['datos'] = datos
            buffer_zonas[zona]['predicciones'] = {
                'lluvia': round(prob_lluvia, 1),
                'sol': round(prob_sol, 1),
                'nublado': round(prob_nublado, 1),
                'clasificacion': clasificacion,
                'confianza': round(confianza, 1)
            }

            contador_mensajes += 1

            # Guardar cada 6 mensajes (todas las zonas)
            if contador_mensajes % 6 == 0:
                guardar_predicciones_consolidadas()
                print(f"\n[ACTUALIZADO] Predicciones guardadas - {len(buffer_zonas)} zonas")

                # Mostrar resumen
                for z, info in sorted(buffer_zonas.items()):
                    preds = info['predicciones']
                    print(f"  {z:15s} | Lluvia: {preds['lluvia']:5.1f}% | "
                          f"Sol: {preds['sol']:5.1f}% | Nublado: {preds['nublado']:5.1f}% | "
                          f"{preds['clasificacion']}")

    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("Predicciones consolidadas detenidas")
        guardar_predicciones_consolidadas()
        print("=" * 70)
    finally:
        guardar_predicciones_consolidadas()
        consumer.close()

if __name__ == "__main__":
    main()

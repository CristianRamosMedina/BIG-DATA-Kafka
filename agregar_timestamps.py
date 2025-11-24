#!/usr/bin/env python3
"""
Script para agregar timestamps sintéticos al último archivo batch
"""
import json
import os
import glob
from datetime import datetime, timedelta

BATCH_DIR = 'data/batch'

def agregar_timestamps_al_ultimo_batch():
    """Agrega timestamps sintéticos al archivo batch más reciente"""

    # Obtener el archivo más reciente
    archivos = glob.glob(os.path.join(BATCH_DIR, 'stats_*.json'))
    if not archivos:
        print("No hay archivos batch disponibles")
        return

    archivo_reciente = max(archivos, key=os.path.getmtime)
    print(f"Procesando: {archivo_reciente}")

    # Leer el archivo
    with open(archivo_reciente, 'r') as f:
        datos = json.load(f)

    # Extraer timestamp del nombre del archivo
    # Formato: stats_20251124_170536.json
    nombre = os.path.basename(archivo_reciente)
    timestamp_str = nombre.replace('stats_', '').replace('.json', '')
    # timestamp_str es como: 20251124_170536
    fecha_hora = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')

    print(f"Fecha/hora del batch: {fecha_hora}")

    # Para cada zona, agregar timestamps sintéticos
    for zona, stats in datos.items():
        num_registros = stats['registros']

        # Calcular timestamps retroactivos (cada 10 segundos)
        # El último registro es en el momento del batch
        registros_detalle = []

        for i in range(num_registros):
            # Timestamp retroactivo: restar 10 segundos por cada registro anterior
            segundos_atras = (num_registros - 1 - i) * 10
            timestamp_registro = fecha_hora - timedelta(seconds=segundos_atras)

            # Generar valores sintéticos dentro del rango conocido
            # Distribución lineal entre min y max
            temp_range = stats['temp_max'] - stats['temp_min']
            temp_value = stats['temp_min'] + (temp_range * i / max(1, num_registros - 1))

            registros_detalle.append({
                'timestamp': timestamp_registro.isoformat(),
                'temperatura': round(temp_value, 1),
                'humedad': round(stats['humedad_avg'], 0),
                'viento': round(stats['viento_avg'], 1),
                'presion': 1013.0  # Valor por defecto
            })

        # Agregar los registros detallados
        datos[zona]['registros_detalle'] = registros_detalle

        print(f"  {zona}: {num_registros} registros con timestamps")

    # Guardar el archivo actualizado
    with open(archivo_reciente, 'w') as f:
        json.dump(datos, f, indent=2)

    print(f"\n✅ Archivo actualizado con timestamps sintéticos!")
    print(f"Archivo: {archivo_reciente}")
    print(f"\nAhora recarga el dashboard para ver los timestamps")

if __name__ == "__main__":
    agregar_timestamps_al_ultimo_batch()

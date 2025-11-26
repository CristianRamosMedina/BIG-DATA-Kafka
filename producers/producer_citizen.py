#!/usr/bin/env python3
"""
PRODUCER 3: CITIZEN REPORTS
Recibe reportes de clima enviados por ciudadanos en tiempo real
Topic destino: weather-citizen-reports
"""

from flask import Flask, request, jsonify
from kafka import KafkaProducer
import json
import os
from datetime import datetime

# Configuración
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
TOPIC = 'weather-citizen-reports'
PORT = 5000

app = Flask(__name__)

# Producer global (se inicializa en la primera petición)
producer = None

def get_producer():
    """Obtener o crear producer Kafka (lazy initialization con error handling)"""
    global producer
    if producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                request_timeout_ms=10000,
                api_version_auto_timeout_ms=5000
            )
            print(f"[✓] Producer Kafka conectado a {KAFKA_BROKER}")
        except Exception as e:
            print(f"[X] Error conectando a Kafka: {e}")
            raise
    return producer

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "citizen-reports-producer"}), 200

@app.route('/report', methods=['POST'])
def submit_report():
    """
    Endpoint para recibir reportes de ciudadanos
    
    Ejemplo de request:
    {
        "nombre": "Juan Perez",
        "ubicacion": "Lima Centro",
        "lat": -12.046,
        "lon": -77.043,
        "condicion": "Nublado",
        "temperatura_percibida": "Frio",
        "comentario": "Mucha neblina en la costa"
    }
    """
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['nombre', 'ubicacion', 'lat', 'lon', 'condicion']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Campo requerido: {field}"}), 400
        
        # Crear mensaje para Kafka
        mensaje = {
            'timestamp': datetime.now().isoformat(),
            'tipo': 'reporte_ciudadano',
            'ciudadano': {
                'nombre': data['nombre'],
                'ubicacion': data['ubicacion']
            },
            'coordenadas': {
                'lat': float(data['lat']),
                'lon': float(data['lon'])
            },
            'reporte': {
                'condicion': data['condicion'],
                'temperatura_percibida': data.get('temperatura_percibida', 'No especificado'),
                'comentario': data.get('comentario', '')
            },
            'metadata': {
                'fuente': 'Reporte Ciudadano',
                'ip': request.remote_addr
            }
        }
        
        # Enviar a Kafka
        future = get_producer().send(TOPIC, value=mensaje)
        record_metadata = future.get(timeout=10)
        
        print(f"[✓] Reporte recibido de {data['nombre']} en {data['ubicacion']}")
        print(f"    Condición: {data['condicion']}")
        print(f"    Partition: {record_metadata.partition}, Offset: {record_metadata.offset}")
        
        return jsonify({
            "status": "success",
            "message": "Reporte enviado exitosamente",
            "timestamp": mensaje['timestamp']
        }), 201
        
    except Exception as e:
        print(f"[X] Error procesando reporte: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/report/batch', methods=['POST'])
def submit_batch_reports():
    """
    Endpoint para recibir múltiples reportes
    
    Ejemplo:
    {
        "reportes": [
            {...},
            {...}
        ]
    }
    """
    try:
        data = request.get_json()
        reportes = data.get('reportes', [])
        
        if not reportes:
            return jsonify({"error": "No se enviaron reportes"}), 400
        
        enviados = 0
        errores = []
        
        for idx, reporte in enumerate(reportes):
            try:
                # Validar y enviar cada reporte
                mensaje = {
                    'timestamp': datetime.now().isoformat(),
                    'tipo': 'reporte_ciudadano',
                    'ciudadano': {
                        'nombre': reporte.get('nombre', 'Anónimo'),
                        'ubicacion': reporte.get('ubicacion', 'Desconocido')
                    },
                    'coordenadas': {
                        'lat': float(reporte['lat']),
                        'lon': float(reporte['lon'])
                    },
                    'reporte': {
                        'condicion': reporte['condicion'],
                        'temperatura_percibida': reporte.get('temperatura_percibida', 'No especificado'),
                        'comentario': reporte.get('comentario', '')
                    },
                    'metadata': {
                        'fuente': 'Reporte Ciudadano (Batch)',
                        'batch_index': idx
                    }
                }
                
                get_producer().send(TOPIC, value=mensaje)
                enviados += 1
                
            except Exception as e:
                errores.append(f"Reporte {idx}: {str(e)}")
        
        get_producer().flush()
        
        return jsonify({
            "status": "success",
            "enviados": enviados,
            "total": len(reportes),
            "errores": errores
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("=" * 80)
    print("PRODUCER 3: CITIZEN REPORTS - API de Reportes Ciudadanos")
    print("=" * 80)
    print(f"Kafka Broker: {KAFKA_BROKER}")
    print(f"Topic: {TOPIC}")
    print(f"Puerto: {PORT}")
    print("=" * 80)
    print("\nEndpoints disponibles:")
    print(f"  POST http://localhost:{PORT}/report        - Enviar un reporte")
    print(f"  POST http://localhost:{PORT}/report/batch  - Enviar múltiples reportes")
    print(f"  GET  http://localhost:{PORT}/health        - Health check")
    print("\nEjemplo de uso:")
    print(f"""
    curl -X POST http://localhost:{PORT}/report \\
      -H "Content-Type: application/json" \\
      -d '{{
        "nombre": "Juan Perez",
        "ubicacion": "Lima Centro",
        "lat": -12.046,
        "lon": -77.043,
        "condicion": "Nublado",
        "temperatura_percibida": "Frio",
        "comentario": "Mucha neblina"
      }}'
    """)
    print("=" * 80)
    print("\nIniciando servidor Flask...")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)

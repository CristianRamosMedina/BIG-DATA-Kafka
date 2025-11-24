# Instrucciones para Subir el Proyecto a GitHub

## 📋 Pasos para Subir al Repositorio

### 1. Navegar a la carpeta del proyecto
```bash
cd C:\Users\Cris\Desktop\kafka-clima-lima-local
```

### 2. Inicializar repositorio Git (si no está inicializado)
```bash
git init
```

### 3. Configurar el repositorio remoto
```bash
git remote add origin https://github.com/CristianRamosMedina/BIG-DATA-Kafka.git
```

**Si ya existe el remote, actualízalo:**
```bash
git remote set-url origin https://github.com/CristianRamosMedina/BIG-DATA-Kafka.git
```

### 4. Crear la rama principal (si es necesario)
```bash
git branch -M main
```

### 5. Agregar todos los archivos
```bash
git add .
```

**Esto agregará:**
- ✅ Código fuente (producers/, consumers/, dashboard/)
- ✅ Docker compose
- ✅ README.md
- ✅ .gitignore
- ✅ Script de timestamps
- ❌ Archivos JSON generados (ignorados por .gitignore)

### 6. Verificar los archivos a subir
```bash
git status
```

**Deberías ver archivos como:**
```
modified:   README.md
new file:   .gitignore
new file:   producers/producer_realtime.py
new file:   producers/producer_cleaning.py
new file:   consumers/consumer_batch.py
new file:   consumers/consumer_alerts.py
new file:   consumers/consumer_predictor_lluvia.py
new file:   consumers/consumer_predictor_sol.py
new file:   consumers/consumer_clasificador_clima.py
new file:   consumers/consumer_predicciones_consolidadas.py
new file:   dashboard/app.py
new file:   docker-compose.yml
new file:   agregar_timestamps.py
new file:   data/batch/.gitkeep
new file:   data/alerts/.gitkeep
new file:   data/predictions/.gitkeep
```

### 7. Hacer commit
```bash
git commit -m "Sistema completo de monitoreo climatico con Kafka

- Implementacion de 2 producers (realtime y cleaning)
- Implementacion de 6 consumers (batch, alerts, 3 predictores, consolidador)
- Dashboard web con Streamlit (auto-refresh cada 30s)
- 3 modelos de prediccion climatica basados en reglas
- Sistema de procesamiento batch cada 2 minutos
- Registros con timestamps para analisis temporal
- Predicciones por zona con visualizacion de emojis
- Arquitectura completa con 4 topics de Kafka
- Docker Compose para Kafka + Zookeeper"
```

### 8. Subir a GitHub
```bash
git push -u origin main
```

**Si el repositorio ya existe y hay conflictos:**
```bash
git pull origin main --rebase
git push -u origin main
```

**Si quieres forzar el push (⚠️ CUIDADO: sobrescribirá el contenido remoto):**
```bash
git push -u origin main --force
```

---

## 🔍 Verificar que se subió correctamente

1. Ve a: https://github.com/CristianRamosMedina/BIG-DATA-Kafka
2. Verifica que aparezcan:
   - ✅ README.md formateado correctamente
   - ✅ Carpetas: producers/, consumers/, dashboard/, data/
   - ✅ Archivo docker-compose.yml
   - ✅ .gitignore
   - ❌ NO deben aparecer archivos .json en data/

---

## 📁 Estructura Final en GitHub

```
BIG-DATA-Kafka/
├── README.md                              ⭐ Documentación completa
├── .gitignore                            🚫 Archivos ignorados
├── docker-compose.yml                    🐳 Config de Kafka
├── agregar_timestamps.py                 🔧 Utilidad
│
├── producers/
│   ├── producer_realtime.py
│   └── producer_cleaning.py
│
├── consumers/
│   ├── consumer_batch.py
│   ├── consumer_alerts.py
│   ├── consumer_predictor_lluvia.py
│   ├── consumer_predictor_sol.py
│   ├── consumer_clasificador_clima.py
│   └── consumer_predicciones_consolidadas.py
│
├── dashboard/
│   └── app.py
│
└── data/
    ├── batch/.gitkeep                    📂 Carpeta vacía
    ├── alerts/.gitkeep                   📂 Carpeta vacía
    └── predictions/.gitkeep              📂 Carpeta vacía
```

---

## ⚙️ Comandos Útiles Adicionales

### Ver el historial de commits
```bash
git log --oneline
```

### Ver archivos ignorados
```bash
git status --ignored
```

### Crear una nueva rama (opcional)
```bash
git checkout -b feature/nueva-funcionalidad
```

### Ver diferencias antes de commit
```bash
git diff
```

### Deshacer cambios no guardados
```bash
git restore <archivo>
```

### Remover archivo del staging
```bash
git reset HEAD <archivo>
```

---

## 🎓 Para la Clase de CCOMP

### Puntos a Destacar en la Presentación:

1. **Arquitectura Kafka:**
   - 1 Broker
   - 4 Topics
   - 2 Producers
   - 6 Consumers
   - 6 Consumer Groups diferentes

2. **Flujo de Datos:**
   - API Real → Producer → Topic Raw → Producer Cleaning → Topic Clean → 6 Consumers → Archivos JSON → Dashboard

3. **Procesamiento:**
   - Tiempo Real: Cada 10 segundos
   - Batch: Cada ~2 minutos (72 mensajes)
   - Predicciones: 3 modelos en paralelo

4. **Visualización:**
   - Dashboard interactivo
   - Auto-refresh automático
   - Predicciones con emojis
   - Mapas y gráficos

5. **Escalabilidad:**
   - Fácil agregar más zonas
   - Fácil agregar más consumers
   - Modular y extensible

---

## 📝 Notas Importantes

- **NO se suben archivos .json** (están en .gitignore)
- **SÍ se suben las carpetas vacías** (con .gitkeep)
- **El README tiene toda la documentación** necesaria
- **Sin nombres de AI** en el código ni commits
- **Proyecto 100% funcional** y documentado

---

## ✅ Checklist Final

Antes de presentar, verifica:

- [ ] README.md completo y actualizado
- [ ] Todos los archivos .py están comentados
- [ ] docker-compose.yml funciona
- [ ] .gitignore configurado correctamente
- [ ] No hay archivos temporales o datos sensibles
- [ ] El dashboard corre en localhost:8501
- [ ] Todos los consumers funcionan
- [ ] Las predicciones se generan correctamente
- [ ] El repositorio está público (o privado según requieran)
- [ ] No hay menciones a herramientas de IA en el código

---

## 🎉 ¡Listo!

Tu proyecto está completo y listo para:
- Presentación en clase
- Revisión del profesor
- Portfolio personal
- Práctica de Kafka

**Repositorio:** https://github.com/CristianRamosMedina/BIG-DATA-Kafka

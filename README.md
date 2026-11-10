# Terraquipu API 🛰️⚙️

> **Geo-Backend, Base de Datos Espacial, Motor Determinista y Agente RAG Explicativo**  
> *Parte del ecosistema [Terraquipu](https://github.com/TerraQuipu)*

---

## 📌 Propósito del Repositorio

`terraquipu-api` constituye el núcleo computacional y de inteligencia de Terraquipu. Se encarga de:
1. Ingestar y almacenar telemetría en tiempo real de nodos IoT en campo.
2. Integrar datos satelitales en vivo (NASA POWER, SoilGrids, DEM SRTM).
3. Ejecutar el **Motor Multicriterio Determinista** para calcular la compatibilidad matemática de rotación de cultivos sin alucinaciones.
4. Orquestar el **Agente RAG (Retrieval-Augmented Generation)** para generar explicaciones técnicas fundamentadas citando manuales oficiales de **INIA** y **SENAMHI**.

---

## 👥 Equipo y Roles Asignados

| Integrante | Rol | Responsabilidad en el Sprint de 48h |
| :--- | :--- | :--- |
| **Sistemas 1** | **Geo-Backend & PostGIS Lead** | Arquitectura de la API en FastAPI, base de datos PostgreSQL/PostGIS, ingesta de telemetría IoT, proxy y caché para APIs de NASA/SoilGrids y cálculo del balance hídrico. |
| **Sistemas 3** | **IA / RAG & Integración LLM** | Extracción e indexación de fragmentos de PDFs técnicos del INIA/SENAMHI (vectorstore Chroma/FAISS), prompt engineering con guardrails anti-alucinaciones y despliegue del endpoint explicativo. |

---

## 🛠️ Stack Tecnológico

* **Lenguaje & Framework:** Python 3.10+ con **FastAPI** y Pydantic v2.
* **Base de Datos:** PostgreSQL 15+ con extensión espacial **PostGIS** y SQLAlchemy 2.0.
* **Vectorstore & RAG:** ChromaDB / FAISS / pgvector con embeddings de Gemini (`text-embedding-004`) o LangChain.
* **LLM Engine:** Google Gemini 1.5 Pro / Flash con función de citas obligatorias.
* **Servidor ASGI:** Uvicorn con recarga en caliente.

---

## 📡 Endpoints de la API REST

### 1. Ingesta de Telemetría IoT
* **Ruta:** `POST /api/v1/telemetry`
* **Descripción:** Recibe lecturas de humedad y temperatura del suelo enviadas por el nodo ESP32 o el script simulador.
* **Payload:** Estructura `iot_telemetry.json` (Contrato 2).

### 2. Diagnóstico Territorial
* **Ruta:** `GET /api/v1/diagnose?lat={lat}&lon={lon}`
* **Descripción:** Consulta NASA POWER (anomalía de precipitación), SoilGrids v2.0 (pH, nitrógeno, materia orgánica) y Open-Meteo DEM (piso altitudinal y pendiente).
* **Respuesta:** Estructura `territorial_diagnosis.json` (Contrato 3).

### 3. Recomendación y Explicación de Rotación
* **Ruta:** `POST /api/v1/recommend`
* **Descripción:** Ejecuta el motor determinista cruzando el diagnóstico con `crop_matrix.json`, clasifica las 3 mejores secuencias y genera la justificación RAG con citas oficiales.
* **Respuesta:** Estructura `rotation_recommendation.json` (Contrato 4).

---

## 🧠 Arquitectura Híbrida del Motor

```
[ Solicitud de Parcela ]
         │
         ▼
┌──────────────────────────────────────────────┐
│       1. MOTOR DETERMINISTA MATEMÁTICO       │
│  - Cruce de umbrales INIA (Requerimiento mm) │
│  - Ponderación de déficit hídrico por El Niño│
│  - Balance de Nitrógeno y corte de plagas    │
│  -> Resultado: Ranking ordenado (0 - 100%)    │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│       2. AGENTE EXPLICATIVO CON RAG          │
│  - Consulta Vectorstore de Manuales INIA/SEN │
│  - Redacta recomendación al técnico/campesino│
│  - Cita explícitamente documento y página    │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
           [ Respuesta al Frontend ]
```

---

## 💻 Puesta en Marcha Local

```bash
# 1. Clonar el repositorio
git clone https://github.com/TerraQuipu/terraquipu-api.git
cd terraquipu-api

# 2. Crear entorno virtual
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate

# 3. Instalar dependencias
pip install fastapi uvicorn pydantic requests sqlalchemy psycopg2-binary langchain-google-genai chromadb

# 4. Configurar variables de entorno (.env)
GEMINI_API_KEY=tu_api_key_aqui
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/terraquipu

# 5. Ejecutar la API
uvicorn main:app --reload --port 8000
```

Documentación interactiva disponible en `http://localhost:8000/docs` (Swagger UI).


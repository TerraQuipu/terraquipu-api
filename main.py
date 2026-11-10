"""
Terraquipu API - Main Application
Geo-Backend, PostGIS Integration, Deterministic Scoring & RAG Explanations
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from services.nasa_power import fetch_nasa_agroclimate
from services.soil_elevation import fetch_elevation_and_soil
from services.scoring import generate_rotation_strategies
from services.rag_explainer import generate_rag_explanation

app = FastAPI(
    title="Terraquipu API",
    version="1.0.0",
    description="Sistema de Inteligencia Territorial y Rotación de Cultivos para los Andes - NASA Space Apps"
)

# Enable CORS for Frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory IoT state store
latest_telemetry: Optional[Dict[str, Any]] = {
    "device_id": "terraquipu-node-cusco-01",
    "firmware_version": "v1.2.0-esp32",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "location": {"latitude": -13.5321, "longitude": -71.9675, "elevation_masl": 3410.5},
    "readings": {
        "soil_moisture_vwc_percent": 18.4,
        "soil_temperature_celsius": 12.3,
        "air_temperature_celsius": 16.8,
        "air_humidity_percent": 42.1,
        "battery_level_percent": 88
    },
    "calibration_factors": {
        "smap_bias_offset": -3.2,
        "soil_texture_profile": "franco-arcilloso",
        "status": "calibrated"
    }
}

# --- Pydantic Request Models ---
class TelemetryPayload(BaseModel):
    device_id: str
    firmware_version: str
    timestamp: str
    location: Dict[str, Any]
    readings: Dict[str, Any]
    calibration_factors: Optional[Dict[str, Any]] = None

class RecommendationRequest(BaseModel):
    plot_id: Optional[str] = "parcela-chinchero-sector-b"
    latitude: float = -13.5321
    longitude: float = -71.9675
    previous_crop_id: str = Field(default="papa_nativa", description="Último cultivo sembrado")

# --- Routes ---

@app.get("/")
def read_root():
    return {
        "project": "Terraquipu",
        "system": "Geo-Backend & Rotation Intelligence API",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/api/v1/telemetry")
def ingest_telemetry(payload: TelemetryPayload):
    """
    Contrato 2: Recibe telemetría en tiempo real del nodo ESP32 o simulador mock_telemetry.py.
    """
    global latest_telemetry
    latest_telemetry = payload.model_dump()
    return {
        "status": "accepted",
        "device_id": payload.device_id,
        "recorded_at": payload.timestamp
    }

@app.get("/api/v1/telemetry/latest")
def get_latest_telemetry():
    """
    Devuelve la última lectura calibrada en campo.
    """
    if not latest_telemetry:
        raise HTTPException(status_code=404, detail="No telemetry available")
    return latest_telemetry

@app.get("/api/v1/diagnose")
def get_territorial_diagnosis(
    lat: float = -13.5321,
    lon: float = -71.9675,
    district: str = "Chinchero"
):
    """
    Contrato 3: Diagnóstico territorial combinando NASA POWER, SoilGrids y sensores in-situ.
    """
    nasa_climate = fetch_nasa_agroclimate(lat, lon)
    topo_soil = fetch_elevation_and_soil(lat, lon)

    # Inyectar calibración IoT local si está en el radio
    current_vwc = 18.4
    if latest_telemetry and "readings" in latest_telemetry:
        current_vwc = latest_telemetry["readings"].get("soil_moisture_vwc_percent", 18.4)

    soil_profile = topo_soil["soil_profile"]
    soil_profile["current_moisture_vwc_percent"] = current_vwc

    return {
        "plot_id": f"parcela-{district.lower()}-01",
        "location": {
            "latitude": lat,
            "longitude": lon,
            "department": "Cusco",
            "province": "Urubamba",
            "district": district,
            "elevation_masl": topo_soil["elevation_masl"],
            "ecological_floor": topo_soil["ecological_floor"],
            "slope_degrees": topo_soil["slope_degrees"]
        },
        "climate_context": {
            "enso_phase": "El Niño Moderado",
            "source": nasa_climate["source"],
            "historical_annual_rainfall_mm": nasa_climate["historical_annual_rainfall_mm"],
            "projected_season_rainfall_mm": nasa_climate["projected_season_rainfall_mm"],
            "rainfall_anomaly_percent": nasa_climate["rainfall_anomaly_percent"],
            "frost_risk_level": nasa_climate["frost_risk_level"],
            "heat_wave_days_expected": nasa_climate["heat_wave_days_expected"]
        },
        "soil_health_profile": soil_profile
    }

@app.post("/api/v1/recommend")
def get_rotation_recommendation(body: RecommendationRequest):
    """
    Contrato 4: Motor de recomendación determinista + capa explicativa RAG.
    """
    # 1. Obtener diagnóstico de la parcela
    diag = get_territorial_diagnosis(lat=body.latitude, lon=body.longitude)

    # 2. Generar estrategias mediante motor determinista
    strategies = generate_rotation_strategies(diag, previous_crop_id=body.previous_crop_id)

    # 3. Añadir explicación RAG con citas del INIA
    for st in strategies:
        st["rag_explanation"] = generate_rag_explanation(
            strategy_title=st["strategy_title"],
            anomaly_percent=diag["climate_context"]["rainfall_anomaly_percent"],
            previous_crop=body.previous_crop_id
        )

    return {
        "diagnosis_ref_id": diag["plot_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "current_culture_history": [body.previous_crop_id],
        "recommended_strategies": strategies
    }

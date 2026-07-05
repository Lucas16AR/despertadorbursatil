"""Cliente de dolarapi.com — cotizaciones del dólar."""
import requests

DOLARAPI_URL = "https://dolarapi.com/v1/dolares"

# casa (dolarapi) -> etiqueta para el reporte
CASAS_RELEVANTES = {
    "oficial": "Oficial",
    "blue": "Blue",
    "bolsa": "MEP",
    "contadoconliqui": "CCL",
}


def fetch_dolares() -> dict:
    """Devuelve {casa: {"nombre", "compra", "venta", "fecha_origen"}} para las casas
    relevantes del MVP. `fecha_origen` es el `fechaActualizacion` que informa dolarapi.com
    (ISO 8601 UTC) — sirve para detectar valores que la fuente no actualizó hoy (ej. el
    dólar oficial, que se mueve con lag)."""
    response = requests.get(DOLARAPI_URL, timeout=10)
    response.raise_for_status()
    cotizaciones = response.json()
    return {
        item["casa"]: {
            "nombre": CASAS_RELEVANTES[item["casa"]],
            "compra": item["compra"],
            "venta": item["venta"],
            "fecha_origen": item.get("fechaActualizacion"),
        }
        for item in cotizaciones
        if item["casa"] in CASAS_RELEVANTES
    }

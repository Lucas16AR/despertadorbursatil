"""Cliente de dolarapi.com — cotizaciones del dólar."""
import requests

DOLARAPI_URL = "https://dolarapi.com/v1/dolares"

# casa (dolarapi) -> etiqueta para el reporte
CASAS_RELEVANTES = {
    "oficial": "Oficial",
    "blue": "Blue",
    "bolsa": "MEP",
    "contadoconliqui": "CCL",
    "cripto": "Cripto",
}


def fetch_dolares() -> dict:
    """Devuelve {casa: {"nombre", "compra", "venta", "fecha_origen"}} para las casas
    relevantes del MVP. `fecha_origen` es el `fechaActualizacion` que informa dolarapi.com
    (ISO 8601 UTC) — sirve para detectar valores que la fuente no actualizó hoy (ej. el
    dólar oficial, que se mueve con lag)."""
    response = requests.get(DOLARAPI_URL, timeout=10)
    response.raise_for_status()
    cotizaciones = response.json()
    dolares = {}
    for item in cotizaciones:
        casa = item.get("casa")
        if casa not in CASAS_RELEVANTES:
            continue
        compra, venta = item.get("compra"), item.get("venta")
        # Defensa ante datos inválidos de la fuente: una casa sin precio numérico se omite,
        # mejor que el mensaje salga sin esa línea a que el formateo tire todo el envío.
        if not isinstance(compra, (int, float)) or not isinstance(venta, (int, float)) or venta <= 0:
            print(f"dolarapi.com devolvió un valor inválido para '{casa}' — se omite esa casa.")
            continue
        dolares[casa] = {
            "nombre": CASAS_RELEVANTES[casa],
            "compra": compra,
            "venta": venta,
            "fecha_origen": item.get("fechaActualizacion"),
        }
    return dolares

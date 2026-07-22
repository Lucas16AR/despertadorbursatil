"""Tests unitarios de la lógica más frágil del pipeline: parseo de fechas, frescura,
variaciones, brecha, agrupador de titulares y momentos del día.

Sólo cubre módulos sin dependencias externas (formatter, agrupador, momento, snapshot) para
poder correr sin instalar nada: `python -m unittest tests -v`. Los fetchers (dolar, bcra,
riesgo_pais, rss_news) y los generadores con IA se validan con corridas reales, no acá."""
from __future__ import annotations

import unittest
from datetime import date

from agrupador import agrupar_titulares
from formatter import (
    DISCLAIMER,
    _fecha_mes_anio,
    _fecha_origen_a_fecha,
    _miles,
    _precio_texto,
    _sufijo_frescura,
    _variacion_brecha_texto,
    _variacion_texto,
    armar_mensaje,
    calcular_brecha_mep_oficial,
    detectar_anomalias,
)
from momento import MOMENTOS, obtener_momento


def _dolares(fecha="2026-07-09T18:55:00.000Z"):
    """Lote de dólares de ejemplo con todas las casas frescas."""
    return {
        "oficial": {"nombre": "Oficial", "compra": 1460.0, "venta": 1510.0, "fecha_origen": fecha},
        "blue": {"nombre": "Blue", "compra": 1490.0, "venta": 1510.0, "fecha_origen": fecha},
        "bolsa": {"nombre": "MEP", "compra": 1525.0, "venta": 1532.0, "fecha_origen": fecha},
        "contadoconliqui": {"nombre": "CCL", "compra": 1563.0, "venta": 1566.0, "fecha_origen": fecha},
        "cripto": {"nombre": "Cripto", "compra": 1558.0, "venta": 1560.0, "fecha_origen": fecha},
    }


class TestFechaOrigen(unittest.TestCase):
    def test_iso_con_hora_utc_convierte_a_fecha_argentina(self):
        # 01:30 UTC del día 10 son las 22:30 ART del día 9.
        self.assertEqual(_fecha_origen_a_fecha("2026-07-10T01:30:00.000Z"), date(2026, 7, 9))

    def test_solo_fecha_se_toma_literal_sin_correr_zona(self):
        self.assertEqual(_fecha_origen_a_fecha("2024-08-30"), date(2024, 8, 30))

    def test_none_y_vacio(self):
        self.assertIsNone(_fecha_origen_a_fecha(None))
        self.assertIsNone(_fecha_origen_a_fecha(""))

    def test_texto_invalido(self):
        self.assertIsNone(_fecha_origen_a_fecha("no es una fecha"))
        self.assertIsNone(_fecha_origen_a_fecha("2026-13-45T99:00:00Z"))


class TestSufijoFrescura(unittest.TestCase):
    def test_dato_fresco_sin_sufijo(self):
        self.assertEqual(_sufijo_frescura("2026-07-09", date(2026, 7, 9)), "")

    def test_dato_rezagado_mismo_anio(self):
        self.assertEqual(_sufijo_frescura("2026-07-07", date(2026, 7, 9)), " (al 07/07)")

    def test_dato_de_otro_anio_incluye_anio(self):
        self.assertEqual(_sufijo_frescura("2024-08-30", date(2026, 7, 9)), " (al 30/08/2024)")

    def test_sin_fecha_o_sin_referencia(self):
        self.assertEqual(_sufijo_frescura(None, date(2026, 7, 9)), "")
        self.assertEqual(_sufijo_frescura("2026-07-09", None), "")


class TestPrecioYMiles(unittest.TestCase):
    def test_precio_entero_sin_decimales(self):
        self.assertEqual(_precio_texto(1460.0), "1460")

    def test_precio_con_centavos(self):
        self.assertEqual(_precio_texto(1513.3), "1513.30")
        self.assertEqual(_precio_texto(1561.21), "1561.21")

    def test_miles_separador_argentino(self):
        self.assertEqual(_miles(1714487.0), "1.714.487")
        self.assertEqual(_miles(999.0), "999")


class TestFechaMesAnio(unittest.TestCase):
    def test_formatea_mes_en_espanol(self):
        self.assertEqual(_fecha_mes_anio("2026-05-31"), "mayo 2026")

    def test_sin_fecha(self):
        self.assertEqual(_fecha_mes_anio(None), "")
        self.assertEqual(_fecha_mes_anio("no es una fecha"), "")


class TestVariaciones(unittest.TestCase):
    def test_variacion_precio(self):
        self.assertEqual(_variacion_texto(0.5), " 🟢▲ (+0.5%)")
        self.assertEqual(_variacion_texto(-1.2), " 🔴▼ (-1.2%)")
        self.assertEqual(_variacion_texto(0.0), " ➖ (+0.0%)")
        self.assertEqual(_variacion_texto(None), "")

    def test_variacion_brecha_colores_invertidos_y_pp(self):
        # Brecha más ancha = desfavorable (rojo); más angosta = favorable (verde).
        self.assertEqual(_variacion_brecha_texto(3.0), " 🔴▲ (+3.0pp)")
        self.assertEqual(_variacion_brecha_texto(-2.4), " 🟢▼ (-2.4pp)")
        self.assertEqual(_variacion_brecha_texto(0.0), " ➖ (+0.0pp)")
        self.assertEqual(_variacion_brecha_texto(None), "")


class TestBrecha(unittest.TestCase):
    def test_brecha_normal(self):
        brecha = calcular_brecha_mep_oficial(_dolares())
        self.assertAlmostEqual(brecha, (1532 - 1510) / 1510 * 100)

    def test_falta_una_casa_devuelve_none_no_crashea(self):
        dolares = _dolares()
        del dolares["bolsa"]
        self.assertIsNone(calcular_brecha_mep_oficial(dolares))
        del dolares["oficial"]
        self.assertIsNone(calcular_brecha_mep_oficial(dolares))
        self.assertIsNone(calcular_brecha_mep_oficial({}))


class TestArmarMensaje(unittest.TestCase):
    def test_mensaje_completo_con_disclaimer(self):
        msg = armar_mensaje(_dolares(), None, None, momento=obtener_momento("cierre"))
        self.assertIn("Despertador Bursátil · Cierre", msg)
        self.assertIn("Brecha MEP/oficial", msg)
        self.assertIn("Cripto:", msg)
        self.assertTrue(msg.endswith(DISCLAIMER))

    def test_sin_brecha_omite_destacado_pero_no_crashea(self):
        dolares = _dolares()
        del dolares["bolsa"]
        msg = armar_mensaje(dolares, None, None)
        self.assertNotIn("Destacado del día", msg)
        self.assertIn("Oficial:", msg)

    def test_variacion_solo_con_snapshot_y_dato_fresco(self):
        ayer = {"dolares": {"blue": {"venta": 1500.0}}, "brecha_mep_oficial": 1.0}
        msg = armar_mensaje(_dolares(), None, ayer)
        linea_blue = next(l for l in msg.split("\n") if l.startswith("Blue"))
        self.assertIn("(+0.7%)", linea_blue)

    def test_dato_rezagado_sin_flecha_ni_variacion(self):
        dolares = _dolares()
        dolares["oficial"]["fecha_origen"] = "2026-07-07T18:00:00.000Z"
        ayer = {"dolares": {"oficial": {"venta": 1400.0}}, "brecha_mep_oficial": 1.0}
        msg = armar_mensaje(dolares, None, ayer)
        linea = next(l for l in msg.split("\n") if l.startswith("Oficial"))
        self.assertIn("(al 07/07)", linea)
        self.assertNotIn("▲", linea)
        self.assertNotIn("▼", linea)

    def test_variacion_del_dia_solo_en_cierre_con_inicio(self):
        inicio = {"dolares": {"blue": {"venta": 1490.0}}}
        con_inicio = armar_mensaje(_dolares(), None, None, snapshot_inicio_dia=inicio)
        sin_inicio = armar_mensaje(_dolares(), None, None)
        self.assertIn("· día +1.3%", con_inicio)
        self.assertNotIn("· día", sin_inicio)

    def test_merval_congelado_marcado_sin_flecha(self):
        merval = {"valor": 1714487.0, "variacion_pct": 2.9, "fecha_origen": "2024-08-30"}
        msg = armar_mensaje(_dolares(), merval, None)
        linea = next(l for l in msg.split("\n") if l.startswith("MERVAL"))
        self.assertIn("(al 30/08/2024)", linea)
        self.assertNotIn("+2.9%", linea)

    def test_riesgo_pais_sin_flecha_de_color(self):
        rp = {"valor": 405.0, "variacion_pct": -0.7, "fecha_origen": "2026-07-07"}
        msg = armar_mensaje(_dolares(), None, None, riesgo_pais=rp)
        linea = next(l for l in msg.split("\n") if l.startswith("Riesgo país"))
        self.assertIn("405 pts", linea)
        self.assertIn("(-0.7%)", linea)
        self.assertNotIn("🔴", linea)
        self.assertNotIn("🟢", linea)

    def test_leyenda_dolarapi_toma_la_fecha_mas_reciente(self):
        dolares = _dolares(fecha="2026-07-11T20:59:00.000Z")
        msg = armar_mensaje(dolares, None, None)
        self.assertIn("Datos obtenidos de DolarApi.com (https://dolarapi.com/)", msg)
        self.assertIn("Actualizado el 11/07/2026 a las 17:59", msg)

    def test_inflacion_mensual_e_interanual(self):
        inflacion = {
            "mensual": {"valor": 2.1, "fecha_origen": "2026-05-31"},
            "interanual": {"valor": 45.3, "fecha_origen": "2026-05-31"},
        }
        msg = armar_mensaje(_dolares(), None, None, inflacion=inflacion)
        linea = next(l for l in msg.split("\n") if l.startswith("Inflación"))
        self.assertEqual(linea, "Inflación: 2.1% mensual / 45.3% interanual (dato de mayo 2026)")

    def test_inflacion_solo_una_serie_disponible(self):
        inflacion = {"mensual": {"valor": 2.1, "fecha_origen": "2026-05-31"}, "interanual": None}
        msg = armar_mensaje(_dolares(), None, None, inflacion=inflacion)
        linea = next(l for l in msg.split("\n") if l.startswith("Inflación"))
        self.assertEqual(linea, "Inflación: 2.1% mensual (dato de mayo 2026)")

    def test_sin_inflacion_no_aparece_la_linea(self):
        msg = armar_mensaje(_dolares(), None, None)
        self.assertNotIn("Inflación", msg)

    def test_pie_con_fuentes_de_noticias(self):
        msg = armar_mensaje(_dolares(), None, None, fuentes_noticias=["Ámbito", "Infobae"])
        self.assertIn("<i>Noticias: Ámbito, Infobae.</i>", msg)
        self.assertIn("<i>Datos: dolarapi.com, estadisticasbcra.com, argentinadatos.com.</i>", msg)

    def test_pie_sin_fuentes_de_noticias_omite_la_linea(self):
        msg = armar_mensaje(_dolares(), None, None)
        self.assertNotIn("Noticias:", msg)

    def test_dolar_mayorista_y_tarjeta_con_centavos(self):
        dolares = _dolares()
        dolares["mayorista"] = {
            "nombre": "Mayorista", "compra": 1440.0, "venta": 1445.5, "fecha_origen": dolares["oficial"]["fecha_origen"]
        }
        dolares["tarjeta"] = {
            "nombre": "Tarjeta", "compra": 1900.0, "venta": 1963.0, "fecha_origen": dolares["oficial"]["fecha_origen"]
        }
        msg = armar_mensaje(dolares, None, None)
        self.assertIn("Mayorista: compra $1440 / venta $1445.50", msg)
        self.assertIn("Tarjeta: compra $1900 / venta $1963", msg)
        # Mayorista antes que Cripto, Cripto antes que Tarjeta (ORDEN_CASAS).
        pos = {l.split(":")[0]: i for i, l in enumerate(msg.split("\n"))}
        self.assertLess(pos["Mayorista"], pos["Cripto"])
        self.assertLess(pos["Cripto"], pos["Tarjeta"])


class TestDetectarAnomalias(unittest.TestCase):
    def test_campo_rezagado_detectado(self):
        dolares = _dolares()
        dolares["oficial"]["fecha_origen"] = "2026-07-07T18:00:00.000Z"
        merval = {"valor": 1.0, "variacion_pct": 0.0, "fecha_origen": "2024-08-30"}
        campos = {a["campo"] for a in detectar_anomalias(dolares, merval)}
        self.assertEqual(campos, {"oficial", "merval"})

    def test_todo_fresco_sin_anomalias(self):
        self.assertEqual(detectar_anomalias(_dolares(), None), [])


class TestAgrupador(unittest.TestCase):
    def test_mismo_evento_se_agrupa_y_rankea_por_fuentes(self):
        titulares = [
            {"fuente": "Ámbito", "titulo": "El FMI aprobó la revisión del acuerdo con Argentina", "resumen": ""},
            {"fuente": "Infobae", "titulo": "El FMI aprobó la revisión del acuerdo y habrá desembolso", "resumen": ""},
            {"fuente": "La Nación", "titulo": "FMI: se aprobó la revisión del acuerdo argentino", "resumen": ""},
            {"fuente": "El Cronista", "titulo": "Suben las acciones energéticas por el petróleo", "resumen": ""},
        ]
        grupos = agrupar_titulares(titulares)
        self.assertEqual(len(grupos), 2)
        self.assertEqual(grupos[0]["n_fuentes"], 3)  # el evento FMI, cubierto por 3 medios, primero
        self.assertEqual(sorted(grupos[0]["fuentes"]), ["Infobae", "La Nación", "Ámbito"])

    def test_titulares_distintos_no_se_mezclan(self):
        titulares = [
            {"fuente": "A", "titulo": "La inflación de junio fue del 2 por ciento", "resumen": ""},
            {"fuente": "B", "titulo": "Aumenta la nafta en todo el país desde mañana", "resumen": ""},
        ]
        self.assertEqual(len(agrupar_titulares(titulares)), 2)

    def test_lista_vacia_y_titulo_vacio(self):
        self.assertEqual(agrupar_titulares([]), [])
        self.assertEqual(agrupar_titulares([{"fuente": "A", "titulo": "", "resumen": ""}]), [])


class TestMomento(unittest.TestCase):
    def test_clave_valida_y_resuelta(self):
        m = obtener_momento("cierre_global")
        self.assertEqual(m["clave"], "cierre_global")
        self.assertEqual(m["tipo"], "datos")

    def test_fallback_a_pre_apertura(self):
        self.assertEqual(obtener_momento(None)["clave"], "pre_apertura")
        self.assertEqual(obtener_momento("no-existe")["clave"], "pre_apertura")

    def test_devuelve_copia_sin_mutar_la_tabla(self):
        m = obtener_momento("apertura")
        m["titulo"] = "MUTADO"
        self.assertNotEqual(MOMENTOS["apertura"].get("titulo"), "MUTADO")

    def test_todos_los_momentos_tienen_lo_necesario(self):
        for clave, cfg in MOMENTOS.items():
            self.assertIn(cfg["tipo"], ("datos", "contenido"), clave)
            for campo in ("emoji", "titulo", "subtitulo"):
                self.assertTrue(cfg.get(campo), f"{clave} sin {campo}")
            if cfg["tipo"] == "datos":
                self.assertTrue(cfg.get("enfoque_macro"), f"{clave} sin enfoque_macro")


if __name__ == "__main__":
    unittest.main()

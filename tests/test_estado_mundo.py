"""Pruebas del diccionario del estado del mundo (Checkpoint 3, sin pygame)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from estado_mundo import (PUERTA_LOBBY, PUERTA_TERRAZA, actualizar, aplicar_efecto,
                          avanzar_tiempo, clave_puerta, consultar, crear_estado_inicial,
                          eliminar, insertar, misiones_con_estado, puertas_cerradas,
                          resumen, revertir_cambios, salas_iluminadas)


class TestEstadoMundo(unittest.TestCase):
    def setUp(self):
        self.e = crear_estado_inicial()

    def test_consultar_inexistente_devuelve_defecto(self):
        self.assertIsNone(consultar(self.e, "luces", "no_existe"))
        self.assertEqual(consultar(self.e, "luces", "no_existe", "sin datos"), "sin datos")
        self.assertEqual(consultar(self.e, "seccion_rara", "x", 0), 0)
        self.assertEqual(consultar(self.e, "luces", ["no", "hasheable"], "ok"), "ok")
        self.assertEqual(consultar(None, "luces", "lobby", "ok"), "ok")

    def test_clave_puerta_en_cualquier_orden(self):
        self.assertEqual(clave_puerta("terraza_n", "terraza"), ("terraza", "terraza_n"))
        self.assertEqual(consultar(self.e, "puertas", ("terraza_n", "terraza")), "cerrada")
        self.assertEqual(consultar(self.e, "puertas", ("terraza", "terraza_n")), "cerrada")

    def test_insertar_repetido_y_eliminar_inexistente(self):
        self.assertTrue(insertar(self.e, "misiones", "biblioteca", "disponible"))
        self.assertFalse(insertar(self.e, "misiones", "biblioteca", "completada"))
        self.assertEqual(consultar(self.e, "misiones", "biblioteca"), "disponible")
        self.assertFalse(insertar(self.e, "no_existe", "x", 1))
        self.assertTrue(eliminar(self.e, "misiones", "biblioteca"))
        self.assertFalse(eliminar(self.e, "misiones", "biblioteca"))
        self.assertFalse(eliminar(self.e, "no_existe", "x"))

    def test_actualizar_devuelve_valor_anterior(self):
        self.assertTrue(actualizar(self.e, "luces", "lobby", False))
        self.assertFalse(consultar(self.e, "luces", "lobby"))
        self.assertIsNone(actualizar(self.e, "luces", "nueva", True))

    def test_efecto_abre_terraza_y_se_revierte(self):
        cambios = aplicar_efecto(self.e, {"abre": PUERTA_TERRAZA})
        self.assertEqual(puertas_cerradas(self.e), [])
        revertir_cambios(self.e, cambios)
        self.assertEqual(puertas_cerradas(self.e), [PUERTA_TERRAZA])

    def test_efecto_apaga_y_revertir_clave_nueva_la_elimina(self):
        cambios = aplicar_efecto(self.e, {"apaga": "biblioteca", "enciende": "bodega"})
        self.assertNotIn("biblioteca", salas_iluminadas(self.e))
        self.assertIn("bodega", salas_iluminadas(self.e))
        revertir_cambios(self.e, cambios)
        self.assertIn("biblioteca", salas_iluminadas(self.e))
        self.assertIsNone(consultar(self.e, "luces", "bodega"))

    def test_efecto_none_o_desconocido(self):
        self.assertEqual(aplicar_efecto(self.e, None), [])
        self.assertEqual(aplicar_efecto(self.e, {"vuela": 1}), [])
        self.assertEqual(aplicar_efecto(self.e, {"abre": "no_es_tupla"}), [])
        revertir_cambios(self.e, [None, ("x",)])   # basura: no falla

    def test_toque_de_queda_cierra_el_lobby(self):
        self.assertNotIn(PUERTA_LOBBY, puertas_cerradas(self.e))
        avanzar_tiempo(self.e, 45)
        self.assertTrue(self.e["toque_queda_activo"])
        self.assertIn(PUERTA_LOBBY, puertas_cerradas(self.e))

    def test_alerta_vence_con_el_tiempo(self):
        insertar(self.e, "alertas", "lab_siemens", 3)
        self.assertEqual(avanzar_tiempo(self.e, 2), [])
        self.assertEqual(consultar(self.e, "alertas", "lab_siemens"), 1)
        self.assertEqual(avanzar_tiempo(self.e, 1), ["lab_siemens"])
        self.assertIsNone(consultar(self.e, "alertas", "lab_siemens"))

    def test_resumen_y_filtros(self):
        insertar(self.e, "misiones", "biblioteca", "completada")
        insertar(self.e, "misiones", "r101", "disponible")
        insertar(self.e, "misiones", "cafeteria", "disponible")
        insertar(self.e, "misiones", "bodega", "bloqueada")
        aplicar_efecto(self.e, {"apaga": "biblioteca"})
        insertar(self.e, "alertas", "sur", 5)
        self.assertEqual(misiones_con_estado(self.e, "disponible"), ["cafeteria", "r101"])
        r = resumen(self.e)
        self.assertEqual(r["hora"], "20:15")
        self.assertFalse(r["toque_queda"])
        self.assertEqual(r["puertas_cerradas"], 1)
        self.assertEqual(r["luces_encendidas"], 3)
        self.assertEqual(r["misiones"], {"completada": 1, "disponible": 2, "bloqueada": 1})
        self.assertEqual(r["alertas"], 1)

    def test_claves_viejas_siguen(self):
        for clave in ("hora_actual_min", "hora_toque_queda_min", "toque_queda_activo"):
            self.assertIn(clave, self.e)


if __name__ == "__main__":
    unittest.main()

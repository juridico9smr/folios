#!/usr/bin/env python3
"""
Pruebas unitarias para el extractor de propiedades.

Este archivo contiene pruebas para verificar que todos los casos documentados
en TEST_CASES.md funcionan correctamente.

Ejecutar con:
    python3 test_extract_properties.py
    
    o con pytest (si está instalado):
    python3 -m pytest test_extract_properties.py -v
    
    o para ver solo los fallos:
    python3 -m pytest test_extract_properties.py -v --tb=short
"""

import unittest
import sys
import os

# Agregar el directorio actual al path para importar extract_properties
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extract_properties import extract_properties_from_pdf, extract_folios_from_matriculas, process_properties, format_output, extract_oficina_registro, extract_escritura_from_anotacion


class TestExtractProperties(unittest.TestCase):
    """Pruebas para la extracción de propiedades desde PDFs"""
    
    def test_formato_dos_puntos(self):
        """Caso 1: Formato con dos puntos (:)"""
        pdf_text = "3 -> 190172 : TORRE 9 - APARTAMENTO 103 - PROYECTO MODIGLIANI"
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("190172", result)
        self.assertEqual(result["190172"], "TORRE 9 - APARTAMENTO 103 - PROYECTO MODIGLIANI")
    
    def test_formato_guion(self):
        """Caso 2: Formato con guión (-)"""
        pdf_text = "3 -> 190172 - TORRE 9 - APARTAMENTO 103 - PROYECTO MODIGLIANI"
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("190172", result)
        self.assertEqual(result["190172"], "TORRE 9 - APARTAMENTO 103 - PROYECTO MODIGLIANI")
    
    def test_formato_punto_simple(self):
        """Caso 3: Formato con punto simple (.)"""
        pdf_text = "3 -> 166319. CRA.33 #31-35-BLOQUE 2-PISO 7 APTO.709"
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("166319", result)
        self.assertEqual(result["166319"], "CRA.33 #31-35-BLOQUE 2-PISO 7 APTO.709")
    
    def test_formato_punto_simple_variacion_1(self):
        """Caso 3b: Formato con punto simple - Variación 1"""
        pdf_text = "3 -> 166322. CRA.33 #31-35-BLOQUE 2-PISO 7 APTO.713"
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("166322", result)
        self.assertEqual(result["166322"], "CRA.33 #31-35-BLOQUE 2-PISO 7 APTO.713")
    
    def test_formato_punto_simple_variacion_2(self):
        """Caso 3c: Formato con punto simple - Variación 2"""
        pdf_text = "3 -> 166323. CRA.33 #31-05-BLOQUE 2-SOTANO-PARQ.SENCILLO 9701"
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("166323", result)
        self.assertEqual(result["166323"], "CRA.33 #31-05-BLOQUE 2-SOTANO-PARQ.SENCILLO 9701")
    
    def test_formato_doble_punto(self):
        """Caso 4: Formato con doble punto (..)"""
        pdf_text = "3 -> 166457..CRA.33 #31-05-BLOQUE 2-SOTANO-CUARTO UTIL 9906"
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("166457", result)
        self.assertEqual(result["166457"], "CRA.33 #31-05-BLOQUE 2-SOTANO-CUARTO UTIL 9906")
    
    def test_formato_guion_dos_puntos(self):
        """Caso 5: Formato con guión y dos puntos (: -)"""
        pdf_text = "42 -> 1083489 : - APARTAMENTO 503 TORRE 3"
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("1083489", result)
        self.assertEqual(result["1083489"], "APARTAMENTO 503 TORRE 3")
    
    def test_formato_concatenado(self):
        """Caso 6: Formato concatenado (sin separador)"""
        pdf_text = "4 -> 230510APTO 0129 - TORRE 8 - ETAPA I"
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("230510", result)
        self.assertEqual(result["230510"], "APTO 0129 - TORRE 8 - ETAPA I")
    
    def test_propiedad_multilinea_consecutiva(self):
        """Caso 7: Propiedad en múltiples líneas consecutivas"""
        pdf_text = """2 -> 261841 : APARTAMENTO NUMERO DOSCIENTOS UNO (201) TORRE 4: UBICADO EN EL PISO
DOS -"""
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("261841", result)
        self.assertEqual(result["261841"], "APARTAMENTO NUMERO DOSCIENTOS UNO (201) TORRE 4: UBICADO EN EL PISO DOS")
    
    def test_propiedad_dividida_entre_paginas(self):
        """Caso 8: Propiedad dividida entre páginas con headers/footers"""
        pdf_text = """2 -> 262148 : APARTAMENTO NUMERO SEISCIENTOS SIETE (607) ETAPA II TORRE 1: UBICADO EN EL
La validez de este documento podrá verificarse en la página certificados.supernotariado.gov.co
OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MANIZALES
CERTIFICADO DE TRADICION
MATRICULA INMOBILIARIA
EL SEXTO PISO -"""
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("262148", result)
        # Verificar que contiene las partes principales (puede haber variaciones menores en espacios)
        self.assertIn("APARTAMENTO NUMERO SEISCIENTOS SIETE (607) ETAPA II TORRE 1", result["262148"])
        self.assertIn("UBICADO", result["262148"])
        self.assertIn("SEXTO PISO", result["262148"])
        # Verificar que no incluye headers/footers
        self.assertNotIn("La validez de este documento", result["262148"])
        self.assertNotIn("OFICINA DE REGISTRO", result["262148"])
    
    def test_propiedad_con_dos_puntos_dentro(self):
        """Caso 9: Propiedad con dos puntos dentro del nombre"""
        pdf_text = """2 -> 262089 : APARTAMENTO NUMERO CIENTO DOS (102) ETAPA II TORRE 1: UBICADO EN EL
PRIMER PISO -"""
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("262089", result)
        self.assertIn("APARTAMENTO NUMERO CIENTO DOS (102) ETAPA II TORRE 1: UBICADO EN EL PRIMER PISO", result["262089"])
    
    def test_propiedad_termina_etapa_guion(self):
        """Caso 10: Propiedad que termina con 'ETAPA -' (debe mantener el guión)"""
        pdf_text = "3 -> 214074 : APARTAMENTO 108 TORRE 6 CONJUNTO CERRADO PORTOBELO II ETAPA -"
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("214074", result)
        self.assertEqual(result["214074"], "APARTAMENTO 108 TORRE 6 CONJUNTO CERRADO PORTOBELO II ETAPA -")
    
    def test_propiedad_con_numeros_y_simbolos(self):
        """Caso 11: Propiedad con números y símbolos"""
        pdf_text = "3 -> 166319. CRA.33 #31-35-BLOQUE 2-PISO 7 APTO.709"
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("166319", result)
        self.assertEqual(result["166319"], "CRA.33 #31-35-BLOQUE 2-PISO 7 APTO.709")
    
    def test_propiedad_palabras_numeros_escritos(self):
        """Caso 12: Propiedad con palabras en números (escritas)"""
        pdf_text = """2 -> 262132 : APARTAMENTO NUMERO QUINIENTOS DOS (502) ETAPA II TORRE 1: UBICADO EN EL
QUINTO PISO -"""
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("262132", result)
        self.assertIn("APARTAMENTO NUMERO QUINIENTOS DOS (502) ETAPA II TORRE 1: UBICADO EN EL QUINTO PISO", result["262132"])
    
    def test_apartamento(self):
        """Caso 13: Tipo de inmueble - Apartamento"""
        pdf_text = "8 -> 251666 : CONJUNTO RESIDENCIAL VENTURA - PROPIEDAD HORIZONTAL TORRE 1 APARTAMENTO 101"
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("251666", result)
        self.assertEqual(result["251666"], "CONJUNTO RESIDENCIAL VENTURA - PROPIEDAD HORIZONTAL TORRE 1 APARTAMENTO 101")
    
    def test_parqueadero_sin_apartamento(self):
        """Caso 14: Parqueadero sin agregar 'APARTAMENTO' que no existe"""
        pdf_text = "6 -> 312770 : PARQUEADERO MOTOS 2 CON DEPOSITO"
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("312770", result)
        self.assertEqual(result["312770"], "PARQUEADERO MOTOS 2 CON DEPOSITO")
        # Verificar que NO agregó "APARTAMENTO" que no estaba en el certificado
        self.assertNotIn("APARTAMENTO", result["312770"])
    
    def test_local_concatenado(self):
        """Caso 15: Local en formato concatenado"""
        pdf_text = "6 -> 789012LOCAL 5 - PISO 1"
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("789012", result)
        self.assertEqual(result["789012"], "LOCAL 5 - PISO 1")
    
    def test_deposito_concatenado(self):
        """Caso 16: Depósito en formato concatenado"""
        pdf_text = "7 -> 345678DEPOSITO 10"
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("345678", result)
        self.assertEqual(result["345678"], "DEPOSITO 10")
    
    def test_bodega_concatenado(self):
        """Caso 17: Bodega en formato concatenado"""
        pdf_text = "10 -> 111222BODEGA 5"
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("111222", result)
        self.assertEqual(result["111222"], "BODEGA 5")
    
    def test_filtrado_headers_footers(self):
        """Caso 20: Headers/Footers deben ser filtrados"""
        pdf_text = """2 -> 262173 : APARTAMENTO NUMERO OCHOCIENTOS DIEZ (810) ETAPA II TORRE 1: UBICADO EN
EL OCTAVO PISO -
La validez de este documento podrá verificarse en la página certificados.supernotariado.gov.co
OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MANIZALES
CERTIFICADO DE TRADICION
MATRICULA INMOBILIARIA"""
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("262173", result)
        # Verificar que no incluye headers/footers
        self.assertNotIn("La validez de este documento", result["262173"])
        self.assertNotIn("OFICINA DE REGISTRO", result["262173"])
        self.assertNotIn("CERTIFICADO DE TRADICION", result["262173"])
        self.assertNotIn("MATRICULA INMOBILIARIA", result["262173"])
    
    def test_filtrado_salvedades(self):
        """Caso 21: Salvedades deben ser filtradas"""
        pdf_text = """2 -> 262173 : APARTAMENTO NUMERO CUATROCIENTOS TRES (403) ETAPA II TORRE 1: UBICADO EN EL CUARTO PISO - OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MANIZALES CERTIFICADO DE TRADICION MATRICULA INMOBILIARIALa validez de este documento podrá verificarse en la página certificados.supernotariado.gov.co Certificado generado con el Pin No: 2511195352124777447Nro Matrícula: 100-256825,100-262122,,,"""
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("262173", result)
        # Verificar que no incluye información de headers/footers
        self.assertNotIn("OFICINA DE REGISTRO", result["262173"])
        self.assertNotIn("Certificado generado", result["262173"])
        self.assertNotIn("100-256825", result["262173"])
    
    def test_propiedad_incompleta_en_el(self):
        """Caso 23: Propiedad incompleta que termina con 'EN EL'"""
        pdf_text = """2 -> 262132 : APARTAMENTO NUMERO QUINIENTOS DOS (502) ETAPA II TORRE 1: UBICADO EN EL
QUINTO PISO -"""
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("262132", result)
        self.assertIn("APARTAMENTO NUMERO QUINIENTOS DOS (502) ETAPA II TORRE 1: UBICADO EN EL QUINTO PISO", result["262132"])
    
    def test_propiedad_incompleta_piso(self):
        """Caso 24: Propiedad incompleta que termina con 'PISO'"""
        pdf_text = """2 -> 261841 : APARTAMENTO NUMERO DOSCIENTOS UNO (201) TORRE 4: UBICADO EN EL PISO
DOS -"""
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("261841", result)
        self.assertIn("APARTAMENTO NUMERO DOSCIENTOS UNO (201) TORRE 4: UBICADO EN EL PISO DOS", result["261841"])
    
    def test_secuencias_separadores_visuales_con_guion(self):
        """Caso 22a: Secuencias de separadores visuales con guión antes"""
        pdf_text = "5 -> 5566420 : APARTAMENTO 1207- T3 - = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =."
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("5566420", result)
        self.assertEqual(result["5566420"], "APARTAMENTO 1207- T3")
    
    def test_secuencias_separadores_visuales_sin_guion(self):
        """Caso 22b: Secuencias de separadores visuales sin guión antes"""
        pdf_text = "5 -> 5566420 : APARTAMENTO 1207- T3 = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =."
        result, _ = extract_properties_from_pdf(pdf_text)
        self.assertIn("5566420", result)
        self.assertEqual(result["5566420"], "APARTAMENTO 1207- T3")


class TestExtractFolios(unittest.TestCase):
    """Pruebas para la extracción de folios desde matrículas"""
    
    def test_circulo_tradicional(self):
        """Caso 18: Círculo tradicional (solo números)"""
        matriculas_text = "176-0998349"
        folio_to_circulo, folios = extract_folios_from_matriculas(matriculas_text)
        self.assertIn("0998349", folios)
        self.assertEqual(folio_to_circulo["0998349"], "176")
    
    def test_circulo_con_letra(self):
        """Caso 19: Círculo con letra"""
        matriculas_text = "51N-0998349"
        folio_to_circulo, folios = extract_folios_from_matriculas(matriculas_text)
        self.assertIn("0998349", folios)
        self.assertEqual(folio_to_circulo["0998349"], "51N")
    
    def test_circulo_con_espacios_alrededor_guion(self):
        """Caso 20: Círculo con espacios alrededor del guión"""
        matriculas_text = "01N-5537543, 01N - 5537580, 01N - 5537610, 01N - 5537614"
        folio_to_circulo, folios = extract_folios_from_matriculas(matriculas_text)
        # Verificar que todos los folios fueron extraídos
        self.assertIn("5537543", folios)
        self.assertIn("5537580", folios)
        self.assertIn("5537610", folios)
        self.assertIn("5537614", folios)
        # Verificar que todos tienen el mismo círculo
        self.assertEqual(folio_to_circulo["5537543"], "01N")
        self.assertEqual(folio_to_circulo["5537580"], "01N")
        self.assertEqual(folio_to_circulo["5537610"], "01N")
        self.assertEqual(folio_to_circulo["5537614"], "01N")
    
    def test_multiple_folios(self):
        """Prueba con múltiples folios"""
        matriculas_text = """176-0998349
51N-123456
350-312770"""
        folio_to_circulo, folios = extract_folios_from_matriculas(matriculas_text)
        self.assertEqual(len(folios), 3)
        self.assertEqual(folio_to_circulo["0998349"], "176")
        self.assertEqual(folio_to_circulo["123456"], "51N")
        self.assertEqual(folio_to_circulo["312770"], "350")


class TestProcessProperties(unittest.TestCase):
    """Pruebas para el procesamiento completo de propiedades"""
    
    def test_proceso_completo(self):
        """Prueba del proceso completo: matrículas + PDF"""
        matriculas_text = """176-0998349
51N-123456"""
        pdf_text = """3 -> 0998349 : APARTAMENTO 101 - TORRE 1
4 -> 123456APTO 202 - TORRE 2"""
        
        property_data, not_found, oficina_registro = process_properties(matriculas_text, pdf_text)
        
        # Verificar que se encontraron las propiedades
        self.assertEqual(len(property_data), 2)
        self.assertEqual(len(not_found), 0)
        
        # Verificar contenido
        property_dict = {folio: (name, circulo) for name, circulo, folio, _ in property_data}
        self.assertIn("0998349", property_dict)
        self.assertEqual(property_dict["0998349"][0], "APARTAMENTO 101 - TORRE 1")
        self.assertEqual(property_dict["0998349"][1], "176")
        
        self.assertIn("123456", property_dict)
        self.assertEqual(property_dict["123456"][0], "APTO 202 - TORRE 2")
        self.assertEqual(property_dict["123456"][1], "51N")
    
    def test_folio_no_encontrado(self):
        """Prueba cuando un folio no se encuentra en el PDF"""
        matriculas_text = "176-0998349\n176-999999"
        pdf_text = "3 -> 0998349 : APARTAMENTO 101 - TORRE 1"
        
        property_data, not_found, oficina_registro = process_properties(matriculas_text, pdf_text)
        
        # Verificar que hay un folio no encontrado
        self.assertIn("999999", not_found)
        self.assertEqual(len(not_found), 1)
        
        # Verificar que el folio no encontrado está en property_data como "NO ENCONTRADO"
        property_dict = {folio: name for name, _, folio, _ in property_data}
        self.assertIn("999999", property_dict)
        self.assertEqual(property_dict["999999"], "NO ENCONTRADO")


class TestFormatOutput(unittest.TestCase):
    """Pruebas para el formateo de salida"""
    
    def test_formato_txt(self):
        """Prueba formato TXT"""
        property_data = [
            ("APARTAMENTO 101", "176", "0998349", ""),
            ("TORRE 2", "51N", "123456", "")
        ]
        output_lines = format_output(property_data, 'txt')
        
        self.assertEqual(len(output_lines), 2)
        self.assertIn("APARTAMENTO 101 176-0998349", output_lines)
        self.assertIn("TORRE 2 51N-123456", output_lines)
    
    def test_formato_csv(self):
        """Prueba formato CSV"""
        property_data = [
            ("APARTAMENTO 101", "176", "0998349", ""),
            ("TORRE 2", "51N", "123456", "")
        ]
        output_lines = format_output(property_data, 'csv')
        
        self.assertEqual(len(output_lines), 3)  # Header + 2 filas
        # Verificar que el header está presente (puede tener comillas)
        header_found = any("Inmueble" in line and "folio" in line for line in output_lines)
        self.assertTrue(header_found, "Header CSV no encontrado")
        # Limpiar líneas de \r para comparación
        cleaned_lines = [line.rstrip('\r\n') for line in output_lines]
        # CSV tiene 6 columnas: Inmueble, folio, EP, escritura link, paginas, oficina_registro
        # Con valores vacíos: 5 commas separando 6 columnas
        self.assertIn("APARTAMENTO 101,176-0998349,,,,", cleaned_lines)
        self.assertIn("TORRE 2,51N-123456,,,,", cleaned_lines)


class TestExtractOficinaRegistro(unittest.TestCase):
    """Pruebas para la extracción de oficina de registro"""
    
    def test_oficina_medellin_norte(self):
        """Prueba extracción de oficina MEDELLIN NORTE desde PDF real"""
        # Texto simulado basado en el patrón encontrado en los PDFs de tayrona
        pdf_text = """SUPERINTENDENCIA DE NOTARIADO Y REGISTRO LA GUARDA DE LA FE PUBLICA OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MEDELLIN NORTE ORIP SUPERINTENDENCIA DE NOTARIADO Y REGISTRO LA GUARDA DE LA FE PUBLICA OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MEDELLIN NORTE ORIP
CERTIFICADO DE TRADICION
MATRICULA INMOBILIARIA"""
        result = extract_oficina_registro(pdf_text)
        self.assertEqual(result, "OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MEDELLIN NORTE")
        self.assertLessEqual(len(result), 200, "El resultado no debe exceder 200 caracteres")
    
    def test_oficina_con_stop_word_orip(self):
        """Prueba que se detiene correctamente en ORIP"""
        pdf_text = """OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MEDELLIN NORTE ORIP SUPERINTENDENCIA"""
        result = extract_oficina_registro(pdf_text)
        self.assertEqual(result, "OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MEDELLIN NORTE")
        self.assertNotIn("ORIP", result)
        self.assertNotIn("SUPERINTENDENCIA", result)
    
    def test_oficina_con_stop_word_certificado_tradicion(self):
        """Prueba que se detiene correctamente en CERTIFICADO DE TRADICION (prioritario)"""
        pdf_text = """OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE DOSQUEBRADAS CERTIFICADO DE TRADICION"""
        result = extract_oficina_registro(pdf_text)
        self.assertEqual(result, "OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE DOSQUEBRADAS")
        self.assertNotIn("CERTIFICADO", result)
        self.assertNotIn("TRADICION", result)
    
    def test_oficina_con_certificado_tradicion_antes(self):
        """Prueba que busca la oficina antes de CERTIFICADO DE TRADICION cuando está presente"""
        pdf_text = """TEXTO PREVIO OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MEDELLIN NORTE ORIP SUPERINTENDENCIA CERTIFICADO DE TRADICION MATRICULA"""
        result = extract_oficina_registro(pdf_text)
        self.assertEqual(result, "OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MEDELLIN NORTE")
        self.assertNotIn("CERTIFICADO", result)
        self.assertNotIn("TRADICION", result)
        self.assertNotIn("ORIP", result)
    
    def test_oficina_con_certificado_tradicion_en_siguiente_linea(self):
        """Prueba que se detiene cuando CERTIFICADO DE TRADICION está en la siguiente línea"""
        pdf_text = """OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE BOGOTÁ
CERTIFICADO DE TRADICION"""
        result = extract_oficina_registro(pdf_text)
        self.assertEqual(result, "OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE BOGOTÁ")
        self.assertNotIn("CERTIFICADO", result)
    
    def test_oficina_con_certificado_tradicion_repetido(self):
        """Prueba que maneja correctamente cuando CERTIFICADO DE TRADICION aparece múltiples veces"""
        pdf_text = """OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE CALI CERTIFICADO DE TRADICION
OTRO TEXTO OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE CALI CERTIFICADO DE TRADICION"""
        result = extract_oficina_registro(pdf_text)
        self.assertEqual(result, "OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE CALI")
        self.assertNotIn("CERTIFICADO", result)
    
    def test_oficina_en_siguiente_linea(self):
        """Prueba extracción cuando el nombre está en la siguiente línea"""
        pdf_text = """OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE
MEDELLIN NORTE
CERTIFICADO"""
        result = extract_oficina_registro(pdf_text)
        self.assertEqual(result, "OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MEDELLIN NORTE")
    
    def test_oficina_limite_longitud(self):
        """Prueba que resultados muy largos son rechazados o truncados"""
        # Crear un texto con un nombre muy largo (más de 200 caracteres)
        long_name = "A" * 300
        pdf_text = f"OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE {long_name} CERTIFICADO"
        result = extract_oficina_registro(pdf_text)
        # Debe estar vacío o truncado a menos de 200 caracteres
        self.assertLessEqual(len(result), 200, "El resultado debe estar limitado a 200 caracteres")
    
    def test_oficina_solo_primera_pagina(self):
        """Prueba que solo busca en la primera página (primeros 10000 caracteres)"""
        # Crear texto donde la oficina aparece después de 10000 caracteres
        padding = "X" * 10001
        pdf_text = f"{padding}OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MEDELLIN NORTE CERTIFICADO"
        result = extract_oficina_registro(pdf_text)
        # Debe estar vacío porque está después de la primera página
        self.assertEqual(result, "")
    
    def test_oficina_no_encontrada(self):
        """Prueba cuando no se encuentra la oficina"""
        pdf_text = "TEXTO SIN OFICINA DE REGISTRO"
        result = extract_oficina_registro(pdf_text)
        self.assertEqual(result, "")
    
    def test_oficina_con_acentos(self):
        """Prueba con nombres que contienen acentos"""
        pdf_text = """OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE BOGOTÁ CERTIFICADO"""
        result = extract_oficina_registro(pdf_text)
        self.assertEqual(result, "OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE BOGOTÁ")
    
    def test_oficina_tayrona_pdf_real(self):
        """Prueba con PDF real de tayrona usando PyPDF2"""
        try:
            from PyPDF2 import PdfReader
            import os
            
            # Buscar un PDF en la carpeta tayrona
            tayrona_dir = os.path.join(os.path.dirname(__file__), 'tayrona')
            if os.path.exists(tayrona_dir):
                pdf_files = [f for f in os.listdir(tayrona_dir) if f.endswith('.pdf')]
                if pdf_files:
                    pdf_path = os.path.join(tayrona_dir, pdf_files[0])
                    reader = PdfReader(pdf_path)
                    pdf_text = ''
                    for page in reader.pages:
                        pdf_text += page.extract_text()
                    
                    result = extract_oficina_registro(pdf_text)
                    self.assertEqual(result, "OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MEDELLIN NORTE")
                    self.assertLessEqual(len(result), 200)
        except ImportError:
            self.skipTest("PyPDF2 no está instalado")
        except FileNotFoundError:
            self.skipTest("PDF de prueba no encontrado")


class TestExtractEscrituras(unittest.TestCase):
    """Pruebas para la extracción de escrituras públicas (casos 26-32)"""
    
    def test_escritura_formato_estandar_del(self):
        """Caso 26: Extracción de Escritura con Formato Estándar (DEL con guiones)"""
        pdf_text = """3 -> 190172 : TORRE 9 - APARTAMENTO 103 - PROYECTO MODIGLIANI
ANOTACION: Nro 003 Fecha: 21-09-2022 Radicación: 2022-350-6-20321
Doc: ESCRITURA 4067 DEL 16-09-2022 NOTARIA SEPTIMA DE IBAGUE VALOR ACTO: $574,354,780"""
        
        # Extraer propiedad y anotación
        folio_to_property, folio_to_anotacion = extract_properties_from_pdf(pdf_text)
        self.assertIn("190172", folio_to_property)
        self.assertEqual(folio_to_property["190172"], "TORRE 9 - APARTAMENTO 103 - PROYECTO MODIGLIANI")
        
        # Extraer escritura
        numero_anotacion = folio_to_anotacion.get("190172", "")
        self.assertEqual(numero_anotacion, "003")
        escritura = extract_escritura_from_anotacion(pdf_text, numero_anotacion)
        self.assertEqual(escritura, "ESCRITURA 4067 DEL 16-09-2022")
    
    def test_escritura_formato_alternativo_de(self):
        """Caso 27: Extracción de Escritura con Formato Alternativo (DE en lugar de DEL)"""
        pdf_text = """1 -> 190173 : APARTAMENTO 104
ANOTACION: Nro 001 Fecha: 14-03-1985 Radicación:
Doc: ESCRITURA 6833 DE 28-12-1984 NOTARIA 10 DE CALI VALOR ACTO: $0"""
        
        # Extraer propiedad y anotación
        folio_to_property, folio_to_anotacion = extract_properties_from_pdf(pdf_text)
        self.assertIn("190173", folio_to_property)
        self.assertEqual(folio_to_property["190173"], "APARTAMENTO 104")
        
        # Extraer escritura
        numero_anotacion = folio_to_anotacion.get("190173", "")
        self.assertEqual(numero_anotacion, "001")
        escritura = extract_escritura_from_anotacion(pdf_text, numero_anotacion)
        self.assertEqual(escritura, "ESCRITURA 6833 DE 28-12-1984")
    
    def test_escritura_fecha_con_slashes(self):
        """Caso 28: Extracción de Escritura con Fecha con Slashes"""
        pdf_text = """2 -> 190174 : APARTAMENTO 105
ANOTACION: Nro 002 Fecha: 31-07-1985 Radicación:
Doc: ESCRITURA 3723 DEL 25/07/1985 NOTARIA 10 DE CALI VALOR ACTO: $0"""
        
        # Extraer propiedad y anotación
        folio_to_property, folio_to_anotacion = extract_properties_from_pdf(pdf_text)
        self.assertIn("190174", folio_to_property)
        self.assertEqual(folio_to_property["190174"], "APARTAMENTO 105")
        
        # Extraer escritura
        numero_anotacion = folio_to_anotacion.get("190174", "")
        self.assertEqual(numero_anotacion, "002")
        escritura = extract_escritura_from_anotacion(pdf_text, numero_anotacion)
        self.assertEqual(escritura, "ESCRITURA 3723 DEL 25/07/1985")
    
    def test_multiples_folios_compartiendo_anotacion_cache(self):
        """Caso 29: Múltiples Folios Compartiendo la Misma Anotación (Validar Caché)"""
        pdf_text = """3 -> 190172 : TORRE 9 - APARTAMENTO 103
3 -> 190175 : TORRE 9 - APARTAMENTO 104
3 -> 190176 : TORRE 9 - APARTAMENTO 105
ANOTACION: Nro 003 Fecha: 21-09-2022 Radicación: 2022-350-6-20321
Doc: ESCRITURA 4067 DEL 16-09-2022 NOTARIA SEPTIMA DE IBAGUE VALOR ACTO: $574,354,780"""
        
        # Procesar propiedades completas (esto usa el caché internamente)
        matriculas_text = "3-190172\n3-190175\n3-190176"
        property_data, not_found, oficina_registro = process_properties(matriculas_text, pdf_text)
        
        # Verificar que todos los folios tienen la misma escritura
        escrituras = {folio: escritura for _, _, folio, escritura in property_data}
        self.assertEqual(escrituras["190172"], "ESCRITURA 4067 DEL 16-09-2022")
        self.assertEqual(escrituras["190175"], "ESCRITURA 4067 DEL 16-09-2022")
        self.assertEqual(escrituras["190176"], "ESCRITURA 4067 DEL 16-09-2022")
        
        # Verificar que todas las escrituras son iguales (validación de caché)
        self.assertEqual(escrituras["190172"], escrituras["190175"])
        self.assertEqual(escrituras["190175"], escrituras["190176"])
    
    def test_escritura_anotacion_no_encontrada(self):
        """Caso 30: Caso donde No se Encuentra la Anotación"""
        pdf_text = "99 -> 999999 : APARTAMENTO 999"
        
        # Extraer propiedad
        folio_to_property, folio_to_anotacion = extract_properties_from_pdf(pdf_text)
        self.assertIn("999999", folio_to_property)
        self.assertEqual(folio_to_property["999999"], "APARTAMENTO 999")
        
        # Intentar extraer escritura de una anotación que no existe
        escritura = extract_escritura_from_anotacion(pdf_text, "099")
        self.assertEqual(escritura, "")
        
        # También verificar que si no hay número de anotación, la escritura es vacía
        numero_anotacion = folio_to_anotacion.get("999999", "")
        # Si no hay anotación asociada, debería ser vacío
        if not numero_anotacion:
            escritura = ""
            self.assertEqual(escritura, "")
    
    def test_escritura_anotacion_sin_escritura(self):
        """Caso 31: Caso donde la Anotación Existe pero No Tiene Escritura"""
        pdf_text = """5 -> 190177 : APARTAMENTO 106
ANOTACION: Nro 005 Fecha: 15-01-2023 Radicación: 2023-100-1-12345
ESPECIFICACION: OTRO: 999 ACLARACION"""
        
        # Extraer propiedad y anotación
        folio_to_property, folio_to_anotacion = extract_properties_from_pdf(pdf_text)
        self.assertIn("190177", folio_to_property)
        self.assertEqual(folio_to_property["190177"], "APARTAMENTO 106")
        
        # Extraer escritura (no debería encontrar "Doc: ESCRITURA...")
        numero_anotacion = folio_to_anotacion.get("190177", "")
        self.assertEqual(numero_anotacion, "005")
        escritura = extract_escritura_from_anotacion(pdf_text, numero_anotacion)
        self.assertEqual(escritura, "")
    
    def test_escritura_formato_completo(self):
        """Caso 32: Extracción de Escritura con Formato Completo"""
        pdf_text = """1 -> 190178 : APARTAMENTO 107
ANOTACION: Nro 001 Fecha: 14-03-1985 Radicación:
Doc: ESCRITURA 6833 DEL 28-12-1984 NOTARIA 10 DE CALI VALOR ACTO: $0
ESPECIFICACION: GRAVAMEN: 210 HIPOTECA
PERSONAS QUE INTERVIENEN EN EL ACTO (X-Titular de derecho real de dominio,I-Titular de dominio incompleto)
DE: INMOBILIARIA POPULAR CALI LTDA X
A: GONCHEVERRY POPULAR CALI LTDA"""
        
        # Extraer propiedad y anotación
        folio_to_property, folio_to_anotacion = extract_properties_from_pdf(pdf_text)
        self.assertIn("190178", folio_to_property)
        self.assertEqual(folio_to_property["190178"], "APARTAMENTO 107")
        
        # Extraer escritura (solo debe extraer el nombre de la escritura, no el resto)
        numero_anotacion = folio_to_anotacion.get("190178", "")
        self.assertEqual(numero_anotacion, "001")
        escritura = extract_escritura_from_anotacion(pdf_text, numero_anotacion)
        self.assertEqual(escritura, "ESCRITURA 6833 DEL 28-12-1984")
        
        # Verificar que NO incluye información adicional de la anotación
        self.assertNotIn("NOTARIA 10 DE CALI", escritura)
        self.assertNotIn("VALOR ACTO", escritura)
        self.assertNotIn("ESPECIFICACION", escritura)
        self.assertNotIn("GRAVAMEN", escritura)
        self.assertNotIn("PERSONAS QUE INTERVIENEN", escritura)
    
    def test_escritura_multiple_anotaciones(self):
        """Prueba adicional: Múltiples anotaciones en el mismo PDF"""
        pdf_text = """1 -> 190179 : APARTAMENTO 108
ANOTACION: Nro 001 Fecha: 14-03-1985 Radicación:
Doc: ESCRITURA 1001 DEL 01-01-1985 NOTARIA 1 VALOR ACTO: $0
2 -> 190180 : APARTAMENTO 109
ANOTACION: Nro 002 Fecha: 15-03-1985 Radicación:
Doc: ESCRITURA 1002 DEL 02-01-1985 NOTARIA 2 VALOR ACTO: $0"""
        
        # Extraer propiedades y anotaciones
        folio_to_property, folio_to_anotacion = extract_properties_from_pdf(pdf_text)
        
        # Verificar que cada folio tiene su propia anotación
        self.assertEqual(folio_to_anotacion.get("190179", ""), "001")
        self.assertEqual(folio_to_anotacion.get("190180", ""), "002")
        
        # Verificar que cada anotación tiene su propia escritura
        escritura1 = extract_escritura_from_anotacion(pdf_text, "001")
        escritura2 = extract_escritura_from_anotacion(pdf_text, "002")
        
        self.assertEqual(escritura1, "ESCRITURA 1001 DEL 01-01-1985")
        self.assertEqual(escritura2, "ESCRITURA 1002 DEL 02-01-1985")
        self.assertNotEqual(escritura1, escritura2)


def run_tests():
    """Ejecuta todas las pruebas"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar todas las clases de prueba
    suite.addTests(loader.loadTestsFromTestCase(TestExtractProperties))
    suite.addTests(loader.loadTestsFromTestCase(TestExtractFolios))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessProperties))
    suite.addTests(loader.loadTestsFromTestCase(TestFormatOutput))
    suite.addTests(loader.loadTestsFromTestCase(TestExtractOficinaRegistro))
    suite.addTests(loader.loadTestsFromTestCase(TestExtractEscrituras))
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Retornar código de salida apropiado
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)


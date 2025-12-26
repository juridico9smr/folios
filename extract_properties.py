#!/usr/bin/env python3
"""
Script para extraer nombres de propiedades del certificado PDF
y asociarlos con los números de folio.

Uso:
    python3 extract_properties.py [nombre_proyecto] [--format txt|csv]
    
    Si no se proporciona nombre_proyecto, se usa el valor definido en PROYECTO_NOMBRE
    
    Ejemplo:
    python3 extract_properties.py "2 1 P110701 VENTURA"
    python3 extract_properties.py "2 1 P110701 VENTURA" --format csv

El script:
1. Lee los números de folio del archivo '<nombre_proyecto>/matriculas.txt'
2. Extrae las propiedades del PDF '<nombre_proyecto>/certificado.pdf'
3. Genera el archivo '<nombre_proyecto>/<nombre_proyecto>.txt' o '.csv' según el formato:
   - TXT: [nombre propiedad] [numero_circulo]-[folio]
   - CSV: nombre_inmueble,folio (sin headers)
"""

import re
import os
import sys
import io
import csv

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("Instalando PyPDF2...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PyPDF2'])
    from PyPDF2 import PdfReader


def extract_properties_from_pdf(pdf_text):
    """
    Extrae las propiedades de un PDF dado su texto.
    Maneja propiedades que pueden estar en múltiples líneas.
    
    Args:
        pdf_text: Texto extraído del PDF
        
    Returns:
        tuple: (dict, dict) donde:
            - Primer dict: folio -> nombre de propiedad
            - Segundo dict: folio -> numero_anotacion
    """
    folio_to_property = {}
    folio_to_anotacion = {}
    
    # Dividir en líneas para procesar propiedades multilínea
    lines = pdf_text.split('\n')
    
    # Patrón para detectar inicio de una propiedad: numero -> folio : o numero -> folio -
    # También maneja casos con puntos: numero -> folio. propiedad o numero -> folio..propiedad
    # También maneja casos donde el folio y la propiedad están concatenados (ej: "230510APTO")
    # Usamos dos patrones: uno para formato normal y otro para formato concatenado
    # El patrón normal acepta: :, -, ., o espacios después del folio
    # Nota: el guión debe estar al final o escapado en la clase de caracteres
    # 
    # Ejemplos de formatos soportados:
    # - "5 -> 5566420 : APARTAMENTO 101" (dos puntos)
    # - "5 -> 5566420 - APARTAMENTO 101" (guión)
    # - "5 -> 5566420 : - APARTAMENTO NRO 0121 PRIMER PISO TORRE 1 ETAPA 1" (dos puntos y guión)
    # - "5 -> 5566420. APARTAMENTO 101" (punto)
    # - "5 -> 5566420 APARTAMENTO 101" (solo espacio)
    pattern_folio_normal = r'(\d+)\s*->\s*(\d+)\s*[\.:\s-]+\s*(.*)'
    
    def extract_concatenated_folio(line):
        """
        Extrae folio y propiedad cuando están concatenados sin separador.
        Detecta cuando el folio termina y comienza la propiedad usando palabras clave comunes.
        
        Ejemplos:
        - "4 -> 230510APTO 0129" -> folio: 230510, propiedad: "APTO 0129"
        - "4 -> 230510TORRE 8" -> folio: 230510, propiedad: "TORRE 8"
        - "4 -> 2305100129" -> folio: 230510, propiedad: "0129" (si 0129 parece ser parte de la propiedad)
        """
        # Patrón base: numero -> folio seguido de algo
        base_pattern = r'(\d+)\s*->\s*(\d+)'
        base_match = re.search(base_pattern, line)
        
        if not base_match:
            return None
        
        num_before = base_match.group(1)
        folio_start_pos = base_match.end(2)
        remaining_text = line[folio_start_pos:].strip()
        
        # Si hay separador (: o -), usar el patrón normal
        if re.match(r'^\s*[:-]\s*', remaining_text):
            return None
        
        # Si está vacío, no hay propiedad
        if not remaining_text:
            return None
        
        # Palabras clave comunes que indican inicio de propiedad
        property_keywords = [
            r'^APTO\.?\s*',        # APTO o APTO. seguido de espacio o directamente número
            r'^APARTAMENTO\s+',     # APARTAMENTO seguido de espacio
            r'^TORRE\s+',          # TORRE seguido de espacio
            r'^LOCAL\s+',          # LOCAL seguido de espacio
            r'^DEPOSITO\s+',       # DEPOSITO seguido de espacio
            r'^PARQUEADERO\s+',    # PARQUEADERO seguido de espacio
            r'^ETAPA\s+',          # ETAPA seguido de espacio
            r'^PISO\s+',           # PISO seguido de espacio
            r'^BODEGA\s+',         # BODEGA seguido de espacio
            r'^OFICINA\s+',        # OFICINA seguido de espacio
            r'^LOTE\s+',           # LOTE seguido de espacio
            r'^MANZANA\s+',        # MANZANA seguido de espacio
            r'^CESION\s+',         # CESION seguido de espacio
            r'^CESIÓN\s+',         # CESIÓN seguido de espacio
        ]
        
        # Buscar si comienza con alguna palabra clave
        for keyword_pattern in property_keywords:
            if re.search(keyword_pattern, remaining_text, re.IGNORECASE):
                # Encontrar dónde termina el folio (justo antes de la palabra clave)
                # Usar un lookahead más flexible que capture todo después de la palabra clave
                folio_match = re.search(rf'(\d+)\s*->\s*(\d+)(?={keyword_pattern})', line, re.IGNORECASE)
                if folio_match:
                    folio = folio_match.group(2)
                    # Capturar todo el texto después del folio, no solo hasta la palabra clave
                    property_start = remaining_text
                    return (num_before, folio, property_start)
        
        # Si no comienza con palabra clave, buscar transición de dígitos a letras
        # Ejemplo: "230510APTO" -> folio termina en 0, propiedad empieza con A
        # Incluir punto (.) en el patrón para casos como "174484APTO. 102"
        transition_match = re.search(r'(\d+)\s*->\s*(\d+)([A-Z][A-Z0-9\s\-\.]*)', line)
        if transition_match:
            num_before = transition_match.group(1)
            folio = transition_match.group(2)
            property_start = transition_match.group(3)
            return (num_before, folio, property_start)
        
        # Si hay un número seguido de texto (ej: "2305100129 TORRE"), 
        # asumir que el folio termina cuando empiezan las letras
        # Pero esto es más arriesgado, así que lo dejamos como último recurso
        number_letter_match = re.search(r'(\d+)\s*->\s*(\d+)(\d*\s*[A-Z][A-Z0-9\s\-]*)', line)
        if number_letter_match:
            num_before = number_letter_match.group(1)
            folio = number_letter_match.group(2)
            property_start = number_letter_match.group(3).lstrip('0123456789').strip()
            if property_start:  # Solo si hay algo después de quitar los números
                return (num_before, folio, property_start)
        
        return None
    
    # Patrones comunes de headers y footers a filtrar (definirlos antes del loop principal)
    footer_patterns = [
            r'La validez de este documento',
            r'certificados\.supernotariado\.gov\.co',
            r'SNR',
            r'SUPERINTENDENCIA',
            r'OFICINA DE REGISTRO',
            r'CERTIFICADO DE TRADICION',
            r'MATRICULA INMOBILIARIA',
            r'Pagina \d+',
            r'TURNO:',
            r'Impreso el',
            r'No tiene validez sin la firma',
            r'ESTE CERTIFICADO REFLEJA',
            r'HASTA LA FECHA Y HORA',
            r'Certificado generado con el Pin No:',
            r'Nro Matrícula:',
            r'SALVEDADES:',
            r'Información Anterior o Corregida',
            r'Anotación',
            r'Anotacion',
            r'Nro corrección',
            r'Radicación:',
            r'Radicacion:',
            r'CORREGIDO EN CABIDA',
            r'CORREGIDO EN LINDEROS',
            r'NUMERO DE DOCUMENTO',
            r'VALE\.',
            r'ART\.\d+',
            r'LEY \d+',
            r'SE CORRIGE',
            r'SE CREA',
            r'\* ?\* ?\*',  # Filtrar "***" (cualquier número de espacios intermedios)
        ]
    
    def is_footer_or_header(line):
        """Verifica si una línea es un footer o header común"""
        line_upper = line.upper()
        for pattern in footer_patterns:
            if re.search(pattern, line_upper, re.IGNORECASE):
                return True
        return False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Buscar el patrón de folio primero
        # NO saltar líneas que contengan el patrón de folio, incluso si también tienen headers
        # (los headers se limpiarán después durante el proceso de limpieza)
        match = re.search(pattern_folio_normal, line)
        
        # Si no encontramos con el patrón normal, intentar con el concatenado
        if not match:
            concatenated_result = extract_concatenated_folio(line)
            if not concatenated_result:
                i += 1
                continue
            num_before, folio, property_start = concatenated_result
        else:
            num_before, folio, property_start = match.groups()
        
        # Si el folio ya lo tenemos, saltarlo (tomar el primero)
        if folio in folio_to_property:
            i += 1
            continue
        
        # Comenzar a construir el nombre de la propiedad
        property_parts = [property_start.strip()]
        
        # Continuar leyendo líneas siguientes hasta encontrar:
        # 1. El siguiente patrón de folio (numero -> folio)
        # 2. La continuación completa de la propiedad (puede estar después de headers/footers)
        # 3. Máximo 20 líneas adicionales (para permitir saltar headers/footers entre páginas)
        j = i + 1
        lines_read = 0
        max_additional_lines = 20  # Aumentado para permitir saltar headers/footers
        
        def looks_incomplete(property_text):
            """Verifica si una propiedad parece estar incompleta"""
            # Palabras que sugieren que la propiedad continúa
            incomplete_indicators = [
                    r'\bEN\s*$',           # Termina con "EN"
                    r'\bEN EL\s*$',        # Termina con "EN EL"
                    r'\bEN LA\s*$',        # Termina con "EN LA"
                    r'\bEN LOS\s*$',       # Termina con "EN LOS"
                    r'\bEN LAS\s*$',       # Termina con "EN LAS"
                    r'\bEL\s*$',           # Termina con "EL"
                    r'\bDE\s*$',           # Termina con "DE"
                    r'\bDEL\s*$',          # Termina con "DEL"
                    r'\bLA\s*$',           # Termina con "LA"
                    r'\bLAS\s*$',          # Termina con "LAS"
                    r'\bLOS\s*$',          # Termina con "LOS"
                    r'\bUN\s*$',           # Termina con "UN"
                    r'\bUNA\s*$',          # Termina con "UNA"
                    r'\bPISO\s*$',         # Termina con "PISO" (sin número, ej: "PISO DOS")
                    r'\bTORRE\s*$',        # Termina con "TORRE" (sin número)
                    r'\bAPARTAMENTO\s*$',   # Termina con "APARTAMENTO" (sin número)
                    r'\bLOCAL\s*$',        # Termina con "LOCAL" (sin número)
                    r'\bDEPOSITO\s*$',     # Termina con "DEPOSITO" (sin número)
                    r'\bPARQUEADERO\s*$',   # Termina con "PARQUEADERO" (sin número)
                r'-\s*$',              # Termina con guión
            ]
            for pattern in incomplete_indicators:
                if re.search(pattern, property_text, re.IGNORECASE):
                    return True
            return False
        
        def looks_like_continuation(line, previous_text=''):
            """Verifica si una línea parece ser continuación de una propiedad"""
            line_upper = line.upper().strip()
            if not line_upper:
                return False
            
            # Si la línea anterior termina con "PISO" y esta línea tiene números o palabras ordinales, es continuación
            if previous_text:
                prev_upper = previous_text.upper()
                if re.search(r'\bPISO\s*$', prev_upper):
                    # Si la línea actual tiene números ordinales o números, es continuación
                    if re.search(r'^(PRIMER|SEGUNDO|TERCER|CUARTO|QUINTO|SEXTO|SEPTIMO|OCTAVO|NOVENO|DECIMO|UNO|DOS|TRES|CUATRO|CINCO|SEIS|SIETE|OCHO|NUEVE|DIEZ|\d+)', line_upper):
                        return True
            
            # Patrones que indican continuación de propiedad
            continuation_patterns = [
                    r'^(PRIMER|SEGUNDO|TERCER|CUARTO|QUINTO|SEXTO|SEPTIMO|OCTAVO|NOVENO|DECIMO)\s+PISO',  # "QUINTO PISO"
                    r'^(UNO|DOS|TRES|CUATRO|CINCO|SEIS|SIETE|OCHO|NUEVE|DIEZ)\s*-',  # "DOS -" después de "PISO"
                    r'^\d+\s+PISO',  # "5 PISO"
                    r'^PISO\s+\d+',  # "PISO 5"
                    r'^TORRE\s+\d+',  # "TORRE 1"
                    r'^APARTAMENTO\s+\d+',  # "APARTAMENTO 101"
                    r'^LOCAL\s+\d+',  # "LOCAL 5"
                    r'^DEPOSITO\s+\d+',  # "DEPOSITO 10"
                    r'^PARQUEADERO',  # "PARQUEADERO..."
                    r'^UBICADO',  # "UBICADO..."
                    r'^EN EL',  # "EN EL..."
                    r'^EN LA',  # "EN LA..."
                    r'^DEL\s+\w+',  # "DEL PRIMER..."
                r'^DE\s+\w+',  # "DE PRIMER..."
            ]
            
            for pattern in continuation_patterns:
                if re.search(pattern, line_upper):
                    return True
            
            # Si la línea es muy corta (1-3 palabras) y tiene palabras comunes de propiedades, probablemente es continuación
            words = line_upper.split()
            if len(words) <= 3:
                common_words = ['PISO', 'TORRE', 'APARTAMENTO', 'LOCAL', 'DEPOSITO', 'PARQUEADERO', 'UBICADO', 
                               'PRIMER', 'SEGUNDO', 'TERCER', 'CUARTO', 'QUINTO', 'SEXTO', 'SEPTIMO', 'OCTAVO', 'NOVENO', 'DECIMO',
                               'UNO', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE', 'DIEZ']
                if any(word in line_upper for word in common_words):
                    return True
            
            return False
        
        # Contador de headers/footers consecutivos
        consecutive_headers = 0
        max_consecutive_headers = 15  # Aumentado para permitir saltar más headers/footers
        
        # Verificar si la propiedad inicial parece incompleta
        is_incomplete = looks_incomplete(property_start.strip())
        
        while j < len(lines) and lines_read < max_additional_lines:
            next_line = lines[j].strip()
            
            # Si encontramos el siguiente patrón de folio, parar
            if re.search(pattern_folio_normal, lines[j]) or extract_concatenated_folio(lines[j]):
                break
            
            # Si es un footer o header
            if is_footer_or_header(next_line):
                consecutive_headers += 1
                
                # Verificar el estado actual de la propiedad
                current_property = ' '.join(property_parts)
                is_currently_incomplete = looks_incomplete(current_property)
                
                # Estrategia mejorada para manejar headers/footers:
                # 1. Si aún no hemos capturado contenido de la propiedad (solo el inicio),
                #    y encontramos un header/footer, probablemente es un header antes de la propiedad
                #    que ya fue procesado. Continuar buscando.
                if len(property_parts) == 1 and len(property_parts[0].strip()) < 50:
                    # Probablemente es un header antes de la propiedad, continuar
                    j += 1
                    continue
                
                # 2. Si la propiedad está incompleta, podemos continuar buscando después de footers
                #    (para casos donde la propiedad está dividida entre páginas)
                if is_currently_incomplete and consecutive_headers <= 5:
                    # Continuar buscando si la propiedad está incompleta y no hay demasiados headers
                    j += 1
                    continue
                
                # 3. Si la propiedad parece completa y encontramos headers/footers,
                #    verificar si hay más contenido útil después
                if not is_currently_incomplete:
                    # Buscar en las siguientes 3 líneas si hay contenido que parezca continuación
                    found_useful_content = False
                    for k in range(j + 1, min(j + 4, len(lines))):
                        check_line = lines[k].strip()
                        if check_line and not is_footer_or_header(check_line):
                            # Si hay contenido que parece continuación, continuar
                            if looks_like_continuation(check_line, current_property):
                                found_useful_content = True
                                break
                            # Si encontramos otro folio, definitivamente parar
                            if re.search(pattern_folio_normal, check_line) or extract_concatenated_folio(check_line):
                                break
                    
                    if not found_useful_content:
                        # No hay más contenido útil, terminar
                        break
                    else:
                        # Hay contenido útil después, continuar
                        j += 1
                        continue
                else:
                    # Si la propiedad parece completa o hay muchos headers, terminar
                    # Esto evita capturar información de la siguiente página
                    break
            else:
                consecutive_headers = 0  # Resetear contador
            
            # Si la línea está vacía
            if not next_line:
                # Si la propiedad está incompleta, continuar buscando
                if is_incomplete:
                    j += 1
                    continue
                # Si parece completa, verificar si hay más contenido
                elif property_parts:
                    current_property = ' '.join(property_parts)
                    if not looks_incomplete(current_property):
                        # Verificar las siguientes líneas para ver si hay continuación
                        found_continuation = False
                        for k in range(j + 1, min(j + 5, len(lines))):
                            check_line = lines[k].strip()
                            if check_line and not is_footer_or_header(check_line):
                                if looks_like_continuation(check_line) or re.search(pattern_folio_normal, check_line) or extract_concatenated_folio(check_line):
                                    found_continuation = True
                                    break
                        if not found_continuation:
                            break
                j += 1
                continue
            
            # Si la línea tiene contenido y no es footer/header
            if next_line:
                current_property = ' '.join(property_parts)
                
                # Si la propiedad está incompleta o parece continuación, agregarla
                if is_incomplete or looks_like_continuation(next_line, current_property) or not property_parts:
                    property_parts.append(next_line)
                    lines_read += 1
                    # Actualizar estado de incompletitud
                    updated_property = ' '.join(property_parts)
                    is_incomplete = looks_incomplete(updated_property)
                else:
                    # Si no parece continuación y ya tenemos contenido, verificar si debemos parar
                    if not looks_incomplete(current_property):
                        # Verificar si esta línea es realmente continuación
                        if not looks_like_continuation(next_line, current_property):
                            # Probablemente es otra cosa, parar
                            break
                        else:
                            property_parts.append(next_line)
                            lines_read += 1
                            updated_property = ' '.join(property_parts)
                            is_incomplete = looks_incomplete(updated_property)
            
            j += 1
        
        # Combinar todas las partes de la propiedad
        property_name_raw = ' '.join(property_parts)
        
        # Limpiar el nombre de la propiedad
        property_name = property_name_raw.strip()
        
        # Remover headers/footers que puedan estar concatenados en el texto
        # (a veces el PDF los concatena sin espacios)
        # Buscar headers conocidos y eliminar desde ahí hasta el final
        # Solo eliminar si viene después de un guión o espacio (para evitar eliminar parte del nombre)
        footer_cleanup_patterns = [
                r'\s*-\s*OFICINA DE REGISTRO.*$',
                r'\s*OFICINA DE REGISTRO.*$',
                r'\s*CERTIFICADO DE TRADICION.*$',
                r'\s*MATRICULA INMOBILIARIA.*$',
                r'\s*La validez de este documento.*$',
                r'\s*certificados\.supernotariado\.gov\.co.*$',
                r'\s*Certificado generado con el Pin No:.*$',
                r'\s*Nro Matrícula:.*$',
                r'\s*Pagina \d+.*$',
                r'\s*TURNO:.*$',
                r'\s*Impreso el.*$',
                r'\s*No tiene validez.*$',
                r'\s*ESTE CERTIFICADO REFLEJA.*$',
                r'\s*HASTA LA FECHA Y HORA.*$',
                r'\s*SNR.*$',
                r'\s*SUPERINTENDENCIA.*$',
                r'\s*SALVEDADES:.*$',
                r'\s*Información Anterior o Corregida.*$',
                r'\s*Anotación.*$',
                r'\s*Anotacion.*$',
                r'\s*Nro corrección.*$',
                r'\s*Nro correccion.*$',
                r'\s*Radicación:.*$',
                r'\s*Radicacion:.*$',
                r'\s*CORREGIDO EN CABIDA.*$',
                r'\s*CORREGIDO EN LINDEROS.*$',
                r'\s*NUMERO DE DOCUMENTO.*$',
                r'\s*VALE\..*$',
                r'\s*ART\.\d+.*$',
                r'\s*LEY \d+.*$',
        ]
        
        for pattern in footer_cleanup_patterns:
            property_name = re.sub(pattern, '', property_name, flags=re.IGNORECASE)
        
        # Remover espacios múltiples
        property_name = re.sub(r'\s+', ' ', property_name)
        
        # Remover secuencias de "= = = = ..." que aparecen como separadores visuales
        # Pueden aparecer con guiones antes (ej: "APARTAMENTO 1207- T3 - = = = = ...")
        # y pueden terminar con un punto
        # Patrón: busca guión opcional seguido de secuencia de "= = = = ..." (con espacios) y punto opcional al final
        property_name = re.sub(r'\s*-\s*(?:\s*=\s*){2,}\.?\s*$', '', property_name).strip()
        property_name = re.sub(r'(?:\s*=\s*){2,}\.?\s*$', '', property_name).strip()
        
        # Remover puntos y guiones al final si existen (con espacios antes)
        # PERO mantener el guión si es parte de una palabra (ej: "ETAPA -" o "PISO -")
        # Solo remover si hay múltiples guiones/puntos o si está claramente separado
        # Si termina con "ETAPA -", "PISO -", etc., mantener el guión
        if not re.search(r'\b(ETAPA|PISO|TORRE|APARTAMENTO|LOCAL|DEPOSITO|PARQUEADERO|BODEGA|OFICINA|LOTE|MANZANA)\s+-\s*$', property_name, re.IGNORECASE):
            property_name = re.sub(r'\s*[-.]+\s*$', '', property_name).strip()
        
        # Remover guiones al inicio si existen (como en "- APARTAMENTO...")
        # Esto maneja casos como "5 -> 5566420 : - APARTAMENTO..." donde el patrón
        # captura el guión inicial, pero lo removemos aquí para limpiar el resultado
        property_name = re.sub(r'^\s*[-]+\s*', '', property_name).strip()
        
        # Remover cualquier número de matrícula que quede al final (ej: "100-256825,100-262122,,,")
        property_name = re.sub(r'\d+-\d+[,\s]*$', '', property_name).strip()
        property_name = re.sub(r',+$', '', property_name).strip()
        
        # Si la propiedad está vacía después de limpiar, saltarla
        if property_name:
            folio_to_property[folio] = property_name
            # Guardar el número de anotación (num_before) para este folio
            # Formatear con 3 dígitos (ej: "3" -> "003")
            numero_anotacion = num_before.zfill(3)
            folio_to_anotacion[folio] = numero_anotacion
        
        i = j  # Continuar desde donde paramos
    else:
        i += 1
    
    return folio_to_property, folio_to_anotacion


def extract_oficina_registro(pdf_text):
    """
    Extrae la oficina de registro del certificado PDF.
    Busca el texto "OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE" 
    y extrae lo que viene después (ej: "DOSQUEBRADAS").
    Siempre está en la primera página.
    
    Args:
        pdf_text: Texto extraído del PDF
        
    Returns:
        str: Nombre de la oficina de registro (ej: "DOSQUEBRADAS") 
             o string vacío "" si no se encuentra
    """
    # Buscar el patrón: "OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE" seguido del nombre
    # El nombre puede estar en la misma línea o en la siguiente línea
    # Ejemplo: "OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE DOSQUEBRADAS"
    #          o "OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE\nDOSQUEBRADAS"
    
    # Patrón que captura el nombre después de "OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE"
    # hasta encontrar un salto de línea, "CERTIFICADO", "MATRICULA" o fin de línea
    pattern = r'OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE\s+([A-ZÁÉÍÓÚÑ\s]+?)(?:\s*\n|CERTIFICADO|MATRICULA|$)'
    match = re.search(pattern, pdf_text, re.IGNORECASE | re.MULTILINE)
    
    if match:
        oficina = match.group(1).strip()
        # Limpiar espacios múltiples
        oficina = re.sub(r'\s+', ' ', oficina)
        # Remover cualquier texto que pueda venir después (como "CERTIFICADO DE TRADICION")
        oficina = re.sub(r'\s+(CERTIFICADO|MATRICULA).*$', '', oficina, flags=re.IGNORECASE)
        oficina = oficina.strip()
        if oficina:
            return oficina
    
    # Si no se encontró en la misma línea, intentar buscar en la siguiente línea
    # Buscar la línea que contiene "OFICINA DE REGISTRO..." y tomar la siguiente línea
    lines = pdf_text.split('\n')
    for i, line in enumerate(lines):
        if re.search(r'OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE', line, re.IGNORECASE):
            # Si la línea siguiente existe y no es "CERTIFICADO" o "MATRICULA", usarla
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # Verificar que no sea un header común
                if next_line and not re.search(r'^(CERTIFICADO|MATRICULA)', next_line, re.IGNORECASE):
                    # Limpiar y retornar
                    oficina = re.sub(r'\s+', ' ', next_line)
                    oficina = re.sub(r'\s+(CERTIFICADO|MATRICULA).*$', '', oficina, flags=re.IGNORECASE)
                    oficina = oficina.strip()
                    if oficina:
                        return oficina
    
    return ""


def extract_escritura_from_anotacion(pdf_text, numero_anotacion):
    """
    Extrae el nombre de la escritura pública de una anotación específica en el PDF.
    
    Args:
        pdf_text: Texto extraído del PDF
        numero_anotacion: Número de anotación con 3 dígitos (ej: "001", "002", "003")
        
    Returns:
        str: Nombre completo de la escritura (ej: "ESCRITURA 6833 DEL 28-12-1984") 
             o string vacío "" si no se encuentra
    """
    # Buscar la sección de anotación con el número especificado
    # Patrón: ANOTACION: Nro 001, ANOTACION: Nro 002, etc.
    anotacion_pattern = rf'ANOTACION:\s*Nro\s+{numero_anotacion}'
    anotacion_match = re.search(anotacion_pattern, pdf_text, re.IGNORECASE)
    
    if not anotacion_match:
        return ""
    
    # Encontrar el inicio de la anotación
    anotacion_start = anotacion_match.start()
    
    # Buscar el final de esta anotación (inicio de la siguiente anotación o fin del texto)
    # Buscar la siguiente anotación
    next_anotacion_pattern = r'ANOTACION:\s*Nro\s+\d{3}'
    next_matches = list(re.finditer(next_anotacion_pattern, pdf_text[anotacion_start + 1:], re.IGNORECASE))
    
    if next_matches:
        # Hay otra anotación después, usar su posición como límite
        anotacion_end = anotacion_start + 1 + next_matches[0].start()
    else:
        # No hay más anotaciones, usar el resto del texto
        anotacion_end = len(pdf_text)
    
    # Extraer el texto de esta anotación
    anotacion_text = pdf_text[anotacion_start:anotacion_end]
    
    # Buscar el patrón de escritura dentro de la anotación
    # Patrón flexible: Doc: ESCRITURA XXXX DEL/DE DD-MM-YYYY o DD/MM/YYYY
    escritura_pattern = r'Doc:\s*(ESCRITURA\s+\d+\s+(?:DEL|DE)\s+\d{1,2}[-/]\d{1,2}[-/]\d{4})'
    escritura_match = re.search(escritura_pattern, anotacion_text, re.IGNORECASE)
    
    if escritura_match:
        return escritura_match.group(1).strip()
    
    return ""


def extract_folios_from_matriculas(matriculas_text):
    """
    Extrae los folios y sus números de círculo del texto de matrículas.
    Maneja formatos como:
    - 176-0998349 (formato tradicional)
    - 51N-0998349 (formato con letra después del número)
    
    Args:
        matriculas_text: Texto del archivo matriculas.txt
        
    Returns:
        tuple: (folio_to_circulo dict, folios list)
    """
    # Patrón que acepta números opcionalmente seguidos de letras (ej: 176, 51N)
    # Acepta espacios opcionales antes y después del guión para manejar casos como:
    # - "307-111067" (formato normal)
    # - "307- 111067" (con espacio después del guión)
    # - "307 - 111067" (con espacios antes y después)
    folio_pattern = r'(\d+[A-Z]?)\s*-\s*(\d+)'
    matches = re.findall(folio_pattern, matriculas_text)
    
    folio_to_circulo = {}
    folios = []
    
    for circulo, folio in matches:
        if folio not in folio_to_circulo:
            folio_to_circulo[folio] = circulo
            folios.append(folio)
    
    return folio_to_circulo, folios


def process_properties(matriculas_text, pdf_text):
    """
    Procesa las matrículas y el PDF para extraer las propiedades y escrituras.
    
    Args:
        matriculas_text: Texto del archivo matriculas.txt
        pdf_text: Texto extraído del PDF
        
    Returns:
        tuple: (property_data list, not_found list, oficina_registro str)
            property_data: Lista de tuplas (property_name, circulo, folio, escritura)
            not_found: Lista de folios no encontrados
            oficina_registro: Nombre de la oficina de registro extraída del PDF
    """
    # Extraer folios y círculos
    folio_to_circulo, folios = extract_folios_from_matriculas(matriculas_text)
    
    # Extraer propiedades y números de anotación del PDF
    folio_to_property, folio_to_anotacion = extract_properties_from_pdf(pdf_text)
    
    # Extraer oficina de registro (siempre está en la primera página)
    oficina_registro = extract_oficina_registro(pdf_text)
    
    # Diccionario de caché para escrituras (anotacion -> escritura)
    anotacion_to_escritura = {}
    
    # Generar datos estructurados
    property_data = []
    not_found = []
    
    for folio in folios:
        circulo = folio_to_circulo.get(folio, '')
        if folio in folio_to_property:
            property_name = folio_to_property[folio]
            
            # Obtener número de anotación para este folio
            numero_anotacion = folio_to_anotacion.get(folio, "")
            
            # Buscar escritura usando caché
            escritura = ""
            if numero_anotacion:
                # Verificar si ya tenemos esta escritura en caché
                if numero_anotacion not in anotacion_to_escritura:
                    # Buscar la escritura y guardarla en caché
                    escritura = extract_escritura_from_anotacion(pdf_text, numero_anotacion)
                    anotacion_to_escritura[numero_anotacion] = escritura
                else:
                    # Obtener del caché
                    escritura = anotacion_to_escritura[numero_anotacion]
            
            property_data.append((property_name, circulo, folio, escritura))
        else:
            not_found.append(folio)
            property_data.append(("NO ENCONTRADO", circulo, folio, ""))
    
    return property_data, not_found, oficina_registro


def format_output(property_data, output_format='txt', oficina_registro=''):
    """
    Formatea los datos de propiedades según el formato especificado.
    
    Args:
        property_data: Lista de tuplas (property_name, circulo, folio, escritura)
        output_format: 'txt' o 'csv'
        oficina_registro: Nombre de la oficina de registro (solo para CSV)
        
    Returns:
        list: Lista de líneas formateadas
    """
    output_lines = []
    
    if output_format.lower() == 'csv':
        # Formato CSV: 6 columnas (Inmueble, folio, EP, escritura link, paginas, oficina_registro)
        # Usar csv.writer para manejar correctamente comas y comillas dentro de los valores
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        
        # Agregar headers
        csv_writer.writerow(["Inmueble", "folio", "EP", "escritura link", "paginas", "oficina_registro"])
        
        # Llenamos Inmueble, folio, EP (con numero_circulo-folio) y oficina_registro
        for property_name, circulo, folio, escritura in property_data:
            csv_writer.writerow([property_name, f"{circulo}-{folio}", escritura, "", "", oficina_registro])
        
        # Obtener las líneas del CSV (ya con comillas donde sea necesario)
        csv_content = csv_buffer.getvalue()
        output_lines = csv_content.strip().split('\n')
    else:
        # Formato TXT: [nombre propiedad] [numero_circulo]-[folio]
        for property_name, circulo, folio, _ in property_data:
            output_lines.append(f"{property_name} {circulo}-{folio}")
    
    return output_lines


def get_oauth_credentials(client_id, client_secret, redirect_uri, token=None):
    """
    Obtiene credenciales OAuth 2.0 para Google.
    
    Args:
        client_id: Client ID de OAuth 2.0
        client_secret: Client Secret de OAuth 2.0
        redirect_uri: URI de redirección
        token: Token existente (opcional)
        
    Returns:
        google.oauth2.credentials.Credentials: Credenciales OAuth
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import Flow
        import os
    except ImportError:
        raise ImportError("google-auth-oauthlib debe estar instalado. Ejecuta: pip install google-auth-oauthlib")
    
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    if token:
        # Usar token existente
        return Credentials.from_authorized_user_info(token, scopes=scopes)
    else:
        # Crear flow para autenticación
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=scopes,
            redirect_uri=redirect_uri
        )
        return flow


def create_google_sheet(property_data, title="Extractor de Propiedades", credentials=None, oficina_registro=''):
    """
    Crea un Google Sheet público y editable con los datos de propiedades.
    
    Args:
        property_data: Lista de tuplas (property_name, circulo, folio, escritura)
        title: Título del spreadsheet
        credentials: Credenciales OAuth o Service Account (opcional)
        oficina_registro: Nombre de la oficina de registro (opcional)
        
    Returns:
        str: URL del Google Sheet creado
        
    Raises:
        Exception: Si hay un error al crear el sheet
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials as ServiceAccountCredentials
        from google.oauth2.credentials import Credentials as OAuthCredentials
        import json
        import os
    except ImportError:
        raise ImportError("gspread y google-auth deben estar instalados. Ejecuta: pip install gspread google-auth")
    
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # Si se proporcionan credenciales OAuth, usarlas
    if credentials and isinstance(credentials, OAuthCredentials):
        client = gspread.authorize(credentials)
    else:
        # Usar Service Account (método anterior)
        credentials_path = os.path.join(os.path.dirname(__file__), 'google_credentials.json')
        
        if os.path.exists(credentials_path):
            with open(credentials_path, 'r') as f:
                creds_dict = json.load(f)
        else:
            creds_dict = {
                "type": "service_account",
                "project_id": "TU_PROJECT_ID",
                "private_key_id": "TU_PRIVATE_KEY_ID",
                "private_key": "-----BEGIN PRIVATE KEY-----\nTU_PRIVATE_KEY_AQUI\n-----END PRIVATE KEY-----\n",
                "client_email": "tu-service-account@tu-project.iam.gserviceaccount.com",
                "client_id": "TU_CLIENT_ID",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/tu-service-account%40tu-project.iam.gserviceaccount.com"
            }
            
            if creds_dict["project_id"] == "TU_PROJECT_ID":
                raise ValueError(
                    "Credenciales de Google no configuradas.\n"
                    "Opción 1: Crea un archivo 'google_credentials.json' con tus credenciales.\n"
                    "Opción 2: Autentícate usando OAuth 2.0 en la aplicación."
                )
        
        credentials = ServiceAccountCredentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(credentials)
    
    # Crear nuevo spreadsheet
    spreadsheet = client.create(title)
    
    # Obtener la primera hoja
    worksheet = spreadsheet.sheet1
    
    # Preparar datos: headers y filas
    headers = ["Inmueble", "folio", "EP", "escritura link", "paginas", "oficina_registro"]
    worksheet.append_row(headers)
    
    # Agregar datos
    for property_name, circulo, folio, escritura in property_data:
        row = [property_name, f"{circulo}-{folio}", escritura, "", "", oficina_registro]
        worksheet.append_row(row)
    
    # Hacer el spreadsheet público y editable por todos
    spreadsheet.share('', perm_type='anyone', role='writer')
    
    # Retornar la URL
    return spreadsheet.url


# ============================================================================
# CONFIGURACIÓN: Puedes quemar el nombre del proyecto aquí si prefieres
# ============================================================================
PROYECTO_NOMBRE = '2 1 P109018 EDIFICIO PARQUE 76' 
# ============================================================================

def main():
    """Función principal que se ejecuta cuando se llama el script directamente"""
    # Obtener el nombre del proyecto y formato
    proyecto_nombre = None
    output_format = 'txt'
    
    # Parsear argumentos
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--format' and i + 1 < len(sys.argv):
            output_format = sys.argv[i + 1].lower()
            if output_format not in ['txt', 'csv']:
                print(f"Error: Formato '{output_format}' no válido. Use 'txt' o 'csv'")
                sys.exit(1)
            i += 2
        elif not proyecto_nombre and not arg.startswith('--'):
            proyecto_nombre = arg
            i += 1
        else:
            i += 1
    
    # Si no se proporcionó nombre, usar el de configuración
    if not proyecto_nombre:
        if PROYECTO_NOMBRE:
            proyecto_nombre = PROYECTO_NOMBRE
        else:
            print("Error: Debes proporcionar el nombre del proyecto")
            print("Opción 1: Pasarlo como parámetro")
            print('  Uso: python3 extract_properties.py "2 1 P110701 VENTURA"')
            print('  Uso: python3 extract_properties.py "2 1 P110701 VENTURA" --format csv')
            print("Opción 2: Definirlo en PROYECTO_NOMBRE en el código")
            sys.exit(1)

    # Construir rutas de archivos
    base_dir = os.path.dirname(os.path.abspath(__file__))
    carpeta_path = os.path.join(base_dir, proyecto_nombre)
    input_file = os.path.join(carpeta_path, 'matriculas.txt')
    extension = 'csv' if output_format == 'csv' else 'txt'
    output_file = os.path.join(carpeta_path, f'{proyecto_nombre}.{extension}')

    # Validar que existan los archivos de entrada
    if not os.path.exists(input_file):
        print(f"Error: No se encontró el archivo {input_file}")
        sys.exit(1)

    # Buscar el archivo PDF (puede ser certificado.pdf o <nombre_proyecto>.pdf)
    pdf_file = os.path.join(carpeta_path, 'certificado.pdf')
    if not os.path.exists(pdf_file):
        # Intentar con el nombre del proyecto
        pdf_file_alt = os.path.join(carpeta_path, f'{proyecto_nombre}.pdf')
        if os.path.exists(pdf_file_alt):
            pdf_file = pdf_file_alt
        else:
            print(f"Error: No se encontró el archivo PDF")
            print(f"  Buscado: {os.path.join(carpeta_path, 'certificado.pdf')}")
            print(f"  Buscado: {pdf_file_alt}")
            sys.exit(1)

    # Leer el archivo de entrada
    with open(input_file, 'r', encoding='utf-8') as f:
        input_content = f.read()

    print(f"Leyendo PDF: {pdf_file}")
    reader = PdfReader(pdf_file)
    pdf_text = ""
    for page in reader.pages:
        pdf_text += page.extract_text()

    print(f"PDF leído. Total de caracteres: {len(pdf_text)}")

    # Usar las funciones reutilizables
    property_data, not_found, oficina_registro = process_properties(input_content, pdf_text)
    output_lines = format_output(property_data, output_format, oficina_registro)

    # Escribir al archivo de salida
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"\nResultados escritos en {output_file} (formato: {output_format.upper()})")
    print(f"Total de folios procesados: {len(output_lines)}")
    print(f"Folios encontrados: {len(output_lines) - len(not_found)}")
    print(f"Folios no encontrados: {len(not_found)}")
    if oficina_registro:
        print(f"Oficina de registro: {oficina_registro}")

    if not_found:
        print(f"\nFolios no encontrados (primeros 10): {not_found[:10]}")


if __name__ == '__main__':
    main()


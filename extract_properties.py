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
        dict: Diccionario que mapea folio -> nombre de propiedad
    """
    folio_to_property = {}
    
    # Dividir en líneas para procesar propiedades multilínea
    lines = pdf_text.split('\n')
    
    # Patrón para detectar inicio de una propiedad: numero -> folio : o numero -> folio -
    # También maneja casos donde el folio y la propiedad están concatenados (ej: "230510APTO")
    # Usamos dos patrones: uno para formato normal y otro para formato concatenado
    pattern_folio_normal = r'(\d+)\s*->\s*(\d+)\s*[:-]\s*(.*)'
    
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
            r'^APTO\s+',           # APTO seguido de espacio
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
        ]
        
        # Buscar si comienza con alguna palabra clave
        for keyword_pattern in property_keywords:
            if re.search(keyword_pattern, remaining_text, re.IGNORECASE):
                # Encontrar dónde termina el folio (justo antes de la palabra clave)
                folio_match = re.search(rf'(\d+)\s*->\s*(\d+)(?={keyword_pattern})', line, re.IGNORECASE)
                if folio_match:
                    folio = folio_match.group(2)
                    property_start = remaining_text
                    return (num_before, folio, property_start)
        
        # Si no comienza con palabra clave, buscar transición de dígitos a letras
        # Ejemplo: "230510APTO" -> folio termina en 0, propiedad empieza con A
        transition_match = re.search(r'(\d+)\s*->\s*(\d+)([A-Z][A-Z0-9\s\-]*)', line)
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
    
    i = 0
    while i < len(lines):
        line = lines[i]
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
        
        # Patrones comunes de headers y footers a filtrar
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
        ]
        
        def is_footer_or_header(line):
            """Verifica si una línea es un footer o header común"""
            line_upper = line.upper()
            for pattern in footer_patterns:
                if re.search(pattern, line_upper, re.IGNORECASE):
                    return True
            return False
        
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
                # Si la propiedad está incompleta, continuar buscando después de headers
                if is_incomplete and consecutive_headers <= max_consecutive_headers:
                    j += 1
                    continue
                # Si hay demasiados headers consecutivos y la propiedad parece completa, parar
                elif consecutive_headers > max_consecutive_headers:
                    break
                j += 1
                continue
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
        footer_cleanup_patterns = [
                r'OFICINA DE REGISTRO[^\n]*',
                r'CERTIFICADO DE TRADICION[^\n]*',
                r'MATRICULA INMOBILIARIA[^\n]*',
                r'La validez de este documento[^\n]*',
                r'certificados\.supernotariado\.gov\.co[^\n]*',
                r'Certificado generado con el Pin No:[^\n]*',
                r'Nro Matrícula:[^\n]*',
                r'Pagina \d+[^\n]*',
                r'TURNO:[^\n]*',
                r'Impreso el[^\n]*',
                r'No tiene validez[^\n]*',
                r'ESTE CERTIFICADO REFLEJA[^\n]*',
                r'HASTA LA FECHA Y HORA[^\n]*',
                r'SNR[^\n]*',
                r'SUPERINTENDENCIA[^\n]*',
            r'SALVEDADES:[^\n]*',
            r'Información Anterior o Corregida[^\n]*',
        ]
        
        for pattern in footer_cleanup_patterns:
            property_name = re.sub(pattern, '', property_name, flags=re.IGNORECASE)
        
        # Remover espacios múltiples
        property_name = re.sub(r'\s+', ' ', property_name)
        
        # Remover puntos y guiones al final si existen (con espacios antes)
        property_name = re.sub(r'\s*[-.]+\s*$', '', property_name).strip()
        
        # Remover guiones al inicio si existen (como en "- APARTAMENTO...")
        property_name = re.sub(r'^\s*[-]+\s*', '', property_name).strip()
        
        # Remover cualquier número de matrícula que quede al final (ej: "100-256825,100-262122,,,")
        property_name = re.sub(r'\d+-\d+[,\s]*$', '', property_name).strip()
        property_name = re.sub(r',+$', '', property_name).strip()
        
        # Si la propiedad está vacía después de limpiar, saltarla
        if property_name:
            folio_to_property[folio] = property_name
        
        i = j  # Continuar desde donde paramos
    else:
        i += 1
    
    return folio_to_property


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
    folio_pattern = r'(\d+[A-Z]?)-(\d+)'
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
    Procesa las matrículas y el PDF para extraer las propiedades.
    
    Args:
        matriculas_text: Texto del archivo matriculas.txt
        pdf_text: Texto extraído del PDF
        
    Returns:
        tuple: (property_data list, not_found list)
            property_data: Lista de tuplas (property_name, circulo, folio)
            not_found: Lista de folios no encontrados
    """
    # Extraer folios y círculos
    folio_to_circulo, folios = extract_folios_from_matriculas(matriculas_text)
    
    # Extraer propiedades del PDF
    folio_to_property = extract_properties_from_pdf(pdf_text)
    
    # Generar datos estructurados
    property_data = []
    not_found = []
    
    for folio in folios:
        circulo = folio_to_circulo.get(folio, '')
        if folio in folio_to_property:
            property_name = folio_to_property[folio]
            property_data.append((property_name, circulo, folio))
        else:
            not_found.append(folio)
            property_data.append(("NO ENCONTRADO", circulo, folio))
    
    return property_data, not_found


def format_output(property_data, output_format='txt'):
    """
    Formatea los datos de propiedades según el formato especificado.
    
    Args:
        property_data: Lista de tuplas (property_name, circulo, folio)
        output_format: 'txt' o 'csv'
        
    Returns:
        list: Lista de líneas formateadas
    """
    output_lines = []
    
    if output_format.lower() == 'csv':
        # Formato CSV: 5 columnas (Inmueble, folio, escritura publica, escritura, paginas)
        # Agregar headers
        output_lines.append("Inmueble,folio,EP,escritura link,paginas")
        # Solo llenamos Inmueble y folio (con numero_circulo-folio)
        for property_name, circulo, folio in property_data:
            output_lines.append(f"{property_name},{circulo}-{folio},,,")
    else:
        # Formato TXT: [nombre propiedad] [numero_circulo]-[folio]
        for property_name, circulo, folio in property_data:
            output_lines.append(f"{property_name} {circulo}-{folio}")
    
    return output_lines

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
    pdf_file = os.path.join(carpeta_path, 'certificado.pdf')
    extension = 'csv' if output_format == 'csv' else 'txt'
    output_file = os.path.join(carpeta_path, f'{proyecto_nombre}.{extension}')

    # Validar que existan los archivos de entrada
    if not os.path.exists(input_file):
        print(f"Error: No se encontró el archivo {input_file}")
        sys.exit(1)

    if not os.path.exists(pdf_file):
        print(f"Error: No se encontró el archivo {pdf_file}")
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
    property_data, not_found = process_properties(input_content, pdf_text)
    output_lines = format_output(property_data, output_format)

    # Escribir al archivo de salida
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"\nResultados escritos en {output_file} (formato: {output_format.upper()})")
    print(f"Total de folios procesados: {len(output_lines)}")
    print(f"Folios encontrados: {len(output_lines) - len(not_found)}")
    print(f"Folios no encontrados: {len(not_found)}")

    if not_found:
        print(f"\nFolios no encontrados (primeros 10): {not_found[:10]}")


if __name__ == '__main__':
    main()


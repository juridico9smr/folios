#!/usr/bin/env python3
"""
Script para extraer nombres de propiedades del certificado PDF
y asociarlos con los números de folio.

Uso:
    python3 extract_properties.py [nombre_proyecto]
    
    Si no se proporciona nombre_proyecto, se usa el valor definido en PROYECTO_NOMBRE
    
    Ejemplo:
    python3 extract_properties.py "2 1 P110701 VENTURA"

El script:
1. Lee los números de folio del archivo '<nombre_proyecto>/matriculas.txt'
2. Extrae las propiedades del PDF '<nombre_proyecto>/certificado.pdf'
3. Genera el archivo '<nombre_proyecto>/<nombre_proyecto>.txt' con el formato: [nombre propiedad] [numero_circulo]-[folio]
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
    
    Args:
        pdf_text: Texto extraído del PDF
        
    Returns:
        dict: Diccionario que mapea folio -> nombre de propiedad
    """
    folio_to_property = {}
    
    # Patrón general: cualquier número -> folio : cualquier cosa hasta el final de línea
    pattern_general = r'(\d+)\s*->\s*(\d+)\s*:\s*([^\n]+)'
    matches = re.findall(pattern_general, pdf_text)
    
    for num_before, folio, property_name_raw in matches:
        if folio in folio_to_property:
            continue  # Ya lo tenemos (tomar el primero si hay duplicados)
        
        # Limpiar el nombre de la propiedad
        property_name = property_name_raw.strip()
        
        # Remover espacios múltiples
        property_name = re.sub(r'\s+', ' ', property_name)
        
        # Remover puntos y guiones al final si existen
        property_name = property_name.rstrip('.-').strip()
        
        # Remover guiones al inicio si existen (como en "- APARTAMENTO...")
        property_name = property_name.lstrip('-').strip()
        
        # Si la propiedad está vacía después de limpiar, saltarla
        if not property_name:
            continue
        
        # IMPORTANTE: Usar el nombre de propiedad exactamente como aparece en el PDF
        folio_to_property[folio] = property_name
    
    return folio_to_property


def extract_folios_from_matriculas(matriculas_text):
    """
    Extrae los folios y sus números de círculo del texto de matrículas.
    
    Args:
        matriculas_text: Texto del archivo matriculas.txt
        
    Returns:
        tuple: (folio_to_circulo dict, folios list)
    """
    folio_pattern = r'(\d+)-(\d+)'
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
        list: Lista de líneas con el formato: [nombre propiedad] [numero_circulo]-[folio]
    """
    # Extraer folios y círculos
    folio_to_circulo, folios = extract_folios_from_matriculas(matriculas_text)
    
    # Extraer propiedades del PDF
    folio_to_property = extract_properties_from_pdf(pdf_text)
    
    # Generar output
    output_lines = []
    not_found = []
    
    for folio in folios:
        if folio in folio_to_property:
            property_name = folio_to_property[folio]
            circulo = folio_to_circulo.get(folio, '')
            output_lines.append(f"{property_name} {circulo}-{folio}")
        else:
            not_found.append(folio)
            circulo = folio_to_circulo.get(folio, '')
            output_lines.append(f"NO ENCONTRADO {circulo}-{folio}")
    
    return output_lines, not_found

# ============================================================================
# CONFIGURACIÓN: Puedes quemar el nombre del proyecto aquí si prefieres
# ============================================================================
PROYECTO_NOMBRE = '2 1 P109018 EDIFICIO PARQUE 76' 
# ============================================================================

def main():
    """Función principal que se ejecuta cuando se llama el script directamente"""
    # Obtener el nombre del proyecto
    if PROYECTO_NOMBRE:
        proyecto_nombre = PROYECTO_NOMBRE
    elif len(sys.argv) >= 2:
        proyecto_nombre = sys.argv[1]
    else:
        print("Error: Debes proporcionar el nombre del proyecto")
        print("Opción 1: Pasarlo como parámetro")
        print('  Uso: python3 extract_properties.py "2 1 P110701 VENTURA"')
        print("Opción 2: Definirlo en PROYECTO_NOMBRE en el código")
        sys.exit(1)

    # Construir rutas de archivos
    base_dir = os.path.dirname(os.path.abspath(__file__))
    carpeta_path = os.path.join(base_dir, proyecto_nombre)
    input_file = os.path.join(carpeta_path, 'matriculas.txt')
    pdf_file = os.path.join(carpeta_path, 'certificado.pdf')
    output_file = os.path.join(carpeta_path, f'{proyecto_nombre}.txt')

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
    output_lines, not_found = process_properties(input_content, pdf_text)

    # Escribir al archivo de salida
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"\nResultados escritos en {output_file}")
    print(f"Total de folios procesados: {len(output_lines)}")
    print(f"Folios encontrados: {len(output_lines) - len(not_found)}")
    print(f"Folios no encontrados: {len(not_found)}")

    if not_found:
        print(f"\nFolios no encontrados (primeros 10): {not_found[:10]}")


if __name__ == '__main__':
    main()


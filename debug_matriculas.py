#!/usr/bin/env python3
"""
Script de diagnóstico para verificar por qué no se encuentran folios en el PDF.

Uso:
    python3 debug_matriculas.py <archivo_pdf> <matriculas_text>
    
Ejemplo:
    python3 debug_matriculas.py "2 1 P86746 VILLA FUERTE MATRICULA 01N-5239948.pdf" "01N-5537007, 01N-5537071"
"""

import sys
import re
import os
from PyPDF2 import PdfReader
from extract_properties import extract_properties_from_pdf, extract_folios_from_matriculas, process_properties

def debug_matriculas(pdf_path, matriculas_text):
    """Diagnostica por qué no se encuentran folios"""
    
    print("="*80)
    print("DIAGNÓSTICO DE MATRÍCULAS")
    print("="*80)
    print()
    
    # 1. Verificar que el PDF existe (buscar en diferentes ubicaciones)
    if not os.path.exists(pdf_path):
        # Intentar buscar en el directorio actual y subdirectorios
        base_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            pdf_path,  # Ruta original
            os.path.join(base_dir, pdf_path),  # En el directorio del script
            os.path.join(os.getcwd(), pdf_path),  # En el directorio actual
        ]
        
        # Buscar en subdirectorios
        pdf_filename = os.path.basename(pdf_path)
        for root, dirs, files in os.walk(base_dir):
            if pdf_filename in files:
                possible_paths.append(os.path.join(root, pdf_filename))
        
        # Intentar cada ruta posible
        found = False
        for path in possible_paths:
            if os.path.exists(path):
                pdf_path = path
                found = True
                print(f"✅ PDF encontrado en: {pdf_path}")
                break
        
        if not found:
            print(f"❌ ERROR: El archivo PDF no existe: {pdf_path}")
            print(f"   Buscado en: {base_dir} y subdirectorios")
            print(f"   Nombre buscado: {pdf_filename}")
            return
    else:
        print(f"✅ PDF encontrado: {pdf_path}")
    
    print(f"✅ PDF encontrado: {pdf_path}")
    print()
    
    # 2. Extraer folios de las matrículas
    print("1. EXTRAYENDO FOLIOS DE MATRÍCULAS")
    print("-"*80)
    folio_to_circulo, folios = extract_folios_from_matriculas(matriculas_text)
    print(f"   Total de folios encontrados: {len(folios)}")
    print(f"   Folios: {folios[:10]}{'...' if len(folios) > 10 else ''}")
    print()
    
    # 3. Leer el PDF
    print("2. LEYENDO PDF")
    print("-"*80)
    reader = PdfReader(pdf_path)
    pdf_text = ""
    for page in reader.pages:
        pdf_text += page.extract_text()
    
    print(f"   Total de páginas: {len(reader.pages)}")
    print(f"   Total de caracteres en el texto: {len(pdf_text)}")
    print()
    
    # 4. Buscar folios específicos en el texto del PDF
    print("3. BUSCANDO FOLIOS EN EL PDF")
    print("-"*80)
    folios_encontrados_en_pdf = []
    folios_no_encontrados = []
    
    for folio in folios[:20]:  # Limitar a los primeros 20 para no saturar
        # Buscar el folio en el texto
        # Buscar patrones como: "-> 5537007" o "-> 5537007LOTE" o "5537007 :"
        patterns = [
            rf'\d+\s*->\s*{folio}',
            rf'->\s*{folio}',
            rf'{folio}\s*[:\.-]',
            rf'{folio}[A-Z]',
        ]
        
        encontrado = False
        for pattern in patterns:
            if re.search(pattern, pdf_text):
                encontrado = True
                # Buscar el contexto alrededor del folio
                matches = list(re.finditer(pattern, pdf_text))
                if matches:
                    match = matches[0]
                    start = max(0, match.start() - 50)
                    end = min(len(pdf_text), match.end() + 100)
                    contexto = pdf_text[start:end].replace('\n', ' ')
                    print(f"   ✅ Folio {folio} encontrado:")
                    print(f"      Contexto: ...{contexto}...")
                break
        
        if encontrado:
            folios_encontrados_en_pdf.append(folio)
        else:
            folios_no_encontrados.append(folio)
            print(f"   ❌ Folio {folio} NO encontrado en el PDF")
    
    print()
    print(f"   Resumen: {len(folios_encontrados_en_pdf)} encontrados, {len(folios_no_encontrados)} no encontrados")
    print()
    
    # 5. Extraer propiedades del PDF
    print("4. EXTRAYENDO PROPIEDADES DEL PDF")
    print("-"*80)
    folio_to_property = extract_properties_from_pdf(pdf_text)
    print(f"   Total de propiedades extraídas: {len(folio_to_property)}")
    
    # Mostrar algunos ejemplos
    print("   Ejemplos de folios extraídos:")
    for i, (folio, prop) in enumerate(list(folio_to_property.items())[:5]):
        print(f"      {folio}: {prop[:60]}...")
    print()
    
    # 6. Procesar todo junto
    print("5. PROCESANDO MATRÍCULAS + PDF")
    print("-"*80)
    property_data, not_found = process_properties(matriculas_text, pdf_text)
    
    encontrados = [p for p in property_data if p[0] != "NO ENCONTRADO"]
    print(f"   Propiedades encontradas: {len(encontrados)}")
    print(f"   Propiedades NO encontradas: {len(not_found)}")
    
    if not_found:
        print(f"   Folios no encontrados: {not_found[:10]}{'...' if len(not_found) > 10 else ''}")
    
    print()
    
    # 7. Comparar folios buscados vs encontrados
    print("6. COMPARACIÓN")
    print("-"*80)
    folios_buscados = set(folios)
    folios_en_pdf = set(folio_to_property.keys())
    
    encontrados_set = folios_buscados & folios_en_pdf
    no_encontrados_set = folios_buscados - folios_en_pdf
    
    print(f"   Folios buscados: {len(folios_buscados)}")
    print(f"   Folios en PDF: {len(folios_en_pdf)}")
    print(f"   Folios encontrados: {len(encontrados_set)}")
    print(f"   Folios NO encontrados: {len(no_encontrados_set)}")
    
    if no_encontrados_set:
        print()
        print("   Folios que NO se encontraron en el PDF:")
        for folio in sorted(list(no_encontrados_set))[:20]:
            print(f"      - {folio}")
    
    print()
    print("="*80)
    print("FIN DEL DIAGNÓSTICO")
    print("="*80)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Uso: python3 debug_matriculas.py <archivo_pdf> <matriculas_text>")
        print()
        print("Ejemplo:")
        print('  python3 debug_matriculas.py "archivo.pdf" "01N-5537007, 01N-5537071"')
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    matriculas_text = sys.argv[2]
    
    debug_matriculas(pdf_path, matriculas_text)


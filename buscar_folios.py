#!/usr/bin/env python3
"""
Script para buscar folios específicos en un PDF.

Uso:
    python3 buscar_folios.py <archivo_pdf> "5537007, 5537071, 5537072"
"""

import sys
import re
import os
from PyPDF2 import PdfReader

def buscar_folios_en_pdf(pdf_path, folios_buscados):
    """Busca folios específicos en un PDF"""
    
    if not os.path.exists(pdf_path):
        print(f"❌ ERROR: El archivo no existe: {pdf_path}")
        return
    
    # Leer PDF
    reader = PdfReader(pdf_path)
    pdf_text = ""
    for page_num, page in enumerate(reader.pages, 1):
        page_text = page.extract_text()
        pdf_text += page_text
        
        # Buscar folios en esta página
        for folio in folios_buscados:
            # Buscar el folio en diferentes formatos
            patterns = [
                rf'\d+\s*->\s*{folio}',
                rf'->\s*{folio}',
                rf'{folio}\s*[:\.-]',
                rf'{folio}[A-Z]',
                rf'{folio}\s',
            ]
            
            for pattern in patterns:
                if re.search(pattern, page_text):
                    print(f"✅ Folio {folio} encontrado en página {page_num}")
                    # Mostrar contexto
                    matches = list(re.finditer(pattern, page_text))
                    if matches:
                        match = matches[0]
                        start = max(0, match.start() - 100)
                        end = min(len(page_text), match.end() + 100)
                        contexto = page_text[start:end].replace('\n', ' ')
                        print(f"   Contexto: ...{contexto}...")
                    break
            else:
                # Si no se encontró en esta página, continuar
                continue
    
    # Resumen
    print()
    print("="*80)
    print("RESUMEN")
    print("="*80)
    
    # Buscar todos los folios en el texto completo
    folios_encontrados = []
    folios_no_encontrados = []
    
    for folio in folios_buscados:
        patterns = [
            rf'\d+\s*->\s*{folio}',
            rf'->\s*{folio}',
            rf'{folio}\s*[:\.-]',
            rf'{folio}[A-Z]',
        ]
        
        encontrado = False
        for pattern in patterns:
            if re.search(pattern, pdf_text):
                folios_encontrados.append(folio)
                encontrado = True
                break
        
        if not encontrado:
            folios_no_encontrados.append(folio)
    
    print(f"Total de folios buscados: {len(folios_buscados)}")
    print(f"✅ Encontrados: {len(folios_encontrados)}")
    print(f"❌ NO encontrados: {len(folios_no_encontrados)}")
    
    if folios_encontrados:
        print(f"\nFolios encontrados: {folios_encontrados}")
    
    if folios_no_encontrados:
        print(f"\nFolios NO encontrados: {folios_no_encontrados}")
        print("\n⚠️  Estos folios no aparecen en el PDF.")
        print("   Verifica que:")
        print("   1. El PDF sea el correcto")
        print("   2. Los folios estén escritos correctamente")
        print("   3. El PDF contenga todas las páginas necesarias")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Uso: python3 buscar_folios.py <archivo_pdf> \"folio1, folio2, folio3\"")
        print()
        print("Ejemplo:")
        print('  python3 buscar_folios.py "archivo.pdf" "5537007, 5537071, 5537072"')
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    folios_str = sys.argv[2]
    
    # Extraer folios de la cadena
    folios = [f.strip() for f in folios_str.split(',')]
    
    buscar_folios_en_pdf(pdf_path, folios)


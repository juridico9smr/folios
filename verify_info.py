#!/usr/bin/env python3
"""
Script para verificar que la información extraída del PDF sea correcta.

Uso:
    python3 verify_info.py <numero_carpeta> [--sample N] [--folio FOLIO]
    
    Ejemplo:
    python3 verify_info.py 176                    # Verifica 10 folios aleatorios
    python3 verify_info.py 176 --sample 20         # Verifica 20 folios aleatorios
    python3 verify_info.py 176 --folio 251666     # Verifica un folio específico
"""

import re
import os
import sys
import random

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("Instalando PyPDF2...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PyPDF2'])
    from PyPDF2 import PdfReader

def extract_folio_from_pdf(pdf_text, folio_num):
    """Extrae el contexto del PDF para un folio específico"""
    # Buscar el folio en el PDF
    pattern = rf'(\d+)\s*->\s*{folio_num}\s*:\s*(CONJUNTO RESIDENCIAL\s+VENTURA[^\n]*)'
    match = re.search(pattern, pdf_text)
    
    if not match:
        return None, None, None
    
    num_before, property_name = match.groups()
    folio_idx = pdf_text.find(f"{num_before} -> {folio_num}")
    
    # Buscar APARTAMENTO antes y después
    search_start = max(0, folio_idx-500)
    before_text = pdf_text[search_start:folio_idx]
    after_text = pdf_text[folio_idx:min(len(pdf_text), folio_idx+200)]
    
    apt_before = None
    apt_after = None
    
    apt_matches_before = list(re.finditer(r'APARTAMENTO\s+(\d+)', before_text))
    if apt_matches_before:
        apt_before = apt_matches_before[-1].group(1)
    
    apt_match_after = re.search(r'APARTAMENTO\s+(\d+)', after_text)
    if apt_match_after:
        apt_after = apt_match_after.group(1)
    
    # Mostrar contexto
    lines = pdf_text.split('\n')
    pdf_lines = []
    for i, line in enumerate(lines):
        if folio_num in line or (apt_before and apt_before in line) or (apt_after and apt_after in line):
            pdf_lines.append((i, line))
    
    # Buscar líneas relevantes alrededor
    context_lines = []
    for line_num, line in pdf_lines:
        start = max(0, line_num-3)
        end = min(len(lines), line_num+4)
        for j in range(start, end):
            if j not in [l[0] for l in context_lines]:
                context_lines.append((j, lines[j]))
    
    context_lines.sort()
    
    return property_name.strip(), apt_before, apt_after, context_lines

def verify_folio_info(carpeta_numero, folio_num, output_line, pdf_text):
    """Verifica que la información de un folio sea correcta"""
    print(f"\n{'='*80}")
    print(f"🔍 VERIFICANDO FOLIO: {folio_num}")
    print(f"{'='*80}")
    
    # Extraer información del output
    # Formato: [nombre propiedad] APARTAMENTO [apt], [folio],
    parts = output_line.rsplit(',', 2)
    if len(parts) < 2:
        print(f"❌ Error: Formato incorrecto en output: {output_line}")
        return False
    
    output_property = parts[0].strip()
    
    # Extraer APARTAMENTO del output
    apt_match = re.search(r'APARTAMENTO\s+(\d+)', output_property)
    if not apt_match:
        print(f"❌ Error: No se encontró número de apartamento en: {output_property}")
        return False
    
    output_apt = apt_match.group(1)
    output_property_base = re.sub(r'\s+APARTAMENTO\s+\d+', '', output_property).strip()
    
    print(f"\n📄 INFORMACIÓN EN OUTPUT:")
    print(f"   Propiedad: {output_property_base}")
    print(f"   Apartamento: {output_apt}")
    
    # Buscar en el PDF
    property_name, apt_before, apt_after, context_lines = extract_folio_from_pdf(pdf_text, folio_num)
    
    if not property_name:
        print(f"\n❌ ERROR: No se encontró el folio {folio_num} en el PDF")
        return False
    
    print(f"\n📋 INFORMACIÓN EN PDF:")
    print(f"   Propiedad: {property_name}")
    print(f"   APARTAMENTO antes: {apt_before}")
    print(f"   APARTAMENTO después: {apt_after}")
    
    # Mostrar contexto del PDF
    print(f"\n📖 CONTEXTO EN PDF (líneas relevantes):")
    for line_num, line in context_lines[:15]:  # Mostrar hasta 15 líneas
        marker = ">>>" if folio_num in line else "   "
        print(f"{marker} {line_num}: {line[:120]}")
    
    # Comparar
    print(f"\n🔎 COMPARACIÓN:")
    
    # Verificar propiedad base
    property_match = output_property_base.upper().replace('  ', ' ') == property_name.upper().replace('  ', ' ')
    if property_match:
        print(f"   ✅ Propiedad base: CORRECTO")
    else:
        print(f"   ❌ Propiedad base: DIFERENTE")
        print(f"      Output: {output_property_base}")
        print(f"      PDF:    {property_name}")
    
    # Verificar apartamento (preferir el que está después, como en el script)
    apt_correct = None
    if apt_after:
        apt_correct = apt_after
        print(f"   📍 Usando APARTAMENTO después del folio: {apt_after}")
    elif apt_before:
        apt_correct = apt_before
        print(f"   📍 Usando APARTAMENTO antes del folio: {apt_before}")
    
    apt_match = output_apt == apt_correct if apt_correct else False
    
    if apt_match:
        print(f"   ✅ Apartamento: CORRECTO ({output_apt})")
    else:
        print(f"   ❌ Apartamento: DIFERENTE")
        print(f"      Output: {output_apt}")
        print(f"      PDF esperado: {apt_correct}")
        if apt_before and apt_after:
            print(f"      (PDF tiene: antes={apt_before}, después={apt_after})")
    
    return property_match and apt_match

def main():
    if len(sys.argv) < 2:
        print("Error: Debes proporcionar el número de carpeta como parámetro")
        print(__doc__)
        sys.exit(1)
    
    carpeta_numero = sys.argv[1]
    sample_size = 10
    specific_folio = None
    
    # Parsear argumentos
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--sample' and i + 1 < len(sys.argv):
            sample_size = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--folio' and i + 1 < len(sys.argv):
            specific_folio = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    # Construir rutas
    base_dir = os.path.dirname(os.path.abspath(__file__))
    carpeta_path = os.path.join(base_dir, carpeta_numero)
    pdf_file = os.path.join(carpeta_path, 'certificado.pdf')
    output_file = os.path.join(carpeta_path, f'{carpeta_numero}.txt')
    
    if not os.path.exists(pdf_file):
        print(f"❌ Error: No se encontró el archivo {pdf_file}")
        sys.exit(1)
    
    if not os.path.exists(output_file):
        print(f"❌ Error: No se encontró el archivo {output_file}")
        sys.exit(1)
    
    # Leer PDF
    print(f"📖 Leyendo PDF: {pdf_file}")
    reader = PdfReader(pdf_file)
    pdf_text = ""
    for page in reader.pages:
        pdf_text += page.extract_text()
    print(f"✅ PDF leído ({len(pdf_text)} caracteres)")
    
    # Leer output
    print(f"📄 Leyendo output: {output_file}")
    with open(output_file, 'r', encoding='utf-8') as f:
        output_lines = [line.strip() for line in f if line.strip()]
    print(f"✅ Output leído ({len(output_lines)} líneas)")
    
    # Seleccionar folios a verificar
    if specific_folio:
        # Verificar folio específico
        folios_to_check = [specific_folio]
    else:
        # Seleccionar folios aleatorios
        folios_to_check = []
        for line in output_lines:
            if 'NO ENCONTRADO' not in line.upper():
                parts = line.rsplit(',', 2)
                if len(parts) >= 2:
                    folio = parts[-2].strip()
                    folios_to_check.append((folio, line))
        
        if len(folios_to_check) > sample_size:
            folios_to_check = random.sample(folios_to_check, sample_size)
    
    print(f"\n🔍 Verificando {len(folios_to_check)} folio(s)...")
    
    # Verificar cada folio
    correctos = 0
    incorrectos = 0
    
    for item in folios_to_check:
        if specific_folio:
            folio_num = item
            # Buscar la línea en el output
            output_line = None
            for line in output_lines:
                if f", {folio_num}," in line:
                    output_line = line
                    break
            if not output_line:
                print(f"❌ No se encontró el folio {folio_num} en el output")
                incorrectos += 1
                continue
        else:
            folio_num, output_line = item
        
        es_correcto = verify_folio_info(carpeta_numero, folio_num, output_line, pdf_text)
        if es_correcto:
            correctos += 1
        else:
            incorrectos += 1
    
    # Resumen
    print(f"\n{'='*80}")
    print(f"📊 RESUMEN DE VERIFICACIÓN")
    print(f"{'='*80}")
    print(f"✅ Correctos: {correctos}")
    print(f"❌ Incorrectos: {incorrectos}")
    print(f"📊 Total verificado: {len(folios_to_check)}")
    
    if incorrectos == 0:
        print(f"\n🎉 ¡TODOS LOS FOLIOS VERIFICADOS SON CORRECTOS!")
    else:
        print(f"\n⚠️  Se encontraron {incorrectos} folio(s) con información incorrecta.")

if __name__ == '__main__':
    main()


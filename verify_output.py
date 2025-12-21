#!/usr/bin/env python3
"""
Script para verificar que el archivo de salida generado esté correcto.

Uso:
    python3 verify_output.py <numero_carpeta>
    
    Ejemplo:
    python3 verify_output.py 176
"""

import re
import os
import sys

def verify_output(carpeta_numero):
    """Verifica que el archivo de salida esté correcto"""
    
    # Construir rutas
    base_dir = os.path.dirname(os.path.abspath(__file__))
    carpeta_path = os.path.join(base_dir, carpeta_numero)
    input_file = os.path.join(carpeta_path, 'matriculas.txt')
    output_file = os.path.join(carpeta_path, f'{carpeta_numero}.txt')
    
    if not os.path.exists(input_file):
        print(f"❌ Error: No se encontró el archivo {input_file}")
        return False
    
    if not os.path.exists(output_file):
        print(f"❌ Error: No se encontró el archivo {output_file}")
        return False
    
    # Leer archivo de entrada
    with open(input_file, 'r', encoding='utf-8') as f:
        input_content = f.read()
    
    # Extraer folios del archivo de entrada
    folio_pattern = rf'{carpeta_numero}-(\d+)'
    folios_input = set(re.findall(folio_pattern, input_content))
    
    print(f"📋 Folios en archivo de entrada: {len(folios_input)}")
    
    # Leer archivo de salida
    with open(output_file, 'r', encoding='utf-8') as f:
        output_lines = f.readlines()
    
    print(f"📄 Líneas en archivo de salida: {len(output_lines)}")
    
    # Verificar cada línea del output
    folios_output = set()
    problemas = []
    formato_correcto = 0
    formato_incorrecto = 0
    no_encontrados = 0
    
    for i, line in enumerate(output_lines, 1):
        line = line.strip()
        if not line:
            continue
        
        # Verificar formato: debería tener al menos una coma
        if ',' not in line:
            problemas.append(f"Línea {i}: No tiene formato correcto (falta coma): {line[:80]}")
            formato_incorrecto += 1
            continue
        
        # Extraer folio de la línea
        # Formato esperado: [nombre], [folio],
        parts = line.rsplit(',', 2)  # Dividir desde la derecha
        if len(parts) >= 2:
            folio = parts[-2].strip()  # El penúltimo elemento es el folio
            folios_output.add(folio)
            
            # Verificar si es "NO ENCONTRADO"
            if 'NO ENCONTRADO' in line.upper():
                no_encontrados += 1
            else:
                formato_correcto += 1
        else:
            problemas.append(f"Línea {i}: Formato inesperado: {line[:80]}")
            formato_incorrecto += 1
    
    # Comparar folios
    folios_faltantes = folios_input - folios_output
    folios_extra = folios_output - folios_input
    
    # Mostrar resultados
    print("\n" + "="*60)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("="*60)
    
    print(f"\n✅ Líneas con formato correcto: {formato_correcto}")
    print(f"⚠️  Folios no encontrados: {no_encontrados}")
    print(f"❌ Líneas con formato incorrecto: {formato_incorrecto}")
    
    print(f"\n📋 Comparación de folios:")
    print(f"   Folios en entrada: {len(folios_input)}")
    print(f"   Folios en salida: {len(folios_output)}")
    
    if folios_faltantes:
        print(f"\n❌ Folios que están en entrada pero NO en salida ({len(folios_faltantes)}):")
        for folio in sorted(list(folios_faltantes))[:10]:
            print(f"   - {folio}")
        if len(folios_faltantes) > 10:
            print(f"   ... y {len(folios_faltantes) - 10} más")
    
    if folios_extra:
        print(f"\n⚠️  Folios que están en salida pero NO en entrada ({len(folios_extra)}):")
        for folio in sorted(list(folios_extra))[:10]:
            print(f"   - {folio}")
        if len(folios_extra) > 10:
            print(f"   ... y {len(folios_extra) - 10} más")
    
    if problemas:
        print(f"\n❌ Problemas encontrados ({len(problemas)}):")
        for problema in problemas[:10]:
            print(f"   {problema}")
        if len(problemas) > 10:
            print(f"   ... y {len(problemas) - 10} más")
    
    # Verificar algunos ejemplos
    print(f"\n📝 Ejemplos de líneas (primeras 5):")
    for i, line in enumerate(output_lines[:5], 1):
        print(f"   {i}. {line.strip()[:100]}")
    
    # Resultado final
    print("\n" + "="*60)
    if not folios_faltantes and not folios_extra and not problemas and no_encontrados == 0:
        print("✅ ¡TODO CORRECTO! El archivo está bien formateado y completo.")
        return True
    elif not folios_faltantes and not problemas:
        print("✅ El archivo está bien formateado, pero hay algunos folios no encontrados.")
        return True
    else:
        print("⚠️  Se encontraron algunos problemas. Revisa los detalles arriba.")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Error: Debes proporcionar el número de carpeta como parámetro")
        print("Uso: python3 verify_output.py <numero_carpeta>")
        print("Ejemplo: python3 verify_output.py 176")
        sys.exit(1)
    
    carpeta_numero = sys.argv[1]
    success = verify_output(carpeta_numero)
    sys.exit(0 if success else 1)


#!/usr/bin/env python3
"""
Aplicación web para extraer nombres de propiedades del certificado PDF
y asociarlos con los números de folio.

Uso:
    streamlit run app.py
"""

import streamlit as st
import re
import io

try:
    from PyPDF2 import PdfReader
except ImportError:
    st.error("PyPDF2 no está instalado. Por favor ejecuta: pip install PyPDF2")
    st.stop()

st.set_page_config(
    page_title="Extractor de Propiedades",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Extractor de Propiedades")
st.markdown("Pega el contenido de matrículas y sube el certificado PDF para extraer las propiedades")

# Sección de inputs
st.header("📥 Entrada de Datos")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Matrículas")
    st.caption("Pega aquí el contenido del archivo matriculas.txt")
    matriculas_text = st.text_area(
        "Contenido de matrículas",
        height=200,
        placeholder="Ejemplo: 176-250064 176-250070 176-250083...",
        key='matriculas',
        label_visibility="collapsed"
    )

with col2:
    st.subheader("Certificado PDF")
    certificado_file = st.file_uploader(
        "Sube el archivo certificado.pdf",
        type=['pdf'],
        key='certificado'
    )

# Botón para procesar
st.markdown("---")
if st.button("🚀 Procesar", type="primary", use_container_width=True):
    if not matriculas_text or not matriculas_text.strip():
        st.error("❌ Por favor ingresa el contenido de matrículas")
    elif certificado_file is None:
        st.error("❌ Por favor sube el archivo certificado PDF")
    else:
        try:
            with st.spinner("Procesando archivos..."):
                # Extraer folios del texto de matrículas
                folio_pattern = r'(\d+)-(\d+)'
                matches = re.findall(folio_pattern, matriculas_text)
                
                if not matches:
                    st.error("❌ No se encontraron folios en el formato esperado (ej: 176-250064)")
                    st.stop()
                
                folio_to_circulo = {}
                folios = []
                
                for circulo, folio in matches:
                    if folio not in folio_to_circulo:
                        folio_to_circulo[folio] = circulo
                        folios.append(folio)
                
                st.info(f"✅ Encontrados {len(folios)} números de folio únicos")
                
                # Leer PDF
                pdf_bytes = certificado_file.read()
                reader = PdfReader(io.BytesIO(pdf_bytes))
                pdf_text = ""
                for page in reader.pages:
                    pdf_text += page.extract_text()
                
                if not pdf_text:
                    st.error("❌ No se pudo extraer texto del PDF. Verifica que el PDF no esté escaneado o protegido.")
                    st.stop()
                
                # Extraer propiedades del PDF
                folio_to_property = {}
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
                    
                    # Si el nombre de propiedad NO contiene "APARTAMENTO", buscar el APARTAMENTO más cercano
                    if 'APARTAMENTO' not in property_name.upper():
                        # Buscar la posición del folio en el texto
                        folio_pattern_search = f"{num_before} -> {folio}"
                        folio_idx = pdf_text.find(folio_pattern_search)
                        
                        if folio_idx > 0:
                            # Buscar el APARTAMENTO más cercano, primero después, luego antes
                            # Buscar después del folio (más cercano)
                            after_text = pdf_text[folio_idx:min(len(pdf_text), folio_idx+200)]
                            apt_match_after = re.search(r'APARTAMENTO\s+(\d+)', after_text)
                            
                            # Buscar antes del folio
                            search_start = max(0, folio_idx-500)
                            before_text = pdf_text[search_start:folio_idx]
                            apt_matches_before = list(re.finditer(r'APARTAMENTO\s+(\d+)', before_text))
                            
                            # Preferir el APARTAMENTO después si existe, sino el más cercano antes
                            if apt_match_after:
                                apt_num = apt_match_after.group(1)
                                property_name = f"{property_name} APARTAMENTO {apt_num}"
                            elif apt_matches_before:
                                # Tomar el último (más cercano al folio)
                                apt_match = apt_matches_before[-1]
                                apt_num = apt_match.group(1)
                                property_name = f"{property_name} APARTAMENTO {apt_num}"
                    
                    folio_to_property[folio] = property_name
                
                # Procesar cada folio y generar el output
                output_lines = []
                not_found = []
                
                for folio in folios:
                    if folio in folio_to_property:
                        property_name = folio_to_property[folio]
                        # Obtener el número de círculo para este folio
                        circulo = folio_to_circulo.get(folio, '')
                        # Formato: [nombre propiedad] [numero_circulo]-[folio]
                        output_lines.append(f"{property_name} {circulo}-{folio}")
                    else:
                        not_found.append(folio)
                        # Si no se encuentra, poner solo el folio con su círculo
                        circulo = folio_to_circulo.get(folio, '')
                        output_lines.append(f"NO ENCONTRADO {circulo}-{folio}")
                
                # Mostrar resultados
                st.success("✅ Procesamiento completado!")
                
                # Estadísticas
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                with col_stats1:
                    st.metric("Total Folios", len(folios))
                with col_stats2:
                    st.metric("Encontrados", len(folios) - len(not_found), 
                             delta=f"{((len(folios) - len(not_found)) / len(folios) * 100):.1f}%")
                with col_stats3:
                    st.metric("No Encontrados", len(not_found),
                             delta=f"{(len(not_found) / len(folios) * 100):.1f}%")
                
                # Mostrar resultados
                st.markdown("---")
                st.subheader("📋 Resultados")
                
                result_text = '\n'.join(output_lines)
                
                # Área de texto para ver y copiar resultados
                st.text_area(
                    "Resultado (puedes copiar todo el contenido):",
                    result_text,
                    height=400,
                    key='resultado',
                    label_visibility="visible"
                )
                
                # Botón para descargar
                st.download_button(
                    label="📥 Descargar Resultado como .txt",
                    data=result_text,
                    file_name="resultado.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
                # Advertencia si hay folios no encontrados
                if not_found:
                    st.warning(f"⚠️ {len(not_found)} folios no encontrados en el PDF")
                    with st.expander("Ver folios no encontrados"):
                        st.text(', '.join(not_found[:50]))
                        if len(not_found) > 50:
                            st.caption(f"... y {len(not_found) - 50} más")
        
        except Exception as e:
            st.error(f"❌ Error al procesar: {str(e)}")
            with st.expander("Detalles del error"):
                st.exception(e)

# Footer
st.markdown("---")
st.caption("💡 Tip: Puedes copiar y pegar todo el contenido del archivo matriculas.txt en el campo de texto")


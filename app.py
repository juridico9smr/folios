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
import os
from datetime import datetime
from google.auth.transport.requests import Request

try:
    from PyPDF2 import PdfReader
except ImportError:
    st.error("PyPDF2 no está instalado. Por favor ejecuta: pip install PyPDF2")
    st.stop()

# Importar las funciones del script extract_properties
try:
    from extract_properties import process_properties, format_output, create_google_sheet, get_oauth_credentials
except ImportError as e:
    st.error(f"Error al importar funciones: {str(e)}")
    st.stop()


def save_sheet_link(sheet_url):
    """
    Guarda el link del Google Sheet en un archivo dentro de la carpeta STREAMLIT_LINKS.
    Crea la carpeta si no existe.
    
    Args:
        sheet_url: URL del Google Sheet creado
    """
    # Obtener el directorio base del script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    links_dir = os.path.join(base_dir, 'STREAMLIT_LINKS')
    
    # Crear la carpeta si no existe
    os.makedirs(links_dir, exist_ok=True)
    
    # Crear nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sheet_{timestamp}.txt"
    filepath = os.path.join(links_dir, filename)
    
    # Guardar el link en el archivo
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Google Sheet creado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"URL: {sheet_url}\n")
        return filepath
    except Exception as e:
        # Si falla, no romper el flujo, solo loguear
        print(f"Error al guardar link: {str(e)}")
        return None

# Configuración OAuth 2.0
# Detectar si estamos en desarrollo (local) o producción (Streamlit Cloud)

# Detectar desarrollo: si no hay secrets disponibles o estamos en localhost
def is_development():
    """Detecta si estamos en modo desarrollo"""
    # Verificar si estamos en localhost
    server_address = os.getenv("STREAMLIT_SERVER_ADDRESS", "")
    if "localhost" in server_address or "127.0.0.1" in server_address:
        return True
    
    # Verificar si no hay secrets disponibles (típico en desarrollo local)
    try:
        _ = st.secrets.get("GOOGLE_CLIENT_ID", None)
        return False  # Hay secrets, probablemente producción
    except:
        return True  # No hay secrets, probablemente desarrollo

IS_DEVELOPMENT = is_development()

# Para obtener estos valores: https://console.cloud.google.com/apis/credentials
if IS_DEVELOPMENT:
    # DESARROLLO: Cargar desde archivo .env
    from dotenv import load_dotenv
    load_dotenv()  # Carga variables de entorno desde .env
    
    OAUTH_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    OAUTH_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501")
else:
    # PRODUCCIÓN: Usar secrets de Streamlit Cloud
    try:
        OAUTH_CLIENT_ID = st.secrets.get("GOOGLE_CLIENT_ID", "")
        OAUTH_CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET", "")
        OAUTH_REDIRECT_URI = st.secrets.get("GOOGLE_REDIRECT_URI", "")
    except:
        # Fallback: valores vacíos si no hay secrets
        OAUTH_CLIENT_ID = ""
        OAUTH_CLIENT_SECRET = ""
        OAUTH_REDIRECT_URI = ""

st.set_page_config(
    page_title="Extractor de Propiedades",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Extractor de Propiedades")
st.markdown("Pega el contenido de matrículas y sube uno o múltiples archivos certificado PDF para extraer las propiedades")

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
    st.caption("Puedes subir uno o múltiples archivos PDF")
    certificado_files = st.file_uploader(
        "Sube el/los archivo(s) certificado.pdf",
        type=['pdf'],
        key='certificado',
        accept_multiple_files=True
    )

# Selector de formato de salida
st.markdown("---")
st.subheader("⚙️ Configuración de Salida")
output_format = st.radio(
    "Formato de salida:",
    ["TXT", "CSV"],
    horizontal=True,
    help="TXT: Formato original con nombre y círculo-folio. CSV: Formato CSV con headers."
)

# Botón para procesar
st.markdown("---")
if st.button("🚀 Procesar", type="primary", use_container_width=True):
    if not matriculas_text or not matriculas_text.strip():
        st.error("❌ Por favor ingresa el contenido de matrículas")
    elif not certificado_files or len(certificado_files) == 0:
        st.error("❌ Por favor sube al menos un archivo certificado PDF")
    else:
        try:
            with st.spinner(f"Procesando {len(certificado_files)} archivo(s) PDF..."):
                # Validar que haya folios en el formato esperado
                # Acepta formatos como: 176-250064 o 51N-0998349
                folio_pattern = r'(\d+[A-Z]?)-(\d+)'
                matches = re.findall(folio_pattern, matriculas_text)
                
                if not matches:
                    st.error("❌ No se encontraron folios en el formato esperado (ej: 176-250064 o 51N-0998349)")
                    st.stop()
                
                # Leer todos los PDFs y combinar el texto
                pdf_text = ""
                pdf_count = 0
                
                for certificado_file in certificado_files:
                    pdf_bytes = certificado_file.read()
                    reader = PdfReader(io.BytesIO(pdf_bytes))
                    
                    file_text = ""
                    for page in reader.pages:
                        file_text += page.extract_text()
                    
                    if file_text:
                        pdf_text += file_text + "\n\n"  # Separador entre PDFs
                        pdf_count += 1
                
                if not pdf_text.strip():
                    st.error("❌ No se pudo extraer texto de los PDFs. Verifica que los PDFs no estén escaneados o protegidos.")
                    st.stop()
                
                if pdf_count < len(certificado_files):
                    st.warning(f"⚠️ Se procesaron {pdf_count} de {len(certificado_files)} archivo(s) PDF. Algunos archivos pueden estar vacíos o protegidos.")
                
                # Usar la función reutilizable
                property_data, not_found = process_properties(matriculas_text, pdf_text)
                
                # Calcular total de folios únicos desde las matrículas
                folios = list(set([folio for _, folio in matches]))
                
                # Guardar property_data en session_state para usar después con Google Sheets
                # IMPORTANTE: Guardar siempre, incluso si no es CSV, para que persista después de redirección
                st.session_state['property_data'] = property_data
                st.session_state['not_found'] = not_found
                st.session_state['folios'] = folios
                st.session_state['data_processed'] = True  # Flag para saber que hay datos procesados
                
                # Formatear según el formato seleccionado
                format_lower = output_format.lower()
                output_lines = format_output(property_data, format_lower)
                
                # Mostrar resultados
                st.success("✅ Procesamiento completado!")
                
                # Estadísticas
                col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
                with col_stats1:
                    st.metric("Archivos PDF", len(certificado_files))
                with col_stats2:
                    st.metric("Total Folios", len(folios))
                with col_stats3:
                    st.metric("Encontrados", len(folios) - len(not_found), 
                             delta=f"{((len(folios) - len(not_found)) / len(folios) * 100):.1f}%" if len(folios) > 0 else "0%")
                with col_stats4:
                    st.metric("No Encontrados", len(not_found),
                             delta=f"{(len(not_found) / len(folios) * 100):.1f}%" if len(folios) > 0 else "0%")
                
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
                
                # Botón para descargar con el formato correcto
                file_extension = format_lower
                mime_type = "text/csv" if format_lower == "csv" else "text/plain"
                st.download_button(
                    label=f"📥 Descargar Resultado como .{file_extension}",
                    data=result_text,
                    file_name=f"resultado.{file_extension}",
                    mime=mime_type,
                    use_container_width=True
                )
                
                # Si es CSV, mostrar opción para generar Google Sheet
                if format_lower == "csv":
                    st.markdown("---")
                    st.subheader("📊 Google Sheets")
                    st.markdown("¿Quieres crear un Google Sheet público y editable con estos datos?")
                    
                    # Verificar si hay credenciales OAuth configuradas
                    use_oauth = OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET and OAUTH_REDIRECT_URI
                    
                    if use_oauth:
                        # Usar OAuth 2.0
                        # Si ya hay un sheet creado, mostrarlo
                        if 'google_sheet_url' in st.session_state:
                            st.success("✅ Google Sheet creado exitosamente!")
                            
                            sheet_url = st.session_state['google_sheet_url']
                            
                            # Mostrar el link
                            st.markdown(f"**URL del Google Sheet:**")
                            st.code(sheet_url, language=None)
                            
                            # Botón para abrir
                            st.markdown(
                                f'<a href="{sheet_url}" target="_blank">'
                                '<button style="background-color: #4CAF50; color: white; padding: 10px 20px; '
                                'border: none; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%;">'
                                '📊 Abrir Google Sheet</button></a>',
                                unsafe_allow_html=True
                            )
                            
                            st.info("💡 El Google Sheet es público y editable por todos. Comparte el link con quien necesites.")
                            
                            if st.button("🔄 Crear otro Sheet", key="new_sheet"):
                                del st.session_state['google_sheet_url']
                                st.rerun()
                        
                        elif 'google_credentials' not in st.session_state:
                            # Verificar si hay un código en la URL (callback de Google)
                            # Usar la API correcta según la versión de Streamlit
                            try:
                                query_params = st.query_params
                                # En versiones nuevas, query_params es un objeto
                                auth_code = query_params.get('code', None)
                                clear_params = lambda: st.query_params.clear()
                            except (AttributeError, TypeError):
                                # Fallback para versiones antiguas de Streamlit
                                query_params = st.experimental_get_query_params()
                                # En versiones antiguas, query_params es un dict con listas
                                auth_code = query_params.get('code', [None])[0] if 'code' in query_params else None
                                clear_params = lambda: st.experimental_set_query_params()
                            
                            if auth_code:
                                # Google redirigió con el código, procesarlo automáticamente
                                st.info("🔄 Procesando código de autenticación...")
                                
                                try:
                                    from google_auth_oauthlib.flow import Flow
                                    
                                    scopes = [
                                        'https://www.googleapis.com/auth/spreadsheets',
                                        'https://www.googleapis.com/auth/drive'
                                    ]
                                    
                                    flow = Flow.from_client_config(
                                        {
                                            "web": {
                                                "client_id": OAUTH_CLIENT_ID,
                                                "client_secret": OAUTH_CLIENT_SECRET,
                                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                                "token_uri": "https://oauth2.googleapis.com/token",
                                                "redirect_uris": [OAUTH_REDIRECT_URI]
                                            }
                                        },
                                        scopes=scopes,
                                        redirect_uri=OAUTH_REDIRECT_URI
                                    )
                                    
                                    # Intercambiar código por token
                                    flow.fetch_token(code=auth_code)
                                    
                                    # Guardar credenciales en session_state
                                    st.session_state['google_credentials'] = flow.credentials
                                    
                                    # Limpiar la URL (remover el código) - NO hacer esto antes de procesar
                                    # clear_params()  # Comentado para debugging
                                    
                                    # Debug: mostrar qué datos hay disponibles
                                    with st.expander("🔍 Debug - Estado actual"):
                                        st.write("Keys en session_state:", list(st.session_state.keys()))
                                        st.write("pending_property_data existe:", 'pending_property_data' in st.session_state)
                                        st.write("property_data existe:", 'property_data' in st.session_state)
                                        if 'pending_property_data' in st.session_state:
                                            st.write("pending_property_data length:", len(st.session_state['pending_property_data']))
                                        if 'property_data' in st.session_state:
                                            st.write("property_data length:", len(st.session_state['property_data']))
                                    
                                    # Si hay datos guardados, crear el sheet automáticamente
                                    # Intentar primero con pending_property_data, luego con property_data
                                    data_to_use = None
                                    if 'pending_property_data' in st.session_state:
                                        data_to_use = st.session_state['pending_property_data']
                                        st.info(f"📊 Usando pending_property_data ({len(data_to_use)} registros)")
                                    elif 'property_data' in st.session_state:
                                        data_to_use = st.session_state['property_data']
                                        st.info(f"📊 Usando property_data ({len(data_to_use)} registros)")
                                    
                                    if data_to_use and len(data_to_use) > 0:
                                        try:
                                            with st.spinner("Creando Google Sheet..."):
                                                credentials = st.session_state['google_credentials']
                                                sheet_url = create_google_sheet(
                                                    data_to_use,
                                                    title="Extractor de Propiedades"
                                                )
                                                
                                                # Guardar el URL del sheet
                                                st.session_state['google_sheet_url'] = sheet_url
                                                
                                                # Guardar el link en archivo
                                                save_sheet_link(sheet_url)
                                                
                                                # Limpiar datos pendientes
                                                if 'pending_property_data' in st.session_state:
                                                    del st.session_state['pending_property_data']
                                                
                                                # Limpiar la URL ahora que todo está listo
                                                try:
                                                    clear_params()
                                                except:
                                                    pass
                                                
                                                st.success("✅ Google Sheet creado exitosamente!")
                                                st.rerun()
                                        except Exception as sheet_error:
                                            st.error(f"❌ Error al crear Google Sheet: {str(sheet_error)}")
                                            with st.expander("Detalles del error"):
                                                st.exception(sheet_error)
                                            # Guardar el error para debugging
                                            st.session_state['sheet_error'] = str(sheet_error)
                                    else:
                                        st.warning("⚠️ Autenticación exitosa, pero no hay datos para crear el sheet.")
                                        st.info("💡 Por favor procesa los datos nuevamente y luego intenta crear el sheet.")
                                        if 'pending_property_data' in st.session_state:
                                            del st.session_state['pending_property_data']
                                        
                                        # Limpiar la URL
                                        try:
                                            clear_params()
                                        except:
                                            pass
                                        
                                        st.rerun()
                                    
                                except Exception as token_error:
                                    st.error(f"❌ Error al procesar autenticación: {str(token_error)}")
                                    with st.expander("Detalles del error"):
                                        st.exception(token_error)
                                    # Limpiar parámetros de URL en caso de error
                                    try:
                                        clear_params()
                                    except:
                                        pass
                            else:
                                # No hay código, mostrar link de autenticación
                                st.info("🔐 Necesitas autenticarte con Google para crear el Sheet")
                                
                                try:
                                    from google_auth_oauthlib.flow import Flow
                                    
                                    scopes = [
                                        'https://www.googleapis.com/auth/spreadsheets',
                                        'https://www.googleapis.com/auth/drive'
                                    ]
                                    
                                    flow = Flow.from_client_config(
                                        {
                                            "web": {
                                                "client_id": OAUTH_CLIENT_ID,
                                                "client_secret": OAUTH_CLIENT_SECRET,
                                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                                "token_uri": "https://oauth2.googleapis.com/token",
                                                "redirect_uris": [OAUTH_REDIRECT_URI]
                                            }
                                        },
                                        scopes=scopes,
                                        redirect_uri=OAUTH_REDIRECT_URI
                                    )
                                    
                                    auth_url, state = flow.authorization_url(
                                        prompt='consent',
                                        access_type='offline',
                                        include_granted_scopes='true'
                                    )
                                    
                                    # Guardar el state para validación (opcional pero recomendado)
                                    st.session_state['oauth_state'] = state
                                    
                                    # Guardar los datos para crear el sheet después de autenticarse
                                    # IMPORTANTE: Guardar en múltiples lugares para asegurar persistencia
                                    st.session_state['pending_property_data'] = property_data
                                    # También guardar como backup en property_data si no existe
                                    if 'property_data' not in st.session_state:
                                        st.session_state['property_data'] = property_data
                                    
                                    st.info(f"💾 Datos guardados ({len(property_data)} registros). Serán usados después de autenticarte.")
                                    
                                    st.markdown(f"### [🔗 Autenticarse con Google]({auth_url})")
                                    st.caption("Haz clic en el link para autorizar el acceso a tu Google Drive. Después de autorizar, se creará automáticamente el Google Sheet y verás el link aquí.")
                                    
                                except Exception as oauth_error:
                                    st.error(f"Error en autenticación OAuth: {str(oauth_error)}")
                                    with st.expander("Detalles"):
                                        st.exception(oauth_error)
                        else:
                            # Ya autenticado, mostrar botón para crear sheet
                            st.success("✅ Autenticado con Google")
                            
                            if st.button("🔗 Generar Link de Google Sheets", type="secondary", use_container_width=True):
                                try:
                                    with st.spinner("Creando Google Sheet..."):
                                        credentials = st.session_state['google_credentials']
                                        sheet_url = create_google_sheet(
                                            property_data,
                                            title="Extractor de Propiedades",
                                            credentials=credentials
                                        )
                                        
                                        # Guardar el link en archivo
                                        save_sheet_link(sheet_url)
                                        
                                        st.success("✅ Google Sheet creado exitosamente!")
                                        
                                        # Mostrar el link
                                        st.markdown(f"**URL:** [{sheet_url}]({sheet_url})")
                                        st.code(sheet_url, language=None)
                                        
                                        # Botón para abrir
                                        st.markdown(
                                            f'<a href="{sheet_url}" target="_blank">'
                                            '<button style="background-color: #4CAF50; color: white; padding: 10px 20px; '
                                            'border: none; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%;">'
                                            '📊 Abrir Google Sheet</button></a>',
                                            unsafe_allow_html=True
                                        )
                                        
                                        st.info("💡 El Google Sheet es público y editable por todos. Comparte el link con quien necesites.")
                                except Exception as sheet_error:
                                    st.error(f"❌ Error al crear Google Sheet: {str(sheet_error)}")
                                    with st.expander("Detalles del error"):
                                        st.exception(sheet_error)
                                    # Si el token expiró, limpiar y pedir re-autenticación
                                    if "invalid_grant" in str(sheet_error).lower() or "expired" in str(sheet_error).lower():
                                        del st.session_state['google_credentials']
                                        st.warning("⚠️ Tu sesión expiró. Por favor autentícate nuevamente.")
                                        st.rerun()
                                        
                            if st.button("🚪 Cerrar sesión", key="logout"):
                                del st.session_state['google_credentials']
                                st.rerun()
                                
                        # Manejar errores de token expirado
                        if 'google_credentials' in st.session_state:
                            try:
                                # Intentar refrescar si es necesario
                                creds = st.session_state['google_credentials']
                                if creds.expired and creds.refresh_token:
                                    creds.refresh(Request())
                            except Exception:
                                # Si falla, limpiar credenciales
                                if 'google_credentials' in st.session_state:
                                    del st.session_state['google_credentials']
                                    st.warning("⚠️ Tu sesión expiró. Por favor autentícate nuevamente.")
                                    st.rerun()
                    else:
                        # Usar Service Account (método anterior)
                        if st.button("🔗 Generar Link de Google Sheets", type="secondary", use_container_width=True):
                            try:
                                with st.spinner("Creando Google Sheet..."):
                                    sheet_url = create_google_sheet(property_data, title="Extractor de Propiedades")
                                    
                                    # Guardar el link en archivo
                                    save_sheet_link(sheet_url)
                                    
                                    st.success("✅ Google Sheet creado exitosamente!")
                                    
                                    # Mostrar el link
                                    st.markdown(f"**URL:** [{sheet_url}]({sheet_url})")
                                    st.code(sheet_url, language=None)
                                    
                                    # Botón para abrir
                                    st.markdown(
                                        f'<a href="{sheet_url}" target="_blank">'
                                        '<button style="background-color: #4CAF50; color: white; padding: 10px 20px; '
                                        'border: none; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%;">'
                                        '📊 Abrir Google Sheet</button></a>',
                                        unsafe_allow_html=True
                                    )
                                    
                                    st.info("💡 El Google Sheet es público y editable por todos. Comparte el link con quien necesites.")
                            except Exception as sheet_error:
                                st.error(f"❌ Error al crear Google Sheet: {str(sheet_error)}")
                                with st.expander("Detalles del error"):
                                    st.exception(sheet_error)
                
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


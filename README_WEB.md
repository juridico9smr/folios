# Extractor de Propiedades - Aplicación Web

Aplicación web simple para extraer nombres de propiedades de certificados PDF y asociarlos con números de folio.

## Instalación Local

1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecuta la aplicación:
```bash
streamlit run app.py
```

3. Abre tu navegador en la URL que aparece (normalmente `http://localhost:8501`)

## Uso

1. **Matrículas**: Pega el contenido del archivo `matriculas.txt` en el campo de texto
2. **Certificado**: Sube el archivo PDF del certificado
3. Haz clic en "Procesar"
4. Los resultados aparecerán en la página y podrás copiarlos o descargarlos

## Despliegue en Internet (Gratis)

### Opción 1: Streamlit Cloud (Recomendado - Gratis)

1. Crea una cuenta en [Streamlit Cloud](https://streamlit.io/cloud)
2. Sube este código a un repositorio de GitHub
3. Conecta tu repositorio en Streamlit Cloud
4. ¡Listo! Tu app estará en internet

### Opción 2: Otras plataformas gratuitas

- **Railway**: https://railway.app
- **Render**: https://render.com
- **Heroku**: https://heroku.com (tiene plan gratuito limitado)

## Notas

- Los archivos no se guardan en el servidor, todo se procesa en memoria
- La aplicación es completamente stateless (sin estado)
- Funciona mejor con PDFs que tienen texto extraíble (no escaneados)


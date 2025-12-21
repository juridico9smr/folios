# Configuración de Google Sheets

Para usar la funcionalidad de Google Sheets, necesitas configurar un Service Account de Google Cloud.

## Pasos para Configurar:

### 1. Crear un Proyecto en Google Cloud
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente

### 2. Habilitar las APIs necesarias
1. Ve a "APIs & Services" > "Library"
2. Busca y habilita:
   - **Google Sheets API**
   - **Google Drive API**

### 3. Crear un Service Account
1. Ve a "APIs & Services" > "Credentials"
2. Click en "Create Credentials" > "Service Account"
3. Dale un nombre (ej: "folios-sheets-creator")
4. Click en "Create and Continue"
5. Opcional: Asigna un rol (no es necesario para esto)
6. Click en "Done"

### 4. Crear y Descargar la Key
1. En la lista de Service Accounts, click en el que acabas de crear
2. Ve a la pestaña "Keys"
3. Click en "Add Key" > "Create new key"
4. Selecciona "JSON"
5. Click en "Create" - esto descargará un archivo JSON

### 5. Configurar el Archivo de Credenciales
1. Renombra el archivo descargado a `google_credentials.json`
2. Colócalo en la misma carpeta que `app.py` y `extract_properties.py`
3. **IMPORTANTE**: Agrega `google_credentials.json` al `.gitignore` para no subirlo a GitHub

### 6. (Opcional) Quemar Credenciales en el Código
Si prefieres tener las credenciales directamente en el código (como mencionaste), puedes modificar la función `create_google_sheet` en `extract_properties.py` para usar un diccionario directamente en lugar de leer el archivo.

## Notas de Seguridad:
- ⚠️ **NUNCA** subas `google_credentials.json` a GitHub
- El archivo ya está en `.gitignore` por defecto
- Si quemas las credenciales en el código, ten cuidado al hacer push

## Verificar que Funciona:
Una vez configurado, cuando selecciones "Google Sheets" en la app, debería crear un spreadsheet público y editable automáticamente.


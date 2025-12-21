# Configuración de OAuth 2.0 para Google Sheets

Esta guía te ayudará a configurar OAuth 2.0 para que los usuarios puedan autenticarse con su propia cuenta de Google.

## Pasos para Configurar OAuth 2.0

### 1. Crear un Proyecto en Google Cloud
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente

### 2. Habilitar las APIs necesarias
1. Ve a "APIs & Services" > "Library"
2. Busca y habilita:
   - **Google Sheets API**
   - **Google Drive API**

### 3. Crear Credenciales OAuth 2.0
1. Ve a "APIs & Services" > "Credentials"
2. Click en "Create Credentials" > "OAuth client ID"
3. Si es la primera vez, configura la pantalla de consentimiento:
   - Tipo de aplicación: "External" (o "Internal" si solo es para tu organización)
   - Nombre de la app: "Extractor de Propiedades"
   - Email de soporte: tu email
   - **IMPORTANTE**: Agrega tu email como "Test user" si es External
   - Guarda y continúa
4. **CRÍTICO - Agregar Test Users**:
   - Después de crear las credenciales, ve a "APIs & Services" > "OAuth consent screen"
   - En la sección "Test users", haz clic en "+ ADD USERS"
   - Agrega el email de cada persona que va a usar la app (incluyendo el tuyo)
   - Guarda los cambios
   - **Nota**: Sin esto, recibirás el error 403: access_denied
4. Crea el OAuth client ID:
   - Tipo de aplicación: **"Web application"**
   - Nombre: "Folios Web App"
   - **Authorized redirect URIs**: 
     - Para producción: `https://tu-app.streamlit.app`
     - Para desarrollo local: `http://localhost:8501`
   - Click en "Create"
5. **Copia el Client ID y Client Secret** (los necesitarás)

### 4. Configurar en Streamlit

#### Opción A: Usar Secrets de Streamlit (Recomendado)
1. En Streamlit Cloud, ve a tu app
2. Settings > Secrets
3. Agrega:
```toml
GOOGLE_CLIENT_ID = "tu-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "GOCSPX-tu-client-secret"
GOOGLE_REDIRECT_URI = "https://tu-app.streamlit.app"
```

#### Opción B: Quemar en el Código (Para desarrollo)
Edita `app.py` y reemplaza las líneas 30-38:
```python
OAUTH_CLIENT_ID = "tu-client-id.apps.googleusercontent.com"
OAUTH_CLIENT_SECRET = "GOCSPX-tu-client-secret"
OAUTH_REDIRECT_URI = "https://tu-app.streamlit.app"  # o "http://localhost:8501" para local
```

### 5. Cómo Funciona

1. Usuario selecciona formato CSV y procesa
2. Si no está autenticado, ve un link para autenticarse
3. Click en el link → Google pide permisos
4. Después de autorizar, Google muestra un código
5. Usuario pega el código en la app
6. La app guarda las credenciales en la sesión
7. Usuario puede crear Google Sheets en su cuenta

### 6. Notas Importantes

- ⚠️ **Redirect URI debe coincidir exactamente** con la URL de tu app
- 🔒 Las credenciales se guardan solo en la sesión del navegador (no se persisten)
- 🔄 Si el token expira, el usuario debe autenticarse nuevamente
- 📝 Cada usuario crea sheets en su propia cuenta de Google

### 7. Troubleshooting

**Error: "redirect_uri_mismatch"**
- Verifica que el redirect URI en Google Cloud coincida exactamente con tu app URL

**Error: "invalid_client"**
- Verifica que el Client ID y Secret sean correctos

**El código no funciona**
- Asegúrate de copiar el código completo después de autorizar
- El código expira rápido, úsalo inmediatamente

## Ventajas de OAuth vs Service Account

✅ Cada usuario usa su propia cuenta  
✅ No necesitas mantener credenciales del servidor  
✅ Más seguro (cada usuario controla sus permisos)  
✅ Los sheets se crean en la cuenta del usuario  


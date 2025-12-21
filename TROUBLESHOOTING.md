# Troubleshooting - Errores Comunes

## Error 403: access_denied

**Síntoma**: Al intentar autenticarse con Google, recibes:
```
SMR (my google user) has not completed the Google verification process. 
The app is currently being tested, and can only be accessed by developer-approved testers.
Error 403: access_denied
```

**Causa**: Tu aplicación OAuth está en modo de prueba y tu email no está agregado como tester.

**Solución**:

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto
3. Ve a **"APIs & Services"** > **"OAuth consent screen"**
4. En la sección **"Test users"**, haz clic en **"+ ADD USERS"**
5. Agrega el email de cada persona que va a usar la app (incluyendo el tuyo)
6. Haz clic en **"ADD"**
7. Guarda los cambios
8. Intenta autenticarte nuevamente

**Nota**: Si quieres que cualquiera pueda usar la app sin ser agregado como tester, necesitas:
- Verificar la aplicación con Google (proceso largo que requiere revisión)
- O cambiar el tipo de app a "Internal" (solo para tu organización Google Workspace)

## Error: redirect_uri_mismatch

**Síntoma**: Error al autenticarse que menciona que el redirect URI no coincide.

**Solución**:
1. Ve a "APIs & Services" > "Credentials"
2. Click en tu OAuth 2.0 Client ID
3. Verifica que el "Authorized redirect URI" coincida EXACTAMENTE con:
   - Desarrollo: `http://localhost:8501`
   - Producción: `https://tu-app.streamlit.app`
4. Guarda los cambios

## Error: invalid_client

**Síntoma**: Error que dice que el cliente es inválido.

**Solución**:
1. Verifica que el `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` sean correctos
2. Asegúrate de que no haya espacios extra al copiar/pegar
3. Verifica que estén en el formato correcto:
   - Client ID: `123456789-abc.apps.googleusercontent.com`
   - Client Secret: `GOCSPX-abc123...`

## El código de autorización no funciona

**Síntoma**: Pegas el código pero no funciona.

**Solución**:
1. Asegúrate de copiar el código completo (puede ser largo)
2. El código expira rápido, úsalo inmediatamente después de obtenerlo
3. Si expiró, vuelve a hacer clic en el link de autenticación

## La app no detecta desarrollo vs producción

**Síntoma**: La app no carga las variables de `.env` en desarrollo.

**Solución**:
1. Verifica que el archivo `.env` esté en la misma carpeta que `app.py`
2. Verifica que las variables se llamen exactamente:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI`
3. Reinicia la app de Streamlit después de crear/modificar `.env`


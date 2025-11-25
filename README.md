# Discord Bot - Pana

Bot de Discord personal con comandos de IA, música y utilidades.

## Comandos Disponibles

### 📌 Comandos Generales

- **panaHola**
  - Saludo del bot
  - Uso: `panaHola`

- **panaSay `<texto>`**
  - El bot repite el texto y elimina tu mensaje
  - Uso: `panaSay Hola a todos`

- **panaPing `<usuario> <cantidad> [mensaje]`**
  - Menciona a un usuario múltiples veces
  - Límite: 10 pings máximo
  - Uso: `panaPing @Usuario 3 Hola`

- **panaPurge `<cantidad>`**
  - Elimina mensajes del canal
  - Rango: 1-100 mensajes
  - Uso: `panaPurge 50`

- **panaAvatar `[usuario]`**
  - Muestra el avatar de un usuario
  - Si no especificas usuario, muestra el tuyo
  - Uso: `panaAvatar @Usuario` o `panaAvatar`

- **panaHelp**
  - Muestra la lista de comandos disponibles
  - Uso: `panaHelp`

### 🤖 Comandos de IA

- **panaIA `<prompt>`**
  - Pregunta a Google Gemini
  - Responde conversaciones, preguntas, información
  - Uso: `panaIA ¿Qué es Python?`

- **panaImageIA `<prompt>`**
  - Genera imágenes con IA (Stable Diffusion)
  - Describe la imagen que quieres
  - Uso: `panaImageIA A cyberpunk city at night`

### 🎵 Comandos de Música

- **panaPlay `<canción>`**
  - Reproduce música de YouTube
  - Busca por nombre o pega URL
  - Añade a cola si ya está reproduciendo
  - Uso: `panaPlay Never Gonna Give You Up`

- **panaPause**
  - Pausa la reproducción actual
  - Uso: `panaPause`

- **panaResume**
  - Reanuda la reproducción pausada
  - Uso: `panaResume`

- **panaStop**
  - Detiene la música y limpia la cola
  - Uso: `panaStop`

- **panaPlayNext**
  - Salta a la siguiente canción de la cola
  - Uso: `panaPlayNext`

- **panaJoin**
  - El bot se une a tu canal de voz
  - Uso: `panaJoin`

- **panaLeave**
  - El bot sale del canal de voz
  - Uso: `panaLeave`

### ⚙️ Comandos de Sistema

- **panaReloadBot**
  - Recarga el bot (solo propietario)
  - Uso: `panaReloadBot`

## Características

✅ Múltiples comandos de utilidad
✅ Integración con Google Gemini AI
✅ Generación de imágenes con IA
✅ Reproductor de música de YouTube
✅ Sistema de colas para música
✅ Logging completo
import logging
import aiohttp
from config import Config

logger = logging.getLogger(__name__)

async def data(prompt):
    if not Config.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not configured")
        return "Error: Gemini API key no configurada"

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={Config.GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, headers=headers) as response:
                if response.status == 200:
                    respuesta = await response.json()
                    texto = respuesta["candidates"][0]["content"]["parts"][0]["text"]
                    return texto
                elif response.status == 429:
                    logger.warning("Gemini API rate limit exceeded")
                    return "⏳ Límite de uso de la API alcanzado. Intenta de nuevo en unos segundos."
                else:
                    error_text = await response.text()
                    logger.error(f"Gemini API error {response.status}: {error_text}")
                    return f"Error: {response.status} - No se pudo procesar la solicitud"
    except aiohttp.ClientError as e:
        logger.error(f"Network error calling Gemini API: {e}", exc_info=True)
        return "Error: Problema de conexión con la API de Gemini"
    except KeyError as e:
        logger.error(f"Unexpected response format from Gemini API: {e}", exc_info=True)
        return "Error: Respuesta inesperada de la API"
    except Exception as e:
        logger.error(f"Unexpected error in Gemini API call: {e}", exc_info=True)
        return f"Error inesperado: {str(e)}"

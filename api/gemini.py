# api/gemini.py
import os

import aiohttp  # usaremos requests asíncrono

async def data(prompt):
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={os.getenv('GEMINI_API_KEY')}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"{prompt}"
                    }
                ]
            }
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json=payload, headers=headers) as response:
            if response.status == 200:
                respuesta = await response.json()
                texto = respuesta["candidates"][0]["content"]["parts"][0]["text"]
                return texto
            else:
                return f"Error: {response.status}, {await response.text()}"

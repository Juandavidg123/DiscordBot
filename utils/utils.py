from config import Config

def dividir_texto(texto, limite=None):
    if limite is None:
        limite = Config.MAX_MESSAGE_LENGTH

    if not texto:
        return [""]

    partes = []
    while len(texto) > limite:
        punto_final = texto.rfind(' ', 0, limite)
        if punto_final == -1:
            punto_final = limite
        partes.append(texto[:punto_final])
        texto = texto[punto_final:].lstrip()

    if texto:
        partes.append(texto)

    return partes

def dividir_texto(texto, limite=2000):
    partes = []
    while len(texto) > limite:
        punto_final = texto.rfind(' ', 0, limite)
        if punto_final == -1:
            punto_final = limite
        partes.append(texto[:punto_final])
        texto = texto[punto_final:].lstrip()
    partes.append(texto)
    return partes

def determinar_direcao(historico):
    """Determina a direção da entrada com base na média móvel dos últimos 5 fechamentos."""
    if len(historico) < 5:
        return "Indefinida"

    media_movel_5 = sum(historico[-5:]) / 5
    preco_atual = historico[-1]
    preco_anterior = historico[-2]

    if preco_atual > media_movel_5 and preco_anterior < preco_atual:
        return "call"

    if preco_atual < media_movel_5 and preco_anterior > preco_atual:
        return "put"

    return "Indefinida"

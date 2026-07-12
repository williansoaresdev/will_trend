from pathlib import Path

arquivo = Path(__file__).with_name("historico.txt")

# Setup do Ensaio
entrada_inicial = 2
profit = 0.85
saldo_inicial = 100
max_soro = 6
max_gale = 16

saldo_final = saldo_inicial
primeira_linha = True
resultado_anterior = ""
soma_loss = 0
qtd_loss = 0

print("-------------------------------------------------------")
print("Ensaio para entradas")
print("-------------------------------------------------------")

with arquivo.open("r", encoding="utf-8") as f:
    for linha in f:
        resultado = linha.rstrip("\n")

        # Calcula a entrada da operação
        if primeira_linha:
            entrada = entrada_inicial
        else:
            if resultado_anterior == "Loss":
                if qtd_loss == 1:
                    entrada = entrada_inicial / profit
                else:
                    entrada = soma_loss / profit
                    if entrada > max_gale:
                        entrada = entrada_inicial
            else:
                entrada = entrada * (1 + profit)
                if entrada > max_soro:
                    entrada = entrada_inicial

        entrada = round(entrada, 2)

        lucro = 0
        if resultado == "Gain":
            soma_loss = 0
            lucro = round(entrada * profit, 2)
            qtd_loss = 0
        elif resultado == "Loss":
            lucro = -entrada
            soma_loss += entrada
            qtd_loss += 1

        saldo_final += lucro

        print("Ent: {:<6} | Res: {:<5} | Lucro: {:<6} | Saldo: {:<6}".format(entrada, resultado, lucro, round(saldo_final, 2)))

        resultado_anterior = resultado
        primeira_linha = False
from getpass import getpass
from iqoptionapi.stable_api import IQ_Option
import time
import datetime


LOGIN = "usandodocs@gmail.com"

senha = getpass("Senha: ")

print(f"Logando na IQ como {LOGIN}")

iq = IQ_Option(LOGIN, senha)

ok, motivo = iq.connect()

if not ok:
    print("Erro:", motivo)
    exit()

while True:
    print("Escolha a conta:")
    print("1 - Conta de prática")
    print("2 - Conta Real")
    opcao_conta = input("Opção: ").strip()

    if opcao_conta == "1":
        conta_selecionada = "PRACTICE"
        print("Usando conta de prática...")
        break
    elif opcao_conta == "2":
        conta_selecionada = "REAL"
        print("Usando conta real...")
        break
    else:
        print("Opção inválida. Digite 1 ou 2.")

print("Login OK - alterando para a conta selecionada...")

iq.change_balance(conta_selecionada)

saldo = iq.get_balance()
if conta_selecionada == "PRACTICE":
    print(f"Saldo prática: {saldo}")
else:
    print(f"Saldo real: {saldo}")

# Verifica ativo disponível
ativo = "EURUSD-OTC"

# Valor padrao de operacao
valor_operacao = 2

# Stop Loss e Stop Gain
stop_loss = saldo * 0.9
stop_gain = saldo * 1.1

# Tempo padrao de operacao
tempo_operacao = 1

# Segundos para analisar e entrar
segundos_analise = 59

# Direção da operação (call ou put)
direcao = "Indefinida"

# Conta as vitorias
qtd_vitorias = 0
qtd_derrotas = 0

# Para controle das entradas
check, order_id = False, 0

print("Monitorando:", ativo)

historico = []

while True:
    try:
        processa_entrada = True

        #print("Lendo último candle")
        vela = iq.get_candles(
            ativo,
            60,
            1,
            time.time()
        )[0]

        fechamento = vela["close"]

        historico.append(fechamento)

        if len(historico) > 9:
            historico.pop(0)

        alerta_hora = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"{alerta_hora} {fechamento:.5f}")

        if len(historico) >= 9:
            # Se veio de uma operação anterior, faz a análise de vitória ou derrota
            if direcao != "Indefinida":
                processa_entrada = False # Não processa nova entrada logo após uma operação, só analisa a anterior

                saldo_antes = saldo
                saldo = iq.get_balance()
                profit = saldo - saldo_antes
                print(f"Resultado: {profit}")

                if profit > 0:
                    if valor_operacao == 2:
                        valor_operacao = 3.72
                    elif valor_operacao == 3.72:
                        valor_operacao = 6.90
                    elif valor_operacao == 6.90:
                        valor_operacao = 2
                    qtd_vitorias += 1
                    with open("historico.txt", "a", encoding="utf-8") as arquivo_historico:
                        arquivo_historico.write("Gain\n")
                    print(f"## OPERAÇÃO VENCEDORA [{qtd_vitorias}x{qtd_derrotas}] Saldo antes: {saldo_antes:.2f}, Saldo depois: {saldo:.2f}")
                elif profit < 0:
                    qtd_derrotas += 1
                    valor_operacao = 2
                    with open("historico.txt", "a", encoding="utf-8") as arquivo_historico:
                        arquivo_historico.write("Loss\n")
                    print(f"## OPERAÇÃO PERDEDORA [{qtd_vitorias}x{qtd_derrotas}] Saldo antes: {saldo_antes:.2f}, Saldo depois: {saldo:.2f}")

                if saldo <= stop_loss:
                    print(f"## STOP LOSS ATINGIDO! Saldo atual: {saldo:.2f}, Stop Loss: {stop_loss:.2f}")
                    exit()
                    
                if saldo >= stop_gain:
                    print(f"## STOP GAIN ATINGIDO! Saldo atual: {saldo:.2f}, Stop Gain: {stop_gain:.2f}")
                    exit()

            direcao = "Indefinida"

            ultimos_quatro = historico[-4:]
            preco_atual = ultimos_quatro[-1]
            media_movel = sum(historico[-9:]) / 9

            engolfo_alta = (
                ultimos_quatro[2] < ultimos_quatro[1]
                and ultimos_quatro[3] > ultimos_quatro[2]
                and ultimos_quatro[3] > ultimos_quatro[1]
                and preco_atual > media_movel
            )
            engolfo_baixa = (
                ultimos_quatro[2] > ultimos_quatro[1]
                and ultimos_quatro[3] < ultimos_quatro[2]
                and ultimos_quatro[3] < ultimos_quatro[1]
                and preco_atual < media_movel
            )

            delta3 = abs(ultimos_quatro[3] - ultimos_quatro[2]) # ultimo candle
            delta2 = abs(ultimos_quatro[2] - ultimos_quatro[1]) # penultimo candle

            delta3_ideal = delta2 * 1.25

            if processa_entrada:
                if delta2 >= 0.0003 and delta3 >= delta3_ideal:
                    if engolfo_alta or engolfo_baixa:
                        ultimos_tres = historico[-3:]
                        ultimos_tres_formatados = ", ".join(f"{valor:.5f}" for valor in ultimos_tres)

                        if engolfo_alta:
                            print(f"ALERTA: Engolfo de alta - Fechamentos últimos 3 candles: {ultimos_tres_formatados}")
                            direcao = "call"
                        elif engolfo_baixa:
                            print(f"ALERTA: Engolfo de baixa - Fechamentos últimos 3 candles: {ultimos_tres_formatados}")
                            direcao = "put"

                if direcao != "Indefinida":
                    check, order_id = iq.buy(valor_operacao, ativo, direcao, tempo_operacao)
                    if check:
                        print(f"Ordem inserida! ID: {order_id}")

        # Wait until some seconds of the next minute
        now = datetime.datetime.now()
        seconds_until = (segundos_analise - now.second) % 60
        if seconds_until == 0:
            seconds_until = 60
        # Quando faz entrada só analisa 2 minutos depois
        if direcao != "Indefinida":
            seconds_until += 60
        time.sleep(seconds_until)

    except Exception as e:
        print("Erro:", e)
        # Wait until some seconds of the next minute
        now = datetime.datetime.now()
        seconds_until = (segundos_analise - now.second) % 60
        if seconds_until == 0:
            seconds_until = 60
        time.sleep(seconds_until)
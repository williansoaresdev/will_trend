'''
    Executor de ordens IQOption
    -> Media Móvel 9 fechamentos
    -> Entrada de 1 min
    -> 1 Soro
    -> 4 Gales
'''

# Para pedir a senha no console
from getpass import getpass

# Para usar a API da IQOption
from iqoptionapi.stable_api import IQ_Option

# Rotinas de data e hora
import time
import datetime

# Para enviar notificações ao Slack
import requests

# Webhook do Slack
SLACK_WEBHOOK = "https://hooks.slack.com/services/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"

def send_slack_notification(mensagem):
    """Envia uma notificação para o Slack via webhook"""
    try:
        payload = {"text": mensagem}
        requests.post(SLACK_WEBHOOK, json=payload)
    except Exception as e:
        print(f"Erro ao enviar notificação ao Slack: {e}")

# Meu email de login
LOGIN = "usandodocs@gmail.com"

# Pede a senha
senha = getpass("Senha: ")

print(f"Logando na IQ como {LOGIN}")

iq = IQ_Option(LOGIN, senha)

ok, motivo = iq.connect()

# Se o login falhar:
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

# Valor padrao de operacao (5%)
entrada_padrao = saldo * 0.05
valor_operacao = entrada_padrao

# Taxa padrão de profit mínimo
taxa_profit = 0.86

# Maximo de Soro (valor de entrada) e Gales (quantidade de perdas consecutivas)
max_soro = 4

# Soma das percas (para o gale)
soma_percas = 0
qtd_percas = 0
max_gales = entrada_padrao * 2

# Stop Loss e Stop Gain
stop_loss = saldo * 0.5
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


def get_server_datetime():
    server_timestamp = iq.get_server_timestamp()
    if isinstance(server_timestamp, (int, float)):
        if server_timestamp > 10**12:
            server_timestamp = server_timestamp / 1000
        return datetime.datetime.fromtimestamp(server_timestamp)
    return datetime.datetime.now()


# Roda a cada minuto até que caia no stop loss ou stop gain
while True:
    try:
        server_time = get_server_datetime()
        vela = iq.get_candles(
            ativo,
            60,
            1,
            server_time.timestamp()
        )[0]

        fechamento = vela["close"]

        historico.append(fechamento)

        if len(historico) > 9:
            historico.pop(0)

        alerta_hora = server_time.strftime("%H:%M:%S")
        print(f"{alerta_hora} {fechamento:.5f}")

        if len(historico) >= 9:
            # Se veio de uma operação anterior, faz a análise de vitória ou derrota
            if direcao != "Indefinida":
                saldo_antes = saldo
                saldo = iq.get_balance()
                profit = saldo - saldo_antes
                print(f"Resultado: {profit}")

                # Processa vitórias
                if profit > 0:
                    # Se veio de uma derrota anterior (primeira vitoria), reinicia com a entrada padrao daqui pra frente
                    if qtd_percas > 0:
                        valor_operacao = entrada_padrao
                    
                    valor_operacao = valor_operacao * round(1 + taxa_profit, 2)
                    if valor_operacao > max_soro:
                        valor_operacao = entrada_padrao

                    qtd_vitorias += 1
                    soma_percas = 0
                    qtd_percas = 0

                    with open("historico_avg.txt", "a", encoding="utf-8") as arquivo_historico:
                        arquivo_historico.write("Gain\n")

                    print(f"## OPERAÇÃO VENCEDORA [{qtd_vitorias}x{qtd_derrotas}] Saldo antes: {saldo_antes:.2f}, Saldo depois: {saldo:.2f}")
                    
                # Processa derrotas
                elif profit < 0:
                    # Se é a primeira derrota, considera para os calculos de gale a entrada padrao
                    if qtd_percas == 0:
                        valor_operacao = entrada_padrao
                    
                    qtd_derrotas += 1
                    soma_percas += valor_operacao
                    qtd_percas += 1

                    valor_operacao = round(soma_percas / taxa_profit, 2)
                    
                    if qtd_percas > max_gales:
                        valor_operacao = entrada_padrao

                    with open("historico_avg.txt", "a", encoding="utf-8") as arquivo_historico:
                        arquivo_historico.write("Loss\n")

                    print(f"## OPERAÇÃO PERDEDORA [{qtd_vitorias}x{qtd_derrotas}] Saldo antes: {saldo_antes:.2f}, Saldo depois: {saldo:.2f}")

                if saldo <= stop_loss:
                    mensagem = f"## STOP LOSS ATINGIDO! Saldo atual: {saldo:.2f}, Stop Loss: {stop_loss:.2f}"
                    print(mensagem)
                    send_slack_notification(mensagem)
                    exit()

                if saldo >= stop_gain:
                    mensagem = f"## STOP GAIN ATINGIDO! Saldo atual: {saldo:.2f}, Stop Gain: {stop_gain:.2f}"
                    print(mensagem)
                    send_slack_notification(mensagem)
                    exit()

            direcao = "Indefinida"

            ultimos_quatro = historico[-4:]
            preco_atual = ultimos_quatro[-1]
            media_movel = sum(historico[-9:]) / 9

            qtd_altas = 0
            qtd_baixas = 0
            for i in range(len(historico) - 1, 1, -1):
                # Conta as altas
                if historico[i] > historico[i-1]:
                    qtd_altas += 1

                # Conta as baixas
                if historico[i] < historico[i-1]:
                    qtd_baixas += 1           
           
            # 1 - Estar acima da média, 2 - Estar acima do último fechamento, 3 - A maioria dos ultimos candles forem de alta
            if preco_atual > media_movel and preco_atual > ultimos_quatro[-2] and qtd_altas > 5:
                direcao = "call"
            if preco_atual < media_movel and preco_atual < ultimos_quatro[-2] and qtd_baixas > 5:
                direcao = "put"

            if direcao != "Indefinida":
                check, order_id = iq.buy(valor_operacao, ativo, direcao, tempo_operacao)
                if check:
                    print(f"Ordem inserida! ID: {order_id}")

        # Entra sempre no mesmo horario de cada minuto
        now = server_time
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
        now = get_server_datetime()
        seconds_until = (segundos_analise - now.second) % 60
        if seconds_until == 0:
            seconds_until = 60
        time.sleep(seconds_until)
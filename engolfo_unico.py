'''
    Executor de ordens IQOption
    -> Media Móvel 9 fechamentos
    -> Engolfo em direção a tendência da média
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
from pathlib import Path
import requests


def load_slack_webhook():
    hook_file = Path(__file__).with_name("hook.txt")
    try:
        with hook_file.open("r", encoding="utf-8") as arquivo:
            return arquivo.read().strip()
    except FileNotFoundError:
        return ""


# Webhook do Slack
SLACK_WEBHOOK = load_slack_webhook()

print("*=================================================================*")
print("|                                                                 |")
print("|                                                                 |")
print("| IQ OPTION - ENGOLFO EM TENDENCIA 9M                             |")
print("|                                                 Willian Soares  |")
print("|                                                                 |")
print("*=================================================================*")


def send_slack_notification(mensagem):
    """Envia uma notificação para o Slack via webhook"""
    try:
        payload = {"text": mensagem}
        headers = {
            "Content-Type": "application/json"
        }

        requests.post(SLACK_WEBHOOK, json=payload, headers=headers, timeout=10)

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

send_slack_notification(f"IQ logado via engolfo_unico.py em {conta_selecionada}")

saldo = iq.get_balance()
if conta_selecionada == "PRACTICE":
    print(f"Saldo prática: {saldo}")
else:
    print(f"Saldo real: {saldo}")

# Verifica ativo disponível
ativo = "EURUSD-OTC"

# Valor padrao de operacao
while True:
    try:
        entrada_padrao_texto = input("Digite o valor para entrada_padrao (entre 2 e 100): ").strip()
        entrada_padrao = float(entrada_padrao_texto)
        if 2 <= entrada_padrao <= 100:
            break
        print("Valor inválido. Informe um valor entre 2 e 100.")
    except ValueError:
        print("Valor inválido. Informe um valor numérico entre 2 e 100.")

valor_operacao = entrada_padrao

# Taxa padrão de profit mínimo
taxa_profit = 0.86

# Maximo de Soro (valor de entrada) e Gales (quantidade de perdas consecutivas)
max_soro = entrada_padrao * 2

# Soma das percas (para o gale)
soma_percas = 0
qtd_percas = 0
max_gales = 0

# Stop Loss e Stop Gain
stop_loss = saldo * 0.5
stop_gain = saldo * 1.04

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

# Para controle humano das entradas
para_apos_primeira_entrada = False

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
        processa_entrada = True

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
                processa_entrada = False # Não processa nova entrada logo após uma operação, só analisa a anterior

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

                    with open("historico.txt", "a", encoding="utf-8") as arquivo_historico:
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

                    with open("historico.txt", "a", encoding="utf-8") as arquivo_historico:
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

            engolfo_alta = (
                ultimos_quatro[2] < ultimos_quatro[1]
                and ultimos_quatro[3] > ultimos_quatro[2]
                and ultimos_quatro[3] > ultimos_quatro[1]
                and preco_atual > media_movel
                #and qtd_altas > 5
            )
            engolfo_baixa = (
                ultimos_quatro[2] > ultimos_quatro[1]
                and ultimos_quatro[3] < ultimos_quatro[2]
                and ultimos_quatro[3] < ultimos_quatro[1]
                and preco_atual < media_movel
                #and qtd_baixas > 5
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
                        mensagem = f"Ordem de {direcao} {valor_operacao} inserida! ID: {order_id}"
                        print(mensagem)
                        send_slack_notification(mensagem)
                        if para_apos_primeira_entrada:
                            exit()


        # Wait until some seconds of the next minute
        now = get_server_datetime()
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
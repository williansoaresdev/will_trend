'''
    Executor de ordens IQOption
    -> Analise de 15 minutos
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

print("*=================================================================*")
print("|                                                                 |")
print("|                                                                 |")
print("| IQ OPTION - EXPIRACAO 5 MINUTOS SEGUIR CANDLE ANTERIOR          |")
print("|                                                 Willian Soares  |")
print("|                                                                 |")
print("*=================================================================*")

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

print(f"Login OK - alterando para a conta {conta_selecionada}...")

iq.change_balance(conta_selecionada)

send_slack_notification(f"IQ logado via avg.py em {conta_selecionada}")

saldo = iq.get_balance()
if conta_selecionada == "PRACTICE":
    print(f"Saldo prática: {saldo}")
else:
    print(f"Saldo real: {saldo}")

saldo_inicial = saldo
saldo_maximo = saldo

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
taxa_profit = 0.85

# Maximo de Soro (valor de entrada) e Gales (quantidade de perdas consecutivas)
max_soro = entrada_padrao * 2

# Soma das percas (para o gale)
soma_percas = 0
qtd_percas_seguidas = 0
max_gales = 5
checa_profit = True
para_na_evolucao = False

# Stop Loss e Stop Gain
stop_loss = saldo - (entrada_padrao * 45)
stop_gain = saldo + (entrada_padrao * 2)

# Tempo padrao de operacao
tempo_operacao = 5

# Segundos para analisar e entrar
segundos_analise = 5 * 60

# Direção da operação (call ou put)
direcao = "Indefinida"

# Conta as vitorias
qtd_vitorias = 0
qtd_vitorias_seguidas = 0
qtd_derrotas = 0
qtd_operacoes = 0
max_vitorias = 30
max_derrotas = 30
analisa_stop_qtd = False
max_operacoes = 100

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


def calcular_segundos_ate_proximo_analise(now):
    intervalo = 5 * 60
    segundos_restantes = (intervalo - (now.minute % 5) * 60 - now.second) % intervalo
    if segundos_restantes == 0:
        return intervalo
    return segundos_restantes


# Roda a cada 15 minutos até que caia no stop loss ou stop gain
while True:
    try:
        server_time = get_server_datetime()
        vela = iq.get_candles(
            ativo,
            300,
            1,
            server_time.timestamp()
        )[0]

        fechamento = vela["close"]

        historico.append(fechamento)

        if len(historico) > 2:
            historico.pop(0)

        alerta_hora = server_time.strftime("%H:%M:%S")
        print(f"{alerta_hora} {fechamento:.5f}")
        
        if len(historico) >= 2:

            # Se veio de uma operação anterior, faz a análise de vitória ou derrota
            if direcao != "Indefinida":
                saldo_anterior = saldo

                saldo = iq.get_balance()

                if checa_profit:
                    profit = round(saldo - saldo_anterior, 2)
                    
                    # Processa vitórias
                    if profit > 0:
                        qtd_vitorias += 1
                        qtd_vitorias_seguidas += 1

                        print(f"## OPERAÇÃO VENCEDORA [{qtd_vitorias}x{qtd_derrotas}]")

                        if qtd_vitorias_seguidas > 1:
                            para_na_evolucao = True

                        # Se veio de uma derrota anterior (primeira vitoria), reinicia com a entrada padrao daqui pra frente
                        if qtd_percas_seguidas > 0:
                            valor_operacao = entrada_padrao

                        valor_operacao = valor_operacao * round(1 + taxa_profit, 2)
                        if valor_operacao > max_soro:
                            valor_operacao = entrada_padrao
                            print(f"Valor da operação atingiu o máximo de Soro ({max_soro}), reiniciando com entrada padrão {valor_operacao:.2f}.")
                        else:
                            print(f"Valor da operação atualizado para {valor_operacao:.2f} após vitória.")

                        soma_percas = 0
                        qtd_percas_seguidas = 0

                        with open("historico_5.txt", "a", encoding="utf-8") as arquivo_historico:
                            arquivo_historico.write("Gain\n")

                        if saldo > saldo_maximo:
                            saldo_maximo = saldo
                            send_slack_notification(f"🎉 Saldo evoluiu de {saldo_inicial:.2f} para {saldo_maximo:.2f} 🍀")
                            if para_na_evolucao:
                                send_slack_notification("🛑 Estou parando aqui pois já chegamos na vitória do dia.")
                                exit()

                    # Processa derrotas
                    elif profit < 0:
                        qtd_derrotas += 1
                        
                        print(f"## OPERAÇÃO PERDEDORA [{qtd_vitorias}x{qtd_derrotas}]")

                        # Se é a primeira derrota, considera para os calculos de gale a entrada padrao
                        if qtd_vitorias_seguidas > 0:
                            valor_operacao = entrada_padrao

                        qtd_vitorias_seguidas = 0
                        
                        soma_percas += valor_operacao
                        qtd_percas_seguidas += 1

                        valor_operacao = round(soma_percas / taxa_profit, 2)
                        
                        if qtd_percas_seguidas > max_gales:
                            valor_operacao = entrada_padrao
                            print(f"Quantidade de perdas seguidas atingiu o máximo de Gales ({max_gales}), reiniciando com entrada padrão {valor_operacao:.2f}.")
                        else:
                            print(f"Valor da operação atualizado para {valor_operacao:.2f} após derrota.")

                        with open("historico_5.txt", "a", encoding="utf-8") as arquivo_historico:
                            arquivo_historico.write("Loss\n")

                if saldo <= stop_loss:
                    mensagem = f"## STOP LOSS ATINGIDO! Saldo ini {saldo_inicial:.2f} atual: {saldo:.2f}, Stop Loss: {stop_loss:.2f}"
                    print(mensagem)
                    send_slack_notification(mensagem)
                    exit()

                if saldo >= stop_gain:
                    mensagem = f"## STOP GAIN ATINGIDO! Saldo ini {saldo_inicial:.2f} atual: {saldo:.2f}, Stop Gain: {stop_gain:.2f}"
                    print(mensagem)
                    send_slack_notification(mensagem)
                    exit()

                if analisa_stop_qtd:
                    if qtd_derrotas >= max_derrotas:
                        mensagem = f"## MAX PERDAS ATINGIDO! Saldo ini {saldo_inicial:.2f} atual: {saldo:.2f}"
                        print(mensagem)
                        send_slack_notification(mensagem)
                        exit()

                    if qtd_vitorias >= max_vitorias:
                        mensagem = f"## MAX VITORIAS ATINGIDO! Saldo ini {saldo_inicial:.2f} atual: {saldo:.2f}"
                        print(mensagem)
                        send_slack_notification(mensagem)
                        exit()

            direcao = "Indefinida"
            
            candle_atual_em_alta = historico[-1] > historico[-2]
            candle_atual_em_baixa = historico[-1] < historico[-2]

            delta_minimo = 0.0001
            delta_maximo = 0.03
            
            delta = abs(historico[-1] - historico[-2])

            if delta >= delta_minimo and delta <= delta_maximo:
                if candle_atual_em_alta:
                    direcao = "call"
                elif candle_atual_em_baixa:
                    direcao = "put"
                else:
                    direcao = "Indefinida"

            if direcao != "Indefinida":
                check, order_id = iq.buy(valor_operacao, ativo, direcao, tempo_operacao)
                if check:
                    qtd_operacoes += 1
                    print(f"Ordem inserida em {direcao}! ID: {order_id}")
                    if qtd_operacoes > max_operacoes:
                        print(f"Encerrando aqui, {max_operacoes} entradas feitas. Tchau.")
                        exit()

        now = server_time
        seconds_until = calcular_segundos_ate_proximo_analise(now)
        time.sleep(seconds_until)

    except Exception as e:
        print("Erro:", e)
        now = get_server_datetime()
        seconds_until = calcular_segundos_ate_proximo_analise(now)
        time.sleep(seconds_until)
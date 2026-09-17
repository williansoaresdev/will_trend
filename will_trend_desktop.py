'''
    Executor de ordens IQOption
    -> Autor: Willian Soares
    -> willian_zt@hotmail.com
    
    1 - Atua nos candles de 5 minutos
    2 - Identifica o padrão do momento (tendência ou reversão)
    3 - Faz a entrada seguindo o padrão entendido da última meia hora
    4 - Busca vitória em no máximo 3 gales
    5 - Avisa por slack os resultantes
'''


# ---------------------- Bibliotecas ---------------------------- #

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

# Para números aleaórios
import random
import sys

# Para automação pelo clique na tela
from automacoes import existe_5minutos, clicar_no_elemento, entrada_call, entrada_put


# ---------------------- Funções ---------------------------- #


def calcular_segundos_ate_proximo_analise(now):
    intervalo = (5 * 60)
    segundos_restantes = (intervalo - (now.minute % 5) * 60 - now.second) % intervalo
    if segundos_restantes == 0:
        return intervalo
    return segundos_restantes 


def candles_em_tendencia_forte(historico):
    if len(historico) < 6:
        print("candles_em_tendencia_forte: Histórico insuficiente")
        return False

    conta_baixas = 0
    conta_altas = 0
    direcoes = []
    for i in range(len(historico) - 1, 0, -1):
        if historico[i] > historico[i - 1]:
            direcoes.append("alta")
            conta_altas += 1
        elif historico[i] < historico[i - 1]:
            direcoes.append("baixa")
            conta_baixas += 1

    sequencias = 0
    for i in range(1, len(direcoes)):
        if direcoes[i] == direcoes[i - 1]:
            sequencias += 1
    
    if conta_altas > conta_baixas:
        ultima_tendencia_forte = "alta"
    elif conta_baixas > conta_altas:
        ultima_tendencia_forte = "baixa"
    else:
        ultima_tendencia_forte = ""

    print(f"candles_em_tendencia_forte: {sequencias} seq em {len(historico)} candles {ultima_tendencia_forte}.")
    return sequencias >= 5


def candles_em_variacao(historico):
    if len(historico) < 6:
        print("candles_em_variacao: Histórico insuficiente")
        return False

    direcoes = []
    for i in range(len(historico) - 1, 0, -1):
        if historico[i] > historico[i - 1]:
            direcoes.append("alta")
        elif historico[i] < historico[i - 1]:
            direcoes.append("baixa")

    alternancias = 0
    for i in range(1, len(direcoes)):
        if direcoes[i] != direcoes[i - 1]:
            alternancias += 1

    print(f"candles_em_variacao: {alternancias} alternancias em {len(historico)} candles.")
    return alternancias >= 3


def define_direcao(historico):
    global tendencia

    if len(historico) < 6:
        return "Indefinida"

    # A direção do último candle é importante par a ação
    candle_atual_em_alta = historico[-1] > historico[-2]
    candle_atual_em_baixa = historico[-1] < historico[-2]

    delta_minimo = 0.0001
    delta_maximo = 0.03

    # Doji ou candles mto longos a gente nao entra
    delta = abs(historico[-1] - historico[-2])

    if delta < delta_minimo or delta > delta_maximo:
        tendencia = "Indefinida"
        print("Candle fora do tamanho ideal.")
        return "Indefinida"

    # Para tendencia, ele segue a tendencia, mesmo que o ultimo candle seja do sentido oposto
    if candles_em_tendencia_forte(historico):
        tendencia = "Tendência"
        if ultima_tendencia_forte == "alta":
            return "call"
        elif ultima_tendencia_forte == "baixa":
            return "put"

    # Para reversão, aplica-se o sentido contrário do último candle
    if candles_em_variacao(historico):
        tendencia = "Reversão"
        if candle_atual_em_alta:
            return "put"
        elif candle_atual_em_baixa:
            return "call"

    tendencia = "Indefinida"
    return "Indefinida"


def espera_proximo_horario():
    global historico, tendencia, direcao
    global valor_operacao, comecando_dia, qtd_vitorias, qtd_vitorias_seguidas
    global qtd_derrotas, soma_percas, qtd_percas_seguidas

    # Define o tempo de espera
    candles_espera = random.randint(1, 3)
    send_slack_notification(f"⌛ Vou esperar {candles_espera} candles para começar de novo.")
    
    # Reinicia os parametros de entrada
    historico = []
    valor_operacao = entrada_padrao
    comecando_dia = True
    direcao = "Indefinida"
    tendencia = "Indefinida"
    qtd_vitorias = 0
    qtd_vitorias_seguidas = 0
    qtd_derrotas = 0
    soma_percas = 0
    qtd_percas_seguidas = 0
    operacao_aberta = False

    time.sleep(candles_espera * 60 * 5)
    

def get_server_datetime():
    server_timestamp = iq.get_server_timestamp()
    if isinstance(server_timestamp, (int, float)):
        if server_timestamp > 10**12:
            server_timestamp = server_timestamp / 1000
        return datetime.datetime.fromtimestamp(server_timestamp)
    return datetime.datetime.now()


def load_slack_webhook():
    hook_file = Path(__file__).with_name("hook.txt")
    try:
        with hook_file.open("r", encoding="utf-8") as arquivo:
            return arquivo.read().strip()
    except FileNotFoundError:
        return ""


def send_slack_notification(mensagem):
    print(mensagem)

    """Envia uma notificação para o Slack via webhook"""
    try:
        payload = {"text": mensagem}
        
        headers = {
            "Content-Type": "application/json"
        }

        requests.post(SLACK_WEBHOOK, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(f"Erro ao enviar notificação ao Slack: {e}")


# ---------------------- Variáveis iniciais ---------------------------- #

# Webhook do Slack
SLACK_WEBHOOK = load_slack_webhook()

# Meu email de login
LOGIN = "usandodocs@gmail.com"

# Verifica ativo disponível
ativo = "EURUSD-OTC"

# Taxa padrão de profit mínimo
taxa_profit = 0.85

# Define se esta com entrada aberta ou nao
operacao_aberta = False

# Soma das percas (para o gale)
soma_percas = 0
qtd_percas_seguidas = 0
max_gales = 3
para_na_evolucao = True

# Tempo padrao de operacao
tempo_operacao = 5

# Segundos para analisar e entrar
segundos_analise = 5 * 60

# Direção da operação (call ou put)
direcao = "Indefinida"
tendencia = "Indefinida"
ultima_tendencia_forte = ""

# Conta as vitorias
qtd_vitorias = 0
qtd_vitorias_seguidas = 0
qtd_derrotas = 0
qtd_operacoes = 0
max_vitorias = 30
max_derrotas = 30
analisa_stop_qtd = False
max_operacoes = 60

# Para controle das entradas
check, order_id = False, 0

# Controla se está iniciando o dia:
comecando_dia = True


# ---------------------- Script das Entradas ---------------------------- #

print("*=======================================*")
print("|                                       |")
print("| IQ OPTION - WILL TREND by WILL SOARES |")
print("| 5 minutos seguindo padrao da ultima   |")
print("| meia hora                             |")
print("|                                       |")
print("*=======================================*")


# Pede a senha
senha = getpass("Senha: ")

print(f"Logando na IQ como {LOGIN}")

iq = IQ_Option(LOGIN, senha)

ok, motivo = iq.connect()

# Se o login falhar:
if not ok:
    print("Erro:", motivo)
    exit()

conta_selecionada = "PRACTICE"

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

entrada_padrao = 2
valor_operacao = entrada_padrao

# Maximo de Soro (valor de entrada) e Gales (quantidade de perdas consecutivas)
max_soro = entrada_padrao

# Stop Loss e Stop Gain
stop_loss = saldo - (entrada_padrao * 12)

ganho = 2
stop_gain = saldo + ganho

print("Monitorando:", ativo)

historico = []

# Roda a cada 5 minutos até que caia no stop loss ou stop gain
while True:
    try:
        # Começa o dia lendo os ultimos 6 candles do histórico, depois vai lendo apenas o último candle
        if comecando_dia:
            server_time = get_server_datetime()
            initial_candles = iq.get_candles(
                ativo,
                300,
                6,
                server_time.timestamp()
            )
            
            for candle in initial_candles:
                historico.append(candle["close"])
                print(f"{datetime.datetime.fromtimestamp(candle['from']).strftime('%H:%M:%S')} {candle['close']:.5f}")

            print(f"Carregando histórico inicial de {len(initial_candles)} candles...")
            
            fechamento = historico[-1]
            
            comecando_dia = False
        else:
            server_time = get_server_datetime()
            vela = iq.get_candles(
                ativo,
                300,
                1,
                server_time.timestamp()
            )[0]

            fechamento = vela["close"]

            historico.append(fechamento)

            # Se ainda não definiu direção o faz agora:
            if direcao == "Indefinida":
                direcao = define_direcao(historico)
                print(f"📊 Novo candle: {fechamento:.5f}, direção assumida: {direcao}, padrão: {tendencia}")

        if len(historico) > 6:
            historico.pop(0)

        alerta_hora = server_time.strftime("%H:%M:%S")
        print(f"{alerta_hora} {fechamento:.5f}")

        # Checa de novo pois pode ter sido alterado no espera_proximo_horario()
        if direcao != "Indefinida":
            if existe_5minutos():
                check = False
                suspiro = True
                if direcao == "call":
                    time.sleep(10)
                    novo_candle = iq.get_candles(
                        ativo,
                        300,
                        1,
                        get_server_datetime().timestamp()
                    )[0]
                    novo_fechamento = novo_candle["close"]
                    if novo_fechamento < fechamento:
                        check = entrada_call()
                    else:
                        suspiro = False
                elif direcao == "put":
                    time.sleep(10)
                    novo_candle = iq.get_candles(
                        ativo,
                        300,
                        1,
                        get_server_datetime().timestamp()
                    )[0]
                    novo_fechamento = novo_candle["close"]
                    if novo_fechamento > fechamento:
                        check = entrada_put()
                    else:
                        suspiro = False

                if check:
                    send_slack_notification("✅ Fiz uma entrada aqui, acompanhe ai pela tela por favor.")
                    # espera_proximo_horario()
                    exit()
                else:
                    if suspiro:
                        send_slack_notification("⏰ O preço não tem um suspiro, vamos aguardar mais um pouco.")
                    else:
                        send_slack_notification("😐 Não achei a imagem para dar entrada.")
                    direcao = "Indefinida"
            else:
                send_slack_notification("😐 Não achei a indicação de 5 minutos.")
                direcao = "Indefinida"


        now = server_time
        seconds_until = calcular_segundos_ate_proximo_analise(now)
        print(f"Aguardando {seconds_until} segundos até a próxima análise...")
        time.sleep(seconds_until)

    except Exception as e:
        print("Erro:", e)
        now = get_server_datetime()
        seconds_until = calcular_segundos_ate_proximo_analise(now)
        print(f"Aguardando {seconds_until} segundos até a próxima análise...")
        time.sleep(seconds_until)
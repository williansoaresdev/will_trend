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

MOCK_MODE = "-mock" in sys.argv


class MockIQOption:
    def __init__(self):
        self._balance = 1000.0
        self._order_id = 1
        self._last_buy_result = 0

    def connect(self):
        print("[MOCK] Conexão simulada com IQOption habilitada.")
        return True, "mock"

    def change_balance(self, conta):
        print(f"[MOCK] Conta selecionada: {conta}")
        return True

    def get_balance(self):
        return self._balance

    def get_server_timestamp(self):
        return int(time.time() * 1000)

    def get_candles(self, ativo, timeframe, count, timestamp):
        candles = []
        ultimo = random.uniform(1.0001, 1.03)
        for index in range(count):
            direction = random.choice([-1, 1])
            variacao = random.uniform(0.0001, 0.002)
            ultimo = max(1.0001, min(1.03, ultimo + (direction * variacao)))
            candles.append({
                "close": round(ultimo, 5),
                "from": int(timestamp) - (count - index) * timeframe,
            })
        return candles

    def buy(self, valor, ativo, direcao, expiracao):
        resultado = random.randint(1, 100) > 40
        if resultado:
            lucro = valor * 0.85
            self._balance += lucro
            self._last_buy_result = 1
        else:
            perda = valor
            self._balance -= perda
            self._last_buy_result = -1

        self._order_id += 1
        return True, self._order_id

    def check_win_v3(self, order_id):
        return self._last_buy_result


# ---------------------- Funções ---------------------------- #


def calcular_segundos_ate_proximo_analise(now):
    if MOCK_MODE:
        return 1

    intervalo = 5 * 60
    segundos_restantes = (intervalo - (now.minute % 5) * 60 - now.second) % intervalo
    if segundos_restantes == 0:
        return intervalo
    return segundos_restantes + 3


def candles_em_tendencia_forte(historico):
    if len(historico) < 6:
        print("candles_em_tendencia_forte: Histórico insuficiente")
        return False

    direcoes = []
    for i in range(len(historico) - 1, 0, -1):
        if historico[i] > historico[i - 1]:
            direcoes.append("alta")
        elif historico[i] < historico[i - 1]:
            direcoes.append("baixa")

    sequencias = 0
    for i in range(1, len(direcoes)):
        if direcoes[i] == direcoes[i - 1]:
            sequencias += 1

    print(f"candles_em_tendencia_forte: {sequencias} sequencias em {len(historico)} candles.")
    return sequencias >= 4


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

    if candles_em_tendencia_forte(historico):
        tendencia = "Tendência"
        if candle_atual_em_alta:
            return "call"
        elif candle_atual_em_baixa:
            return "put"

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
    global MOCK_MODE

    # Define o tempo de espera
    candles_espera = random.randint(3, 5)
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

    if MOCK_MODE:
        time.sleep(3)
    else:
        time.sleep(candles_espera * 60)
    

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
    if MOCK_MODE:
        time.sleep(1)
        print(f"[MOCK] {mensagem}")
        return

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


if MOCK_MODE:
    print("[MOCK] Modo de simulação habilitado. Nenhuma conexão real com a IQOption será feita.")
    iq = MockIQOption()
    ok, motivo = True, "mock"
else:
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
    if MOCK_MODE:
        conta_selecionada = "PRACTICE"
        break

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

# Valor padrao de operacao
if MOCK_MODE:
    entrada_padrao = 10.0
else:
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

# Maximo de Soro (valor de entrada) e Gales (quantidade de perdas consecutivas)
max_soro = entrada_padrao

# Stop Loss e Stop Gain
stop_loss = saldo - (entrada_padrao * 12)
stop_gain = saldo + (entrada_padrao * 1.5)

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

        # Se tem uma direção a seguir e não for o primeiro loop:
        if direcao != "Indefinida":
            if operacao_aberta:
                saldo_anterior = saldo
                saldo = iq.get_balance()

                profit = round(saldo - saldo_anterior, 2)
                
                # Processa vitórias
                if profit > 0:
                    qtd_vitorias += 1
                    qtd_vitorias_seguidas += 1

                    print(f"🎉 OPERAÇÃO VENCEDORA [{qtd_vitorias}x{qtd_derrotas}]")

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

                    with open("will_trend.txt", "a", encoding="utf-8") as arquivo_historico:
                        arquivo_historico.write("Gain\n")

                    if saldo > saldo_maximo:
                        saldo_maximo = saldo
                        send_slack_notification(f"🎉 Saldo evoluiu de {saldo_inicial:.2f} para {saldo_maximo:.2f} 🍀")
                        if para_na_evolucao:
                            send_slack_notification("🛑 Estou parando aqui pois já chegamos na vitória desse momento.")
                            espera_proximo_horario()

                # Processa derrotas
                elif profit < 0:
                    qtd_derrotas += 1
                    
                    print(f"😢 OPERAÇÃO PERDEDORA [{qtd_vitorias}x{qtd_derrotas}]")

                    # Se é a primeira derrota, considera para os calculos de gale a entrada padrao * 1.2
                    if qtd_derrotas == 1:
                        valor_operacao = entrada_padrao * 1.2

                    qtd_vitorias_seguidas = 0
                    
                    soma_percas += valor_operacao
                    qtd_percas_seguidas += 1

                    valor_operacao = round(soma_percas / taxa_profit, 2)
                    
                    if qtd_percas_seguidas > max_gales:
                        valor_operacao = entrada_padrao
                        print(f"Quantidade de perdas seguidas atingiu o máximo de Gales ({max_gales}), reiniciando com entrada padrão {valor_operacao:.2f}.")
                        send_slack_notification(f"😥 Perdemos {qtd_percas_seguidas} vezes seguidas, foi mal, parando aqui.")
                        espera_proximo_horario()
                    else:
                        print(f"Valor da operação atualizado para {valor_operacao:.2f} após derrota.")

                    with open("will_trend.txt", "a", encoding="utf-8") as arquivo_historico:
                        arquivo_historico.write("Loss\n")

                if saldo <= stop_loss:
                    mensagem = f"## STOP LOSS ATINGIDO! Saldo ini {saldo_inicial:.2f} atual: {saldo:.2f}, Stop Loss: {stop_loss:.2f}"
                    send_slack_notification(mensagem)
                    exit()

                if saldo >= stop_gain:
                    mensagem = f"## STOP GAIN ATINGIDO! Saldo ini {saldo_inicial:.2f} atual: {saldo:.2f}, Stop Gain: {stop_gain:.2f}"
                    send_slack_notification(mensagem)
                    exit()

                if analisa_stop_qtd:
                    if qtd_derrotas >= max_derrotas:
                        mensagem = f"## MAX PERDAS ATINGIDO! Saldo ini {saldo_inicial:.2f} atual: {saldo:.2f}"
                        send_slack_notification(mensagem)
                        exit()

                    if qtd_vitorias >= max_vitorias:
                        mensagem = f"## MAX VITORIAS ATINGIDO! Saldo ini {saldo_inicial:.2f} atual: {saldo:.2f}"
                        send_slack_notification(mensagem)
                        exit()

            # Checa de novo pois pode ter sido alterado no espera_proximo_horario()
            if direcao != "Indefinida":
                check, order_id = iq.buy(valor_operacao, ativo, direcao, tempo_operacao)
                if check:
                    operacao_aberta = True
                    qtd_operacoes += 1
                    print(f"Ordem inserida em {direcao}! ID: {order_id}")
                    if qtd_operacoes > max_operacoes:
                        send_slack_notification(f"Encerrando aqui, {max_operacoes} entradas feitas. Tchau.")
                        exit()
                else:
                    send_slack_notification("😐 Não gerou ordem de compra.")

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
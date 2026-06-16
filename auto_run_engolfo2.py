from getpass import getpass
from iqoptionapi.stable_api import IQ_Option
import time
import datetime


LOGIN = "usandodocs@gmail.com"

senha = getpass("Senha: ")

iq = IQ_Option(LOGIN, senha)

ok, motivo = iq.connect()

if not ok:
    print("Erro:", motivo)
    exit()

iq.change_balance("PRACTICE")

saldo = iq.get_balance()
print(f"Saldo prática: {saldo}")

# Verifica ativo disponível
ativos = iq.get_all_open_time()

# Valor padrao de operacao
valor_operacao = 10

# Tempo padrao de operacao
tempo_operacao = 1

# Segundos para analisar e entrar
segundos_analise = 59

if ativos["binary"]["EURUSD"]["open"]:
    ativo = "EURUSD"
elif ativos["binary"]["EURUSD-OTC"]["open"]:
    ativo = "EURUSD-OTC"
else:
    print("Nenhum ativo disponível.")
    exit()

print("Monitorando:", ativo)

historico = []

while True:
    try:
        vela = iq.get_candles(
            ativo,
            60,
            1,
            time.time()
        )[0]

        fechamento = vela["close"]

        historico.append(fechamento)

        if len(historico) > 4:
            historico.pop(0)

        alerta_hora = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"{alerta_hora} {fechamento:.5f}")

        if len(historico) == 4:
            direcao = "Indefinida"

            engolfo_alta = historico[2] < historico[1] and historico[3] > historico[2] and historico[3] > historico[1]
            engolfo_baixa = historico[2] > historico[1] and historico[3] < historico[2] and historico[3] < historico[1]

            padrao_alta = historico[3] > historico[2] and historico[2] > historico[1]
            padrao_baixa = historico[3] < historico[2] and historico[2] < historico[1]

            delta3 = abs(historico[3] - historico[2]) # ultimo candle
            delta2 = abs(historico[2] - historico[1]) # penultimo candle

            delta3_ideal = delta2 * 1.25

            if delta2 > 0.0003 and delta3 >= delta3_ideal:
                ultimos_tres = historico[-3:]
                ultimos_tres_formatados = ", ".join(f"{valor:.5f}" for valor in ultimos_tres)

                if engolfo_alta or engolfo_baixa:
                    if engolfo_alta:
                        print(f"ALERTA: Engolfo de alta - Fechamentos últimos 3 candles: {ultimos_tres_formatados}")
                        direcao = "call"
                    elif engolfo_baixa:
                        print(f"ALERTA: Engolfo de baixa - Fechamentos últimos 3 candles: {ultimos_tres_formatados}")
                        direcao = "put"

                if padrao_alta or padrao_baixa:
                    if padrao_alta:
                        print(f"ALERTA: Padrão de alta - Fechamentos últimos 3 candles: {ultimos_tres_formatados}")
                        direcao = "call"
                    elif padrao_baixa:
                        print(f"ALERTA: Padrão de baixa - Fechamentos últimos 3 candles: {ultimos_tres_formatados}")
                        direcao = "put"


            if direcao != "Indefinida":
                iq.buy(valor_operacao, ativo, direcao, tempo_operacao)

        # Wait until some seconds of the next minute
        now = datetime.datetime.now()
        seconds_until = (segundos_analise - now.second) % 60
        if seconds_until == 0:
            seconds_until = 60
        time.sleep(seconds_until)

    except Exception as e:
        print("Erro:", e)
        # Wait until some seconds of the next minute
        now = datetime.datetime.now()
        seconds_until = (segundos_analise - now.second) % 60
        if seconds_until == 0:
            seconds_until = 60
        time.sleep(seconds_until)
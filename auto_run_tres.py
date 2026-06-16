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
segundos_analise = 50

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

        if len(historico) == 4:
            direcao = "Indefinida"

            d1 = historico[1] > historico[0]
            d2 = historico[2] > historico[1]
            d3 = historico[3] > historico[2]

            q1 = historico[1] < historico[0]
            q2 = historico[2] < historico[1]
            q3 = historico[3] < historico[2]

            if d1 and d2 and d3:
                print("ALERTA: 3 altas consecutivas")
                direcao = "call"
            elif q1 and q2 and q3:
                print("ALERTA: 3 baixas consecutivas")
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
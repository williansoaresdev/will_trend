from getpass import getpass
from iqoptionapi.stable_api import IQ_Option
import time
import datetime
import automacoes


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
            d1 = historico[1] > historico[0]
            d2 = historico[2] > historico[1]
            d3 = historico[3] > historico[2]

            q1 = historico[1] < historico[0]
            q2 = historico[2] < historico[1]
            q3 = historico[3] < historico[2]

            if d1 and d2 and d3:
                print("ALERTA: 3 altas consecutivas")
                automacoes.entrada_call()

            elif q1 and q2 and q3:
                print("ALERTA: 3 baixas consecutivas")
                automacoes.entrada_put()

            else:
                automacoes.volta_para_o_centro()

        # Wait until :45 seconds of the next minute
        now = datetime.datetime.now()
        seconds_until_45 = (45 - now.second) % 60
        if seconds_until_45 == 0:
            seconds_until_45 = 60
        time.sleep(seconds_until_45)

    except Exception as e:
        print("Erro:", e)
        # Wait until :45 seconds of the next minute
        now = datetime.datetime.now()
        seconds_until_45 = (45 - now.second) % 60
        if seconds_until_45 == 0:
            seconds_until_45 = 60
        time.sleep(seconds_until_45)
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

# Para usar nas entradas depois
operando_digitais = False

# Valor padrao de operacao
valor_operacao = 10

# Tempo padrao de operacao
tempo_operacao = 1

if ativos["binary"]["EURUSD"]["open"]:
    ativo = "EURUSD"
elif ativos["binary"]["EURUSD-OTC"]["open"]:
    ativo = "EURUSD-OTC"
else:
    print("Nenhum ativo disponível.")
    exit()

print("Realizando entrada...", ativo)

iq.buy(valor_operacao, ativo, "call", tempo_operacao)

print("Entrada realizada. Aguarde...")
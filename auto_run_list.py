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

print("Ativos binários disponíveis:")
for ativo in sorted(ativos["binary"]):
    if ativos["binary"][ativo]["open"]:
        print(f"{ativo}")

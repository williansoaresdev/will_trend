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

# Para usar nas entradas depois
operando_digitais = False

# Valor padrao de operacao
valor_operacao = 10

# Tempo padrao de operacao
tempo_operacao = 1

ativo = "EURUSD-OTC"

print("Realizando entrada...", ativo)

check, order_id = iq.buy(valor_operacao, ativo, "call", tempo_operacao)

if check:
    print(f"Entrada realizada com sucesso! Order ID: {order_id}")
    time.sleep(110)
    print("Verificando resultado da operação...")
    win = iq.check_win(order_id)
    print(f"Resultado da operação: {win}")
from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
import csv
from pathlib import Path

EMAIL = "usandodocs@gmail.com"
SENHA = "Rps$2018"

Iq = IQ_Option(EMAIL, SENHA)

check, reason = Iq.connect()

if not check:
    print("Falha na conexão:", reason)
    exit()

ATIVO = "EURUSD-OTC"

# Timestamp atual do servidor IQ
end_time = Iq.get_server_timestamp()

# 1 hora = 3600 segundos
# Candle de 5 segundos
candles = Iq.get_candles(
    ATIVO,
    5,
    720,      # 3600 / 5 = 720 candles
    end_time
)

precos_close = []

for candle in candles:
    data_hora = datetime.fromtimestamp(candle["from"])

    precos_close.append({
        "datahora": data_hora.strftime("%Y-%m-%d %H:%M:%S"),
        "close": candle["close"]
    })

arquivo_precos = Path(__file__).with_name("60minutos.csv")
with arquivo_precos.open("w", newline="", encoding="utf-8") as arquivo:
    escritor = csv.DictWriter(arquivo, fieldnames=["datahora", "close"], delimiter=";")
    escritor.writeheader()
    escritor.writerows(precos_close)

for item in precos_close:
    print(f'{item["datahora"]};{item["close"]}')

print(f"\nTotal de registros: {len(precos_close)}")
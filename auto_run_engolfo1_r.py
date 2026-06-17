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

iq.change_balance("REAL")

saldo = iq.get_balance()
print(f"Saldo real: {saldo}")

stop_loss = saldo * 0.9

# Verifica ativo disponível
ativos = iq.get_all_open_time()

# Valor padrao de operacao
valor_operacao = 2

# Tempo padrao de operacao
tempo_operacao = 1

# Segundos para analisar e entrar
segundos_analise = 59

# Direção da operação (call ou put)
direcao = "Indefinida"

# Conta as vitorias
qtd_vitorias = 0
meta_vitorias = 10

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
            # Ajuste e análise de Saldo
            if direcao != "Indefinida":
                saldo_antes = saldo
                saldo = iq.get_balance()
                if saldo > saldo_antes:
                    print(f"## OPERAÇÃO VENCEDORA! Saldo antes: {saldo_antes:.2f}, Saldo depois: {saldo:.2f}")
                    valor_operacao = 2
                    qtd_vitorias += 1
                else:
                    print(f"## OPERAÇÃO PERDEDORA! Saldo antes: {saldo_antes:.2f}, Saldo depois: {saldo:.2f}")
                    if valor_operacao == 16:
                        valor_operacao = 2
                    else:
                        valor_operacao *= 2

                if saldo <= stop_loss:
                    print(f"## STOP LOSS ATINGIDO! Saldo atual: {saldo:.2f}, Stop Loss: {stop_loss:.2f}")
                    exit()
                
                if qtd_vitorias >= meta_vitorias:
                    print(f"## META DE VITÓRIAS ATINGIDA! Vitorias: {qtd_vitorias}, Saldo atual: {saldo:.2f}")
                    exit()

            direcao = "Indefinida"

            engolfo_alta = historico[2] < historico[1] and historico[3] > historico[2] and historico[3] > historico[1]
            engolfo_baixa = historico[2] > historico[1] and historico[3] < historico[2] and historico[3] < historico[1]

            delta3 = abs(historico[3] - historico[2]) # ultimo candle
            delta2 = abs(historico[2] - historico[1]) # penultimo candle

            delta3_ideal = delta2 * 1.25

            if delta2 > 0.0003 and delta3 > 0.0005:
                if engolfo_alta or engolfo_baixa:
                    ultimos_tres = historico[-3:]
                    ultimos_tres_formatados = ", ".join(f"{valor:.5f}" for valor in ultimos_tres)

                    if engolfo_alta:
                        print(f"ALERTA: Engolfo de alta - Fechamentos últimos 3 candles: {ultimos_tres_formatados}")
                        direcao = "call"
                    elif engolfo_baixa:
                        print(f"ALERTA: Engolfo de baixa - Fechamentos últimos 3 candles: {ultimos_tres_formatados}")
                        direcao = "put"

            if direcao != "Indefinida":
                iq.buy(valor_operacao, ativo, direcao, tempo_operacao)

        # Wait until some seconds of the next minute
        now = datetime.datetime.now()
        seconds_until = (segundos_analise - now.second) % 60
        if seconds_until == 0:
            seconds_until = 60
        # Quando faz entrada só analisa 2 minutos depois
        if direcao != "Indefinida":
            seconds_until += 60
        time.sleep(seconds_until)

    except Exception as e:
        print("Erro:", e)
        # Wait until some seconds of the next minute
        now = datetime.datetime.now()
        seconds_until = (segundos_analise - now.second) % 60
        if seconds_until == 0:
            seconds_until = 60
        time.sleep(seconds_until)
import csv
import time
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.stats import kendalltau, theilslopes


preco_anterior = 0.0
BASE_DIR = Path(__file__).resolve().parent


def remover_outliers_mad(valores, thresh=3.5):
    valores = np.array(valores)
    mediana = np.median(valores)
    diff = np.abs(valores - mediana)
    mad = np.median(diff)

    if mad == 0:
        return valores

    z_score = 0.6745 * diff / mad
    return valores[z_score < thresh]


def analisar_tendencia_robusta(valores, remover_outliers=True, slope_minimo=0.00001):
    valores = np.array(valores)

    if remover_outliers:
        valores = remover_outliers_mad(valores)

    if len(valores) < 3:
        return {"erro": "dados insuficientes"}

    x = np.arange(len(valores))
    slope, intercept, lower, upper = theilslopes(valores, x)
    tau, p_value = kendalltau(x, valores)

    if abs(slope) < slope_minimo:
        tendencia = "estavel"
    elif slope > 0:
        tendencia = "subindo"
    else:
        tendencia = "descendo"

    abs_tau = abs(tau)

    if abs_tau > 0.7:
        confianca = "alta"
    elif abs_tau > 0.4:
        confianca = "media"
    else:
        confianca = "baixa"

    return {
        "tendencia": tendencia,
        "confianca": confianca,
        "slope": slope,
        "tau": tau,
        "p_value": p_value,
        "intervalo_slope": (lower, upper),
        "qtd_pontos": len(valores),
    }


def buscar_fechamentos_forex(symbol="EURUSD=X", janela=30):
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError(
            "Dependencia ausente: instale com `pip install -r requirements.txt`."
        ) from exc

    ticker = yf.Ticker(symbol)
    dados = ticker.history(period="1d", interval="1m")

    if dados.empty or "Close" not in dados:
        raise RuntimeError(f"Nenhum dado retornado para {symbol}.")

    fechamentos = dados["Close"].dropna().tail(janela)

    if len(fechamentos) < 3:
        raise RuntimeError(
            f"Dados insuficientes para {symbol}: {len(fechamentos)} ponto(s)."
        )

    ultimo_horario = fechamentos.index[-1]
    ultimo_preco = float(fechamentos.iloc[-1])
    return fechamentos.astype(float).tolist(), ultimo_horario, ultimo_preco


def formatar_nome_moeda(symbol):
    return symbol.replace("=X", "")


def caminho_csv_resultados(symbol):
    moeda = formatar_nome_moeda(symbol)
    nome_seguro = "".join(char for char in moeda if char.isalnum())
    return BASE_DIR / f"resultados_{nome_seguro}.csv"


def salvar_resultado_csv(
    symbol,
    horario_local,
    ultimo_horario,
    ultimo_preco,
    resultado,
    direcao_real,
):
    caminho_csv = caminho_csv_resultados(symbol)
    precisa_cabecalho = not caminho_csv.exists() or caminho_csv.stat().st_size == 0
    campos = [
        "horario_local",
        "symbol",
        "candle",
        "preco",
        "tendencia",
        "confianca",
        "slope",
        "tau",
        "p_value",
        "intervalo_slope_min",
        "intervalo_slope_max",
        "qtd_pontos",
        "direcao_real",
    ]
    linha = {
        "horario_local": horario_local,
        "symbol": symbol,
        "candle": ultimo_horario,
        "preco": f"{ultimo_preco:.5f}",
        "tendencia": resultado["tendencia"],
        "confianca": resultado["confianca"],
        "slope": f"{resultado['slope']:.8f}",
        "tau": f"{resultado['tau']:.4f}",
        "p_value": f"{resultado['p_value']:.8f}",
        "intervalo_slope_min": f"{resultado['intervalo_slope'][0]:.8f}",
        "intervalo_slope_max": f"{resultado['intervalo_slope'][1]:.8f}",
        "qtd_pontos": resultado["qtd_pontos"],
        "direcao_real": direcao_real,
    }

    with caminho_csv.open("a", newline="", encoding="utf-8") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=campos)

        if precisa_cabecalho:
            writer.writeheader()

        writer.writerow(linha)


def notificar_alerta_preco(symbol, tendencia):
    try:
        from winotify import Notification
    except ImportError:
        print(
            "Aviso: instale as dependencias com `pip install -r requirements.txt` "
            "para habilitar notificacoes Windows.",
            flush=True,
        )
        return

    moeda = formatar_nome_moeda(symbol)
    toast = Notification(
        app_id="Will Trend",
        title="Alerta de Preço",
        msg=f"A moeda {moeda} está {tendencia}",
        duration="short",
    )
    toast.show()


def imprimir_tendencia(symbol, janela, slope_minimo):
    global preco_anterior
    
    valores, ultimo_horario, ultimo_preco = buscar_fechamentos_forex(symbol, janela)
    resultado = analisar_tendencia_robusta(valores, slope_minimo=slope_minimo)
    horario_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    direcao_real = ""
    if preco_anterior != 0.0:
        direcao_real = "subindo" if ultimo_preco > preco_anterior else "descendo" if ultimo_preco < preco_anterior else "estavel"

    print(
        f"[{horario_local}] {symbol} | candle: {ultimo_horario} | "
        f"preco: {ultimo_preco:.5f} | tend: {resultado['tendencia']} | "
        f"conf: {resultado['confianca']} | slope: {resultado['slope']:+.8f} | "
        f"tau: {resultado['tau']:+.4f} | real: {direcao_real}",
        flush=True,
    )
    salvar_resultado_csv(
        symbol,
        horario_local,
        ultimo_horario,
        ultimo_preco,
        resultado,
        direcao_real,
    )

    if resultado["confianca"] == "alta":
        notificar_alerta_preco(symbol, resultado["tendencia"])

    preco_anterior = ultimo_preco


def criar_parser():
    parser = ArgumentParser(
        description="Analisa a tendencia do par forex EUR/USD em candles de 1 minuto."
    )
    parser.add_argument(
        "--symbol",
        default="EURUSD=X",
        help="Simbolo do Yahoo Finance para o par forex. Padrao: EURUSD=X.",
    )
    parser.add_argument(
        "--janela",
        type=int,
        default=30,
        help="Quantidade de candles de 1 minuto usados na analise. Padrao: 30.",
    )
    parser.add_argument(
        "--intervalo",
        type=int,
        default=60,
        help="Intervalo entre leituras, em segundos. Padrao: 60.",
    )
    parser.add_argument(
        "--slope-minimo",
        type=float,
        default=0.00001,
        help="Variacao minima por candle para sair de estavel. Padrao: 0.00001.",
    )
    parser.add_argument(
        "--uma-vez",
        action="store_true",
        help="Executa apenas uma leitura e encerra.",
    )
    return parser


def saudacoes():
    print("█████ ████  █████ ██   █ ███")
    print("  █   █   █ █     █ █  █ █  █")
    print("  █   ████  ███   █  █ █ █  █")
    print("  █   █   █ █     █   ██ █  █")
    print("  █   █   █ █████ █    █ ███")
    print(" ")
    print("Iniciando analise de tendencia...")
    print(" ")
    time.sleep(3)


if __name__ == "__main__":
    args = criar_parser().parse_args()

    saudacoes()

    while True:
        try:
            imprimir_tendencia(args.symbol, args.janela, args.slope_minimo)
        except Exception as erro:
            horario_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{horario_local}] erro: {erro}", flush=True)

        if args.uma_vez:
            break

        time.sleep(args.intervalo)

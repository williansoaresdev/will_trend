import time
from argparse import ArgumentParser
from datetime import datetime

import numpy as np
from scipy.stats import kendalltau, theilslopes


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


def imprimir_tendencia(symbol, janela, slope_minimo):
    valores, ultimo_horario, ultimo_preco = buscar_fechamentos_forex(symbol, janela)
    resultado = analisar_tendencia_robusta(valores, slope_minimo=slope_minimo)
    horario_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(
        f"[{horario_local}] {symbol} | candle: {ultimo_horario} | "
        f"preco: {ultimo_preco:.5f} | tendencia: {resultado['tendencia']} | "
        f"confianca: {resultado['confianca']} | slope: {resultado['slope']:.8f} | "
        f"tau: {resultado['tau']:.4f} | pontos: {resultado['qtd_pontos']}",
        flush=True,
    )


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


if __name__ == "__main__":
    args = criar_parser().parse_args()

    while True:
        try:
            imprimir_tendencia(args.symbol, args.janela, args.slope_minimo)
        except Exception as erro:
            horario_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{horario_local}] erro: {erro}", flush=True)

        if args.uma_vez:
            break

        time.sleep(args.intervalo)

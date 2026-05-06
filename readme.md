# Analisador de tendencia EUR/USD

Ative o ambiente virtual e instale as dependencias:

```bash
source venv/Scripts/activate
pip install -r requirements.txt
```

No PowerShell, use:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Execute uma leitura do EUR/USD:

```bash
python main.py --uma-vez
```

Execute leituras continuas a cada 1 minuto:

```bash
python main.py
```

Por padrao, o script usa o simbolo `EURUSD=X` do Yahoo Finance, candles de 1 minuto
e uma janela de 30 candles para calcular a tendencia.

Quando a confianca da tendencia for `alta`, o script exibe uma notificacao Windows
com o titulo `Alerta de Preço` e a mensagem usando a moeda e a tendencia atuais.

Cada analise impressa tambem e adicionada a um CSV na raiz do projeto. Para o par
`EURUSD=X`, o arquivo gerado sera `resultados_EURUSD.csv`.

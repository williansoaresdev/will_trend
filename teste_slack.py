# Para enviar notificações ao Slack
from pathlib import Path
import requests


def load_slack_webhook():
    hook_file = Path(__file__).with_name("hook.txt")
    try:
        with hook_file.open("r", encoding="utf-8") as arquivo:
            return arquivo.read().strip()
    except FileNotFoundError:
        print("Nao leu o arquivo hook.txt")
        return ""


# Webhook do Slack
SLACK_WEBHOOK = load_slack_webhook()

def send_slack_notification(mensagem):
    """Envia uma notificação para o Slack via webhook"""
    try:
        payload = {"text": mensagem}
        
        headers = {
            "Content-Type": "application/json"
        }

        requests.post(SLACK_WEBHOOK, json=payload, headers=headers, timeout=10)
        
        print("Enviado")
    except Exception as e:
        print(f"Erro ao enviar notificação ao Slack: {e}")


send_slack_notification("Teste de Slack")
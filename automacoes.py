import pyautogui

def clicar_no_elemento(caminho_imagem):
    try:
        # 1. Localiza o centro da imagem na tela
        # confidence: nível de confiança (0.1 a 1.0). Requer opencv-python.
        localizacao = pyautogui.locateCenterOnScreen(caminho_imagem, confidence=0.8)

        if localizacao:
            print(f"Elemento encontrado em: {localizacao}")

            # 2. Move o mouse e clica
            pyautogui.click(localizacao)
        else:
            print("Imagem não encontrada na tela.")

    except Exception as e:
        print(f"Não clicou em {caminho_imagem}. {e}")
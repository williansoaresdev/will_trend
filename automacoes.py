import pyautogui
import random
import time


def aleatorio():
    return random.randint(1, 3)


def clicar_no_elemento(caminho_imagem):
    try:
        # 1. Localiza o centro da imagem na tela
        # confidence: nível de confiança (0.1 a 1.0). Requer opencv-python.
        localizacao = pyautogui.locateCenterOnScreen(caminho_imagem, confidence=0.8)

        if localizacao:
            print(f"Elemento encontrado em: {localizacao}")

            # 2. Move o mouse e clica
            pyautogui.click(localizacao)

            time.sleep(1)

            volta_para_o_centro()
        else:
            print("Imagem não encontrada na tela.")

    except Exception as e:
        print(f"Não clicou em {caminho_imagem}. {e}")


def entrada_call():
    clicar_no_elemento('./images/acima{}.png'.format(aleatorio()))


def entrada_put():
    clicar_no_elemento('./images/abaixo{}.png'.format(aleatorio()))


def existe_elemento(caminho_imagem):
    try:
        # 1. Localiza o centro da imagem na tela
        # confidence: nível de confiança (0.1 a 1.0). Requer opencv-python.
        localizacao = pyautogui.locateCenterOnScreen(caminho_imagem, confidence=0.8)

        return localizacao is not None

    except Exception as e:
        print(f"Não achou {caminho_imagem}. {e}")

        return False


def volta_para_o_centro():
    margem_pixels = 100

    largura, altura = pyautogui.size()

    centro_x = largura // 2
    centro_y = altura // 2

    aleatorio_x = random.randint(centro_x - margem_pixels, centro_x + margem_pixels)
    aleatorio_y = random.randint(centro_y - margem_pixels, centro_y + margem_pixels)

    pyautogui.moveTo(aleatorio_x, aleatorio_y, duration=1.0)

    time.sleep(1)
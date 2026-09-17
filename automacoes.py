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
            #print(f"Elemento encontrado em: {localizacao}")

            # 2. Move o mouse e clica
            pyautogui.click(localizacao)

            time.sleep(1)

            volta_para_o_centro()
            
            return True
        else:
            print("Imagem não encontrada na tela.")

    except Exception as e:
        print(f"Não clicou em {caminho_imagem}. {e}")

    return False


def entrada_call():
    return clicar_no_elemento('./images/acima{}.png'.format(aleatorio()))


def entrada_put():
    return clicar_no_elemento('./images/abaixo{}.png'.format(aleatorio()))


def existe_5minutos():
    return existe_elemento('./images/exp_5min.png')
    pass
    

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


def digita_texto(texto, intervalo=0.05):
    """Digita o texto enviado caractere a caractere.

    - `texto`: string a ser digitada.
    - `intervalo`: tempo em segundos entre cada tecla (padrão 0.05).
    Garante suporte básico para letras maiúsculas, espaços, enter e tab.
    """
    for ch in texto:
        try:
            if ch == ' ':
                pyautogui.press('space')
            elif ch == '\n':
                pyautogui.press('enter')
            elif ch == '\t':
                pyautogui.press('tab')
            elif ch.isalpha():
                if ch.isupper():
                    pyautogui.keyDown('shift')
                    pyautogui.press(ch.lower())
                    pyautogui.keyUp('shift')
                else:
                    pyautogui.press(ch)
            elif ch.isdigit():
                pyautogui.press(ch)
            else:
                # tenta enviar o nome da tecla ou escrever o caractere
                try:
                    pyautogui.press(ch)
                except Exception:
                    pyautogui.typewrite(ch)
        except Exception as e:
            print(f"Erro ao digitar '{ch}': {e}")

        time.sleep(intervalo)


def combina_teclas(ctrl, alt, shift, letra_numero):
    """Pressiona combinações de teclas com modificadores.

    - `ctrl`, `alt`, `shift`: booleanos indicando se o modificador deve ser pressionado.
    - `letra_numero`: string com a tecla principal (ex: 'a', '1').

    Exemplo: `combina_teclas(True, False, False, 'a')` envia CTRL+A.
    """
    modifiers = []
    if ctrl:
        modifiers.append('ctrl')
    if alt:
        modifiers.append('alt')
    if shift:
        modifiers.append('shift')

    # Pressiona modificadores
    for m in modifiers:
        pyautogui.keyDown(m)

    try:
        key = letra_numero
        if isinstance(key, str) and len(key) == 1:
            key = key.lower()

        pyautogui.press(key)
    except Exception as e:
        print(f"Erro ao enviar tecla '{letra_numero}': {e}")

    # Solta modificadores na ordem inversa
    for m in reversed(modifiers):
        try:
            pyautogui.keyUp(m)
        except Exception:
            pass


def envia_backspace(qtd=1, intervalo=0.05):
    """Envia a tecla Backspace `qtd` vezes com intervalo entre cada uma.

    - `qtd`: número de backspaces a enviar (int >= 1).
    - `intervalo`: tempo em segundos entre cada backspace (padrão 0.05).
    """
    try:
        qtd = int(qtd)
    except Exception:
        print(f"Quantidade inválida para backspace: {qtd}")
        return

    if qtd <= 0:
        return

    for _ in range(qtd):
        try:
            pyautogui.press('backspace')
        except Exception as e:
            print(f"Erro ao enviar backspace: {e}")
        time.sleep(intervalo)


def envia_delete(qtd=1, intervalo=0.05):
    """Envia a tecla Delete `qtd` vezes com intervalo entre cada uma.

    - `qtd`: número de deletes a enviar (int >= 1).
    - `intervalo`: tempo em segundos entre cada delete (padrão 0.05).
    """
    try:
        qtd = int(qtd)
    except Exception:
        print(f"Quantidade inválida para delete: {qtd}")
        return

    if qtd <= 0:
        return

    for _ in range(qtd):
        try:
            pyautogui.press('delete')
        except Exception as e:
            print(f"Erro ao enviar delete: {e}")
        time.sleep(intervalo)
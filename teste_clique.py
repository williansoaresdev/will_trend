import automacoes

def testa_clique_keep():
    if automacoes.existe_elemento('./images/keep1.png'):
        print("Elemento encontrado. Clicando...")
        automacoes.clicar_no_elemento('./images/keep1.png')

if __name__ == "__main__":
    testa_clique_keep()

import time
import threading
import pandas as pd
import customtkinter as ctk
from iqoptionapi.stable_api import IQ_Option
from datetime import datetime

class JanelaConfiguracoes(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Configurações Avançadas - Robo12")
        self.geometry("450x730")
        self.grab_set() 
        
        self.parent = parent
        self.linhas_horarios = []

        self.scroll = ctk.CTkScrollableFrame(self, width=420, height=610)
        self.scroll.pack(pady=10, padx=10, fill="both", expand=True)

        ctk.CTkLabel(self.scroll, text="Tipo de Mercado:", font=("Arial", 11, "bold")).pack(pady=(5, 0))
        self.mercado_var = ctk.StringVar(value=parent.config_dados["tipo_mercado"])
        self.menu_mercado = ctk.CTkOptionMenu(
            self.scroll, 
            values=["OTC", "Normal"], 
            variable=self.mercado_var,
            command=self.atualizar_lista_ativos
        )
        self.menu_mercado.pack(pady=5, fill="x", padx=10)

        ctk.CTkLabel(self.scroll, text="Selecione o Ativo:", font=("Arial", 11, "bold")).pack(pady=(5, 0))
        self.ativo_var = ctk.StringVar(value=parent.config_dados["ativo"])
        
        self.pares_base = ["EURUSD", "GBPUSD", "GBPJPY", "AUDUSD", "EURJPY", "USDCHF"]
        values_iniciais = [f"{p}-OTC" if self.mercado_var.get() == "OTC" else p for p in self.pares_base]
        
        self.menu_ativo = ctk.CTkOptionMenu(self.scroll, values=values_iniciais, variable=self.ativo_var)
        self.menu_ativo.pack(pady=5, fill="x", padx=10)

        ctk.CTkLabel(self.scroll, text="Valor do Incremento de Soros (Ex: 3, 5, 10):", font=("Arial", 11, "bold")).pack(pady=(10, 0))
        self.input_soros = ctk.CTkEntry(self.scroll, placeholder_text="Digite o valor do incremento (ex: 3)")
        self.input_soros.insert(0, parent.config_dados["soros"])
        self.input_soros.pack(pady=5, fill="x", padx=10)

        self.frame_gain = ctk.CTkFrame(self.scroll)
        self.frame_gain.pack(pady=5, fill="x", padx=10)
        self.ativar_gain = ctk.BooleanVar(value=parent.config_dados["ativar_gain"])
        ctk.CTkCheckBox(self.frame_gain, text="Stop Gain ($)", variable=self.ativar_gain).pack(side="left", padx=5, pady=5)
        self.input_gain = ctk.CTkEntry(self.frame_gain, width=90); self.input_gain.insert(0, parent.config_dados["val_gain"])
        self.input_gain.pack(side="right", padx=5, pady=5)

        self.frame_loss = ctk.CTkFrame(self.scroll)
        self.frame_loss.pack(pady=5, fill="x", padx=10)
        self.ativar_loss = ctk.BooleanVar(value=parent.config_dados["ativar_loss"])
        ctk.CTkCheckBox(self.frame_loss, text="Stop Loss (Qtd)", variable=self.ativar_loss).pack(side="left", padx=5, pady=5)
        self.input_loss = ctk.CTkEntry(self.frame_loss, width=90); self.input_loss.insert(0, parent.config_dados["val_loss"])
        self.input_loss.pack(side="right", padx=5, pady=5)

        self.frame_hora = ctk.CTkFrame(self.scroll)
        self.frame_hora.pack(pady=5, fill="x", padx=10)
        self.ativar_hora = ctk.BooleanVar(value=parent.config_dados["ativar_hora"])
        ctk.CTkCheckBox(self.frame_hora, text="Stop Horário Fixo", variable=self.ativar_hora).pack(side="left", padx=5, pady=5)
        self.input_hora = ctk.CTkEntry(self.frame_hora, width=90); self.input_hora.insert(0, parent.config_dados["val_hora"])
        self.input_hora.pack(side="right", padx=5, pady=5)

        self.frame_periodo = ctk.CTkFrame(self.scroll)
        self.frame_periodo.pack(pady=5, fill="x", padx=10)
        self.ativar_periodo = ctk.BooleanVar(value=parent.config_dados["ativar_periodo"])
        ctk.CTkCheckBox(self.frame_periodo, text="Ativar Período (Vela)", variable=self.ativar_periodo).pack(side="left", padx=5, pady=5)
        self.menu_periodo = ctk.CTkOptionMenu(self.frame_periodo, values=["5s", "1m", "5m", "15m"], width=100)
        self.menu_periodo.set(parent.config_dados["val_periodo"])
        self.menu_periodo.pack(side="right", padx=5, pady=5)

        self.frame_exp = ctk.CTkFrame(self.scroll)
        self.frame_exp.pack(pady=5, fill="x", padx=10)
        self.ativar_exp = ctk.BooleanVar(value=parent.config_dados["ativar_exp"])
        ctk.CTkCheckBox(self.frame_exp, text="Ativar Expiração Fixa", variable=self.ativar_exp).pack(side="left", padx=5, pady=5)
        self.menu_exp = ctk.CTkOptionMenu(self.frame_exp, values=["30 seg", "1 min", "2 min", "3 min", "4 min", "5 min"], width=100)
        self.menu_exp.set(parent.config_dados["val_exp"])
        self.menu_exp.pack(side="right", padx=5, pady=5)

        self.frame_agenda = ctk.CTkFrame(self.scroll)
        self.frame_agenda.pack(pady=5, fill="x", padx=10)
        self.ativar_agenda = ctk.BooleanVar(value=parent.config_dados["ativar_agenda"])
        ctk.CTkCheckBox(self.frame_agenda, text="Ativar Agendamento de Horários", variable=self.ativar_agenda).pack(side="top", anchor="w", padx=5, pady=5)
        
        self.container_linhas = ctk.CTkFrame(self.frame_agenda)
        self.container_linhas.pack(fill="x", padx=5, pady=5)
        
        btn_add = ctk.CTkButton(self.frame_agenda, text="+ Adicionar Horário", command=self.adicionar_linha, fg_color="#555555", height=24)
        btn_add.pack(pady=5)
        
        if parent.config_dados["agenda_linhas"]:
            for h1, h2 in parent.config_dados["agenda_linhas"]:
                self.adicionar_linha(h1, h2)
        else:
            self.adicionar_linha("08:00", "16:00")

        btn_salvar = ctk.CTkButton(self, text="Salvar e Voltar", command=self.salvar_e_fechar, fg_color="#28a745", height=38)
        btn_salvar.pack(pady=10, padx=20, fill="x")

    def atualizar_lista_ativos(self, escolha):
        if escolha == "OTC":
            novos_valores = [f"{p}-OTC" for p in self.pares_base]
        else:
            novos_valores = self.pares_base
        
        self.menu_ativo.configure(values=novos_valores)
        self.ativo_var.set(novos_valores[0])

    def adicionar_linha(self, h_ini="08:00", h_fim="16:00"):
        f = ctk.CTkFrame(self.container_linhas)
        f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text="Ligar:", font=("Arial", 10)).pack(side="left", padx=2)
        e1 = ctk.CTkEntry(f, width=60); e1.pack(side="left", padx=2); e1.insert(0, h_ini)
        ctk.CTkLabel(f, text="Desligar:", font=("Arial", 10)).pack(side="left", padx=2)
        e2 = ctk.CTkEntry(f, width=60); e2.pack(side="left", padx=2); e2.insert(0, h_fim)
        self.linhas_horarios.append((e1, e2))

    def salvar_e_fechar(self):
        self.parent.config_dados["tipo_mercado"] = self.mercado_var.get()
        self.parent.config_dados["ativo"] = self.ativo_var.get()
        self.parent.config_dados["soros"] = self.input_soros.get()
        self.parent.config_dados["ativar_gain"] = self.ativar_gain.get()
        self.parent.config_dados["val_gain"] = self.input_gain.get()
        self.parent.config_dados["ativar_loss"] = self.ativar_loss.get()
        self.parent.config_dados["val_loss"] = self.input_loss.get()
        self.parent.config_dados["ativar_hora"] = self.ativar_hora.get()
        self.parent.config_dados["val_hora"] = self.input_hora.get()
        self.parent.config_dados["ativar_periodo"] = self.ativar_periodo.get()
        self.parent.config_dados["val_periodo"] = self.menu_periodo.get()
        self.parent.config_dados["ativar_exp"] = self.ativar_exp.get()
        self.parent.config_dados["val_exp"] = self.menu_exp.get()
        self.parent.config_dados["ativar_agenda"] = self.ativar_agenda.get()
        
        linhas = []
        for e1, e2 in self.linhas_horarios:
            linhas.append((e1.get().strip(), e2.get().strip()))
        self.parent.config_dados["agenda_linhas"] = linhas
        self.destroy()


class Robo12_Original(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Robo12 - O Retorno da Estratégia Vencedora")
        self.geometry("400x750")
        self.wins, self.losses, self.draws = 0, 0, 0
        self.rodando = False
        
        self.valor_base = 10.0
        self.valor_atual = 10.0
        self.ultima_direcao = None  # Trava de alternância obrigatória
        self.historico_operacoes = []
        self.saldo_inicial_sessao = 0.0

        self.config_dados = {
            "tipo_mercado": "OTC",
            "ativo": "EURUSD-OTC",
            "soros": "3",
            "ativar_gain": False, "val_gain": "300",
            "ativar_loss": False, "val_loss": "3",
            "ativar_hora": False, "val_hora": "23:00",
            "ativar_periodo": False, "val_periodo": "5s",
            "ativar_exp": True, "val_exp": "1 min",
            "ativar_agenda": False, "agenda_linhas": []
        }
        
        self.criar_menu_superior()
        
        self.email = ctk.CTkEntry(self, placeholder_text="E-mail"); self.email.pack(pady=5, padx=20, fill="x")
        self.senha = ctk.CTkEntry(self, placeholder_text="Senha", show="*"); self.senha.pack(pady=5, padx=20, fill="x")
        self.valor = ctk.CTkEntry(self, placeholder_text="Valor Base"); self.valor.insert(0, "10"); self.valor.pack(pady=5, padx=20, fill="x")
        
        self.lbl_tipo_conta = ctk.CTkLabel(self, text="Selecione a Conta:", text_color="black", font=("Arial", 11, "bold")); self.lbl_tipo_conta.pack(pady=(5, 0))
        self.conta_var = ctk.StringVar(value="PRACTICE")
        self.menu_conta = ctk.CTkSegmentedButton(self, values=["PRACTICE", "REAL"], variable=self.conta_var)
        self.menu_conta.pack(pady=5, padx=20, fill="x")

        self.btn_abrir_menu = ctk.CTkButton(self, text="⚙️ Abrir Configurações / Menu Avançado", command=self.abrir_janela_config, fg_color="#555555"); self.btn_abrir_menu.pack(pady=10, padx=20, fill="x")

        self.btn_ligar = ctk.CTkButton(self, text="LIGAR ROBO12", command=self.iniciar, fg_color="#1A73E8"); self.btn_ligar.pack(pady=10, padx=20, fill="x")
        self.btn_desligar = ctk.CTkButton(self, text="DESLIGAR ROBÔ", command=self.desligar, fg_color="#d9534f", height=35, state="disabled"); self.btn_desligar.pack(pady=5, padx=20, fill="x")
        
        self.lbl_saldo = ctk.CTkLabel(self, text="Saldo: Carregando...", font=("Arial", 16, "bold"), text_color="black"); self.lbl_saldo.pack()
        self.lbl_stats = ctk.CTkLabel(self, text="Wins: 0 | Loss: 0 | Draw: 0", text_color="black"); self.lbl_stats.pack()
        self.lbl_log = ctk.CTkLabel(self, text="Status: Aguardando...", text_color="blue"); self.lbl_log.pack(pady=10)

    def criar_menu_superior(self):
        import tkinter as tk
        menubar = tk.Menu(self)
        menu_opcoes = tk.Menu(menubar, tearoff=0)
        menu_opcoes.add_command(label="Exportar Relatório CSV", command=self.salvar_historico_csv)
        menu_opcoes.add_separator()
        menu_opcoes.add_command(label="Sair", command=self.quit)
        menubar.add_cascade(label="Arquivo", menu=menu_opcoes)
        self.config(menu=menubar)

    def abrir_janela_config(self):
        JanelaConfiguracoes(self)

    def validar_horario_funcionamento(self):
        if not self.config_dados["ativar_agenda"]:
            return True
        hora_atual_str = datetime.now().strftime('%H:%M')
        for h_liga, h_desliga in self.config_dados["agenda_linhas"]:
            if h_liga <= hora_atual_str <= h_desliga:
                return True
        return False

    def verificar_paradas(self):
        if self.config_dados["ativar_gain"]:
            try:
                meta = float(self.config_dados["val_gain"])
                if (self.api.get_balance() - self.saldo_inicial_sessao) >= meta:
                    self.lbl_log.configure(text="Status: Parado (Stop Gain Atingido)")
                    return True
            except: pass

        if self.config_dados["ativar_loss"]:
            try:
                limite = int(self.config_dados["val_loss"])
                if self.losses >= limite:
                    self.lbl_log.configure(text="Status: Parado (Stop Loss Atingido)")
                    return True
            except: pass

        if self.config_dados["ativar_hora"]:
            try:
                if datetime.now().strftime('%H:%M') >= self.config_dados["val_hora"]:
                    self.lbl_log.configure(text="Status: Parado (Horário Limite Atingido)")
                    return True
            except: pass
        return False

    def diagnosticar_entrada(self, candles):
        df = pd.DataFrame(candles)
        if len(df) < 50: return None, None  
        
        # Núcleo Original do MACD (12, 26, 9) do Robo12
        exp12 = df['close'].ewm(span=12, adjust=False).mean()
        exp26 = df['close'].ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal = macd.ewm(span=9, adjust=False).mean()
        
        m_atual, s_atual = macd.iloc[-1], signal.iloc[-1]
        m_ant, s_ant = macd.iloc[-2], signal.iloc[-2]
        
        preco_atual = df['close'].iloc[-1]
        abertura_atual = df['open'].iloc[-1]
        fechamento_atual = df['close'].iloc[-1]
        
        abertura_anterior = df['open'].iloc[-2]
        fechamento_anterior = df['close'].iloc[-2]
        
        vela_atual_verde = fechamento_atual > abertura_atual
        vela_atual_vermelha = fechamento_atual < abertura_atual
        
        # Engolfo simples e direto (que dava agilidade aos sinais)
        engolfo_alta = vela_atual_verde and (fechamento_atual >= abertura_anterior) and (abertura_atual <= fechamento_anterior)
        engolfo_baixa = vela_atual_vermelha and (fechamento_atual <= abertura_anterior) and (abertura_atual >= fechamento_anterior)

        afastamento = abs(m_atual - s_atual)
        macd_caindo = m_atual < m_ant
        macd_subindo = m_atual > m_ant

        print(f"[{datetime.now().strftime('%H:%M:%S')}] MACD: {m_atual:.5f} | Signal: {s_atual:.5f} | Preço: {preco_atual:.5f}")

        # REGRA DE VENDA (PUT): Acima de zero, cruzando para baixo com engolfo de baixa
        criterio_put = (
            self.ultima_direcao != "put" and
            m_atual > 0 and s_atual > 0 and          
            m_atual < s_atual and                    
            macd_caindo and                          
            afastamento > 0.00001 and                
            engolfo_baixa                            
        )
        if criterio_put:
            return "put", "PUT_ACIMA_ZERO_PERFEITO"

        # REGRA DE COMPRA (CALL): Abaixo de zero, cruzando para cima com engolfo de alta
        criterio_call = (
            self.ultima_direcao != "call" and
            m_atual < 0 and s_atual < 0 and          
            m_atual > s_atual and                    
            macd_subindo and                         
            afastamento > 0.00001 and                
            engolfo_alta                             
        )
        if criterio_call:
            return "call", "CALL_ABAIXO_ZERO_PERFEITO"
            
        return None, None

    def salvar_historico_csv(self):
        if not self.historico_operacoes: return
        df_hist = pd.DataFrame(self.historico_operacoes)
        nome_arquivo = f"robo12_historico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df_hist.to_csv(nome_arquivo, index=False, encoding='utf-8-sig')

    def executar_operacao(self, direcao, contexto):
        ativo_atual = self.config_dados["ativo"]
        saldo_antes = self.api.get_balance()
        self.ultima_direcao = direcao  # Trava de alternância do Robo12
        
        try:
            self.valor_base = float(self.valor.get())
        except:
            self.valor_base = 10.0

        try:
            texto_exp = self.config_dados["val_exp"]
            if "30" in texto_exp:
                expiracao_api = 1 
                tempo_espera_check = 35
            elif "1" in texto_exp:
                expiracao_api = 1
                tempo_espera_check = 65
            elif "2" in texto_exp:
                expiracao_api = 2
                tempo_espera_check = 125
            elif "3" in texto_exp:
                expiracao_api = 3
                tempo_espera_check = 185
            elif "4" in texto_exp:
                expiracao_api = 4
                tempo_espera_check = 245
            elif "5" in texto_exp:
                expiracao_api = 5
                tempo_espera_check = 305
            else:
                expiracao_api = 1
                tempo_espera_check = 65
        except:
            expiracao_api = 1
            tempo_espera_check = 65

        if "30" in texto_exp:
            tempo_espera_check = 35

        self.lbl_log.configure(text=f"Status: Executando {direcao.upper()}...")
        
        status, id_op = self.api.buy(self.valor_atual, ativo_atual, direcao, expiracao_api)
        
        if status:
            horario = datetime.now().strftime('%H:%M:%S')
            print(f"=== ROBO12 EXECUTOU ({direcao.upper()}) | Contexto: {contexto} ===")
            print(f"Horário: {horario} | Valor: {self.valor_atual:.2f} | Saldo: {saldo_antes:.2f}")
            
            time.sleep(tempo_espera_check)
            resultado = self.api.check_win_v3(id_op)
            
            try:
                incremento_soros = float(self.config_dados["soros"])
            except:
                incremento_soros = 3.0

            if resultado > 0: 
                self.wins += 1
                self.valor_atual += incremento_soros  
                print(f"Resultado: WIN | Próximo Soros: {self.valor_atual:.2f}")
            elif resultado < 0: 
                self.losses += 1
                self.valor_atual = self.valor_base
                print(f"Resultado: LOSS | Retornando à base: {self.valor_atual:.2f}")
            else: 
                self.draws += 1
                print(f"Resultado: DRAW | Mantendo valor: {self.valor_atual:.2f}")
            
            self.historico_operacoes.append({
                "Data": datetime.now().strftime('%Y-%m-%d'), "Horario": horario, "Ativo": ativo_atual,
                "Direcao": direcao.upper(), "Contexto": contexto, "Resultado": "WIN" if resultado > 0 else ("LOSS" if resultado < 0 else "DRAW"),
                "Lucro_Prejuizo": resultado, "Saldo_Apos": self.api.get_balance()
            })
            self.salvar_historico_csv()
            self.lbl_stats.configure(text=f"Wins: {self.wins} | Loss: {self.losses} | Draw: {self.draws}")
            print("=" * 40)

    def monitorar(self):
        while self.rodando:
            try:
                if self.verificar_paradas():
                    self.rodando = False
                    self.btn_ligar.configure(state="normal")
                    self.btn_desligar.configure(state="disabled")
                    break

                if not self.validar_horario_funcionamento():
                    self.lbl_log.configure(text="Status: Fora do Horário Agendado (Aguardando)")
                    time.sleep(10)
                    continue

                self.lbl_saldo.configure(text=f"Saldo: ${self.api.get_balance():.2f}")
                self.lbl_log.configure(text="Status: Analisando Mercado...")
                
                ativo_atual = self.config_dados["ativo"]
                
                periodo_vela = 5  
                if self.config_dados["ativar_periodo"]:
                    texto_periodo = self.config_dados["val_periodo"]
                    if "5s" in texto_periodo: periodo_vela = 5
                    elif "1m" in texto_periodo: periodo_vela = 60
                    elif "5m" in texto_periodo: periodo_vela = 300
                    elif "15m" in texto_periodo: periodo_vela = 900

                candles = self.api.get_candles(ativo_atual, periodo_vela, 100, self.api.get_server_timestamp())
                direcao, contexto = self.diagnosticar_entrada(candles)
                
                if direcao: 
                    self.executar_operacao(direcao, contexto)
                time.sleep(2)
            except: 
                time.sleep(5)

    def iniciar(self):
        if not self.rodando:
            try:
                self.valor_base = float(self.valor.get())
            except:
                self.valor_base = 10.0
            self.valor_atual = self.valor_base
            self.ultima_direcao = None
            
            self.api = IQ_Option(self.email.get(), self.senha.get())
            if self.api.connect():
                self.api.change_balance(self.conta_var.get())
                self.saldo_inicial_sessao = self.api.get_balance()
                self.rodando = True
                
                self.btn_ligar.configure(state="disabled")
                self.btn_desligar.configure(state="normal")
                self.lbl_log.configure(text="Status: Robo12 Ligado / Monitorando...")
                threading.Thread(target=self.monitorar, daemon=True).start()

    def desligar(self):
        if self.rodando:
            self.rodando = False
            self.btn_ligar.configure(state="normal")
            self.btn_desligar.configure(state="disabled")
            self.lbl_log.configure(text="Status: Robo12 Desligado.")

if __name__ == "__main__":
    app = Robo12_Original()
    app.mainloop()
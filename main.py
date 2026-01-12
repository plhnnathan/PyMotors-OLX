import os
import threading
import webbrowser
from datetime import datetime
from tkinter import messagebox
import pandas as pd
import customtkinter as ctk

from src.scraper import OLXScraper
from src.analyser import AnalisadorVeiculo
from src.fipe import ConsultorFipe

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

ESTADOS_BR = [
    "Estado", "BR", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", 
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
]

MOTORES = [
    "Motor", "1.0", "1.4", "1.6", "1.8", "2.0", "2.4", "2.5", 
    "3.0", "Turbo", "V6", "V8", "Diesel", "Híbrido", "Elétrico"
]

class CardAnuncio(ctk.CTkFrame):
    """Componente visual que representa um único anúncio na lista."""
    def __init__(self, master, anuncio):
        bg_color = ("gray90", "gray30")
        border_color = "gray80"
        border_width = 1

        if "Excelente" in anuncio.score_preco:
            border_color = "#00AA66"
            border_width = 2
        elif "Cuidado" in anuncio.score_preco:
            border_color = "#FF5555"
            border_width = 2

        super().__init__(master, fg_color=bg_color, corner_radius=8, 
                         border_width=border_width, border_color=border_color)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        
        lbl_titulo = ctk.CTkLabel(self, text=anuncio.titulo, font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        lbl_titulo.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        
        if anuncio.tags:
            frame_tags = ctk.CTkFrame(self, fg_color="transparent")
            frame_tags.grid(row=1, column=0, padx=10, pady=(5, 0), sticky="w")
            for tag in anuncio.tags:
                cor_tag = "#3B8ED0"
                if "ALERTA" in tag: cor_tag = "#D03B3B"
                elif "Abaixo" in tag or "Baixa" in tag: cor_tag = "#2CC985"
                elif "Acima" in tag or "Alta" in tag: cor_tag = "#E5A000"
                
                lbl_tag = ctk.CTkLabel(frame_tags, text=f" {tag} ", fg_color=cor_tag, text_color="white", 
                                     font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6)
                lbl_tag.pack(side="left", padx=(0, 5))

        km_txt = f"{anuncio.km} km"
        if anuncio.km_anual > 0: km_txt += f" (~{anuncio.km_anual}/ano)"
            
        detalhes = f"{anuncio.ano} • {km_txt} • {anuncio.cambio}"
        lbl_detalhes = ctk.CTkLabel(self, text=detalhes, font=ctk.CTkFont(size=12), text_color=("gray40", "gray70"), anchor="w")
        lbl_detalhes.grid(row=2, column=0, padx=10, pady=(5, 5), sticky="ew")

        local = f"📍 {anuncio.cidade}-{anuncio.estado}"
        lbl_local = ctk.CTkLabel(self, text=local, font=ctk.CTkFont(size=11), text_color=("gray50", "gray60"), anchor="w")
        lbl_local.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        preco_fmt = f"R$ {anuncio.preco:,.0f}".replace(",", ".")
        lbl_preco = ctk.CTkLabel(self, text=preco_fmt, font=ctk.CTkFont(size=16, weight="bold"), text_color="#00AA66")
        lbl_preco.grid(row=0, column=1, rowspan=4, padx=15, pady=10)
        
        btn_link = ctk.CTkButton(self, text="Ver Oferta ↗", width=100, height=25, 
                                 fg_color="transparent", border_width=1, border_color=("gray60", "gray50"),
                                 text_color=("gray10", "gray90"), hover_color=("gray80", "gray40"),
                                 command=lambda: webbrowser.open(anuncio.link))
        btn_link.grid(row=4, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="e")

class PyMotorsApp(ctk.CTk):
    """Aplicação Principal do PyMotors."""
    def __init__(self):
        super().__init__()
        self.title("PyMotors - Consultor Automotivo Inteligente")
        self.geometry("1100x680")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._setup_sidebar()
        self._setup_main_area()

    def _setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        self.lbl_logo = ctk.CTkLabel(self.sidebar, text="🚗 PyMotors", font=ctk.CTkFont(size=26, weight="bold"))
        self.lbl_logo.grid(row=0, column=0, padx=20, pady=(30, 5))
        self.lbl_sub = ctk.CTkLabel(self.sidebar, text="AI Data Miner v4.0", text_color=("gray50", "gray70"))
        self.lbl_sub.grid(row=1, column=0, padx=20, pady=(0, 20))

        self.frame_fipe = ctk.CTkFrame(self.sidebar, fg_color=("gray90", "gray30"))
        self.frame_fipe.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        
        self.lbl_fipe_t = ctk.CTkLabel(self.frame_fipe, text="📊 FIPE Referência", font=ctk.CTkFont(weight="bold", size=12))
        self.lbl_fipe_t.pack(pady=(10,0))
        
        self.lbl_fipe_valor = ctk.CTkLabel(self.frame_fipe, text="--", font=ctk.CTkFont(weight="bold", size=18), text_color="#006CE5")
        self.lbl_fipe_valor.pack(pady=(5,10))
        
        self.lbl_fipe_status = ctk.CTkLabel(self.sidebar, text="Aguardando busca...", 
                                            font=ctk.CTkFont(size=11), text_color="gray60", wraplength=180)
        self.lbl_fipe_status.grid(row=3, column=0, padx=20, pady=0)

        self.switch_excel = ctk.CTkSwitch(self.sidebar, text="Salvar Excel", onvalue=True, offvalue=False)
        self.switch_excel.grid(row=5, column=0, padx=20, pady=10, sticky="s")

        self.opt_tema = ctk.CTkOptionMenu(self.sidebar, values=["Light", "Dark", "System"], command=ctk.set_appearance_mode)
        self.opt_tema.grid(row=6, column=0, padx=20, pady=20)

    def _setup_main_area(self):
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_area.grid_rowconfigure(3, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self.frame_top = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.frame_top.grid(row=0, column=0, sticky="ew")
        self.frame_top.grid_columnconfigure(0, weight=3)
        self.frame_top.grid_columnconfigure(1, weight=2)
        self.frame_top.grid_columnconfigure(2, weight=1)
        self.frame_top.grid_columnconfigure(3, weight=1)
        
        self.entry_busca = ctk.CTkEntry(self.frame_top, placeholder_text="🔍 Ex: Honda Civic", height=45)
        self.entry_busca.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.entry_cidade = ctk.CTkEntry(self.frame_top, placeholder_text="🏙️ Cidade", height=45)
        self.entry_cidade.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        self.opt_motor = ctk.CTkComboBox(self.frame_top, values=MOTORES, height=45)
        self.opt_motor.set("Motor")
        self.opt_motor.grid(row=0, column=2, sticky="ew", padx=(0, 10))

        self.opt_estado = ctk.CTkComboBox(self.frame_top, values=ESTADOS_BR, height=45, width=90)
        self.opt_estado.set("Estado")
        self.opt_estado.grid(row=0, column=3, sticky="ew", padx=(0, 10))

        self.btn_buscar = ctk.CTkButton(self.frame_top, text="ANALISAR", height=45, width=120, font=ctk.CTkFont(weight="bold"), 
                                        fg_color="#006CE5", hover_color="#0056b3", command=self.iniciar_thread)
        self.btn_buscar.grid(row=0, column=4)

        self.frame_filtros = ctk.CTkFrame(self.main_area)
        self.frame_filtros.grid(row=1, column=0, sticky="ew", pady=15)
        self.frame_filtros.grid_columnconfigure((0, 1, 2), weight=1)

        self.frame_p = ctk.CTkFrame(self.frame_filtros, fg_color="transparent")
        self.frame_p.grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkLabel(self.frame_p, text="💰 Preço (R$)").pack(anchor="w")
        self.entry_min_p = ctk.CTkEntry(self.frame_p, placeholder_text="Mín", width=100)
        self.entry_min_p.pack(side="left", padx=(0, 5))
        self.entry_max_p = ctk.CTkEntry(self.frame_p, placeholder_text="Máx", width=100)
        self.entry_max_p.pack(side="left")

        self.frame_a = ctk.CTkFrame(self.frame_filtros, fg_color="transparent")
        self.frame_a.grid(row=0, column=1, padx=10, pady=10)
        ctk.CTkLabel(self.frame_a, text="📅 Ano (Obrigatório p/ FIPE)").pack(anchor="w")
        self.entry_min_a = ctk.CTkEntry(self.frame_a, placeholder_text="De (Ex: 2018)", width=100)
        self.entry_min_a.pack(side="left", padx=(0, 5))
        self.entry_max_a = ctk.CTkEntry(self.frame_a, placeholder_text="Até", width=100)
        self.entry_max_a.pack(side="left")

        self.frame_s = ctk.CTkFrame(self.frame_filtros, fg_color="transparent")
        self.frame_s.grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        self.lbl_paginas = ctk.CTkLabel(self.frame_s, text="📄 Páginas: 2", anchor="w")
        self.lbl_paginas.pack(anchor="w")
        self.slider = ctk.CTkSlider(self.frame_s, from_=1, to=10, number_of_steps=9, command=self.update_slider)
        self.slider.set(2)
        self.slider.pack(fill="x", pady=5)

        self.lbl_status = ctk.CTkLabel(self.main_area, text="Preencha o Ano Inicial para ver a FIPE.", text_color="gray")
        self.lbl_status.grid(row=2, column=0, sticky="w", pady=(0, 5))

        self.scroll_resultados = ctk.CTkScrollableFrame(self.main_area, label_text="Oportunidades Encontradas")
        self.scroll_resultados.grid(row=3, column=0, sticky="nsew")
        self.scroll_resultados.grid_columnconfigure(0, weight=1)

    def update_slider(self, valor):
        self.lbl_paginas.configure(text=f"📄 Páginas: {int(valor)}")

    def iniciar_thread(self):
        carro = self.entry_busca.get()
        if not carro:
            messagebox.showwarning("Atenção", "Digite um modelo (Ex: Honda Civic)")
            return
            
        motor = self.opt_motor.get()
        cidade = self.entry_cidade.get()
        estado = self.opt_estado.get()
        if estado == "Estado": estado = "BR"
        
        try:
            val_min = self.entry_min_a.get()
            a_min = int(val_min) if val_min else None
        except ValueError:
            messagebox.showerror("Erro", "Ano deve ser numérico (Ex: 2020)")
            return

        termo_final = carro
        if motor != "Motor": termo_final += f" {motor}"
        if cidade: termo_final += f" {cidade}"

        self.btn_buscar.configure(state="disabled", text="TRABALHANDO...")
        self.lbl_fipe_valor.configure(text="...")
        self.lbl_fipe_status.configure(text="Consultando...")
        
        for widget in self.scroll_resultados.winfo_children():
            widget.destroy()

        threading.Thread(target=self.rodar_scraper, args=(termo_final, carro, estado, a_min)).start()

    def rodar_scraper(self, termo_completo, termo_fipe, estado, ano_min):
        try:
            fipe_valor = 0.0
            if ano_min:
                self.lbl_status.configure(text=f"🔎 Consultando FIPE para {termo_fipe} ({ano_min})...", text_color="#006CE5")
                consultor = ConsultorFipe()
                
                fipe_valor, fipe_msg = consultor.obter_preco_medio(termo_fipe, ano_min)
                
                if fipe_valor > 0:
                    self.lbl_fipe_valor.configure(text=f"R$ {fipe_valor/1000:.1f}k")
                    self.lbl_fipe_status.configure(text=fipe_msg, text_color="green")
                else:
                    self.lbl_fipe_valor.configure(text="Não achei")
                    self.lbl_fipe_status.configure(text=fipe_msg, text_color="#D03B3B")
            else:
                self.lbl_fipe_valor.configure(text="--")
                self.lbl_fipe_status.configure(text="Ano não informado.")

            self.lbl_status.configure(text=f"🔎 Buscando na OLX...", text_color="#006CE5")
            
            p_min = int(self.entry_min_p.get()) if self.entry_min_p.get() else None
            p_max = int(self.entry_max_p.get()) if self.entry_max_p.get() else None
            a_max = int(self.entry_max_a.get()) if self.entry_max_a.get() else None
            paginas = int(self.slider.get())

            scraper = OLXScraper()
            anuncios_brutos = scraper.buscar(termo_completo, paginas, p_min, p_max, ano_min, a_max, estado)

            if not anuncios_brutos:
                self.lbl_status.configure(text="❌ Nenhum veículo encontrado.", text_color="red")
                self.finalizar()
                return

            analisador = AnalisadorVeiculo(fipe_referencia=fipe_valor)
            anuncios_processados = []
            for a in anuncios_brutos:
                anuncios_processados.append(analisador.analisar(a))

            anuncios_processados.sort(key=lambda x: (x.score_preco != "Excelente", x.score_preco != "Bom"))

            if self.switch_excel.get():
                self.salvar_excel(anuncios_processados, termo_fipe, estado)
                self.lbl_status.configure(text=f"✅ Análise salva no Excel!", text_color="green")
            else:
                self.mostrar_na_tela(anuncios_processados)
                self.lbl_status.configure(text=f"✅ {len(anuncios_processados)} veículos analisados.", text_color="green")

        except Exception as e:
            self.lbl_status.configure(text=f"Erro: {str(e)}", text_color="red")
        
        finally:
            self.finalizar()

    def mostrar_na_tela(self, anuncios):
        for anuncio in anuncios:
            card = CardAnuncio(self.scroll_resultados, anuncio)
            card.pack(fill="x", pady=5, padx=5)

    def salvar_excel(self, anuncios, termo, uf):
        dados = []
        for a in anuncios:
            d = a.model_dump()
            d["tags"] = ", ".join(a.tags)
            dados.append(d)

        df = pd.DataFrame(dados)
        colunas = ["titulo", "preco", "score_preco", "tags", "ano", "km", "km_anual", "cidade", "estado", "link"]
        cols_finais = [c for c in colunas if c in df.columns]
        df = df[cols_finais]

        if not os.path.exists("data"): os.makedirs("data")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        nome = f"data/analise_{uf}_{termo.replace(' ', '_')}_{timestamp}.xlsx"

        with pd.ExcelWriter(nome, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Analise')
            workbook = writer.book
            worksheet = writer.sheets['Analise']
            fmt_moeda = workbook.add_format({'num_format': 'R$ #,##0'})
            fmt_centro = workbook.add_format({'align': 'center'})
            worksheet.set_column('A:A', 40)
            worksheet.set_column('B:B', 15, fmt_moeda)
            worksheet.set_column('J:J', 60)
        
        os.startfile(os.path.abspath("data"))

    def finalizar(self):
        self.btn_buscar.configure(state="normal", text="ANALISAR")

if __name__ == "__main__":
    app = PyMotorsApp()
    app.mainloop()
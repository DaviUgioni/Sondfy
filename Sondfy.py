import os
import threading

import customtkinter as ctk
import sounddevice as sd
import soundfile as sf
from mutagen import File
from PIL import Image, ImageDraw

# Diretório base do script (funciona independente de onde é executado)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")


# =========================
# Configurações
# =========================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

FUNDO = "#121212"
SIDEBAR = "#000000"
CARD = "#181818"
CARD_HOVER = "#282828"
TEXTO_SECUNDARIO = "#b3b3b3"
VERDE = "#1DB954"

PASTA_MUSICAS = "musicas"
EXTENSOES = (".mp3", ".flac", ".wav", ".ogg", ".m4a")


# =========================
# Ícones
# =========================

def criar_icone():
    tamanho = 96
    imagem = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    desenho = ImageDraw.Draw(imagem)
    return imagem, desenho


def icone_play(cor):
    imagem, desenho = criar_icone()

    desenho.polygon(
        [(28, 16), (28, 80), (72, 48)],
        fill=cor
    )

    return imagem.resize((24, 24), Image.LANCZOS)


def icone_pause(cor):
    imagem, desenho = criar_icone()

    desenho.rounded_rectangle(
        [24, 16, 40, 80],
        radius=8,
        fill=cor
    )

    desenho.rounded_rectangle(
        [56, 16, 72, 80],
        radius=8,
        fill=cor
    )

    return imagem.resize((24, 24), Image.LANCZOS)


def icone_proxima(cor):
    imagem, desenho = criar_icone()

    desenho.polygon(
        [(16, 16), (16, 80), (60, 48)],
        fill=cor
    )

    desenho.rounded_rectangle(
        [64, 16, 76, 80],
        radius=5,
        fill=cor
    )

    return imagem.resize((24, 24), Image.LANCZOS)


def icone_anterior(cor):
    imagem, desenho = criar_icone()

    desenho.polygon(
        [(80, 16), (80, 80), (36, 48)],
        fill=cor
    )

    desenho.rounded_rectangle(
        [20, 16, 32, 80],
        radius=5,
        fill=cor
    )

    return imagem.resize((24, 24), Image.LANCZOS)


def icone_loop(cor):
    imagem, desenho = criar_icone()

    desenho.arc(
        [16, 16, 80, 80],
        start=-30,
        end=200,
        fill=cor,
        width=9
    )

    desenho.polygon(
        [(76, 20), (88, 32), (68, 38)],
        fill=cor
    )

    desenho.polygon(
        [(20, 76), (8, 64), (28, 58)],
        fill=cor
    )

    return imagem.resize((24, 24), Image.LANCZOS)


def icone_volume(cor):
    imagem, desenho = criar_icone()

    desenho.polygon(
        [
            (16, 36),
            (36, 36),
            (56, 20),
            (56, 76),
            (36, 60),
            (16, 60)
        ],
        fill=cor
    )

    desenho.arc(
        [54, 24, 88, 72],
        start=-45,
        end=45,
        fill=cor,
        width=7
    )

    return imagem.resize((24, 24), Image.LANCZOS)


def imagem_icone(funcao, cor, tamanho=(20, 20)):
    imagem = funcao(cor)

    return ctk.CTkImage(
        light_image=imagem,
        dark_image=imagem,
        size=tamanho
    )


# =========================
# Funções auxiliares
# =========================

def formatar_tempo(segundos):
    segundos = int(segundos or 0)

    minutos = segundos // 60
    segundos = segundos % 60

    return f"{minutos}:{segundos:02d}"


def procurar_capa(pasta, nome):
    for extensao in (".jpg", ".jpeg", ".png", ".webp"):
        caminho = os.path.join(pasta, nome + extensao)

        if os.path.exists(caminho):
            return caminho

    return None


def carregar_capa(caminho, tamanho):
    if not caminho or not os.path.exists(caminho):
        return None

    try:
        imagem = Image.open(caminho).convert("RGB")

        return ctk.CTkImage(
            light_image=imagem,
            dark_image=imagem,
            size=tamanho
        )

    except Exception:
        return None


def carregar_musicas():
    os.makedirs(PASTA_MUSICAS, exist_ok=True)

    musicas = []

    arquivos = sorted(os.listdir(PASTA_MUSICAS))

    for arquivo in arquivos:
        if not arquivo.lower().endswith(EXTENSOES):
            continue

        caminho = os.path.join(PASTA_MUSICAS, arquivo)
        nome = os.path.splitext(arquivo)[0]

        duracao = 0

        try:
            audio = File(caminho)

            if audio and audio.info:
                duracao = audio.info.length

        except Exception:
            pass

        musicas.append({
            "titulo": nome,
            "artista": "Biblioteca local",
            "caminho": caminho,
            "capa": procurar_capa(PASTA_MUSICAS, nome),
            "duracao": formatar_tempo(duracao),
            "segundos": duracao
        })

    return musicas


# =========================
# Player de áudio
# =========================

class Player:

    def __init__(self, terminou=None, progresso=None):
        self.stream = None
        self.audio = None
        self.samplerate = None
        self.posicao = 0

        self.tocando = False
        self.volume = 0.15

        self.terminou = terminou
        self.progresso = progresso

        self.lock = threading.Lock()

    def carregar(self, arquivo):
        self.parar()

        self.audio, self.samplerate = sf.read(
            arquivo,
            always_2d=True
        )

        self.posicao = 0

    def callback(self, saida, frames, tempo, status):
        with self.lock:

            if self.audio is None:
                saida.fill(0)
                raise sd.CallbackStop()

            restante = len(self.audio) - self.posicao

            if restante <= 0:
                saida.fill(0)
                self.tocando = False
                raise sd.CallbackStop()

            quantidade = min(frames, restante)

            dados = self.audio[
                self.posicao:self.posicao + quantidade
            ]

            saida[:quantidade] = dados * self.volume

            if quantidade < frames:
                saida[quantidade:] = 0

            self.posicao += quantidade

        if self.progresso:
            atual = self.posicao / self.samplerate
            total = len(self.audio) / self.samplerate

            self.progresso(atual, total)

    def finalizou(self):
        self.tocando = False

        if self.audio is None:
            return

        chegou_no_final = self.posicao >= len(self.audio) - 1

        if chegou_no_final and self.terminou:
            self.terminou()

    def play(self):
        if self.audio is None:
            return

        if self.stream is None or not self.stream.active:
            canais = self.audio.shape[1]

            self.stream = sd.OutputStream(
                samplerate=self.samplerate,
                channels=canais,
                callback=self.callback,
                finished_callback=self.finalizou
            )

            self.stream.start()

        self.tocando = True

    def pausar(self):
        if self.stream and self.stream.active:
            self.stream.stop()

        self.tocando = False

    def parar(self):
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass

        self.stream = None
        self.tocando = False
        self.posicao = 0

    def mudar_posicao(self, porcentagem):
        if self.audio is None:
            return

        with self.lock:
            self.posicao = int(
                porcentagem * len(self.audio)
            )

    def mudar_volume(self, valor):
        valor = max(0, min(1, valor))

        # Deixa o volume mais agradável em níveis baixos.
        self.volume = (valor ** 2) * 0.6


# =========================
# Aplicação
# =========================

class Sondfy(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Sondfy")
        self.geometry("1100x650")
        self.configure(fg_color=FUNDO)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.musicas = carregar_musicas()
        self.musica_atual = None

        self.loop = False
        self.deve_tocar = False
        self.arrastando = False

        self.ultima_posicao = 0
        self.ultima_duracao = 0

        self.player = Player(
            terminou=self.musica_terminou,
            progresso=self.atualizar_progresso
        )

        self.criar_sidebar()
        self.criar_conteudo()
        self.criar_player()

        self.atualizar_tela()

    # =========================
    # Sidebar
    # =========================

    def criar_sidebar(self):
        sidebar = ctk.CTkFrame(
            self,
            width=220,
            fg_color=SIDEBAR,
            corner_radius=0
        )

        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        titulo = ctk.CTkLabel(
            sidebar,
            text="🎵 Sondfy",
            font=ctk.CTkFont(size=22, weight="bold")
        )

        titulo.pack(
            anchor="w",
            padx=20,
            pady=(24, 30)
        )

        adicionar = ctk.CTkButton(
            sidebar,
            text="+  Adicionar Música",
            fg_color=VERDE,
            hover_color="#1ed760",
            text_color="black",
            height=36,
            corner_radius=20,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.mostrar_download
        )

        adicionar.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        self.download_frame = ctk.CTkFrame(
            sidebar,
            fg_color="transparent"
        )

        self.link = ctk.CTkEntry(
            self.download_frame,
            width=180,
            placeholder_text="Cole o link do YouTube..."
        )

        self.link.pack(pady=(0, 6))

        self.botao_download = ctk.CTkButton(
            self.download_frame,
            text="Baixar",
            fg_color=CARD_HOVER,
            hover_color="#333333",
            command=self.baixar_musica
        )

        self.botao_download.pack()

        self.status_download = ctk.CTkLabel(
            sidebar,
            text="",
            text_color=TEXTO_SECUNDARIO,
            wraplength=180,
            font=ctk.CTkFont(size=11)
        )

        self.status_download.pack(
            padx=20,
            pady=(4, 20)
        )

        biblioteca = ctk.CTkLabel(
            sidebar,
            text="BIBLIOTECA",
            text_color=TEXTO_SECUNDARIO,
            font=ctk.CTkFont(size=11, weight="bold")
        )

        biblioteca.pack(
            anchor="w",
            padx=20,
            pady=(10, 8)
        )

        todas = ctk.CTkButton(
            sidebar,
            text="🎧  Todas as Músicas",
            fg_color="transparent",
            hover_color=CARD_HOVER,
            anchor="w",
            command=lambda: None
        )

        todas.pack(
            fill="x",
            padx=10
        )

    def mostrar_download(self):
        if self.download_frame.winfo_ismapped():
            self.download_frame.pack_forget()
        else:
            self.download_frame.pack(
                padx=20,
                pady=(0, 10)
            )

    # =========================
    # Download
    # =========================

    def baixar_musica(self):
        url = self.link.get().strip()

        if not url:
            return

        self.botao_download.configure(
            state="disabled",
            text="Baixando..."
        )

        self.status_download.configure(
            text="Baixando áudio, aguarde..."
        )

        thread = threading.Thread(
            target=self.download_thread,
            args=(url,),
            daemon=True
        )

        thread.start()

    def download_thread(self, url):
        try:
            import yt_dlp

            if not os.path.exists(COOKIES_FILE):
                self.after(
                    0,
                    self.download_erro,
                    "Arquivo cookies.txt não encontrado."
                )
                return

            os.makedirs(PASTA_MUSICAS, exist_ok=True)

            opcoes = {
                "format": "bestaudio/best",
                "outtmpl": f"{PASTA_MUSICAS}/%(title)s.%(ext)s",

                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "flac"
                    }
                ],

                "writethumbnail": True,
                "cookiefile": COOKIES_FILE,

                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "web"]
                    }
                },

                "quiet": True,
                "no_warnings": True
            }

            with yt_dlp.YoutubeDL(opcoes) as ydl:
                info = ydl.extract_info(
                    url,
                    download=True
                )

            titulo = info.get("title", "Música")

            self.after(
                0,
                self.download_concluido,
                titulo
            )

        except Exception as erro:
            self.after(
                0,
                self.download_erro,
                str(erro)
            )

    def download_concluido(self, titulo):
        self.botao_download.configure(
            state="normal",
            text="Baixar"
        )

        self.status_download.configure(
            text=f"✅ Baixado: {titulo}"
        )

        self.link.delete(0, "end")

        self.recarregar_musicas()

    def download_erro(self, erro):
        self.botao_download.configure(
            state="normal",
            text="Baixar"
        )

        mensagem = erro[:150]

        if len(erro) > 150:
            mensagem += "..."

        self.status_download.configure(
            text=f"❌ Falhou: {mensagem}"
        )

        print("Erro no download:", erro)

    # =========================
    # Lista de músicas
    # =========================

    def criar_conteudo(self):
        container = ctk.CTkFrame(
            self,
            fg_color=FUNDO,
            corner_radius=0
        )

        container.grid(
            row=0,
            column=1,
            sticky="nsew",
            pady=(0, 90)
        )

        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        titulo = ctk.CTkLabel(
            container,
            text="Todas as Músicas",
            font=ctk.CTkFont(size=26, weight="bold")
        )

        titulo.grid(
            row=0,
            column=0,
            sticky="w",
            padx=30,
            pady=(24, 16)
        )

        self.lista = ctk.CTkScrollableFrame(
            container,
            fg_color="transparent"
        )

        self.lista.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(0, 10)
        )

        self.lista.grid_columnconfigure(0, weight=1)

        self.mostrar_musicas()

    def mostrar_musicas(self):
        for widget in self.lista.winfo_children():
            widget.destroy()

        if not self.musicas:
            vazio = ctk.CTkLabel(
                self.lista,
                text="Nenhuma música ainda. Adicione uma pelo link do YouTube!",
                text_color=TEXTO_SECUNDARIO
            )

            vazio.pack(pady=30)
            return

        for indice, musica in enumerate(self.musicas):
            self.criar_card(
                musica,
                indice
            )

    def criar_card(self, musica, indice):
        card = ctk.CTkFrame(
            self.lista,
            fg_color=CARD,
            corner_radius=8,
            height=64
        )

        card.pack(
            fill="x",
            pady=4,
            padx=4
        )

        card.pack_propagate(False)
        card.grid_columnconfigure(1, weight=1)

        capa_imagem = carregar_capa(
            musica["capa"],
            (44, 44)
        )

        capa = ctk.CTkLabel(
            card,
            text="" if capa_imagem else "🎵",
            image=capa_imagem,
            width=44,
            height=44,
            fg_color=CARD_HOVER,
            corner_radius=6,
            font=ctk.CTkFont(size=18)
        )

        capa.grid(
            row=0,
            column=0,
            padx=(12, 12),
            pady=10
        )

        informacoes = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        informacoes.grid(
            row=0,
            column=1,
            sticky="w",
            pady=10
        )

        titulo = ctk.CTkLabel(
            informacoes,
            text=musica["titulo"],
            font=ctk.CTkFont(size=14, weight="bold")
        )

        titulo.pack(anchor="w")

        artista = ctk.CTkLabel(
            informacoes,
            text=musica["artista"],
            text_color=TEXTO_SECUNDARIO,
            font=ctk.CTkFont(size=12)
        )

        artista.pack(anchor="w")

        duracao = ctk.CTkLabel(
            card,
            text=musica["duracao"],
            text_color=TEXTO_SECUNDARIO,
            font=ctk.CTkFont(size=12)
        )

        duracao.grid(
            row=0,
            column=2,
            padx=20
        )

        widgets = (
            card,
            capa,
            informacoes,
            titulo,
            artista
        )

        for widget in widgets:
            widget.bind(
                "<Button-1>",
                lambda event, i=indice: self.tocar(i)
            )

    def recarregar_musicas(self):
        self.musicas = carregar_musicas()
        self.mostrar_musicas()

    # =========================
    # Música atual
    # =========================

    def tocar(self, indice):
        if indice < 0 or indice >= len(self.musicas):
            return

        musica = self.musicas[indice]

        self.musica_atual = indice
        self.deve_tocar = True

        self.player.carregar(
            musica["caminho"]
        )

        self.player.play()

        self.nome_musica.configure(
            text=musica["titulo"]
        )

        self.nome_artista.configure(
            text=musica["artista"]
        )

        self.botao_play.configure(
            image=self.icone_pause
        )

        capa = carregar_capa(
            musica["capa"],
            (48, 48)
        )

        if capa:
            self.capa_atual.configure(
                image=capa,
                text=""
            )
        else:
            self.capa_atual.configure(
                image=None,
                text="🎵"
            )

    def musica_terminou(self):
        if self.loop:
            self.after(
                0,
                self.repetir
            )
        else:
            self.after(
                0,
                self.proxima
            )

    def repetir(self):
        if self.musica_atual is not None:
            self.tocar(
                self.musica_atual
            )

    # =========================
    # Player inferior
    # =========================

    def criar_player(self):
        barra = ctk.CTkFrame(
            self,
            height=90,
            fg_color=SIDEBAR,
            corner_radius=0
        )

        barra.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew"
        )

        barra.grid_propagate(False)

        barra.grid_columnconfigure(0, weight=1)
        barra.grid_columnconfigure(1, weight=2)
        barra.grid_columnconfigure(2, weight=1)

        # Informações da música

        esquerda = ctk.CTkFrame(
            barra,
            fg_color="transparent"
        )

        esquerda.grid(
            row=0,
            column=0,
            sticky="w",
            padx=16
        )

        self.capa_atual = ctk.CTkLabel(
            esquerda,
            text="🎵",
            width=48,
            height=48,
            fg_color=CARD_HOVER,
            corner_radius=6,
            font=ctk.CTkFont(size=18)
        )

        self.capa_atual.pack(
            side="left",
            padx=(0, 10)
        )

        info = ctk.CTkFrame(
            esquerda,
            fg_color="transparent"
        )

        info.pack(side="left")

        self.nome_musica = ctk.CTkLabel(
            info,
            text="Nenhuma música tocando",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            )
        )

        self.nome_musica.pack(anchor="w")

        self.nome_artista = ctk.CTkLabel(
            info,
            text="—",
            text_color=TEXTO_SECUNDARIO,
            font=ctk.CTkFont(size=11)
        )

        self.nome_artista.pack(anchor="w")

        # Controles

        centro = ctk.CTkFrame(
            barra,
            fg_color="transparent"
        )

        centro.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=20
        )

        centro.grid_columnconfigure(0, weight=1)

        botoes = ctk.CTkFrame(
            centro,
            fg_color="transparent"
        )

        botoes.pack(
            pady=(14, 6)
        )

        self.icone_play = imagem_icone(
            icone_play,
            "black",
            (18, 18)
        )

        self.icone_pause = imagem_icone(
            icone_pause,
            "black",
            (18, 18)
        )

        icone_ant = imagem_icone(
            icone_anterior,
            "white"
        )

        icone_prox = imagem_icone(
            icone_proxima,
            "white"
        )

        self.icone_loop = imagem_icone(
            icone_loop,
            TEXTO_SECUNDARIO
        )

        self.icone_loop_ativo = imagem_icone(
            icone_loop,
            VERDE
        )

        self.icone_volume = imagem_icone(
            icone_volume,
            TEXTO_SECUNDARIO
        )

        anterior = ctk.CTkButton(
            botoes,
            text="",
            image=icone_ant,
            width=36,
            height=36,
            fg_color="transparent",
            hover_color=CARD_HOVER,
            command=self.anterior
        )

        anterior.pack(
            side="left",
            padx=6
        )

        self.botao_play = ctk.CTkButton(
            botoes,
            text="",
            image=self.icone_play,
            width=40,
            height=40,
            fg_color="white",
            hover_color="#e0e0e0",
            corner_radius=20,
            command=self.play_pause
        )

        self.botao_play.pack(
            side="left",
            padx=6
        )

        proxima = ctk.CTkButton(
            botoes,
            text="",
            image=icone_prox,
            width=36,
            height=36,
            fg_color="transparent",
            hover_color=CARD_HOVER,
            command=self.proxima
        )

        proxima.pack(
            side="left",
            padx=6
        )

        self.botao_loop = ctk.CTkButton(
            botoes,
            text="",
            image=self.icone_loop,
            width=36,
            height=36,
            fg_color="transparent",
            hover_color=CARD_HOVER,
            command=self.alternar_loop
        )

        self.botao_loop.pack(
            side="left",
            padx=6
        )

        # Barra de progresso

        progresso = ctk.CTkFrame(
            centro,
            fg_color="transparent"
        )

        progresso.pack(
            fill="x",
            padx=10
        )

        progresso.grid_columnconfigure(
            1,
            weight=1
        )

        self.tempo_atual = ctk.CTkLabel(
            progresso,
            text="0:00",
            width=35,
            text_color=TEXTO_SECUNDARIO,
            font=ctk.CTkFont(size=10)
        )

        self.tempo_atual.grid(
            row=0,
            column=0
        )

        self.barra = ctk.CTkSlider(
            progresso,
            from_=0,
            to=1000,
            height=8,
            progress_color=VERDE,
            button_color="white",
            button_hover_color="white",
            command=self.arrastar_progresso
        )

        self.barra.set(0)

        self.barra.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=6
        )

        self.barra.bind(
            "<ButtonPress-1>",
            lambda event: self.iniciar_arraste()
        )

        self.barra.bind(
            "<ButtonRelease-1>",
            lambda event: self.finalizar_arraste()
        )

        self.tempo_total = ctk.CTkLabel(
            progresso,
            text="0:00",
            width=35,
            text_color=TEXTO_SECUNDARIO,
            font=ctk.CTkFont(size=10)
        )

        self.tempo_total.grid(
            row=0,
            column=2
        )

        # Volume

        direita = ctk.CTkFrame(
            barra,
            fg_color="transparent"
        )

        direita.grid(
            row=0,
            column=2,
            sticky="e",
            padx=20
        )

        volume_icon = ctk.CTkLabel(
            direita,
            text="",
            image=self.icone_volume
        )

        volume_icon.pack(
            side="left",
            padx=(0, 8)
        )

        self.volume = ctk.CTkSlider(
            direita,
            from_=0,
            to=100,
            width=100,
            height=8,
            progress_color=VERDE,
            button_color="white",
            button_hover_color="white",
            command=self.alterar_volume
        )

        self.volume.set(50)

        self.volume.pack(side="left")

    # =========================
    # Controles
    # =========================

    def play_pause(self):
        if self.musica_atual is None:

            if self.musicas:
                self.tocar(0)

            return

        if self.player.tocando:
            self.player.pausar()
            self.deve_tocar = False

            self.botao_play.configure(
                image=self.icone_play
            )

        else:
            self.player.play()
            self.deve_tocar = True

            self.botao_play.configure(
                image=self.icone_pause
            )

    def anterior(self):
        if self.musica_atual is None or not self.musicas:
            return

        novo_indice = (
            self.musica_atual - 1
        ) % len(self.musicas)

        self.tocar(novo_indice)

    def proxima(self):
        if self.musica_atual is None or not self.musicas:
            return

        novo_indice = (
            self.musica_atual + 1
        ) % len(self.musicas)

        self.tocar(novo_indice)

    def alternar_loop(self):
        self.loop = not self.loop

        icone = (
            self.icone_loop_ativo
            if self.loop
            else self.icone_loop
        )

        self.botao_loop.configure(
            image=icone
        )

    def alterar_volume(self, valor):
        self.player.mudar_volume(
            float(valor) / 100
        )

    # =========================
    # Progresso
    # =========================

    def iniciar_arraste(self):
        self.arrastando = True

    def finalizar_arraste(self):
        porcentagem = self.barra.get() / 1000

        self.player.mudar_posicao(
            porcentagem
        )

        self.arrastando = False

    def arrastar_progresso(self, valor):
        if not self.arrastando:
            return

        if self.player.audio is None:
            return

        duracao = (
            len(self.player.audio)
            / self.player.samplerate
        )

        tempo = (
            float(valor) / 1000
        ) * duracao

        self.tempo_atual.configure(
            text=formatar_tempo(tempo)
        )

    def atualizar_progresso(self, atual, total):
        # Essa função pode ser chamada pela thread do áudio.
        # Por isso, a interface só é atualizada no loop principal.
        self.ultima_posicao = atual
        self.ultima_duracao = total

    # =========================
    # Atualização da interface
    # =========================

    def atualizar_tela(self):

        # Se o sistema parar o stream por algum motivo,
        # tenta continuar a música enquanto ela ainda não terminou.
        if (
            self.player.audio is not None
            and not self.player.tocando
            and self.musica_atual is not None
            and self.deve_tocar
            and self.player.posicao < len(self.player.audio) - 1
        ):
            self.player.play()

        if (
            not self.arrastando
            and self.player.audio is not None
        ):
            duracao = (
                len(self.player.audio)
                / self.player.samplerate
            )

            posicao = self.ultima_posicao

            if duracao > 0:
                porcentagem = min(
                    posicao / duracao,
                    1
                )

                self.barra.set(
                    porcentagem * 1000
                )

            self.tempo_atual.configure(
                text=formatar_tempo(posicao)
            )

            self.tempo_total.configure(
                text=formatar_tempo(duracao)
            )

        self.after(
            300,
            self.atualizar_tela
        )


# =========================
# Inicialização
# =========================

def main():
    app = Sondfy()
    app.mainloop()


if __name__ == "__main__":
    main()
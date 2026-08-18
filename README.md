# Sondfy 

Um player de música local moderno e minimalista, inspirado no Spotify, desenvolvido em Python com interface gráfica usando CustomTkinter.

##  Funcionalidades

- **Player de áudio local** — Reproduz MP3, FLAC, WAV, OGG, M4A
- **Download do YouTube** — Baixe músicas diretamente pelo link (usa yt-dlp)
- **Interface estilo Spotify** — Tema escuro, sidebar, cards de música, barra de progresso
- **Controles completos** — Play/pause, anterior/próxima, loop, volume, seek na barra
- **Capas de álbum** — Detecção automática de imagens na pasta da música
- **Metadados** — Leitura de duração, título via mutagen
- **Executável standalone** — Gera .exe com PyInstaller (sem precisar instalar Python)

##  Capturas de tela

*(Adicione screenshots aqui se quiser)*

##  Instalação

### Pré-requisitos

- Python 3.10+
- FFmpeg instalado e no PATH (necessário para conversão de áudio do yt-dlp)
- Cookies do YouTube (opcional, para downloads de conteúdo restrito por idade/região)

### Instalação via pip

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/Sondfy.git
cd Sondfy

# Crie um ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r requirements.txt
```

### Executar

```bash
python Sondfy.py
```

##  Gerar executável (.exe)

```bash
# Instale o PyInstaller se não tiver
pip install pyinstaller

# Gere o executável
pyinstaller Sondfy.spec
```

O executável estará em `dist/Sondfy.exe`.

##  Configuração

### Cookies do YouTube (para downloads)

Crie um arquivo `cookies.txt` na raiz do projeto com os cookies exportados do seu navegador (formato Netscape). Isso permite baixar vídeos com restrição de idade ou região.

### Pasta de músicas

Por padrão, as músicas ficam na pasta `musicas/` na raiz do projeto. Você pode alterar a constante `PASTA_MUSICAS` no código.

##  Dependências principais

| Pacote | Função |
|--------|--------|
| `customtkinter` | Interface gráfica moderna |
| `sounddevice` | Reprodução de áudio de baixa latência |
| `soundfile` | Leitura de arquivos de áudio |
| `mutagen` | Leitura de metadados (duração, tags) |
| `Pillow` | Manipulação de imagens (capas, ícones) |
| `yt-dlp` | Download de áudio do YouTube |

##  Estrutura do projeto

```
Sondfy/
├── Sondfy.py          # Código principal da aplicação
├── Sondfy.spec        # Configuração do PyInstaller
├── requirements.txt   # Dependências Python
├── cookies.txt        # Cookies do YouTube (não versionado)
├── musicas/           # Pasta de músicas baixadas (não versionada)
├── build/             # Arquivos temporários do PyInstaller
├── dist/              # Executável gerado
├── .gitignore
├── LICENSE
└── README.md
```

##  Como usar

1. Abra o Sondfy
2. Clique em **+ Adicionar Música** na sidebar
3. Cole um link do YouTube e clique em **Baixar**
4. A música aparecerá na lista — clique para tocar
5. Use os controles na barra inferior: play/pause, anterior/próxima, loop, volume, seek

##  Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir funcionalidades
- Enviar pull requests

##  Licença

Este projeto está licenciado sob a **GPL-3.0** — veja o arquivo [LICENSE](LICENSE) para detalhes.

##  Agradecimentos

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — Interface moderna
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — Download robusto do YouTube
- [sounddevice](https://python-sounddevice.readthedocs.io/) — Áudio de baixa latência
- [mutagen](https://mutagen.readthedocs.io/) — Metadados de áudio
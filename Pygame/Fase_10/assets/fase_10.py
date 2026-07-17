"""
Escape Room - Fase 10 (Era da Internet e da Mobilidade - anos 1990)
Última fase do jogo. O personagem chega à era da internet: nasce a World
Wide Web, explodem os smartphones e a inteligência artificial. Para abrir
o portal e voltar ao presente, o jogador precisa CONECTAR-SE À REDE CERTA,
montando a "torre de protocolos" da internet na ordem correta
(Cabo/Wi-Fi -> TCP/IP -> HTTP -> WWW). O chatbot da fase é o Tim
Berners-Lee, criador da Web.

Este código foi feito no mesmo esquema da Fase 1 (do ábaco), reaproveitando
a mesma pasta 'assets', o mesmo personagem, a mesma fonte e os mesmos sons.

PONTO DE ENTRADA PARA O MENU GERAL (Pygame/menu/jogo.py): a classe `Jogo`
no final deste arquivo -- mesmo padrão de Fase_9/Fase_4/Fase_5/Fase_1/
Fase_6. Todo o resto do arquivo (janela, cenário, personagem, chatbot,
puzzles) continua rodando dentro da função `_executar_fase10`, chamada
por `Jogo.executar()`.
"""

# ==============================================================================
# === CONFIGURAÇÃO INICIAL (imports, janela, caminhos de assets) ===
# ==============================================================================
# Importa as bibliotecas usadas no jogo: pygame (para criar o jogo), random
# (para embaralhar as peças do puzzle), sys (para encerrar o programa
# corretamente), os (para montar os caminhos dos arquivos), threading (para
# rodar o chatbot sem travar a janela) e ollama (para conversar com o modelo
# de IA que roda localmente no computador).
import math
import os
import pygame
import random
import sys
import threading

# O chatbot (Tim Berners-Lee) depende do pacote `ollama` e de um servidor
# Ollama rodando localmente -- nenhum dos dois é garantido na máquina de
# quem só quer jogar. Se o import falhar (pacote não instalado), o resto da
# fase (personagem, puzzle, porta) tem que continuar funcionando normalmente
# e só o chat fica indisponível.
try:
    import ollama
    OLLAMA_DISPONIVEL = True
except ImportError:
    ollama = None
    OLLAMA_DISPONIVEL = False

pygame.init()

# ---------------------------------------------------------------------------
# Monta caminhos de assets a partir da pasta onde este arquivo .py está,
# em vez de depender da pasta de onde o jogo é executado. Sem isso, rodar o
# jogo a partir de outra pasta faz o Pygame não achar as imagens/fontes,
# porque os caminhos "assets/..." seriam relativos à pasta atual do terminal,
# não à pasta do projeto.
# ---------------------------------------------------------------------------
PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))


def caminho_asset(nome_relativo):
    """Monta o caminho absoluto de um asset a partir da pasta onde este
    arquivo .py está salvo."""
    return os.path.join(PASTA_DO_SCRIPT, nome_relativo)


# ---------------------------------------------------------------------------
# Janela do jogo (mesmo tamanho da Fase 1: 960x600) -- só o TAMANHO é uma
# constante de módulo; a janela DE VERDADE só é criada dentro de
# _executar_fase10 (chamada por Jogo.executar()), pra cada visita à fase
# ganhar uma janela/estado novos.
# ---------------------------------------------------------------------------
LARGURA_JANELA = 960
ALTURA_JANELA = 600

# ---------------------------------------------------------------------------
# ASSETS: dicionário central com TODOS os caminhos de imagem/fonte/som. Só
# guarda CAMINHOS (texto), então fica bem aqui no nível do módulo sem
# depender da janela já existir -- o carregamento de verdade acontece
# dentro de _executar_fase10.
#
# >>> IMPORTANTE (renomear os arquivos exatamente assim): <<<
# Dentro de assets/imagens/cenarios/fase_fim/ devem existir:
#   - cenario_porta_fechada.png  (cenário com o portal FECHADO)
#   - cenario_porta_aberta.png   (cenário com o portal ABERTO)
#   - tim.png                    (retrato do Tim Berners-Lee, quadrado)
# A fonte e os sons são REAPROVEITADOS da Fase 1 (mesma pasta assets):
#   - assets/fontes/PressStart2P-Regular.ttf
#   - assets/sons/musica_fundo.ogg
#   - assets/sons/som_clique.wav
# O personagem também é reaproveitado (pastas personagem/ e personagem2/).
# ---------------------------------------------------------------------------
ASSETS = {
    "fundo_porta_fechada": caminho_asset("imagens/cenarios/fase_fim/cenario_porta_fechada.png"),
    "fundo_porta_aberta": caminho_asset("imagens/cenarios/fase_fim/cenario_porta_aberta.png"),
    "tim_retrato": caminho_asset("imagens/cenarios/fase_fim/tim.png"),
    "fonte_pixel": caminho_asset("fontes/PressStart2P-Regular.ttf"),
    "pasta_personagem_1": caminho_asset("imagens/personagem/"),
    "pasta_personagem_2": caminho_asset("imagens/personagem2/"),
    "musica_fundo": caminho_asset("sons/musica_fundo.ogg"),
    "som_clique": caminho_asset("sons/som_clique.wav"),
}

PASTAS_PERSONAGEM = [ASSETS["pasta_personagem_1"], ASSETS["pasta_personagem_2"]]

# ==============================================================================
# === CARREGADORES SEGUROS (não travam o jogo se faltar algum arquivo) ===
# ==============================================================================
# Como já aconteceu de faltar/estar com nome errado algum arquivo, estas
# funções tentam carregar o asset e, se não conseguirem, devolvem um
# "placeholder" (um retângulo colorido com o nome do arquivo escrito) em
# vez de fechar o jogo com erro. Assim dá pra rodar o jogo mesmo antes de
# todos os arquivos estarem com o nome certinho, e enxergar na tela o que
# está faltando. Ficam no nível do módulo (não dependem de personagem/
# estado de uma visita específica à fase).
# ---------------------------------------------------------------------------
_fonte_aviso = pygame.font.SysFont("consolas", 16)
# Fonte menor pro aviso de "FALTA" dentro da caixinha do personagem (120px de
# largura -- estreita demais pra usar _fonte_aviso sem estourar).
_fonte_aviso_personagem = pygame.font.SysFont("consolas", 11)


def carregar_imagem(caminho, tamanho=None, com_alpha=True):
    """Carrega uma imagem já redimensionada. Se falhar, devolve um retângulo
    de aviso com o nome do arquivo que está faltando."""
    try:
        imagem = pygame.image.load(caminho)
        imagem = imagem.convert_alpha() if com_alpha else imagem.convert()
        if tamanho is not None:
            imagem = pygame.transform.scale(imagem, tamanho)
        return imagem
    except Exception:
        largura, altura = tamanho if tamanho else (200, 200)
        aviso = pygame.Surface((largura, altura), pygame.SRCALPHA)
        aviso.fill((70, 40, 90))
        pygame.draw.rect(aviso, (200, 80, 120), aviso.get_rect(), width=3)
        nome = os.path.basename(caminho)
        texto = _fonte_aviso.render("FALTA: " + nome, True, (255, 220, 220))
        aviso.blit(texto, texto.get_rect(center=(largura // 2, altura // 2)))
        return aviso


def carregar_fonte(caminho, tamanho):
    """Carrega a fonte pixelada; se faltar, usa uma fonte comum do sistema."""
    try:
        return pygame.font.Font(caminho, tamanho)
    except Exception:
        return pygame.font.SysFont("consolas", tamanho + 4)


class _SomVazio:
    """Objeto de som "vazio": tem o método play() mas não faz nada. Usado
    quando o arquivo de som não é encontrado, pra não travar o jogo."""

    def play(self):
        pass


def carregar_som(caminho):
    """Tenta carregar um som; se o nome/extensão estiver diferente, tenta
    .ogg e .wav antes de desistir e devolver um som silencioso."""
    tentativas = [caminho, caminho.replace(".wav", ".ogg"), caminho.replace(".ogg", ".wav")]
    for tentativa in tentativas:
        try:
            return pygame.mixer.Sound(tentativa)
        except Exception:
            continue
    return _SomVazio()


# ---------------------------------------------------------------------------
# Progresso (estrelas + tempo) -- mesmo arquivo/formato compartilhado que
# Fase_2/Fase_9/Fase_4/Fase_5/Fase_1/Fase_6 já usam: {"estrelas": 1-3,
# "completo": true, "tempo": "MM:SS"}. Esta fase NÃO tem cronômetro/limite
# de tempo -- por isso sempre dá 1 estrela ao concluir (ver
# _executar_fase10, no momento da vitória), em vez de calcular a partir de
# tempo restante como as fases com timer fazem. "tempo" ainda é gravado, só
# que é quanto tempo REAL o jogador levou desde que entrou na fase até
# vencer (não tem relação com estrelas aqui).
# ---------------------------------------------------------------------------
_PYGAME_DIR = os.path.dirname(os.path.dirname(PASTA_DO_SCRIPT))
PROGRESSO_PATH = os.path.join(_PYGAME_DIR, "progresso.json")
PROGRESSO_CHAVE_FASE = "fase_10"


def _carregar_progresso():
    """Lê Pygame/progresso.json inteiro (de todas as fases). Devolve um
    dicionário vazio se o arquivo ainda não existir ou vier corrompido --
    assim a gente nunca trava tentando salvar só porque o arquivo está
    ausente ou malformado."""
    import json
    if not os.path.exists(PROGRESSO_PATH):
        return {}
    try:
        with open(PROGRESSO_PATH, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (json.JSONDecodeError, OSError):
        return {}


def _salvar_progresso(estrelas, tempo_formatado):
    """Grava `estrelas` e `tempo_formatado` ("MM:SS", quanto tempo real o
    jogador levou) na chave PROGRESSO_CHAVE_FASE do progresso.json
    compartilhado, preservando as chaves de outras fases que já estiverem
    lá. Nunca sobrescreve um resultado MELHOR já salvo (mesma regra usada
    nas outras fases) -- como esta fase só dá 1 estrela, na prática isso só
    evita sobrescrever o "tempo" de um recorde antigo com um pior."""
    import json
    progresso = _carregar_progresso()
    anterior = progresso.get(PROGRESSO_CHAVE_FASE)
    if anterior is not None and anterior.get("estrelas", 0) >= estrelas:
        if anterior.get("tempo") is not None:
            return
        novo_registro = {**anterior, "estrelas": anterior.get("estrelas", estrelas), "completo": True, "tempo": tempo_formatado}
    else:
        novo_registro = {"estrelas": estrelas, "completo": True, "tempo": tempo_formatado}

    progresso[PROGRESSO_CHAVE_FASE] = novo_registro
    with open(PROGRESSO_PATH, "w", encoding="utf-8") as arquivo:
        json.dump(progresso, arquivo, indent=2, ensure_ascii=False)


def _formatar_tempo(segundos):
    """Formata `segundos` (int/float) como "MM:SS"."""
    total = max(0, int(segundos))
    return f"{total // 60:02d}:{total % 60:02d}"


class Jogo:
    """Ponto de entrada desta fase para o menu geral (Pygame/menu/jogo.py)
    -- mesmo padrão das demais fases: aceita character_image/character_name/
    genero vindos do menu (personagem escolhido lá continua o mesmo aqui).
    `executar()` só devolve "vitoria" quando o jogador conclui a fase (monta
    a torre de protocolos e confirma com Esc na tela final "Você voltou ao
    presente!"); em qualquer outro jeito de sair (Esc antes disso, ou o
    painel de configurações), devolve None. Fechar a JANELA (evento QUIT)
    continua encerrando o programa INTEIRO, não só a fase -- mesmo
    comportamento de sempre desta fase, igual ao que já acontece em
    Pygame/Fase_4/fase4_final.py e Pygame/Fase_5/fase_5_atualizada.py."""

    def __init__(self, character_image=None, character_name="Jogador", genero="m"):
        self.character_image = character_image
        self.character_name = character_name or "Jogador"
        self.genero = genero if genero in ("m", "f") else "m"

    def executar(self):
        return _executar_fase10(self.character_name, self.genero)


def _executar_fase10(character_name, genero):
    """Contém a fase inteira (janela, cenário, personagem, chatbot, menu de
    configurações e os dois puzzles) -- é o antigo corpo deste arquivo (que
    antes rodava direto no import, sem função nenhuma), só que agora dentro
    de uma função pra poder ser chamada de novo a cada vez que o jogador
    entra na fase pelo mapa, sempre com estado limpo (nenhuma variável
    daqui é compartilhada entre uma chamada e outra)."""
    tela = pygame.display.set_mode((LARGURA_JANELA, ALTURA_JANELA))
    pygame.display.set_caption("Escape Room - Fase 10 (Era da Internet)")
    relogio = pygame.time.Clock()

    # Marca de tempo de quando a fase começou -- usada só pra preencher o
    # campo "tempo" do progresso.json na vitória (ver o final desta
    # função). Esta fase não tem cronômetro/limite, então esse tempo é só
    # informativo (quanto tempo real o jogador levou), não afeta estrelas.
    ticks_inicio_fase10 = pygame.time.get_ticks()

    # ---------------------------------------------------------------------------
    # Pasta do personagem escolhido no MENU GERAL (genero "m" -> índice 0,
    # "f" -> índice 1, mesma convenção das outras fases).
    # ---------------------------------------------------------------------------
    personagem_escolhido = 0 if genero == "m" else 1
    pasta_personagem = PASTAS_PERSONAGEM[personagem_escolhido]

    # ==============================================================================
    # === CENÁRIO E PERSONAGEM ===
    # ==============================================================================

    # Carrega os dois cenários (portal fechado e portal aberto), já
    # redimensionados para caber exatamente na janela. fundo_atual guarda qual
    # está sendo mostrado — o jogo começa com o portal FECHADO.
    fundo_porta_fechada = carregar_imagem(
        ASSETS["fundo_porta_fechada"], (LARGURA_JANELA, ALTURA_JANELA), com_alpha=False
    )
    fundo_porta_aberta = carregar_imagem(
        ASSETS["fundo_porta_aberta"], (LARGURA_JANELA, ALTURA_JANELA), com_alpha=False
    )
    fundo_atual = fundo_porta_fechada

    # ---------------------------------------------------------------------------
    # Personagem (reaproveitado da Fase 1). Todas as poses recebem o mesmo fator
    # de escala, calculado a partir da imagem parada, para o personagem crescer
    # sem distorcer.
    # ---------------------------------------------------------------------------
    ALTURA_PERSONAGEM_ALVO = 330

    try:
        _altura_original_parado = pygame.image.load(
            pasta_personagem + "personagem_parado_frente.png"
        ).get_height()
        FATOR_ESCALA_PERSONAGEM = ALTURA_PERSONAGEM_ALVO / _altura_original_parado
    except Exception:
        FATOR_ESCALA_PERSONAGEM = 1.0

    def carregar_imagem_personagem(nome_arquivo, fator_escala):
        """Carrega uma pose do personagem aplicando o fator de escala. Se faltar
        o arquivo, devolve um retângulo com o nome do arquivo escrito (mesmo
        espírito de diagnóstico de carregar_imagem() lá em cima) em vez de um
        retângulo mudo, pra dar pra ver na hora qual arquivo está faltando."""
        try:
            imagem = pygame.image.load(pasta_personagem + nome_arquivo).convert_alpha()
            largura, altura = imagem.get_size()
            return pygame.transform.scale(imagem, (round(largura * fator_escala), round(altura * fator_escala)))
        except Exception:
            largura_ph, altura_ph = 120, ALTURA_PERSONAGEM_ALVO
            ph = pygame.Surface((largura_ph, altura_ph), pygame.SRCALPHA)
            ph.fill((120, 90, 200))
            pygame.draw.rect(ph, (200, 80, 120), ph.get_rect(), width=3)

            # A caixa é estreita (120px) demais pra escrever o nome numa
            # linha só -- quebra em várias linhas curtas, palavra por
            # palavra (usando "_"/"." como separador), centralizadas.
            palavras = nome_arquivo.replace(".", "_").split("_")
            linhas, linha_atual = [], "FALTA:"
            for palavra in palavras:
                testada = (linha_atual + " " + palavra).strip()
                if _fonte_aviso_personagem.size(testada)[0] <= largura_ph - 8:
                    linha_atual = testada
                else:
                    linhas.append(linha_atual)
                    linha_atual = palavra
            linhas.append(linha_atual)

            y = altura_ph // 2 - (len(linhas) * 14) // 2
            for linha in linhas:
                texto = _fonte_aviso_personagem.render(linha, True, (255, 220, 220))
                ph.blit(texto, texto.get_rect(centerx=largura_ph // 2, y=y))
                y += 14
            return ph

    imagem_parado = carregar_imagem_personagem("personagem_parado_frente.png", FATOR_ESCALA_PERSONAGEM)
    imagens_andando = [
        carregar_imagem_personagem("personagem_andando_lado_1.png", FATOR_ESCALA_PERSONAGEM),
        carregar_imagem_personagem("personagem_andando_lado_2.png", FATOR_ESCALA_PERSONAGEM),
    ]

    # Posição inicial, velocidade e variáveis da animação de caminhada.
    PE_PERSONAGEM_Y = ALTURA_JANELA - 20
    VELOCIDADE_PERSONAGEM = 4
    personagem_centro_x = LARGURA_JANELA // 2

    virado_para_esquerda = False
    quadro_animacao = 0
    contador_animacao = 0

    # ---------------------------------------------------------------------------
    # ÁREA DA PORTA / PORTAL: retângulo (invisível) do lado direito da tela.
    # Depois de montar a torre de protocolos, o personagem precisa andar até
    # aqui para voltar ao presente e terminar o jogo.
    # ---------------------------------------------------------------------------
    AREA_PORTA = pygame.Rect(
        int(LARGURA_JANELA * 0.80), int(ALTURA_JANELA * 0.30),
        int(LARGURA_JANELA * 0.17), int(ALTURA_JANELA * 0.55),
    )

    # ==============================================================================
    # === FONTES E FUNÇÕES DE TEXTO ===
    # ==============================================================================
    ESPACAMENTO_LINHA = 16

    fonte = carregar_fonte(ASSETS["fonte_pixel"], 10)
    fonte_grande = carregar_fonte(ASSETS["fonte_pixel"], 16)
    fonte_vitoria = carregar_fonte(ASSETS["fonte_pixel"], 24)
    fonte_pausado = carregar_fonte(ASSETS["fonte_pixel"], 32)
    fonte_nome_personagem = carregar_fonte(ASSETS["fonte_pixel"], 8)  # nome do personagem, embaixo dele

    def quebrar_texto(texto, fonte_usada, largura_maxima):
        """Quebra um texto em várias linhas para caber dentro de uma largura
        máxima (usado para o texto não vazar das caixinhas)."""
        palavras = texto.split(" ")
        linhas = []
        linha_atual = ""
        for palavra in palavras:
            linha_testada = (linha_atual + " " + palavra).strip()
            if fonte_usada.size(linha_testada)[0] <= largura_maxima:
                linha_atual = linha_testada
            else:
                if linha_atual:
                    linhas.append(linha_atual)
                linha_atual = palavra
        if linha_atual:
            linhas.append(linha_atual)
        return linhas

    def desenhar_texto_multilinha(superficie, texto, fonte_usada, cor, x, y, largura_maxima, espacamento=ESPACAMENTO_LINHA):
        """Quebra o texto para caber na largura e desenha uma linha embaixo da
        outra. Devolve o y logo depois da última linha."""
        for linha in quebrar_texto(texto, fonte_usada, largura_maxima):
            superficie.blit(fonte_usada.render(linha, True, cor), (x, y))
            y += espacamento
        return y

    def desenhar_texto_com_contorno(superficie, texto, fonte_usada, cor_texto, cor_contorno, centro_x, centro_y, espessura=2):
        """Desenha um texto com contorno grosso (técnica retrô): desenha o texto
        várias vezes na cor do contorno, deslocado ao redor, e por cima o texto
        de verdade. Garante contraste em cima de qualquer fundo."""
        superficie_texto = fonte_usada.render(texto, True, cor_texto)
        superficie_contorno = fonte_usada.render(texto, True, cor_contorno)
        rect_texto = superficie_texto.get_rect(center=(centro_x, centro_y))
        for dx in (-espessura, 0, espessura):
            for dy in (-espessura, 0, espessura):
                if dx == 0 and dy == 0:
                    continue
                superficie.blit(superficie_contorno, (rect_texto.x + dx, rect_texto.y + dy))
        superficie.blit(superficie_texto, rect_texto)

    # ==============================================================================
    # === CHATBOT (TIM BERNERS-LEE) — VISUAL: ícone e avatar redondos ===
    # ==============================================================================
    # O Tim aparece como um retrato redondo: um ícone pequeno fixo num canto da
    # tela (clicável, para abrir a conversa) e um avatar maior grudado em cima
    # da caixinha durante a conversa, como em caixa de diálogo de RPG.
    imagem_tim_original = carregar_imagem(ASSETS["tim_retrato"], (200, 200))

    def recortar_em_circulo(imagem):
        """Recorta uma imagem quadrada em um círculo (deixa o retrato redondo)."""
        tamanho = imagem.get_size()
        mascara_circulo = pygame.Surface(tamanho, pygame.SRCALPHA)
        pygame.draw.circle(
            mascara_circulo, (255, 255, 255, 255),
            (tamanho[0] // 2, tamanho[1] // 2), tamanho[0] // 2,
        )
        recortada = imagem.copy()
        recortada.blit(mascara_circulo, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        return recortada

    TAMANHO_ICONE_TIM = 60
    TAMANHO_AVATAR_TIM = 80

    imagem_tim_icone = recortar_em_circulo(
        pygame.transform.smoothscale(imagem_tim_original, (TAMANHO_ICONE_TIM, TAMANHO_ICONE_TIM))
    )
    imagem_tim_avatar = recortar_em_circulo(
        pygame.transform.smoothscale(imagem_tim_original, (TAMANHO_AVATAR_TIM, TAMANHO_AVATAR_TIM))
    )

    MARGEM_ICONE_TIM = 15
    AREA_TIM = pygame.Rect(MARGEM_ICONE_TIM, MARGEM_ICONE_TIM, TAMANHO_ICONE_TIM, TAMANHO_ICONE_TIM)

    # Tamanho/posição da caixinha de conversa (também usados para calcular até
    # onde o jogador pode digitar sem o texto vazar).
    CAIXA_TIM_LARGURA, CAIXA_TIM_ALTURA = 330, 225
    MARGEM_CAIXA_TIM = 20
    LARGURA_TEXTO_CAIXA_TIM = CAIXA_TIM_LARGURA - 30

    # ==============================================================================
    # === CHATBOT (TIM) — ESTADO DA CONVERSA E INTEGRAÇÃO COM IA ===
    # ==============================================================================
    # Igual à Fase 1: a conversa tem duas falas fixas no começo (nunca travam,
    # pois não usam IA) e depois libera uma conversa livre opcional com a IA.
    #   ETAPA_NAO_INICIADA -> caixinha fechada; 1º clique no ícone começa a conversa
    #   ETAPA_APRESENTACAO -> Tim se apresenta e pergunta quem é o jogador (Enter avança)
    #   ETAPA_DICA         -> Tim explica a era e o que fazer (Enter fecha)
    #   ETAPA_PRONTO       -> caixinha fechada, esperando novo clique p/ conversa livre
    #   ETAPA_LIVRE        -> conversa livre, respostas geradas pela IA
    ETAPA_NAO_INICIADA = "nao_iniciada"
    ETAPA_APRESENTACAO = "apresentacao"
    ETAPA_DICA = "dica"
    ETAPA_PRONTO = "pronto"
    ETAPA_LIVRE = "livre"

    etapa_conversa_tim = ETAPA_NAO_INICIADA
    caixa_tim_aberta = False
    texto_digitado_tim = ""
    resposta_tim = ""
    tim_pensando = False

    FALA_TIM_APRESENTACAO = (
        "Ola, viajante! Eu sou Tim Berners-Lee, criador da World Wide Web. "
        "Voce chegou aos anos 1990. Quem e voce?"
    )
    FALA_TIM_DICA = (
        "Voce esta na era da internet, dos smartphones e da inteligencia "
        "artificial. Primeiro use o computador para acessar o site. Depois, "
        "para abrir o portal, ARRASTE as pecas certas para montar a TORRE DE "
        "PROTOCOLOS, de baixo pra cima: Cabo/Wi-Fi, depois TCP/IP (o protocolo "
        "da internet), depois HTTP e, no topo, a WWW. Cuidado: FTP, SMTP e "
        "Bluetooth NAO fazem parte dessa pilha!"
    )
    FALA_TIM_CONVITE_LIVRE = "O que voce gostaria de saber sobre a internet?"

    # Instrução de sistema enviada ao modelo para ele responder no papel do Tim.
    # Usada só na conversa livre (as duas primeiras falas são fixas).
    PROMPT_SISTEMA_TIM = (
        "Voce e Tim Berners-Lee, o cientista britanico que criou a World Wide "
        "Web em 1989-1991. Responda sempre em portugues, de forma breve (1-2 "
        "frases), com tom gentil e curioso, adequado para a fase final de um "
        "jogo educativo sobre a historia da computacao. Voce pode falar sobre a "
        "Web, a internet, TCP/IP, HTTP, navegadores, smartphones e inteligencia "
        "artificial."
    )

    # Modelo usado no Ollama (o mesmo obrigatório da Fase 1: qwen2.5:0.5b).
    MODELO_TIM = "qwen2.5:0.5b"
    TIMEOUT_OLLAMA_SEGUNDOS = 30
    if OLLAMA_DISPONIVEL:
        try:
            cliente_ollama = ollama.Client(timeout=TIMEOUT_OLLAMA_SEGUNDOS)
        except Exception:
            cliente_ollama = None
    else:
        cliente_ollama = None

    def perguntar_ao_tim(pergunta):
        """Chama o modelo qwen2.5:0.5b (via Ollama, rodando localmente) pedindo
        uma resposta como se fosse o Tim. Roda em uma thread separada para não
        travar a janela do jogo enquanto espera a resposta chegar."""
        nonlocal resposta_tim, tim_pensando
        if cliente_ollama is None:
            # Pacote ollama não instalado ou servidor indisponível -- o resto
            # da fase continua jogável, só o chat fica indisponível.
            resposta_tim = "Chat indisponível (Ollama não está instalado ou não está rodando)."
            tim_pensando = False
            return
        try:
            resultado = cliente_ollama.chat(
                model=MODELO_TIM,
                messages=[
                    {"role": "system", "content": PROMPT_SISTEMA_TIM},
                    {"role": "user", "content": pergunta},
                ],
            )
            resposta_tim = resultado["message"]["content"].strip()
        except Exception:
            # Cobre timeout, Ollama fora do ar ou qualquer outro erro de conexão.
            resposta_tim = "Tim nao pode responder agora."
        tim_pensando = False

    # Dica visual inicial: nos primeiros ~5s, uma seta aponta pro ícone do Tim.
    DURACAO_DICA_TIM = 300
    contador_dica_tim = DURACAO_DICA_TIM

    # ==============================================================================
    # === PUZZLE: MONTAR O ENDERECO DO SITE (URL) ===
    # ==============================================================================
    # Este puzzle acontece ANTES da torre de protocolos: o jogador clica no
    # computador da esquerda do cenario e precisa montar, na ordem certa, o
    # endereco "https://www.museu.com" clicando nos pedacos embaralhados.
    # So depois de resolver isso o botao "Conectar a rede" (torre) libera.
    PECAS_URL = ["https://", "www.", "museu", ".com"]

    # ---------------------------------------------------------------------------
    # AREA CLICAVEL DO PC: retangulo invisivel em cima da tela do computador da
    # esquerda do cenario (a que mostra "WELCOME TO THE INTERNET!").
    # ---------------------------------------------------------------------------
    AREA_PC = pygame.Rect(
        int(LARGURA_JANELA * 0.08), int(ALTURA_JANELA * 0.60),
        int(LARGURA_JANELA * 0.18), int(ALTURA_JANELA * 0.18),
    )

    # Estado do puzzle da URL:
    url_aberta = False            # o painel da URL esta aberto?
    url_resolvida = False         # jogador ja montou o endereco certo?
    proxima_peca_url = 0          # indice do proximo pedaco correto a colocar
    erros_url = 0                 # quantos erros (a partir do 1o, mostra a dica)
    mensagem_url = ""
    tempo_mensagem_url = 0

    # Bandeja com os indices dos pedacos ainda nao colocados, embaralhados —
    # mesma ideia da bandeja da torre de protocolos, mais abaixo. Reembaralhada
    # aqui dentro (não mais no nível do módulo), então cada nova visita à fase
    # começa com uma ordem diferente.
    bandeja_url = list(range(len(PECAS_URL)))
    random.shuffle(bandeja_url)

    # Geometria do painel da URL (mesmo espirito visual do painel da torre:
    # fundo escuro, borda clara, titulo em fonte pixel).
    URL_LARGURA, URL_ALTURA = 640, 360
    URL_X = (LARGURA_JANELA - URL_LARGURA) // 2
    URL_Y = (ALTURA_JANELA - URL_ALTURA) // 2

    # Barra de endereco: mostra os pedacos ja colocados, na ordem.
    BARRA_URL = pygame.Rect(URL_X + 40, URL_Y + 80, URL_LARGURA - 80, 40)

    # Pedacos disponiveis (bandeja), um abaixo do outro.
    LARGURA_PECA_URL = URL_LARGURA - 80
    ALTURA_PECA_URL = 44
    BANDEJA_URL_X = URL_X + 40
    BANDEJA_URL_Y0 = URL_Y + 150

    def calcular_rects_bandeja_url():
        """Igual a calcular_rects_bandeja(), mas para os pedacos da URL: devolve
        (indice_do_pedaco, rect) para os pedacos que ainda estao na bandeja. Usada
        tanto para DESENHAR quanto para detectar o clique, sempre em sincronia."""
        rects = []
        for k, indice_peca in enumerate(bandeja_url):
            rect = pygame.Rect(
                BANDEJA_URL_X, BANDEJA_URL_Y0 + k * (ALTURA_PECA_URL + 10),
                LARGURA_PECA_URL, ALTURA_PECA_URL,
            )
            rects.append((indice_peca, rect))
        return rects

    # ==============================================================================
    # === PUZZLE: TORRE DE PROTOCOLOS DA INTERNET ===
    # ==============================================================================
    # O jogador precisa ARRASTAR (drag and drop) as 4 peças certas para a torre,
    # de BAIXO para CIMA, na ordem correta (índice 0 = base, índice 3 = topo):
    #   0) Cabo / Wi-Fi -> a conexão física
    #   1) TCP / IP     -> o protocolo da internet (a "estrada" dos dados)
    #   2) HTTP         -> o protocolo da web (como o navegador pede as páginas)
    #   3) WWW          -> a World Wide Web, no topo (a criação do Tim)
    # Além das 4 certas, existem 3 peças FALSAS (decoy) misturadas na bandeja:
    # FTP, SMTP e Bluetooth. Elas parecem protocolos de verdade, mas não fazem
    # parte da pilha da internet — tentar encaixar uma delas derruba a torre,
    # igual a colocar uma peça certa fora de ordem. A única forma de saber quais
    # são as certas é conversando com o Tim (fala fixa dele, mais abaixo).
    # As peças são DESENHADAS pelo código (retângulos + texto), então não
    # precisam de nenhuma imagem nova.
    PECAS_PROTOCOLO = [
        {"rotulo": "Cabo / Wi-Fi", "sub": "conexao fisica", "cor": (95, 95, 115), "correta": True},
        {"rotulo": "TCP / IP", "sub": "protocolo da internet", "cor": (55, 140, 90), "correta": True},
        {"rotulo": "HTTP", "sub": "protocolo da web", "cor": (65, 110, 180), "correta": True},
        {"rotulo": "WWW", "sub": "World Wide Web", "cor": (205, 150, 45), "correta": True},
        {"rotulo": "FTP", "sub": "protocolo de arquivos", "cor": (120, 90, 150), "correta": False},
        {"rotulo": "SMTP", "sub": "protocolo de e-mail", "cor": (170, 100, 60), "correta": False},
        {"rotulo": "Bluetooth", "sub": "conexao sem fio", "cor": (60, 90, 160), "correta": False},
    ]
    PECAS_CORRETAS_TOTAL = sum(1 for peca in PECAS_PROTOCOLO if peca["correta"])

    # Estado do puzzle:
    puzzle_aberto = False                 # o painel da torre está aberto?
    proxima_peca = 0                      # índice da próxima peça correta a colocar
    torre_completa = False                # torre montada certinho?
    tempo_flash_erro = 0                  # quadros de flash vermelho ao errar
    mensagem_puzzle = ""
    tempo_mensagem_puzzle = 0

    # Estado do ARRASTAR (drag and drop): qual peça está "grudada" no cursor e a
    # posição atual dela na tela. peca_arrastando = None quando nada é
    # arrastado. arrasto_dx/arrasto_dy guardam ONDE dentro da peça o jogador
    # clicou, pra ela não "pular" pro canto quando o mouse se move.
    peca_arrastando = None
    arrasto_dx = 0
    arrasto_dy = 0
    arrasto_x = 0
    arrasto_y = 0

    # A "bandeja" guarda os índices das peças ainda não colocadas (certas e
    # falsas), embaralhados, para o jogador ter que pensar na ordem certa.
    bandeja = list(range(len(PECAS_PROTOCOLO)))
    random.shuffle(bandeja)

    # Geometria do painel do puzzle (calculada uma vez). Mais alto que antes
    # porque agora são 7 peças na bandeja (4 certas + 3 falsas) em vez de 4.
    PUZZLE_LARGURA, PUZZLE_ALTURA = 760, 560
    PUZZLE_X = (LARGURA_JANELA - PUZZLE_LARGURA) // 2
    PUZZLE_Y = (ALTURA_JANELA - PUZZLE_ALTURA) // 2

    LARGURA_PECA = 280
    ALTURA_PECA = 46
    ESPACO_VERTICAL_BANDEJA = 8  # espaçamento menor que o da torre, pra caber 7 peças

    # Coluna da esquerda: a torre é montada aqui, de baixo pra cima.
    TORRE_X = PUZZLE_X + 45
    TORRE_BASE_Y = PUZZLE_Y + PUZZLE_ALTURA - 70  # topo da plataforma de base

    # Coluna da direita: as peças disponíveis (bandeja).
    BANDEJA_X = PUZZLE_X + PUZZLE_LARGURA - LARGURA_PECA - 45
    BANDEJA_Y0 = PUZZLE_Y + 110

    def calcular_rects_bandeja():
        """Devolve uma lista de (indice_da_peca, rect) para as peças que estão na
        bandeja. É usada tanto para DESENHAR as peças quanto para detectar em
        qual o jogador clicou pra começar o arraste — assim as duas coisas ficam
        sempre em sincronia."""
        rects = []
        for k, indice_peca in enumerate(bandeja):
            rect = pygame.Rect(
                BANDEJA_X, BANDEJA_Y0 + k * (ALTURA_PECA + ESPACO_VERTICAL_BANDEJA),
                LARGURA_PECA, ALTURA_PECA,
            )
            rects.append((indice_peca, rect))
        return rects

    def desenhar_peca(superficie, rect, peca):
        """Desenha uma peça de protocolo: um retângulo colorido com o nome do
        protocolo em cima e uma legenda menor embaixo."""
        pygame.draw.rect(superficie, peca["cor"], rect, border_radius=6)
        pygame.draw.rect(superficie, (15, 15, 20), rect, width=2, border_radius=6)
        titulo = fonte.render(peca["rotulo"], True, (255, 255, 255))
        superficie.blit(titulo, titulo.get_rect(center=(rect.centerx, rect.centery - 7)))
        legenda = fonte.render(peca["sub"], True, (235, 235, 235))
        superficie.blit(legenda, legenda.get_rect(center=(rect.centerx, rect.centery + 9)))

    # ==============================================================================
    # === EFEITOS VISUAIS (partículas de acerto, brilho, seta de dica) ===
    # ==============================================================================
    particulas_acerto = []
    tempo_flash_acerto = 0
    CORES_PARTICULA_ACERTO = [(120, 220, 255), (255, 255, 255), (140, 200, 120)]

    def disparar_efeito_acerto(centro):
        """Cria partículas que "explodem" a partir de um ponto (usado quando o
        jogador encaixa uma peça certa) e liga um flash rápido de tela."""
        nonlocal tempo_flash_acerto
        tempo_flash_acerto = 8
        cx, cy = centro
        for _ in range(16):
            angulo = random.uniform(0, 2 * math.pi)
            velocidade = random.uniform(1.5, 4)
            particulas_acerto.append({
                "x": float(cx), "y": float(cy),
                "vx": math.cos(angulo) * velocidade,
                "vy": math.sin(angulo) * velocidade,
                "vida": random.randint(20, 40),
                "cor": random.choice(CORES_PARTICULA_ACERTO),
            })

    def desenhar_brilho(superficie, area, tempo_ms):
        """Contorno dourado pulsante ao redor de uma área clicável (indica que dá
        pra clicar). Usa uma superfície com transparência."""
        pulso = (math.sin(tempo_ms / 200) + 1) / 2
        expansao = round(4 + pulso * 6)
        alpha = round(120 + pulso * 100)
        contorno = area.inflate(expansao * 2, expansao * 2)
        brilho = pygame.Surface(contorno.size, pygame.SRCALPHA)
        pygame.draw.rect(brilho, (120, 220, 255, alpha), brilho.get_rect(), width=4, border_radius=8)
        superficie.blit(brilho, contorno.topleft)

    def desenhar_dica_tim(superficie, tempo_ms):
        """Seta animada (só com pygame.draw) + texto 'Clique aqui!' apontando para
        o ícone do Tim, no canto superior esquerdo."""
        oscilacao = round(math.sin(tempo_ms / 250) * 8)
        ponta_x = AREA_TIM.right + 18 + oscilacao
        ponta_y = AREA_TIM.bottom + 18 + oscilacao
        base_x = ponta_x + 45
        base_y = ponta_y + 45
        cor_seta = (120, 220, 255)
        pygame.draw.line(superficie, cor_seta, (base_x, base_y), (ponta_x, ponta_y), 5)
        pygame.draw.polygon(superficie, cor_seta, [
            (ponta_x, ponta_y), (ponta_x + 16, ponta_y + 4), (ponta_x + 4, ponta_y + 16),
        ])
        superficie.blit(fonte.render("Clique aqui!", True, cor_seta), (base_x + 8, base_y - 6))

    # ==============================================================================
    # === BOTÃO "CONECTAR À REDE" (abre o puzzle da torre) ===
    # ==============================================================================
    # Botão sempre visível no alto da tela; clicar nele abre o painel da torre de
    # protocolos. É desenhado pelo código (não precisa de imagem), então sempre
    # aparece, independente da sua arte de cenário.
    BOTAO_CONECTAR = pygame.Rect(0, 0, 260, 48)
    BOTAO_CONECTAR.center = (LARGURA_JANELA // 2, 120)

    # ==============================================================================
    # === MENU DE CONFIGURAÇÕES (engrenagem, painel, botões) ===
    # ==============================================================================
    # Igual em espírito ao da Fase 1, mas o painel é DESENHADO (retângulo de
    # madeira) em vez de usar a imagem menu_madeira.png — assim esta fase não
    # depende de mais nenhum arquivo de imagem.
    menu_aberto = False
    pausado_manual = False
    VOLUME_INICIAL_MUSICA = 0.35
    volume_musica = VOLUME_INICIAL_MUSICA

    MENU_LARGURA, MENU_ALTURA = 420, 420
    MENU_POS_X = (LARGURA_JANELA - MENU_LARGURA) // 2
    MENU_POS_Y = (ALTURA_JANELA - MENU_ALTURA) // 2
    MENU_CENTRO_X = MENU_POS_X + MENU_LARGURA // 2

    CENTRO_ENGRENAGEM = (LARGURA_JANELA - 40, 40)
    RAIO_ENGRENAGEM = 16
    AREA_ENGRENAGEM = pygame.Rect(0, 0, (RAIO_ENGRENAGEM + 10) * 2, (RAIO_ENGRENAGEM + 10) * 2)
    AREA_ENGRENAGEM.center = CENTRO_ENGRENAGEM

    BOTAO_PAUSA = pygame.Rect(0, 0, 44, 44)
    BOTAO_PAUSA.center = (MENU_CENTRO_X, MENU_POS_Y + 105)
    BOTAO_VOLUME_MENOS = pygame.Rect(0, 0, 36, 36)
    BOTAO_VOLUME_MENOS.center = (MENU_CENTRO_X - 80, MENU_POS_Y + 200)
    BOTAO_VOLUME_MAIS = pygame.Rect(0, 0, 36, 36)
    BOTAO_VOLUME_MAIS.center = (MENU_CENTRO_X + 80, MENU_POS_Y + 200)
    BOTAO_CONTINUAR = pygame.Rect(0, 0, 200, 42)
    BOTAO_CONTINUAR.center = (MENU_CENTRO_X, MENU_POS_Y + 270)
    BOTAO_SAIR = pygame.Rect(0, 0, 200, 42)
    BOTAO_SAIR.center = (MENU_CENTRO_X, MENU_POS_Y + 330)

    COR_TEXTO_MENU = (255, 240, 200)
    COR_BOTAO_MENU = (120, 80, 45)
    COR_BORDA_BOTAO_MENU = (60, 35, 15)

    def desenhar_icone_engrenagem(superficie, centro, raio, cor=(210, 210, 215)):
        cx, cy = centro
        for i in range(8):
            angulo = (2 * math.pi / 8) * i
            dente_x = cx + math.cos(angulo) * raio
            dente_y = cy + math.sin(angulo) * raio
            pygame.draw.circle(superficie, cor, (round(dente_x), round(dente_y)), round(raio * 0.4))
        pygame.draw.circle(superficie, cor, centro, raio)
        pygame.draw.circle(superficie, (35, 35, 40), centro, round(raio * 0.45))

    def desenhar_icone_pausa_play(superficie, rect, mostrar_play, cor=(255, 240, 200)):
        cx, cy = rect.center
        if mostrar_play:
            pygame.draw.polygon(superficie, cor, [(cx - 8, cy - 12), (cx - 8, cy + 12), (cx + 12, cy)])
        else:
            pygame.draw.rect(superficie, cor, (cx - 10, cy - 12, 6, 24))
            pygame.draw.rect(superficie, cor, (cx + 4, cy - 12, 6, 24))

    # ---------------------------------------------------------------------------
    # Mensagens temporárias na tela (sucesso/erro/instrução).
    # ---------------------------------------------------------------------------
    mensagem_atual = ""
    tempo_mensagem = 0

    # ==============================================================================
    # === TELA DE INTRODUÇÃO (mostrada uma vez, antes do jogo começar) ===
    # ==============================================================================
    TEXTO_INTRODUCAO = (
        "Anos 1990. Depois de atravessar milenios de historia, voce chega a "
        "ultima era: a internet acaba de nascer. Telas se acendem, a World Wide "
        "Web se espalha pelo mundo e um portal brilha ao fundo, o caminho de "
        "volta ao presente."
    )

    def tela_introducao():
        aguardando = True
        while aguardando:
            relogio.tick(60)
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if evento.type == pygame.KEYDOWN:
                    aguardando = False
            tela.fill((10, 12, 24))
            desenhar_texto_multilinha(
                tela, TEXTO_INTRODUCAO, fonte_grande, (230, 230, 240),
                60, ALTURA_JANELA // 2 - 120, LARGURA_JANELA - 120, espacamento=30,
            )
            continuar = fonte.render("Pressione qualquer tecla para comecar", True, (170, 170, 190))
            tela.blit(continuar, (LARGURA_JANELA // 2 - continuar.get_width() // 2, ALTURA_JANELA - 60))
            pygame.display.flip()

    # ==============================================================================
    # === SONS (música de fundo em loop e som de clique) ===
    # ==============================================================================
    musica_ok = False
    try:
        pygame.mixer.music.load(ASSETS["musica_fundo"])
        pygame.mixer.music.set_volume(volume_musica)
        pygame.mixer.music.play(-1)  # -1 = loop infinito
        musica_ok = True
    except Exception:
        musica_ok = False

    som_clique = carregar_som(ASSETS["som_clique"])

    tela_introducao()

    # ==============================================================================
    # === LOOP PRINCIPAL DO JOGO ===
    # Roda a 60 quadros por segundo: processa eventos, atualiza o estado
    # (movimento, animação, puzzle) e desenha tudo na tela.
    # ==============================================================================
    # vitoria_alcancada e saiu_por_fechar_janela decidem o que a função devolve
    # no final: "vitoria" (montou a torre, chegou no portal e confirmou com Esc
    # na tela final), None (saiu pelo ESC antes disso, ou pelo botão SAIR do
    # menu -- volta pro mapa normalmente) ou, se a janela foi fechada de
    # verdade (evento QUIT), encerra o programa INTEIRO como esta fase sempre
    # fez (mesmo comportamento de Fase_4/Fase_5).
    vitoria_alcancada = False
    saiu_por_fechar_janela = False
    chegou_no_portal = False  # recalculado a cada quadro, iniciado aqui pra sempre existir

    rodando = True
    while rodando:
        relogio.tick(60)
        personagem_andou = False

        for evento in pygame.event.get():
            # Fotografia de "nenhuma sub-tela está aberta" ANTES deste evento
            # ser tratado -- usada só pelo Esc "sair da fase" mais abaixo.
            nenhuma_subtela_aberta_antes_do_evento = (
                not menu_aberto and not puzzle_aberto and not url_aberta and not caixa_tim_aberta
            )

            if evento.type == pygame.QUIT:
                saiu_por_fechar_janela = True
                rodando = False

            # -------------------------------------------------------------------
            # --- EVENTOS DE MOUSE ---
            # -------------------------------------------------------------------
            if evento.type == pygame.MOUSEBUTTONDOWN:
                # A engrenagem é sempre clicável (é o botão de pausa do jogo).
                if not menu_aberto and AREA_ENGRENAGEM.collidepoint(evento.pos):
                    som_clique.play()
                    menu_aberto = True

                elif menu_aberto:
                    # Com o menu aberto, só os botões dele respondem.
                    if BOTAO_PAUSA.collidepoint(evento.pos):
                        pausado_manual = not pausado_manual
                    elif BOTAO_VOLUME_MENOS.collidepoint(evento.pos):
                        volume_musica = max(0.0, round(volume_musica - 0.1, 2))
                        if musica_ok:
                            pygame.mixer.music.set_volume(volume_musica)
                    elif BOTAO_VOLUME_MAIS.collidepoint(evento.pos):
                        volume_musica = min(1.0, round(volume_musica + 0.1, 2))
                        if musica_ok:
                            pygame.mixer.music.set_volume(volume_musica)
                    elif BOTAO_CONTINUAR.collidepoint(evento.pos):
                        menu_aberto = False
                        pausado_manual = False
                    elif BOTAO_SAIR.collidepoint(evento.pos):
                        # "Sair" aqui significa voltar pro mapa de fases (não
                        # fechar o jogo inteiro) -- mesmo significado do botão
                        # SAIR do painel de configurações em Fase_2/Fase_9.
                        rodando = False

                elif puzzle_aberto:
                    # -----------------------------------------------------------
                    # --- PUZZLE: início do ARRASTE de uma peça da bandeja ---
                    # -----------------------------------------------------------
                    for indice_peca, rect in calcular_rects_bandeja():
                        if rect.collidepoint(evento.pos):
                            peca_arrastando = indice_peca
                            arrasto_dx = evento.pos[0] - rect.x
                            arrasto_dy = evento.pos[1] - rect.y
                            arrasto_x = rect.x
                            arrasto_y = rect.y
                            break

                elif url_aberta:
                    # -----------------------------------------------------------
                    # --- PUZZLE DA URL: clique num pedaço da bandeja ---
                    # -----------------------------------------------------------
                    for indice_peca, rect in calcular_rects_bandeja_url():
                        if rect.collidepoint(evento.pos):
                            som_clique.play()
                            if indice_peca == proxima_peca_url:
                                # Pedaço certo: entra na barra de endereço.
                                bandeja_url.remove(indice_peca)
                                proxima_peca_url += 1
                                disparar_efeito_acerto(rect.center)
                                if proxima_peca_url >= len(PECAS_URL):
                                    # URL completa: libera o botão "Conectar à rede".
                                    url_resolvida = True
                                    url_aberta = False
                                    mensagem_atual = "Conexao com o site estabelecida! Agora conecte a rede."
                                    tempo_mensagem = 240
                            else:
                                # Pedaço errado: a URL reseta e recomeça.
                                proxima_peca_url = 0
                                bandeja_url = list(range(len(PECAS_URL)))
                                random.shuffle(bandeja_url)
                                erros_url += 1
                                mensagem_url = "Endereco invalido! Tente de novo."
                                tempo_mensagem_url = 120
                            break

                else:
                    # -----------------------------------------------------------
                    # --- CENÁRIO: computador (URL), botão "Conectar à rede" e ícone do Tim ---
                    # -----------------------------------------------------------
                    if (
                        not torre_completa
                        and not caixa_tim_aberta
                        and BOTAO_CONECTAR.collidepoint(evento.pos)
                    ):
                        if url_resolvida:
                            som_clique.play()
                            puzzle_aberto = True
                        else:
                            mensagem_atual = "Primeiro use o computador para acessar o site."
                            tempo_mensagem = 150

                    elif (
                        not url_resolvida
                        and not caixa_tim_aberta
                        and AREA_PC.collidepoint(evento.pos)
                    ):
                        som_clique.play()
                        url_aberta = True

                    elif (
                        not caixa_tim_aberta
                        and etapa_conversa_tim in (ETAPA_NAO_INICIADA, ETAPA_PRONTO)
                        and AREA_TIM.collidepoint(evento.pos)
                    ):
                        som_clique.play()
                        contador_dica_tim = 0
                        caixa_tim_aberta = True
                        if etapa_conversa_tim == ETAPA_NAO_INICIADA:
                            etapa_conversa_tim = ETAPA_APRESENTACAO
                        else:
                            etapa_conversa_tim = ETAPA_LIVRE
                        texto_digitado_tim = ""
                        resposta_tim = ""
                        tim_pensando = False

            # -------------------------------------------------------------------
            # --- ARRASTAR PEÇA (drag and drop da torre de protocolos) ---
            # -------------------------------------------------------------------
            if evento.type == pygame.MOUSEMOTION and puzzle_aberto and peca_arrastando is not None:
                arrasto_x = evento.pos[0] - arrasto_dx
                arrasto_y = evento.pos[1] - arrasto_dy

            if evento.type == pygame.MOUSEBUTTONUP and puzzle_aberto and peca_arrastando is not None:
                py_alvo = TORRE_BASE_Y - (proxima_peca + 1) * (ALTURA_PECA + 6)
                rect_alvo = pygame.Rect(TORRE_X, py_alvo, LARGURA_PECA, ALTURA_PECA)
                area_encaixe = rect_alvo.inflate(80, 80)
                centro_solto = (arrasto_x + LARGURA_PECA // 2, arrasto_y + ALTURA_PECA // 2)

                if area_encaixe.collidepoint(centro_solto):
                    som_clique.play()
                    if peca_arrastando == proxima_peca:
                        # Peça certa: encaixa e sobe a torre.
                        bandeja.remove(peca_arrastando)
                        proxima_peca += 1
                        centro_peca = (
                            TORRE_X + LARGURA_PECA // 2,
                            TORRE_BASE_Y - proxima_peca * (ALTURA_PECA + 6),
                        )
                        disparar_efeito_acerto(centro_peca)
                        if proxima_peca >= PECAS_CORRETAS_TOTAL:
                            # Torre completa: o portal se abre!
                            torre_completa = True
                            puzzle_aberto = False
                            fundo_atual = fundo_porta_aberta
                            mensagem_atual = "Conexao estabelecida! O portal se abriu."
                            tempo_mensagem = 240
                    else:
                        # Peça errada (ordem errada ou peça FALSA): a torre cai
                        # e as peças voltam todas pra bandeja, embaralhadas.
                        proxima_peca = 0
                        bandeja = list(range(len(PECAS_PROTOCOLO)))
                        random.shuffle(bandeja)
                        tempo_flash_erro = 10
                        mensagem_puzzle = "Sequencia invalida! A conexao caiu."
                        tempo_mensagem_puzzle = 120

                peca_arrastando = None

            # -------------------------------------------------------------------
            # --- EVENTOS DE TECLADO ---
            # -------------------------------------------------------------------
            # Menu aberto: Esc fecha o menu.
            if evento.type == pygame.KEYDOWN and menu_aberto:
                if evento.key == pygame.K_ESCAPE:
                    menu_aberto = False
                    pausado_manual = False

            # Puzzle aberto: Esc fecha o painel (pra andar/pensar) sem perder o
            # progresso já montado.
            elif evento.type == pygame.KEYDOWN and puzzle_aberto:
                if evento.key == pygame.K_ESCAPE:
                    puzzle_aberto = False
                    peca_arrastando = None  # cancela um arraste em andamento

            # Puzzle da URL aberto: Esc fecha o painel do PC sem perder o
            # progresso (os pedaços já colocados continuam na barra).
            elif evento.type == pygame.KEYDOWN and url_aberta:
                if evento.key == pygame.K_ESCAPE:
                    url_aberta = False

            # Chatbot aberto: digitação, conforme a etapa da conversa.
            elif evento.type == pygame.KEYDOWN and caixa_tim_aberta:
                if etapa_conversa_tim == ETAPA_APRESENTACAO:
                    # Fala fixa: jogador digita quem é; Enter avança pra dica.
                    if evento.key == pygame.K_RETURN:
                        if texto_digitado_tim != "":
                            texto_digitado_tim = ""
                            etapa_conversa_tim = ETAPA_DICA
                    elif evento.key == pygame.K_BACKSPACE:
                        texto_digitado_tim = texto_digitado_tim[:-1]
                    elif evento.unicode.isprintable() and fonte.size(texto_digitado_tim + evento.unicode)[0] <= LARGURA_TEXTO_CAIXA_TIM:
                        texto_digitado_tim += evento.unicode

                elif etapa_conversa_tim == ETAPA_DICA:
                    # Fala fixa: só espera Enter para fechar a caixinha.
                    if evento.key == pygame.K_RETURN:
                        caixa_tim_aberta = False
                        etapa_conversa_tim = ETAPA_PRONTO

                elif etapa_conversa_tim == ETAPA_LIVRE:
                    # Conversa livre com IA (thread separada, não trava o jogo).
                    if evento.key == pygame.K_ESCAPE:
                        caixa_tim_aberta = False
                        etapa_conversa_tim = ETAPA_PRONTO
                    elif evento.key == pygame.K_RETURN:
                        if texto_digitado_tim != "" and not tim_pensando:
                            tim_pensando = True
                            resposta_tim = ""
                            threading.Thread(
                                target=perguntar_ao_tim,
                                args=(texto_digitado_tim,),
                                daemon=True,
                            ).start()
                            texto_digitado_tim = ""
                    elif evento.key == pygame.K_BACKSPACE:
                        if not tim_pensando:
                            texto_digitado_tim = texto_digitado_tim[:-1]
                    elif (
                        not tim_pensando
                        and evento.unicode.isprintable()
                        and fonte.size(texto_digitado_tim + evento.unicode)[0] <= LARGURA_TEXTO_CAIXA_TIM
                    ):
                        texto_digitado_tim += evento.unicode

            # Fora de qualquer sub-tela e fora da tela final do portal, Esc
            # volta direto pro mapa de fases -- mesma convenção usada em
            # todas as outras fases já conectadas ao menu. Na tela final
            # (chegou_no_portal), Esc já tem outro significado (confirmar a
            # vitória, ver mais abaixo na seção de desenho) -- por isso fica
            # de fora deste "else" genérico.
            elif (
                evento.type == pygame.KEYDOWN
                and evento.key == pygame.K_ESCAPE
                and nenhuma_subtela_aberta_antes_do_evento
                and not chegou_no_portal
            ):
                rodando = False

        # -----------------------------------------------------------------------
        # --- ATUALIZAÇÃO: MOVIMENTO DO PERSONAGEM ---
        # Bloqueado enquanto qualquer caixinha/menu está aberta.
        # -----------------------------------------------------------------------
        if not puzzle_aberto and not url_aberta and not caixa_tim_aberta and not menu_aberto:
            teclas = pygame.key.get_pressed()
            if teclas[pygame.K_LEFT]:
                personagem_centro_x -= VELOCIDADE_PERSONAGEM
                virado_para_esquerda = True
                personagem_andou = True
            if teclas[pygame.K_RIGHT]:
                personagem_centro_x += VELOCIDADE_PERSONAGEM
                virado_para_esquerda = False
                personagem_andou = True

        # -----------------------------------------------------------------------
        # --- ATUALIZAÇÃO: ANIMAÇÃO DO PERSONAGEM ---
        # -----------------------------------------------------------------------
        if personagem_andou:
            contador_animacao += 1
            if contador_animacao >= 8:
                contador_animacao = 0
                quadro_animacao = (quadro_animacao + 1) % 2
            imagem_personagem = imagens_andando[quadro_animacao]
        else:
            imagem_personagem = imagem_parado

        if virado_para_esquerda:
            imagem_personagem = pygame.transform.flip(imagem_personagem, True, False)

        largura_atual, altura_atual = imagem_personagem.get_size()
        personagem_centro_x = max(largura_atual // 2, min(personagem_centro_x, LARGURA_JANELA - largura_atual // 2))
        personagem_pos_x = personagem_centro_x - largura_atual // 2
        personagem_pos_y = PE_PERSONAGEM_Y - altura_atual

        # -----------------------------------------------------------------------
        # --- ATUALIZAÇÃO: CHEGADA AO PORTAL (fim do jogo) ---
        # Só vale depois de a torre estar completa.
        # -----------------------------------------------------------------------
        retangulo_personagem = pygame.Rect(personagem_pos_x, personagem_pos_y, largura_atual, altura_atual)
        chegou_no_portal = torre_completa and retangulo_personagem.colliderect(AREA_PORTA)

        # =========================================================================
        # === DESENHO: CENÁRIO, PERSONAGEM E ÍCONES FIXOS ===
        # =========================================================================
        tela.blit(fundo_atual, (0, 0))
        tela.blit(imagem_personagem, (personagem_pos_x, personagem_pos_y))

        # Nome do personagem escolhido no menu geral, centralizado embaixo
        # dele -- mesmo padrão visual de Fase_2/Fase_9/Fase_1/Fase_6.
        nome_surf = fonte_nome_personagem.render(character_name, True, (240, 240, 240))
        tela.blit(nome_surf, nome_surf.get_rect(midtop=(personagem_centro_x, personagem_pos_y + altura_atual + 4)))

        # Ícone redondo do Tim, fixo no canto superior esquerdo.
        tela.blit(imagem_tim_icone, (AREA_TIM.x, AREA_TIM.y))

        # Ícone da engrenagem (menu), sempre visível no canto superior direito.
        desenhar_icone_engrenagem(tela, CENTRO_ENGRENAGEM, RAIO_ENGRENAGEM)

        # Dica visual inicial (seta + "Clique aqui!") apontando pro Tim.
        if contador_dica_tim > 0 and not caixa_tim_aberta and not puzzle_aberto and not url_aberta:
            desenhar_dica_tim(tela, pygame.time.get_ticks())
            contador_dica_tim -= 1

        # -----------------------------------------------------------------------
        # --- DESENHO: BOTÃO "CONECTAR À REDE" ---
        # -----------------------------------------------------------------------
        mouse_pos = pygame.mouse.get_pos()
        if not torre_completa and not puzzle_aberto and not url_aberta and not caixa_tim_aberta and not menu_aberto:
            if url_resolvida:
                hover = BOTAO_CONECTAR.collidepoint(mouse_pos)
                cor_botao = (60, 130, 210) if hover else (40, 100, 175)
            else:
                cor_botao = (90, 90, 100)
            pygame.draw.rect(tela, cor_botao, BOTAO_CONECTAR, border_radius=10)
            pygame.draw.rect(tela, (230, 240, 255), BOTAO_CONECTAR, width=2, border_radius=10)
            rotulo_botao = fonte.render("Conectar a rede", True, (255, 255, 255))
            tela.blit(rotulo_botao, rotulo_botao.get_rect(center=BOTAO_CONECTAR.center))

        # -----------------------------------------------------------------------
        # --- DESENHO: BRILHO NO COMPUTADOR (indica que dá pra clicar) ---
        # -----------------------------------------------------------------------
        if (
            not url_resolvida and not url_aberta and not puzzle_aberto
            and not caixa_tim_aberta and not menu_aberto
            and AREA_PC.collidepoint(mouse_pos)
        ):
            desenhar_brilho(tela, AREA_PC, pygame.time.get_ticks())

        # -----------------------------------------------------------------------
        # --- DESENHO: PORTAL ABERTO (brilho + seta) ---
        # -----------------------------------------------------------------------
        if torre_completa and not chegou_no_portal:
            desenhar_brilho(tela, AREA_PORTA, pygame.time.get_ticks())
            aviso_portal = fonte.render("Ande ate o portal ->", True, (255, 255, 255))
            fundo_aviso = pygame.Surface((aviso_portal.get_width() + 12, aviso_portal.get_height() + 8), pygame.SRCALPHA)
            fundo_aviso.fill((0, 0, 0, 130))
            tela.blit(fundo_aviso, (AREA_PORTA.centerx - aviso_portal.get_width() // 2 - 6, AREA_PORTA.top - 30))
            tela.blit(aviso_portal, (AREA_PORTA.centerx - aviso_portal.get_width() // 2, AREA_PORTA.top - 26))

        # -----------------------------------------------------------------------
        # --- DESENHO: PARTÍCULAS E FLASHES (por cima do cenário) ---
        # -----------------------------------------------------------------------
        for particula in particulas_acerto[:]:
            particula["x"] += particula["vx"]
            particula["y"] += particula["vy"]
            particula["vida"] -= 1
            if particula["vida"] <= 0:
                particulas_acerto.remove(particula)
            else:
                raio = max(1, particula["vida"] // 8)
                pygame.draw.circle(tela, particula["cor"], (round(particula["x"]), round(particula["y"])), raio)

        if tempo_flash_acerto > 0:
            flash = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA), pygame.SRCALPHA)
            flash.fill((200, 240, 255, round(150 * (tempo_flash_acerto / 10))))
            tela.blit(flash, (0, 0))
            tempo_flash_acerto -= 1

        if tempo_flash_erro > 0:
            flash = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA), pygame.SRCALPHA)
            flash.fill((255, 80, 80, round(120 * (tempo_flash_erro / 10))))
            tela.blit(flash, (0, 0))
            tempo_flash_erro -= 1

        # Mensagem temporária no topo (sucesso/instrução).
        if tempo_mensagem > 0:
            texto = fonte_grande.render(mensagem_atual, True, (255, 255, 0))
            tela.blit(texto, (LARGURA_JANELA // 2 - texto.get_width() // 2, 30))
            tempo_mensagem -= 1

        # =========================================================================
        # === DESENHO: PAINEL DO PUZZLE (TORRE DE PROTOCOLOS) ===
        # =========================================================================
        if puzzle_aberto:
            escurecido = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA), pygame.SRCALPHA)
            escurecido.fill((0, 0, 0, 160))
            tela.blit(escurecido, (0, 0))

            painel = pygame.Rect(PUZZLE_X, PUZZLE_Y, PUZZLE_LARGURA, PUZZLE_ALTURA)
            pygame.draw.rect(tela, (28, 32, 48), painel, border_radius=12)
            pygame.draw.rect(tela, (120, 200, 255), painel, width=3, border_radius=12)

            titulo = fonte_grande.render("Torre de Protocolos da Internet", True, (200, 230, 255))
            tela.blit(titulo, titulo.get_rect(center=(PUZZLE_X + PUZZLE_LARGURA // 2, PUZZLE_Y + 30)))
            desenhar_texto_multilinha(
                tela, "Arraste as pecas certas, de baixo pra cima. Cuidado com as falsas!",
                fonte, (200, 200, 210), PUZZLE_X + 45, PUZZLE_Y + 58, PUZZLE_LARGURA - 90,
            )

            pygame.draw.rect(tela, (60, 45, 30), (TORRE_X - 12, TORRE_BASE_Y, LARGURA_PECA + 24, 18), border_radius=4)

            for i in range(proxima_peca):
                py = TORRE_BASE_Y - (i + 1) * (ALTURA_PECA + 6)
                desenhar_peca(tela, pygame.Rect(TORRE_X, py, LARGURA_PECA, ALTURA_PECA), PECAS_PROTOCOLO[i])

            for i in range(PECAS_CORRETAS_TOTAL):
                py_num = TORRE_BASE_Y - (i + 1) * (ALTURA_PECA + 6)
                numero = fonte.render(str(i + 1), True, (180, 180, 195))
                tela.blit(numero, numero.get_rect(center=(TORRE_X - 16, py_num + ALTURA_PECA // 2)))

            if proxima_peca == 0:
                py_slot1 = TORRE_BASE_Y - (ALTURA_PECA + 6)
                centro_y_slot1 = py_slot1 + ALTURA_PECA // 2
                ponta_seta_x = TORRE_X + LARGURA_PECA + 12
                pygame.draw.polygon(tela, (255, 230, 120), [
                    (ponta_seta_x, centro_y_slot1),
                    (ponta_seta_x + 14, centro_y_slot1 - 8),
                    (ponta_seta_x + 14, centro_y_slot1 + 8),
                ])
                desenhar_texto_multilinha(
                    tela, "comece pela base", fonte, (255, 230, 120),
                    ponta_seta_x + 18, centro_y_slot1 - 20, 75, espacamento=13,
                )

            centro_arrastando = None
            if peca_arrastando is not None:
                centro_arrastando = (arrasto_x + LARGURA_PECA // 2, arrasto_y + ALTURA_PECA // 2)

            for i in range(proxima_peca, PECAS_CORRETAS_TOTAL):
                py = TORRE_BASE_Y - (i + 1) * (ALTURA_PECA + 6)
                rect_espaco = pygame.Rect(TORRE_X, py, LARGURA_PECA, ALTURA_PECA)
                if i == proxima_peca:
                    sobre_alvo = (
                        centro_arrastando is not None
                        and rect_espaco.inflate(80, 80).collidepoint(centro_arrastando)
                    )
                    if sobre_alvo:
                        pygame.draw.rect(tela, (90, 230, 130), rect_espaco, width=4, border_radius=6)
                    else:
                        pulso = (math.sin(pygame.time.get_ticks() / 200) + 1) / 2
                        brilho = round(140 + pulso * 100)
                        pygame.draw.rect(tela, (brilho, brilho, 255), rect_espaco, width=3, border_radius=6)
                else:
                    pygame.draw.rect(tela, (80, 90, 110), rect_espaco, width=2, border_radius=6)

            legenda_bandeja = fonte.render("Pecas disponiveis:", True, (210, 210, 220))
            tela.blit(legenda_bandeja, (BANDEJA_X, BANDEJA_Y0 - 26))
            for indice_peca, rect in calcular_rects_bandeja():
                if indice_peca == peca_arrastando:
                    continue
                if rect.collidepoint(mouse_pos):
                    pygame.draw.rect(tela, (255, 255, 255), rect.inflate(6, 6), width=2, border_radius=8)
                desenhar_peca(tela, rect, PECAS_PROTOCOLO[indice_peca])

            ajuda = fonte.render("Esc para fechar", True, (150, 150, 160))
            tela.blit(ajuda, (PUZZLE_X + 45, PUZZLE_Y + PUZZLE_ALTURA - 30))

            if tempo_mensagem_puzzle > 0:
                msg = fonte.render(mensagem_puzzle, True, (255, 120, 120))
                tela.blit(msg, msg.get_rect(center=(PUZZLE_X + PUZZLE_LARGURA // 2, PUZZLE_Y + PUZZLE_ALTURA - 90)))
                tempo_mensagem_puzzle -= 1

            if peca_arrastando is not None:
                rect_arrasto = pygame.Rect(arrasto_x, arrasto_y, LARGURA_PECA, ALTURA_PECA)
                desenhar_peca(tela, rect_arrasto, PECAS_PROTOCOLO[peca_arrastando])

        # =========================================================================
        # === DESENHO: PAINEL DO PUZZLE DA URL (tela do computador) ===
        # =========================================================================
        if url_aberta:
            escurecido = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA), pygame.SRCALPHA)
            escurecido.fill((0, 0, 0, 160))
            tela.blit(escurecido, (0, 0))

            painel_url = pygame.Rect(URL_X, URL_Y, URL_LARGURA, URL_ALTURA)
            pygame.draw.rect(tela, (10, 22, 16), painel_url, border_radius=12)
            pygame.draw.rect(tela, (110, 255, 150), painel_url, width=3, border_radius=12)

            titulo_url = fonte_grande.render("Monte o endereco do site (URL)", True, (180, 255, 200))
            tela.blit(titulo_url, titulo_url.get_rect(center=(URL_X + URL_LARGURA // 2, URL_Y + 34)))

            pygame.draw.rect(tela, (240, 240, 240), BARRA_URL, border_radius=4)
            pygame.draw.rect(tela, (20, 20, 20), BARRA_URL, width=2, border_radius=4)
            texto_barra_url = "".join(PECAS_URL[i] for i in range(proxima_peca_url))
            tela.blit(fonte.render(texto_barra_url, True, (20, 20, 20)), (BARRA_URL.x + 8, BARRA_URL.y + 12))

            legenda_url = fonte.render("Clique nos pedacos, na ordem certa:", True, (200, 230, 210))
            tela.blit(legenda_url, (BANDEJA_URL_X, BANDEJA_URL_Y0 - 26))
            for indice_peca, rect in calcular_rects_bandeja_url():
                if rect.collidepoint(mouse_pos):
                    pygame.draw.rect(tela, (255, 255, 255), rect.inflate(6, 6), width=2, border_radius=8)
                pygame.draw.rect(tela, (70, 150, 100), rect, border_radius=6)
                pygame.draw.rect(tela, (15, 30, 20), rect, width=2, border_radius=6)
                rotulo_peca_url = fonte.render(PECAS_URL[indice_peca], True, (255, 255, 255))
                tela.blit(rotulo_peca_url, rotulo_peca_url.get_rect(center=rect.center))

            if erros_url >= 1:
                desenhar_texto_multilinha(
                    tela, "Dica: https:// -> www. -> museu -> .com",
                    fonte, (255, 230, 120), URL_X + 40, URL_Y + URL_ALTURA - 60, URL_LARGURA - 80,
                )

            ajuda_url = fonte.render("Esc para fechar", True, (150, 170, 160))
            tela.blit(ajuda_url, (URL_X + 40, URL_Y + URL_ALTURA - 30))

            if tempo_mensagem_url > 0:
                msg_url = fonte.render(mensagem_url, True, (255, 120, 120))
                tela.blit(msg_url, msg_url.get_rect(center=(URL_X + URL_LARGURA // 2, URL_Y + URL_ALTURA - 90)))
                tempo_mensagem_url -= 1

        # =========================================================================
        # === DESENHO: CHATBOT TIM (caixinha de conversa) ===
        # =========================================================================
        if caixa_tim_aberta:
            caixa_x = MARGEM_CAIXA_TIM
            caixa_y = ALTURA_JANELA - CAIXA_TIM_ALTURA - MARGEM_CAIXA_TIM

            pygame.draw.rect(tela, (245, 245, 220), (caixa_x, caixa_y, CAIXA_TIM_LARGURA, CAIXA_TIM_ALTURA))
            pygame.draw.rect(tela, (0, 0, 0), (caixa_x, caixa_y, CAIXA_TIM_LARGURA, CAIXA_TIM_ALTURA), 3)

            avatar_x = caixa_x + CAIXA_TIM_LARGURA // 2 - TAMANHO_AVATAR_TIM // 2
            avatar_y = caixa_y - TAMANHO_AVATAR_TIM + 15
            tela.blit(imagem_tim_avatar, (avatar_x, avatar_y))

            desenhar_texto_multilinha(tela, "Tim Berners-Lee", fonte, (0, 0, 0), caixa_x + 15, caixa_y + 10, LARGURA_TEXTO_CAIXA_TIM)

            if etapa_conversa_tim == ETAPA_APRESENTACAO:
                fala_tim = FALA_TIM_APRESENTACAO
            elif etapa_conversa_tim == ETAPA_DICA:
                fala_tim = FALA_TIM_DICA
            elif tim_pensando:
                fala_tim = "Tim esta pensando..."
            else:
                fala_tim = resposta_tim or FALA_TIM_CONVITE_LIVRE

            desenhar_texto_multilinha(tela, fala_tim, fonte, (0, 0, 0), caixa_x + 15, caixa_y + 32, LARGURA_TEXTO_CAIXA_TIM)

            if etapa_conversa_tim in (ETAPA_APRESENTACAO, ETAPA_LIVRE):
                campo_y = caixa_y + CAIXA_TIM_ALTURA - 70
                pygame.draw.rect(tela, (255, 255, 255), (caixa_x + 15, campo_y, LARGURA_TEXTO_CAIXA_TIM, 22))
                tela.blit(fonte.render(texto_digitado_tim, True, (0, 0, 0)), (caixa_x + 19, campo_y + 5))

            if etapa_conversa_tim == ETAPA_APRESENTACAO:
                ajuda_tim = "Digite sua resposta e pressione Enter"
            elif etapa_conversa_tim == ETAPA_DICA:
                ajuda_tim = "Pressione Enter para continuar"
            else:
                ajuda_tim = "Enter para perguntar, Esc para fechar"
            desenhar_texto_multilinha(tela, ajuda_tim, fonte, (80, 80, 80), caixa_x + 15, caixa_y + CAIXA_TIM_ALTURA - 40, LARGURA_TEXTO_CAIXA_TIM)

        # =========================================================================
        # === DESENHO: MENU DE CONFIGURAÇÕES ===
        # =========================================================================
        if menu_aberto:
            escurecido = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA), pygame.SRCALPHA)
            escurecido.fill((0, 0, 0, 150))
            tela.blit(escurecido, (0, 0))

            painel_menu = pygame.Rect(MENU_POS_X, MENU_POS_Y, MENU_LARGURA, MENU_ALTURA)
            pygame.draw.rect(tela, (90, 60, 35), painel_menu, border_radius=16)
            pygame.draw.rect(tela, (55, 35, 18), painel_menu, width=5, border_radius=16)

            desenhar_texto_com_contorno(tela, "MENU", fonte_grande, COR_TEXTO_MENU, (60, 30, 10), MENU_CENTRO_X, MENU_POS_Y + 50)

            pygame.draw.rect(tela, COR_BOTAO_MENU, BOTAO_PAUSA, border_radius=8)
            pygame.draw.rect(tela, COR_BORDA_BOTAO_MENU, BOTAO_PAUSA, width=2, border_radius=8)
            desenhar_icone_pausa_play(tela, BOTAO_PAUSA, pausado_manual, COR_TEXTO_MENU)

            rotulo_volume = fonte.render("Volume da musica", True, COR_TEXTO_MENU)
            tela.blit(rotulo_volume, (MENU_CENTRO_X - rotulo_volume.get_width() // 2, MENU_POS_Y + 165))

            for botao, rotulo in ((BOTAO_VOLUME_MENOS, "-"), (BOTAO_VOLUME_MAIS, "+")):
                pygame.draw.rect(tela, COR_BOTAO_MENU, botao, border_radius=6)
                pygame.draw.rect(tela, COR_BORDA_BOTAO_MENU, botao, width=2, border_radius=6)
                t = fonte_grande.render(rotulo, True, COR_TEXTO_MENU)
                tela.blit(t, t.get_rect(center=botao.center))

            porcentagem = fonte.render(f"{round(volume_musica * 100)}%", True, COR_TEXTO_MENU)
            tela.blit(porcentagem, porcentagem.get_rect(center=(MENU_CENTRO_X, BOTAO_VOLUME_MENOS.centery)))

            for botao, rotulo in ((BOTAO_CONTINUAR, "Continuar (Esc)"), (BOTAO_SAIR, "Sair")):
                pygame.draw.rect(tela, COR_BOTAO_MENU, botao, border_radius=8)
                pygame.draw.rect(tela, COR_BORDA_BOTAO_MENU, botao, width=2, border_radius=8)
                t = fonte.render(rotulo, True, COR_TEXTO_MENU)
                tela.blit(t, t.get_rect(center=botao.center))

            if pausado_manual:
                desenhar_texto_com_contorno(tela, "PAUSADO", fonte_pausado, (255, 90, 90), (40, 0, 0), LARGURA_JANELA // 2, ALTURA_JANELA // 2)

        # =========================================================================
        # === DESENHO: TELA FINAL (voltou ao presente = fim do jogo) ===
        # Por ser a última fase, é uma tela de encerramento por cima de tudo.
        # Pressionar Esc aqui CONFIRMA a vitória e devolve o controle pro menu
        # (diferente de um Esc "normal", que só sairia sem concluir).
        # =========================================================================
        if chegou_no_portal:
            fim = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA), pygame.SRCALPHA)
            fim.fill((5, 8, 20, 235))
            tela.blit(fim, (0, 0))

            pulso = (math.sin(pygame.time.get_ticks() / 300) + 1) / 2
            cor_titulo = (120 + round(pulso * 120), 200 + round(pulso * 40), 255)
            desenhar_texto_com_contorno(
                tela, "VOCE VOLTOU AO PRESENTE!", fonte_vitoria, cor_titulo, (0, 0, 0),
                LARGURA_JANELA // 2, ALTURA_JANELA // 2 - 60,
            )
            desenhar_texto_multilinha(
                tela, "Voce atravessou toda a historia da computacao e concluiu a Fuga do Passado.",
                fonte_grande, (230, 230, 240),
                120, ALTURA_JANELA // 2 - 10, LARGURA_JANELA - 240, espacamento=28,
            )
            creditos = fonte.render("Obrigado por jogar! (Esc para sair)", True, (180, 180, 200))
            tela.blit(creditos, (LARGURA_JANELA // 2 - creditos.get_width() // 2, ALTURA_JANELA - 70))

            # Na tela final, Esc confirma a vitória e encerra o loop --
            # devolvendo "vitoria" pro menu (ver o final desta função).
            teclas_fim = pygame.key.get_pressed()
            if teclas_fim[pygame.K_ESCAPE]:
                vitoria_alcancada = True
                rodando = False

        pygame.display.flip()

    # Sai da fase por qualquer caminho -- para a música de fundo e qualquer
    # efeito ainda tocando, pra nada da Fase 10 vazar pro menu (mesmo motivo
    # de audio_fase2.parar_tudo()/audio_fase9.parar_tudo() nas outras fases).
    try:
        pygame.mixer.music.stop()
    except pygame.error:
        pass

    if vitoria_alcancada:
        # Esta fase não tem cronômetro -- sempre 1 estrela por completar
        # (ver o comentário de PROGRESSO_CHAVE_FASE lá em cima). "tempo" é
        # só informativo (quanto tempo real desde que entrou na fase).
        tempo_gasto_segundos = (pygame.time.get_ticks() - ticks_inicio_fase10) / 1000
        _salvar_progresso(1, _formatar_tempo(tempo_gasto_segundos))

    if saiu_por_fechar_janela:
        # Fechar a JANELA (não só sair da fase) continua encerrando o
        # programa inteiro -- mesmo comportamento de sempre desta fase,
        # igual ao que já acontece em Fase_4/fase4_final.py e
        # Fase_5/fase_5_atualizada.py, fora do que dá pra controlar daqui.
        pygame.quit()
        sys.exit()

    return "vitoria" if vitoria_alcancada else None


def run_padrao():
    """Roda a Fase 10 isolada, fora do menu geral, com o Personagem 1 como
    opção padrão (genero="m") -- útil para testar esta fase sozinha
    (ex: `python fase_10.py`) sem precisar abrir o jogo completo nem passar
    por nenhum menu."""
    return Jogo(character_name="Jogador", genero="m").executar()


# =====================================================================
# PONTO DE ENTRADA DO PROGRAMA (rodando este arquivo sozinho)
# =====================================================================
if __name__ == "__main__":
    run_padrao()

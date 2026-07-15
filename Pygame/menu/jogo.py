import json
import math
import os
import sys
import pygame

# menu/ é compartilhado por todas as fases (Pygame/menu/), então não tem como
# jogo.py adivinhar sozinho onde fica o pacote fase2/ de cada uma — isso
# depende de qual fase está te chamando. Quem roda o jogo (o main.py de
# dentro de Pygame/Fase_2/, por exemplo) já garante que o próprio diretório
# dele está no sys.path antes de importar este módulo, e é lá que mora o
# fase2/ daquela fase.
from fase2.fase2 import run as run_fase2

# Fase_9/, Fase_4/ e Fase_5/ (ao contrário de Fase_2/fase2/) não são
# pacotes Python -- não tem __init__.py, só um arquivo .py solto em cada
# pasta. Pra importar de lá sem mexer em nada dentro dessas pastas, cada
# uma tem sua própria pasta inserida no sys.path (e não Pygame/, que é o
# que Fase_2.py já garante) e o ponto de entrada é importado como módulo
# de topo, igual cada uma faria se rodasse standalone.
_PYGAME_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FASE4_DIR = os.path.join(_PYGAME_DIR, "Fase_4")
_FASE5_DIR = os.path.join(_PYGAME_DIR, "Fase_5")
_FASE9_DIR = os.path.join(_PYGAME_DIR, "Fase_9")

PROGRESSO_PATH = os.path.join(_PYGAME_DIR, "progresso.json")


def _carregar_progresso():
    """Lê Pygame/progresso.json (mesmo arquivo que fase2/puzzles/babbage_
    lovelace.py e Fase_9/puzzle_terminal.py escrevem). Devolve um
    dicionário vazio se o arquivo ainda não existir ou vier corrompido."""
    if not os.path.exists(PROGRESSO_PATH):
        return {}
    try:
        with open(PROGRESSO_PATH, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (json.JSONDecodeError, OSError):
        return {}


def _marcar_fase_completa(chave):
    """Fase_4/ e Fase_5/ ainda não têm nenhum sistema de progresso
    próprio (sem estrelas, tempo ou "completo" -- ao contrário de
    fase2/puzzles/babbage_lovelace.py e Fase_9/puzzle_terminal.py, que
    gravam isso sozinhas). Pra mesmo assim dar pra desbloquear a fase
    seguinte da sequência (ver Game._fase_desbloqueada), é O PRÓPRIO
    MENU que grava um "completo": true mínimo em progresso.json quando o
    jogador vence uma dessas fases -- só isso, sem mexer em nada dentro
    de Pygame/Fase_4/ ou Pygame/Fase_5/. Preserva estrelas/tempo se um
    dia essas fases passarem a gravar isso também."""
    progresso = _carregar_progresso()
    registro = dict(progresso.get(chave, {}))
    registro["completo"] = True
    progresso[chave] = registro
    with open(PROGRESSO_PATH, "w", encoding="utf-8") as arquivo:
        json.dump(progresso, arquivo, indent=2, ensure_ascii=False)


def _importar_ponto_de_entrada(diretorio, modulo_fase, *nomes_para_purgar):
    """Fase_4/, Fase_5/ e Fase_9/ importam módulos soltos com NOMES
    REPETIDOS entre si (ex: as três têm seu próprio npc_chatbot.py;
    Fase_4 e Fase_5 também têm cada uma o seu próprio inventario.py --
    com conteúdo diferente em cada pasta). Se o Python já tivesse
    carregado um desses nomes (de uma fase visitada antes nesta mesma
    sessão do menu), ele reaproveitaria pra sempre o módulo ERRADO em
    vez de carregar o da fase atual -- por isso cada fase só é importada
    na hora do clique (não lá no topo deste arquivo), e antes de
    importar, isso aqui remove esses nomes do cache (sys.modules) e põe
    a pasta desta fase na FRENTE do sys.path, garantindo que cada fase
    sempre pegue os seus próprios arquivos, não importa em que ordem o
    jogador visite o mapa."""
    for nome in nomes_para_purgar:
        sys.modules.pop(nome, None)
    sys.path.insert(0, diretorio)
    return __import__(modulo_fase, fromlist=["Jogo"])

pygame.init()

# WIDTH/HEIGHT continuam sendo o tamanho "virtual": todo o desenho e todas as
# coordenadas já calculadas no menu (retângulos de botões, mapa de fases,
# fontes, etc.) usam esse espaço, sem mudar nada. A janela real é menor
# (960x600, padrão decidido pelo grupo) — `screen` é uma Surface comum, não a
# tela de verdade; ela só é redimensionada e mostrada na janela real a cada
# frame, no fim de Game.run().
WIDTH, HEIGHT = 1000, 650
REAL_SIZE = (960, 600)
pygame.display.set_mode(REAL_SIZE)
pygame.display.set_caption("Escape.from_past()")
screen = pygame.Surface((WIDTH, HEIGHT))
clock = pygame.time.Clock()
FPS = 60

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
BACKGROUND_PATH = os.path.join(ASSETS_DIR, "background.jpeg")

# ---------------------------------------------------------------------------
# Música de fundo do menu (tela principal + mapa de fases) -- toca em loop
# assim que o menu abre e continua tocando por trás de main/options/phases;
# só é parada bem antes de entrar em qualquer fase (ver os pontos onde
# _parar_musica_menu()/_iniciar_musica_menu() são chamados em do_action),
# senão ela ficaria tocando por baixo da música/efeitos da fase (ou,
# no caso de Fase_4/Fase_5, que não têm música própria, tocando o jogo
# INTEIRO sem parar nunca).
# ---------------------------------------------------------------------------
MUSICA_MENU_PATH = os.path.join(ASSETS_DIR, "msc_menu.mp3")
VOLUME_MUSICA_MENU = 0.28  # ~28%, dentro da faixa 25-30% pedida


def _iniciar_musica_menu():
    """Toca MUSICA_MENU_PATH em loop contínuo (loops=-1) -- não faz nada
    se o arquivo não existir ou o mixer não estiver disponível (mesmo
    espírito defensivo de audio_fase2.iniciar_musica_fundo/audio_fase9.
    iniciar_musica_fundo: áudio nunca deve travar o jogo)."""
    if not os.path.isfile(MUSICA_MENU_PATH):
        return
    try:
        pygame.mixer.music.load(MUSICA_MENU_PATH)
        pygame.mixer.music.set_volume(VOLUME_MUSICA_MENU)
        pygame.mixer.music.play(loops=-1)
    except pygame.error:
        pass


def _parar_musica_menu():
    """Para a música de fundo do menu -- chamado antes de entrar em
    qualquer fase. pygame.mixer.music só toca UMA faixa por vez, então
    sem isso a música do menu tocaria por cima (ou, pras fases sem
    música própria, por baixo do jogo inteiro, sem nunca parar)."""
    try:
        pygame.mixer.music.stop()
    except pygame.error:
        pass

_bg_raw = pygame.image.load(BACKGROUND_PATH).convert()
BACKGROUND = pygame.transform.smoothscale(_bg_raw, (WIDTH, HEIGHT))

BACKGROUND_OVERLAY = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
BACKGROUND_OVERLAY.fill((5, 6, 14, 130))

PHASES_MAP_PATH = os.path.join(ASSETS_DIR, "phases_map.png")
_phases_raw = pygame.image.load(PHASES_MAP_PATH).convert()
PHASES_ORIG_SIZE = _phases_raw.get_size()  # (1536, 1024)
PHASES_BG = pygame.transform.smoothscale(_phases_raw, (WIDTH, HEIGHT))


def _scale_rect(x, y, w, h):
    sx = WIDTH / PHASES_ORIG_SIZE[0]
    sy = HEIGHT / PHASES_ORIG_SIZE[1]
    return pygame.Rect(int(x * sx), int(y * sy), int(w * sx), int(h * sy))


# Retângulos clicáveis calculados a partir da posição de cada elemento na
# imagem original (1536x1024) e escalados para o tamanho real da janela.
PHASES_BACK_RECT = _scale_rect(10, 15, 220, 85)
PHASES_SETTINGS_RECT = _scale_rect(1415, 5, 110, 95)

_PHASE_COL_CENTERS = [260, 515, 770, 1025, 1280]
_ROW1_Y, _ROW1_H = 150, 375
_ROW2_Y, _ROW2_H = 545, 350
_PHASE_RECT_W = 250

PHASE_RECTS = []
for _i in range(10):
    _col = _i % 5
    _row = _i // 5
    _cx = _PHASE_COL_CENTERS[_col]
    _y_top, _h = (_ROW1_Y, _ROW1_H) if _row == 0 else (_ROW2_Y, _ROW2_H)
    PHASE_RECTS.append(_scale_rect(_cx - _PHASE_RECT_W // 2, _y_top, _PHASE_RECT_W, _h))


def _scale_point(x, y):
    sx = WIDTH / PHASES_ORIG_SIZE[0]
    sy = HEIGHT / PHASES_ORIG_SIZE[1]
    return (x * sx, y * sy)


def _scale_len(v, eixo="x"):
    if eixo == "x":
        return v * WIDTH / PHASES_ORIG_SIZE[0]
    return v * HEIGHT / PHASES_ORIG_SIZE[1]


# ---------------------------------------------------------------------------
# Progresso no mapa de fases -- estrelas douradas, tempo real e o contador
# "X/30" do canto superior direito, sobrepostos por cima dos campos que a
# própria arte de phases_map.png já desenha vazios (estrela cinza/contorno,
# "tempo: --:--", "0/30"). Posições medidas diretamente na imagem original
# (1536x1024, ver PHASES_ORIG_SIZE) -- cada fase tem o centro das 3 estrelas
# e o retângulo do placeholder "--:--" que fica logo abaixo delas.
# ---------------------------------------------------------------------------
GOLD = (212, 168, 67)

PHASE_STAR_CENTERS = {
    0: [(206, 285.5), (247.5, 285.5), (289.5, 285.5)],
    1: [(472, 285), (512, 285), (552.5, 285)],
    2: [(722, 284.5), (762, 284.5), (801.5, 284.5)],
    3: [(984, 284.5), (1024, 284.5), (1064, 284.5)],
    4: [(1235.5, 294.5), (1275, 294.5), (1314.5, 294.5)],
    5: [(225.5, 661.5), (265, 661.5), (305.5, 661.5)],
    6: [(482.5, 664), (522, 663.5), (563, 664)],
    7: [(734, 661.5), (774, 661.5), (814.5, 661.5)],
    8: [(977, 664.5), (1021.5, 664.5), (1062, 664.5)],
    9: [(1236, 663), (1275.5, 663), (1316, 663)],
}
PHASE_STAR_RAIO = 14  # na escala original da imagem

# Retângulo (x0, x1, y0, y1), na escala original, do "--:--" de cada fase --
# onde o tempo real é desenhado por cima quando a fase tem progresso salvo.
PHASE_TEMPO_RECT = {
    0: (255, 299, 310, 327),
    1: (519, 563, 310, 327),
    2: (769, 813, 309, 326),
    3: (1031, 1074, 309, 326),
    4: (1282, 1326, 319, 336),
    5: (272, 316, 686, 703),
    6: (530, 574, 689, 706),
    7: (781, 825, 686, 703),
    8: (1028, 1073, 689, 706),
    9: (1282, 1327, 688, 705),
}

# Retângulo do "0/30" no canto superior direito, na escala original --
# substituído pelo total real de estrelas conquistadas (o "/30", 10 fases x
# 3 estrelas, é fixo).
COUNTER_TEXT_RECT = (1275, 1336, 43, 62)

_CARD_BG_PATCH = (2, 4, 30)
_COUNTER_BG_PATCH = (2, 2, 18)

_FONT_TEMPO_PROGRESSO = pygame.font.SysFont("consolas", 13, bold=True)
_FONT_COUNTER_PROGRESSO = pygame.font.SysFont("consolas", 18, bold=True)


def _pontos_estrela(centro, raio_externo, raio_interno):
    """Devolve os 10 vértices (alternando raio externo/interno, a cada
    36°) de uma estrela de 5 pontas centrada em `centro`, com uma ponta
    voltada pra cima. Mesma fórmula usada em fase2._pontos_estrela e
    Fase_9/fase9._pontos_estrela, copiada aqui pelo mesmo motivo (módulo
    autocontido, sem importar de dentro de uma fase específica)."""
    pontos = []
    angulo_inicial = -math.pi / 2
    for i in range(10):
        angulo = angulo_inicial + i * math.pi / 5
        raio = raio_externo if i % 2 == 0 else raio_interno
        pontos.append((centro[0] + raio * math.cos(angulo), centro[1] + raio * math.sin(angulo)))
    return pontos


def desenhar_progresso_fases(surface, progresso):
    """Sobrepõe o progresso salvo (Pygame/progresso.json) em cima da arte
    do mapa de fases: estrelas douradas nos espaços já conquistados (as
    não conquistadas ficam como a arte já desenha, cinza -- não precisa
    tocar nelas), o tempo real no lugar do "tempo: --:--" de cada fase, e
    o total de estrelas no contador do canto superior direito. Uma fase
    sem entrada em `progresso` mantém os campos vazios da arte, sem
    nenhum desenho extra."""
    total_estrelas = 0
    for index in range(10):
        dados = progresso.get(f"fase_{index + 1}")
        if not dados:
            continue
        estrelas = dados.get("estrelas", 0)
        total_estrelas += estrelas

        raio = _scale_len(PHASE_STAR_RAIO)
        for i in range(min(estrelas, 3)):
            centro = _scale_point(*PHASE_STAR_CENTERS[index][i])
            pontos = _pontos_estrela(centro, raio, raio * 0.42)
            pygame.draw.polygon(surface, GOLD, pontos)
            pygame.draw.polygon(surface, (120, 90, 30), pontos, width=2)

        tempo = dados.get("tempo")
        if tempo:
            x0, x1, y0, y1 = PHASE_TEMPO_RECT[index]
            px0, py0 = _scale_point(x0, y0)
            px1, py1 = _scale_point(x1, y1)
            patch_rect = pygame.Rect(int(px0), int(py0), max(1, int(px1 - px0)), max(1, int(py1 - py0)))
            pygame.draw.rect(surface, _CARD_BG_PATCH, patch_rect)
            texto_surf = _FONT_TEMPO_PROGRESSO.render(tempo, True, (225, 225, 232))
            surface.blit(texto_surf, texto_surf.get_rect(center=patch_rect.center))

    x0, x1, y0, y1 = COUNTER_TEXT_RECT
    px0, py0 = _scale_point(x0, y0)
    px1, py1 = _scale_point(x1, y1)
    counter_rect = pygame.Rect(int(px0), int(py0), max(1, int(px1 - px0)), max(1, int(py1 - py0)))
    pygame.draw.rect(surface, _COUNTER_BG_PATCH, counter_rect)
    counter_surf = _FONT_COUNTER_PROGRESSO.render(f"{total_estrelas}/30", True, (140, 160, 235))
    surface.blit(counter_surf, counter_surf.get_rect(center=counter_rect.center))


_CHARACTER_IMAGE_FILES = {0: "personagem_parado.png", 1: "personagem_parada.png"}
_CHARACTER_BOX_HEIGHT = 165
CHARACTER_IMAGES = {}
for _idx, _fname in _CHARACTER_IMAGE_FILES.items():
    _raw_char = pygame.image.load(os.path.join(ASSETS_DIR, _fname)).convert_alpha()
    _scale_char = (_CHARACTER_BOX_HEIGHT - 15) / _raw_char.get_height()
    CHARACTER_IMAGES[_idx] = pygame.transform.smoothscale(
        _raw_char,
        (int(_raw_char.get_width() * _scale_char), int(_raw_char.get_height() * _scale_char)),
    )

# --- Paleta (tema terminal/rede, igual ao mockup) ---
BG_COLOR = (8, 10, 22)
PANEL_BORDER = (60, 90, 255)
GREEN = (0, 255, 140)
GREEN_DIM = (0, 140, 90)
RED = (255, 60, 60)
WHITE = (225, 230, 235)
DARK_PANEL = (16, 20, 38)
HOVER_BG = (18, 42, 40)

FONT_TITLE = pygame.font.SysFont("consolas", 40, bold=True)
FONT_BIG = pygame.font.SysFont("consolas", 28, bold=True)
FONT_MED = pygame.font.SysFont("consolas", 22, bold=True)
FONT_SMALL = pygame.font.SysFont("consolas", 16)

CX = WIDTH // 2

# --- Textos (apenas Português) ---
TEXTS = {
    "title_main": "Escape.from_past()",
    "subtitle_main": "ENCONTRE O CÓDIGO PARA ESCAPAR",
    "btn_new_game": "JOGAR",
    "btn_options": "OPÇÕES",
    "btn_exit": "SAIR",
    "title_options": "OPÇÕES",
    "btn_volume": "VOLUME DO JOGO",
    "btn_characters": "PERSONAGENS",
    "btn_controls": "CONTROLES",
    "btn_back": "VOLTAR",
    "title_volume": "VOLUME DO JOGO",
    "volume_hint": "Use as setas ESQUERDA/DIREITA ou arraste com o mouse",
    "title_characters": "PERSONAGENS",
    "characters_hint": "Use as setas ou clique em < / >",
    "character_placeholder": "imagem em breve",
    "char_1": "Hacker Verde",
    "char_2": "Analista de Redes",
    "btn_rename": "RENOMEAR",
    "btn_confirm": "CONFIRMAR",
    "btn_cancel": "CANCELAR",
    "rename_hint": "Digite o novo nome e pressione ENTER",
    "title_controls": "CONTROLES",
}

# Cada tecla de movimento com a ação exata que ela executa no jogo.
WASD_KEYS = [("W", "cima"), ("A", "esquerda"), ("S", "baixo"), ("D", "direita")]

# Linhas de controle além do WASD: (rótulo da tecla/ação, descrição explícita).
CONTROL_ROWS = [
    ("SETAS", "fazem o mesmo movimento que W A S D"),
    ("CLIQUE\nDO MOUSE", "move o personagem até o local clicado na tela"),
    ("ESC", "sai da fase e volta para o mapa de fases"),
]


class Button:
    def __init__(self, rect, text, action, font=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.font = font or FONT_MED
        self.hovered = False

    def draw(self, surface, selected=False):
        active = self.hovered or selected
        border_color = GREEN if active else GREEN_DIM
        bg_color = HOVER_BG if active else DARK_PANEL
        text_color = GREEN if active else WHITE

        pygame.draw.rect(surface, bg_color, self.rect, border_radius=6)
        pygame.draw.rect(surface, border_color, self.rect, width=2, border_radius=6)

        txt_surf = self.font.render(self.text, True, text_color)
        surface.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))

    def update_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def clicked(self, pos, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(pos)
        )


class GlowButton(Button):
    """Botão invisível: não desenha texto/fundo, só uma borda verde ao passar
    o mouse ou selecionar pelo teclado. Usado sobre a arte do mapa de fases."""

    def draw(self, surface, selected=False):
        if self.hovered or selected:
            pygame.draw.rect(surface, GREEN, self.rect, width=3, border_radius=10)


class Game:
    def __init__(self):
        self.running = True
        self.state = "main"
        self.selected_index = 0

        # --- Dados de opções ---
        self.volume = 70
        self.dragging_volume = False
        self.slider_rect = pygame.Rect(CX - 200, 333, 400, 14)

        self.personagem_keys = ["char_1", "char_2"]
        self.personagem_index = 0
        self.personagem_overrides = [None] * len(self.personagem_keys)
        self.editing_name = False
        self.name_input_buffer = ""

        self.blink_timer = 0
        self.blink_visible = True

        # Quantidade de fases já desbloqueadas (a Fase 1 sempre começa aberta).
        # TODO: quando a Fase 1 tiver conteúdo e progressão real, isso deve
        # voltar a ser 1 e o avanço deve ser incrementado ao concluir cada fase.
        self.unlocked_phases = 2

        # Para onde o VOLTAR das Opções deve retornar (main ou phases).
        self.options_return_to = "main"

        # Progresso lido de Pygame/progresso.json (estrelas/tempo por fase)
        # -- recarregado sempre que o mapa de fases é (re)construído, ver
        # build_buttons(), pra já aparecer atualizado assim que o jogador
        # volta de uma fase recém-concluída.
        self.progresso = {}

        self.buttons = []
        self.build_buttons()

        # Música de fundo do menu -- começa a tocar assim que o jogo abre
        # (tela principal) e continua até o jogador entrar numa fase (ver
        # do_action, onde é parada/retomada em volta de cada chamada de
        # fase).
        _iniciar_musica_menu()

    # ---------- textos ----------
    def t(self, key):
        return TEXTS[key]

    def get_personagem_name(self, index):
        override = self.personagem_overrides[index]
        if override:
            return override
        return self.t(self.personagem_keys[index])

    # ---------- construção das telas ----------
    def build_buttons(self):
        self.buttons = []
        self.selected_index = 0

        if self.state == "main":
            labels = [
                (self.t("btn_new_game"), "start_game"),
                (self.t("btn_options"), "goto_options"),
                (self.t("btn_exit"), "quit_game"),
            ]
            y = 300
            for text, action in labels:
                self.buttons.append(Button((CX - 160, y, 320, 55), text, action))
                y += 75

        elif self.state == "options":
            labels = [
                (self.t("btn_volume"), "goto_volume"),
                (self.t("btn_characters"), "goto_personagens"),
                (self.t("btn_controls"), "goto_controles"),
                (self.t("btn_back"), "options_back"),
            ]
            y = 240
            for text, action in labels:
                self.buttons.append(Button((CX - 180, y, 360, 55), text, action))
                y += 75

        elif self.state == "volume":
            self.buttons.append(Button((CX - 200, 520, 400, 50), self.t("btn_back"), "goto_options"))

        elif self.state == "controles":
            self.buttons.append(Button((CX - 200, 560, 400, 50), self.t("btn_back"), "goto_options"))

        elif self.state == "personagens":
            if self.editing_name:
                self.buttons.append(
                    Button((CX - 200, 570, 190, 50), self.t("btn_confirm"), "confirm_rename")
                )
                self.buttons.append(
                    Button((CX + 10, 570, 190, 50), self.t("btn_cancel"), "cancel_rename")
                )
            else:
                self.buttons.append(Button((CX - 230, 342, 60, 50), "<", "personagem_prev"))
                self.buttons.append(Button((CX + 170, 342, 60, 50), ">", "personagem_next"))
                self.buttons.append(
                    Button((CX - 200, 510, 400, 50), self.t("btn_rename"), "toggle_rename")
                )
                self.buttons.append(Button((CX - 200, 570, 400, 50), self.t("btn_back"), "goto_options"))

        elif self.state == "phases":
            self.progresso = _carregar_progresso()
            self.buttons.append(GlowButton(PHASES_BACK_RECT, "", "goto_main"))
            self.buttons.append(GlowButton(PHASES_SETTINGS_RECT, "", "goto_options_from_phases"))
            for i in range(10):
                if self._fase_desbloqueada(i):
                    self.buttons.append(GlowButton(PHASE_RECTS[i], "", f"start_phase_{i}"))

    # Mapeia o índice (0-based) de cada fase fora da ordem normal pra
    # chave, em progresso.json, da fase da qual ela depende -- usado por
    # _fase_desbloqueada(). Fase 4 (index 3) e Fase 9 (index 8) libera
    # com a Fase 2 completa, já que as fases 3 e 6-8 ainda não existem;
    # Fase 5 (index 4) já segue a ordem normal, depende só da Fase 4.
    _DEPENDENCIA_DESBLOQUEIO = {3: "fase_2", 4: "fase_4", 8: "fase_2"}

    def _fase_desbloqueada(self, index):
        """Além do avanço sequencial normal (unlocked_phases), algumas
        fases aqui liberam pulando direto pra dependência real (ver
        _DEPENDENCIA_DESBLOQUEIO acima), porque as fases intermediárias
        ainda não existem."""
        if index < self.unlocked_phases:
            return True
        dependencia = self._DEPENDENCIA_DESBLOQUEIO.get(index)
        if dependencia is None:
            return False
        progresso = _carregar_progresso()
        return bool(progresso.get(dependencia, {}).get("completo"))

    # ---------- ações ----------
    def do_action(self, action):
        if action == "start_game":
            self.state = "phases"
            self.build_buttons()
        elif action.startswith("start_phase_"):
            index = int(action.rsplit("_", 1)[-1])
            if self._fase_desbloqueada(index):
                # Música do menu para ANTES de entrar em qualquer fase --
                # pygame.mixer.music só toca uma faixa por vez, então uma
                # fase com música própria (Fase 2/9) já a substituiria,
                # mas Fase_4/Fase_5 não tocam nada, e sem isso a música do
                # menu ficaria tocando por baixo delas o jogo inteiro.
                _parar_musica_menu()
                if index == 1:
                    completed = run_fase2(
                        screen,
                        clock,
                        character_image=CHARACTER_IMAGES.get(self.personagem_index),
                        character_name=self.get_personagem_name(self.personagem_index),
                        genero="m" if self.personagem_index == 0 else "f",
                    )
                    if completed:
                        self.unlocked_phases = max(self.unlocked_phases, 3)
                    _iniciar_musica_menu()
                    self.build_buttons()
                elif index == 8:
                    # fase9 (módulo importado só agora, ver
                    # _importar_ponto_de_entrada acima) não devolve
                    # True/False e cria sua própria pygame.display.set_mode
                    # (mesmo tamanho de REAL_SIZE, então não quebra a janela
                    # do menu) -- por isso, diferente da Fase 2, é este
                    # bloco que tem que parar a música e restaurar o título
                    # da janela ao voltar, já que a Fase_9 não se limpa
                    # sozinha (ver Pygame/Fase_9/fase9.py, Jogo.executar).
                    fase9 = _importar_ponto_de_entrada(_FASE9_DIR, "fase9", "npc_chatbot")
                    fase9.Jogo(
                        character_image=CHARACTER_IMAGES.get(self.personagem_index),
                        character_name=self.get_personagem_name(self.personagem_index),
                        genero="m" if self.personagem_index == 0 else "f",
                    ).executar()
                    _importar_ponto_de_entrada(_FASE9_DIR, "audio_fase9").parar_tudo()
                    pygame.display.set_caption("Escape.from_past()")
                    _iniciar_musica_menu()
                    self.build_buttons()
                elif index in (3, 4):
                    # Fase_4/fase4_atual.py e Fase_5/fase_5.py: mesmo
                    # padrão de import tardio da Fase 9 (ver
                    # _importar_ponto_de_entrada) -- as duas pastas têm
                    # cada uma seu próprio npc_chatbot.py/inventario.py,
                    # com o MESMO nome de módulo (mas conteúdo diferente)
                    # que os da Fase 9, daí o cuidado de só importar na
                    # hora do clique e limpar o cache antes.
                    #
                    # As duas já aceitam character_image/character_name/
                    # genero (mesmo formato que Fase 2/9) e escolhem o
                    # sprite certo sozinhas a partir do `genero` -- assim
                    # o personagem escolhido aqui no menu continua o
                    # mesmo em qualquer fase, não só nessas duas.
                    # Nenhuma das duas toca música/efeito nenhum (sem
                    # módulo de áudio próprio, nada pra parar aqui).
                    #
                    # Jogo.executar() delas só devolve algo (a string
                    # "vitoria") quando o jogador vence e clica no botão
                    # da tela de vitória; se ele fechar a janela (evento
                    # QUIT) em qualquer outro momento, o laço delas mesmo
                    # chama pygame.quit()/sys.exit() e encerra o programa
                    # INTEIRO, não só a fase -- isso já é assim no código
                    # delas (Pygame/Fase_4/fase4_atual.py e
                    # Pygame/Fase_5/fase_5.py), fora do que dá pra
                    # controlar daqui do menu.
                    if index == 3:
                        modulo = _importar_ponto_de_entrada(
                            _FASE4_DIR, "fase4_atual", "npc_chatbot", "inventario"
                        )
                        chave_progresso = "fase_4"
                    else:
                        modulo = _importar_ponto_de_entrada(
                            _FASE5_DIR, "fase_5", "npc_chatbot", "inventario"
                        )
                        chave_progresso = "fase_5"

                    resultado = modulo.Jogo(
                        character_image=CHARACTER_IMAGES.get(self.personagem_index),
                        character_name=self.get_personagem_name(self.personagem_index),
                        genero="m" if self.personagem_index == 0 else "f",
                    ).executar()
                    if resultado == "vitoria":
                        _marcar_fase_completa(chave_progresso)
                    pygame.display.set_caption("Escape.from_past()")
                    _iniciar_musica_menu()
                    self.build_buttons()
                else:
                    # TODO: conectar aqui a lógica real das demais fases.
                    print(f"Iniciando Fase {index + 1}...")
        elif action == "goto_options":
            self.options_return_to = "main"
            self.state = "options"
            self.build_buttons()
        elif action == "goto_options_from_phases":
            self.options_return_to = "phases"
            self.state = "options"
            self.build_buttons()
        elif action == "options_back":
            self.state = self.options_return_to
            self.build_buttons()
        elif action == "goto_main":
            self.state = "main"
            self.build_buttons()
        elif action == "goto_volume":
            self.state = "volume"
            self.build_buttons()
        elif action == "goto_personagens":
            self.state = "personagens"
            self.build_buttons()
        elif action == "goto_controles":
            self.state = "controles"
            self.build_buttons()
        elif action == "quit_game":
            self.running = False
        elif action == "personagem_prev":
            self.personagem_index = (self.personagem_index - 1) % len(self.personagem_keys)
        elif action == "personagem_next":
            self.personagem_index = (self.personagem_index + 1) % len(self.personagem_keys)
        elif action == "toggle_rename":
            self.editing_name = True
            self.name_input_buffer = self.get_personagem_name(self.personagem_index)
            pygame.key.start_text_input()
            self.build_buttons()
        elif action == "confirm_rename":
            new_name = self.name_input_buffer.strip()
            self.personagem_overrides[self.personagem_index] = new_name or None
            self.editing_name = False
            pygame.key.stop_text_input()
            self.build_buttons()
        elif action == "cancel_rename":
            self.editing_name = False
            pygame.key.stop_text_input()
            self.build_buttons()

    def set_volume_from_mouse(self, x):
        rel = (x - self.slider_rect.x) / self.slider_rect.width
        self.volume = int(max(0.0, min(1.0, rel)) * 100)

    # ---------- loop principal ----------
    def run(self):
        while self.running:
            real_screen = pygame.display.get_surface()
            real_w, real_h = real_screen.get_size()
            raw_mouse = pygame.mouse.get_pos()
            # converte de volta pras coordenadas da tela virtual (WIDTHxHEIGHT)
            # antes de checar qualquer colisão de botão/slider.
            mouse_pos = (raw_mouse[0] * WIDTH / real_w, raw_mouse[1] * HEIGHT / real_h)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)

                elif event.type == pygame.TEXTINPUT and self.editing_name:
                    if len(self.name_input_buffer) < 24:
                        self.name_input_buffer += event.text

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "volume" and self.slider_rect.collidepoint(mouse_pos):
                        self.dragging_volume = True
                        self.set_volume_from_mouse(mouse_pos[0])
                    for i, btn in enumerate(self.buttons):
                        if btn.clicked(mouse_pos, event):
                            self.selected_index = i
                            self.do_action(btn.action)
                            break

                elif event.type == pygame.MOUSEBUTTONUP:
                    self.dragging_volume = False

                elif event.type == pygame.MOUSEMOTION and self.dragging_volume:
                    self.set_volume_from_mouse(mouse_pos[0])

            for btn in self.buttons:
                btn.update_hover(mouse_pos)

            self.blink_timer += clock.get_time()
            if self.blink_timer >= 500:
                self.blink_timer = 0
                self.blink_visible = not self.blink_visible

            self.draw()
            clock.tick(FPS)
            # redimensiona a tela virtual (WIDTHxHEIGHT) pro tamanho real da
            # janela (REAL_SIZE) só na hora de mostrar -- nenhuma coordenada
            # de desenho precisa mudar.
            scaled = pygame.transform.smoothscale(screen, (real_w, real_h))
            real_screen.blit(scaled, (0, 0))
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def handle_key(self, key):
        if self.editing_name:
            if key == pygame.K_RETURN:
                self.do_action("confirm_rename")
            elif key == pygame.K_ESCAPE:
                self.do_action("cancel_rename")
            elif key == pygame.K_BACKSPACE:
                self.name_input_buffer = self.name_input_buffer[:-1]
            return

        if key == pygame.K_ESCAPE:
            if self.state == "main":
                self.running = False
            elif self.state in ("volume", "personagens", "controles"):
                self.state = "options"
                self.build_buttons()
            elif self.state == "options":
                self.state = self.options_return_to
                self.build_buttons()
            elif self.state == "phases":
                self.state = "main"
                self.build_buttons()
            return

        if key in (pygame.K_UP, pygame.K_w) and self.buttons:
            self.selected_index = (self.selected_index - 1) % len(self.buttons)
        elif key in (pygame.K_DOWN, pygame.K_s) and self.buttons:
            self.selected_index = (self.selected_index + 1) % len(self.buttons)
        elif key == pygame.K_RETURN and self.buttons:
            self.do_action(self.buttons[self.selected_index].action)
        elif key == pygame.K_LEFT:
            if self.state == "volume":
                self.volume = max(0, self.volume - 5)
            elif self.state == "personagens":
                self.do_action("personagem_prev")
        elif key == pygame.K_RIGHT:
            if self.state == "volume":
                self.volume = min(100, self.volume + 5)
            elif self.state == "personagens":
                self.do_action("personagem_next")

    # ---------- desenho ----------
    def draw(self):
        if self.state == "phases":
            screen.blit(PHASES_BG, (0, 0))
            desenhar_progresso_fases(screen, self.progresso)
            for i, btn in enumerate(self.buttons):
                btn.draw(screen, selected=(i == self.selected_index))
            return

        screen.blit(BACKGROUND, (0, 0))
        screen.blit(BACKGROUND_OVERLAY, (0, 0))
        self.draw_frame()

        if self.state == "main":
            self.draw_title(self.t("title_main"))
            self.draw_subtitle(self.t("subtitle_main"))
        elif self.state == "options":
            self.draw_title(self.t("title_options"))
        elif self.state == "volume":
            self.draw_title(self.t("title_volume"))
            self.draw_volume_screen()
        elif self.state == "personagens":
            self.draw_title(self.t("title_characters"))
            self.draw_personagens_screen()
        elif self.state == "controles":
            self.draw_title(self.t("title_controls"))
            self.draw_controles_screen()

        for i, btn in enumerate(self.buttons):
            btn.draw(screen, selected=(i == self.selected_index))

        self.draw_footer()

    def draw_frame(self):
        margin = 20
        rect = pygame.Rect(margin, margin, WIDTH - margin * 2, HEIGHT - margin * 2)
        pygame.draw.rect(screen, PANEL_BORDER, rect, width=3, border_radius=10)
        for corner in [rect.topleft, rect.topright, rect.bottomleft, rect.bottomright]:
            pygame.draw.circle(screen, GREEN, corner, 4)

    def draw_title(self, text):
        surf = FONT_TITLE.render(text, True, GREEN)
        screen.blit(surf, surf.get_rect(center=(CX, 110)))

    def draw_subtitle(self, text):
        surf = FONT_SMALL.render(text, True, GREEN_DIM)
        screen.blit(surf, surf.get_rect(center=(CX, 165)))

    def draw_volume_screen(self):
        hint = FONT_SMALL.render(self.t("volume_hint"), True, GREEN_DIM)
        screen.blit(hint, hint.get_rect(center=(CX, 250)))

        pygame.draw.rect(screen, DARK_PANEL, self.slider_rect, border_radius=7)
        pygame.draw.rect(screen, GREEN_DIM, self.slider_rect, width=2, border_radius=7)

        fill_width = int(self.slider_rect.width * (self.volume / 100))
        if fill_width > 0:
            fill_rect = pygame.Rect(
                self.slider_rect.x, self.slider_rect.y, fill_width, self.slider_rect.height
            )
            pygame.draw.rect(screen, GREEN, fill_rect, border_radius=7)

        handle_x = self.slider_rect.x + fill_width
        pygame.draw.circle(screen, GREEN, (handle_x, self.slider_rect.centery), 10)
        pygame.draw.circle(screen, BG_COLOR, (handle_x, self.slider_rect.centery), 4)

        percent = FONT_BIG.render(f"{self.volume}%", True, GREEN)
        screen.blit(percent, percent.get_rect(center=(CX, 400)))

    @staticmethod
    def _keycap_surface(label, w, h, font):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        rect = surf.get_rect()
        pygame.draw.rect(surf, DARK_PANEL, rect, border_radius=8)
        pygame.draw.rect(surf, GREEN, rect, width=2, border_radius=8)
        lines = label.split("\n")
        line_h = font.get_height()
        start_y = (h - line_h * len(lines)) // 2
        for i, line in enumerate(lines):
            line_surf = font.render(line, True, GREEN)
            line_rect = line_surf.get_rect(centerx=w // 2, y=start_y + i * line_h)
            surf.blit(line_surf, line_rect)
        return surf

    def draw_controles_screen(self):
        hint = FONT_SMALL.render(
            "Cada tecla abaixo executa exatamente esta ação no jogo:", True, GREEN_DIM
        )
        screen.blit(hint, hint.get_rect(center=(CX, 165)))

        # Grupo W A S D — a ação de cada tecla aparece logo abaixo dela.
        key_w, key_h, gap = 95, 50, 15
        total_w = 4 * key_w + 3 * gap
        x = CX - total_w // 2
        y = 205
        for key, label in WASD_KEYS:
            keycap = self._keycap_surface(key, key_w, key_h, FONT_MED)
            screen.blit(keycap, (x, y))
            label_surf = FONT_SMALL.render(label, True, GREEN_DIM)
            screen.blit(label_surf, label_surf.get_rect(centerx=x + key_w // 2, top=y + key_h + 8))
            x += key_w + gap

        # Larguras fixas para as linhas abaixo ficarem todas alinhadas em
        # colunas (tecla sempre no mesmo X, descrição sempre no mesmo X).
        row_gap = 18
        kc_h = 50
        kc_w = max(
            max(FONT_SMALL.size(line)[0] for line in key_label.split("\n"))
            for key_label, _ in CONTROL_ROWS
        ) + 24
        max_desc_w = max(FONT_SMALL.size(desc)[0] for _, desc in CONTROL_ROWS)
        block_w = kc_w + row_gap + max_desc_w
        row_x = CX - block_w // 2

        row_y = y + key_h + 8 + FONT_SMALL.get_height() + 34
        for key_label, desc in CONTROL_ROWS:
            lines = key_label.split("\n")
            font = FONT_SMALL if len(lines) > 1 else FONT_MED
            keycap = self._keycap_surface(key_label, kc_w, kc_h, font)
            desc_surf = FONT_SMALL.render(desc, True, WHITE)

            screen.blit(keycap, (row_x, row_y))
            screen.blit(desc_surf, (row_x + kc_w + row_gap, row_y + kc_h // 2 - desc_surf.get_height() // 2))
            row_y += kc_h + 24

    def draw_personagens_screen(self):
        hint_key = "rename_hint" if self.editing_name else "characters_hint"
        hint = FONT_SMALL.render(self.t(hint_key), True, GREEN_DIM)
        screen.blit(hint, hint.get_rect(center=(CX, 260)))

        box_center = (CX, 285 + _CHARACTER_BOX_HEIGHT // 2)
        img = CHARACTER_IMAGES.get(self.personagem_index)
        if img:
            screen.blit(img, img.get_rect(center=box_center))
        else:
            placeholder = FONT_SMALL.render(self.t("character_placeholder"), True, GREEN_DIM)
            screen.blit(placeholder, placeholder.get_rect(center=box_center))

        if self.editing_name:
            field = pygame.Rect(CX - 200, 452, 400, 46)
            pygame.draw.rect(screen, DARK_PANEL, field, border_radius=6)
            pygame.draw.rect(screen, GREEN, field, width=2, border_radius=6)
            cursor = "|" if self.blink_visible else " "
            surf = FONT_BIG.render(self.name_input_buffer + cursor, True, GREEN)
            screen.blit(surf, surf.get_rect(center=field.center))
        else:
            name = self.get_personagem_name(self.personagem_index)
            surf = FONT_BIG.render(name, True, GREEN)
            screen.blit(surf, surf.get_rect(center=(CX, 475)))

    def draw_footer(self):
        cursor = ">_" if self.blink_visible else ">"
        surf = FONT_MED.render(cursor, True, GREEN)
        screen.blit(surf, (40, HEIGHT - 55))


if __name__ == "__main__":
    Game().run()

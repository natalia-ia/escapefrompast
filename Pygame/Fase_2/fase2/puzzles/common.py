"""
Este arquivo é uma "caixa de ferramentas" visual compartilhada pelos puzzles
da Fase 2 (hoje só o babbage_lovelace.py usa, mas se um dia tivermos mais de
um puzzle na fase, todos podem reaproveitar daqui): cores padronizadas,
carregamento de fontes, o desenho da moldura decorativa 9-slice e um botão
clicável simples. A ideia é não repetir esse código em cada puzzle.

Mantido dentro de fases/ de propósito: o menu (menu/jogo.py) não importa nada
daqui, e este módulo não importa nada do menu — as duas partes ficam
totalmente independentes.
"""

import os

import pygame

# ---------------------------------------------------------------------------
# Configurações (cores e caminhos)
# ---------------------------------------------------------------------------
# Paleta de cores "base" da tela de puzzle (fundo, painéis e estados de
# hover). Ficam todas juntas aqui em vez de espalhadas pelo código, assim se
# a gente quiser mudar o tema (por exemplo, deixar mais claro) é só mexer
# nessas linhas.
BG_COLOR = (10, 12, 24)
PANEL_COLOR = (43, 30, 20)  # marrom escuro — era azul/teal antes do ajuste de paleta
GREEN = (0, 255, 140)
GREEN_DIM = (0, 140, 90)
RED = (255, 70, 70)
WHITE = (225, 230, 235)
HOVER_BG = (66, 48, 30)  # tom marrom mais claro para hover (era teal)

# Paleta de textos da UI (Fase 2) — dourado para títulos, bege para
# instruções/textos secundários, verde-oliva para status/sucesso.
GOLD = (212, 168, 67)
GOLD_DIM = (140, 112, 55)
CREAM = (232, 212, 176)
OLIVE = (138, 155, 110)

# Pasta assets/ da Fase 2 (um nível acima de puzzles/, onde este arquivo
# está) -- é de lá que carregamos a imagem das molduras logo abaixo.
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# As fontes começam como None e só ganham valor de verdade dentro de
# init_fonts() -- criar uma pygame.font.Font exige que pygame.font.init() (ou
# pygame.init()) já tenha rodado, e não temos garantia de que isso já
# aconteceu no momento em que este arquivo é importado.
FONT_TITLE = None
FONT_BIG = None
FONT_MED = None
FONT_SMALL = None

# Molduras decorativas recortadas de molduras.png — carregadas sob demanda
# (ver _load_frames), já que .convert_alpha() só funciona depois que a janela
# existir. LARGE_FRAME vira o fundo das telas de puzzle (draw_frame);
# SMALL_PANEL é usado onde cartões/ícones aparecem (nos puzzles).
LARGE_FRAME = None
SMALL_PANEL = None
LARGE_FRAME_BORDER = 200
SMALL_PANEL_BORDER = 45


def init_fonts():
    """Cria as 4 fontes usadas pelos puzzles (título, texto grande, médio e
    pequeno), mas só na primeira vez que alguém chamar essa função -- depois
    disso ela não faz mais nada (o `if FONT_TITLE is None` evita recriar as
    fontes toda hora, o que seria um desperdício).

    Importante: isso só funciona depois que pygame.init() (ou
    pygame.font.init()) já rodou, porque criar uma fonte exige que o sistema
    de fontes do pygame já esteja de pé.
    """
    global FONT_TITLE, FONT_BIG, FONT_MED, FONT_SMALL
    if FONT_TITLE is None:
        FONT_TITLE = pygame.font.SysFont("consolas", 32, bold=True)
        FONT_BIG = pygame.font.SysFont("consolas", 24, bold=True)
        FONT_MED = pygame.font.SysFont("consolas", 20, bold=True)
        FONT_SMALL = pygame.font.SysFont("consolas", 15)


def _load_frames():
    """Recorta os dois elementos de molduras.png na primeira vez que forem
    necessários (precisa da janela já existir para usar convert_alpha()).

    A imagem molduras.png tem várias molduras desenhadas dentro dela; aqui a
    gente só recorta (com subsurface) os dois pedaços que realmente usamos:
    um grande (fundo da tela de puzzle) e um pequeno (painel de cartão).
    As coordenadas dos retângulos (100, 56, 233, 230 etc.) foram medidas
    olhando pra imagem original -- não tem fórmula, é só "onde a moldura
    certa fica dentro do arquivo".
    """
    global LARGE_FRAME, SMALL_PANEL
    if LARGE_FRAME is not None:
        return
    raw = pygame.image.load(os.path.join(ASSETS_DIR, "molduras.png")).convert_alpha()
    SMALL_PANEL = raw.subsurface(pygame.Rect(100, 56, 233, 230)).copy()
    LARGE_FRAME = raw.subsurface(pygame.Rect(87, 304, 1382, 647)).copy()


def nine_slice(surface, source, dest_rect, border):
    """Desenha `source` esticado em 9 pedaços (cantos fixos, bordas/centro
    esticados) para caber exatamente em dest_rect.

    Essa técnica se chama "9-slice" e serve pra esticar uma imagem sem
    deformar os cantos (que geralmente têm detalhes como bordas
    arredondadas). A ideia: cortamos a imagem original em uma grade 3x3 --
    os 4 cantos ficam do tamanho original (não esticam), as bordas do meio
    esticam só numa direção (horizontal ou vertical), e o centro estica nas
    duas direções. `border` é o tamanho (em pixels) desses cantos/bordas.
    """
    dest_rect = pygame.Rect(dest_rect)
    sw, sh = source.get_size()
    # Não deixa o "border" ser maior do que a metade da imagem de origem ou
    # do destino -- senão os cortes se sobrepõem e a conta dá errado.
    b = max(1, min(border, sw // 2, sh // 2, dest_rect.width // 2, dest_rect.height // 2))

    # Recorte da imagem de ORIGEM: 3 faixas em X (esquerda/meio/direita) e
    # 3 em Y (topo/meio/baixo) -- juntas formam a grade 3x3 de 9 pedaços.
    src_x = [0, b, sw - b]
    src_w = [b, sw - 2 * b, b]
    src_y = [0, b, sh - b]
    src_h = [b, sh - 2 * b, b]

    # Mesma ideia, mas calculando ONDE cada um dos 9 pedaços vai parar no
    # destino -- os cantos (largura/altura = b) não esticam, só o miolo.
    dst_x = [dest_rect.x, dest_rect.x + b, dest_rect.x + dest_rect.width - b]
    dst_w = [b, dest_rect.width - 2 * b, b]
    dst_y = [dest_rect.y, dest_rect.y + b, dest_rect.y + dest_rect.height - b]
    dst_h = [b, dest_rect.height - 2 * b, b]

    # Percorre a grade 3x3 (linha x coluna) desenhando cada pedaço recortado
    # da origem, esticado (se precisar) pro tamanho de destino calculado
    # acima.
    for row in range(3):
        for col in range(3):
            dw, dh = dst_w[col], dst_h[row]
            if dw <= 0 or dh <= 0:
                continue
            piece = source.subsurface(pygame.Rect(src_x[col], src_y[row], src_w[col], src_h[row]))
            if (dw, dh) != (src_w[col], src_h[row]):
                piece = pygame.transform.scale(piece, (dw, dh))
            surface.blit(piece, (dst_x[col], dst_y[row]))


class Button:
    """Botão retangular simples e reutilizável: desenha um retângulo com
    texto centralizado, muda de cor quando o mouse passa por cima (hover) e
    sabe dizer se foi clicado. Usado hoje só pelo botão "FECHAR" do puzzle
    de Babbage/Lovelace, mas serve pra qualquer botão parecido no futuro.
    """

    def __init__(self, rect, text, font=None):
        # `rect` é a área clicável/desenhável do botão; `font=None` deixa
        # usar a fonte padrão (FONT_MED) se quem criar o botão não passar
        # uma fonte específica.
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.hovered = False  # atualizado por update_hover() a cada frame

    def draw(self, surface):
        """Desenha o botão em `surface`, com cores diferentes conforme
        `self.hovered` (mouse em cima ou não)."""
        font = self.font or FONT_MED
        border = GOLD if self.hovered else GOLD_DIM
        bg = HOVER_BG if self.hovered else PANEL_COLOR
        text_color = GOLD if self.hovered else WHITE
        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=6)
        surf = font.render(self.text, True, text_color)
        surface.blit(surf, surf.get_rect(center=self.rect.center))

    def update_hover(self, pos):
        """Chamado todo frame com a posição atual do mouse (`pos`), pra
        saber se deve desenhar o botão "iluminado" ou não."""
        self.hovered = self.rect.collidepoint(pos)

    def clicked(self, pos, event):
        """True se este `event` é um clique do botão esquerdo do mouse
        (`button == 1`) dentro da área do botão."""
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(pos)
        )


def draw_frame(screen, width, height, title, subtitle=""):
    """Fundo padrão (moldura decorativa 9-slice) + título para as telas de
    puzzle. Chamada logo no início do desenho de cada puzzle, antes de
    desenhar qualquer coisa específica daquele puzzle por cima.

    `screen` é a superfície onde tudo é desenhado; `width`/`height` são o
    tamanho dela; `title`/`subtitle` são os textos mostrados no topo.
    """
    init_fonts()
    _load_frames()
    screen.fill(BG_COLOR)
    margin = 20
    nine_slice(screen, LARGE_FRAME, (margin, margin, width - margin * 2, height - margin * 2), LARGE_FRAME_BORDER)

    title_surf = FONT_TITLE.render(title, True, GOLD)
    screen.blit(title_surf, title_surf.get_rect(midtop=(width // 2, margin + 10)))
    if subtitle:
        sub_surf = FONT_SMALL.render(subtitle, True, CREAM)
        screen.blit(sub_surf, sub_surf.get_rect(midtop=(width // 2, margin + 50)))


def draw_feedback(screen, width, height, message, ok):
    """Mostra uma mensagem de feedback perto do rodapé da tela -- verde-oliva
    (`ok=True`) para sucesso, vermelho (`ok=False`) para erro/aviso."""
    init_fonts()
    color = OLIVE if ok else RED
    surf = FONT_MED.render(message, True, color)
    screen.blit(surf, surf.get_rect(midbottom=(width // 2, height - 34)))


# Texto padrão da dica de "como sair" mostrada nos puzzles -- fica aqui (e
# não espalhado em cada puzzle) pra manter o texto igual em todo lugar.
ESC_HINT = "ESC — voltar para a sala"

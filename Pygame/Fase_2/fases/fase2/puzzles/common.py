"""
Utilidades visuais compartilhadas pelos puzzles da Fase 2.

Mantido dentro de fases/ de propósito: o menu (menu/jogo.py) não importa nada
daqui, e este módulo não importa nada do menu — as duas partes ficam
totalmente independentes.
"""

import os

import pygame

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

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

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
    """Precisa rodar depois de pygame.init()/pygame.font.init()."""
    global FONT_TITLE, FONT_BIG, FONT_MED, FONT_SMALL
    if FONT_TITLE is None:
        FONT_TITLE = pygame.font.SysFont("consolas", 32, bold=True)
        FONT_BIG = pygame.font.SysFont("consolas", 24, bold=True)
        FONT_MED = pygame.font.SysFont("consolas", 20, bold=True)
        FONT_SMALL = pygame.font.SysFont("consolas", 15)


def _load_frames():
    """Recorta os dois elementos de molduras.png na primeira vez que forem
    necessários (precisa da janela já existir para usar convert_alpha())."""
    global LARGE_FRAME, SMALL_PANEL
    if LARGE_FRAME is not None:
        return
    raw = pygame.image.load(os.path.join(ASSETS_DIR, "molduras.png")).convert_alpha()
    SMALL_PANEL = raw.subsurface(pygame.Rect(100, 56, 233, 230)).copy()
    LARGE_FRAME = raw.subsurface(pygame.Rect(87, 304, 1382, 647)).copy()


def nine_slice(surface, source, dest_rect, border):
    """Desenha `source` esticado em 9 pedaços (cantos fixos, bordas/centro
    esticados) para caber exatamente em dest_rect."""
    dest_rect = pygame.Rect(dest_rect)
    sw, sh = source.get_size()
    b = max(1, min(border, sw // 2, sh // 2, dest_rect.width // 2, dest_rect.height // 2))

    src_x = [0, b, sw - b]
    src_w = [b, sw - 2 * b, b]
    src_y = [0, b, sh - b]
    src_h = [b, sh - 2 * b, b]

    dst_x = [dest_rect.x, dest_rect.x + b, dest_rect.x + dest_rect.width - b]
    dst_w = [b, dest_rect.width - 2 * b, b]
    dst_y = [dest_rect.y, dest_rect.y + b, dest_rect.y + dest_rect.height - b]
    dst_h = [b, dest_rect.height - 2 * b, b]

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
    def __init__(self, rect, text, font=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.hovered = False

    def draw(self, surface):
        font = self.font or FONT_MED
        border = GOLD if self.hovered else GOLD_DIM
        bg = HOVER_BG if self.hovered else PANEL_COLOR
        text_color = GOLD if self.hovered else WHITE
        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=6)
        surf = font.render(self.text, True, text_color)
        surface.blit(surf, surf.get_rect(center=self.rect.center))

    def update_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def clicked(self, pos, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(pos)
        )


def draw_frame(screen, width, height, title, subtitle=""):
    """Fundo padrão (moldura decorativa 9-slice) + título para as telas de puzzle."""
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
    init_fonts()
    color = OLIVE if ok else RED
    surf = FONT_MED.render(message, True, color)
    screen.blit(surf, surf.get_rect(midbottom=(width // 2, height - 34)))


ESC_HINT = "ESC — voltar para a sala"

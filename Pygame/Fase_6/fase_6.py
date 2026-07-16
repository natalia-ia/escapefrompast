"""
Escape Room - Fase 6 (Arquitetura de von Neumann / EDVAC)
Base da fase feita com Pygame, reaproveitando a estrutura da Fase 1:
personagem anda pelo laboratório dos anos 1940, conversa com John von
Neumann e resolve o puzzle do EDVAC para abrir a porta.

Clicar no EDVAC abre o puzzle principal: o jogador arrasta 6 cards de
instrução (estilo assembly) para os endereços corretos da memória,
representando o conceito de "programa armazenado" de von Neumann. Ao
energizar a máquina com o programa certo, a porta é liberada.

AINDA NÃO IMPLEMENTADO NESTA ETAPA: a animação do cabo/conector ao
energizar o EDVAC (por enquanto, resolver o puzzle já troca direto para
o cenário ligado).
"""
# ==============================================================================
# === CONFIGURAÇÃO INICIAL (imports, janela, caminhos de assets) ===
# ==============================================================================
import math
import os
import pygame
import random
import sys
import threading

import ollama

pygame.init()

# ---------------------------------------------------------------------------
# Monta caminhos de assets a partir da pasta onde este arquivo .py está, em
# vez de depender da pasta de onde o jogo é executado (mesmo esquema da
# Fase 1).
# ---------------------------------------------------------------------------
PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))


def caminho_asset(nome_relativo):
    """Monta o caminho absoluto de um asset a partir da pasta deste
    arquivo .py."""
    return os.path.join(PASTA_DO_SCRIPT, nome_relativo)

# ---------------------------------------------------------------------------
# Janela do jogo
# ---------------------------------------------------------------------------
LARGURA_JANELA = 960
ALTURA_JANELA = 600

tela = pygame.display.set_mode((LARGURA_JANELA, ALTURA_JANELA))
pygame.display.set_caption("Escape Room - Fase do EDVAC")
relogio = pygame.time.Clock()

# ---------------------------------------------------------------------------
# Enquanto o menu de escolha de personagem não fica pronto, essa variável
# permite trocar manualmente qual personagem é carregado no jogo:
# 0 = para rodar com o primeiro personagem, 1 = para o segundo personagem.
# ---------------------------------------------------------------------------
PERSONAGEM_ESCOLHIDO = 1

# ---------------------------------------------------------------------------
# ASSETS: dicionário centralizado com TODOS os caminhos de imagem/fonte
# usados no jogo, cada um montado com caminho_asset().
# ---------------------------------------------------------------------------
ASSETS = {
    "fundo_desligado": caminho_asset("assets/imagens/cenarios/fase_edvac/cenario_edvac_desligado.png"),
    "fundo_ligado": caminho_asset("assets/imagens/cenarios/fase_edvac/cenario_edvac_ligado.png"),
    "von_neumann_retrato": caminho_asset("assets/imagens/cenarios/fase_edvac/von_neumann_retrato.png"),
    "caixa_dialogo_madeira": caminho_asset("assets/imagens/cenarios/fase_edvac/caixa_dialogo_madeira.png"),
    "capsula_do_tempo": caminho_asset("assets/imagens/cenarios/fase_edvac/capsula_do_tempo.png"),
    "menu_madeira": caminho_asset("assets/imagens/cenarios/fase_edvac/menu_madeira.png"),
    "fonte_pixel": caminho_asset("assets/fontes/PressStart2P-Regular.ttf"),
    "pasta_personagem_1": caminho_asset("assets/imagens/personagem/"),
    "pasta_personagem_2": caminho_asset("assets/imagens/personagem2/"),
    "musica_fundo": caminho_asset("assets/sons/musica_fundo.ogg"),
    "som_clique": caminho_asset("assets/sons/som_clique.wav"),
}

# ==============================================================================
# === CENÁRIO E PERSONAGEM ===
# ==============================================================================

# ---------------------------------------------------------------------------
# Pasta do personagem escolhido, e as duas imagens de cenário (EDVAC
# desligado e ligado), redimensionadas para caber exatamente na janela do
# jogo. fundo_atual guarda qual das duas está sendo exibida — o jogo
# começa com a máquina desligada.
# ---------------------------------------------------------------------------
PASTAS_PERSONAGEM = [
    ASSETS["pasta_personagem_1"],
    ASSETS["pasta_personagem_2"],
]
PASTA_PERSONAGEM = PASTAS_PERSONAGEM[PERSONAGEM_ESCOLHIDO]

fundo_desligado = pygame.transform.scale(
    pygame.image.load(ASSETS["fundo_desligado"]).convert(), (LARGURA_JANELA, ALTURA_JANELA)
)
fundo_ligado = pygame.transform.scale(
    pygame.image.load(ASSETS["fundo_ligado"]).convert(), (LARGURA_JANELA, ALTURA_JANELA)
)
fundo_atual = fundo_desligado

# ---------------------------------------------------------------------------
# Personagem
# As imagens têm proporções (largura x altura) diferentes entre si, então
# aplicamos o MESMO fator de escala a todas, para o personagem crescer sem
# esticar ou distorcer nenhuma das poses.
# ---------------------------------------------------------------------------
ALTURA_PERSONAGEM_ALVO = 330


def carregar_imagem_personagem(nome_arquivo, fator_escala):
    imagem = pygame.image.load(PASTA_PERSONAGEM + nome_arquivo).convert_alpha()
    largura_original, altura_original = imagem.get_size()
    novo_tamanho = (round(largura_original * fator_escala), round(altura_original * fator_escala))
    return pygame.transform.scale(imagem, novo_tamanho)


_altura_original_parado = pygame.image.load(PASTA_PERSONAGEM + "personagem_parado_frente.png").get_height()
FATOR_ESCALA_PERSONAGEM = ALTURA_PERSONAGEM_ALVO / _altura_original_parado

imagem_parado = carregar_imagem_personagem("personagem_parado_frente.png", FATOR_ESCALA_PERSONAGEM)
imagens_andando = [
    carregar_imagem_personagem("personagem_andando_lado_1.png", FATOR_ESCALA_PERSONAGEM),
    carregar_imagem_personagem("personagem_andando_lado_2.png", FATOR_ESCALA_PERSONAGEM),
]

# ---------------------------------------------------------------------------
# Posição inicial e velocidade do personagem, além das variáveis que
# controlam a animação de caminhada.
# ---------------------------------------------------------------------------
PE_PERSONAGEM_Y = ALTURA_JANELA - 20
VELOCIDADE_PERSONAGEM = 4
personagem_centro_x = LARGURA_JANELA // 2  # começa parado no centro da janela

virado_para_esquerda = False
quadro_animacao = 0
contador_animacao = 0

# ---------------------------------------------------------------------------
# Escala entre a imagem original do cenário (1312x816) e o tamanho da
# janela, usada para posicionar as áreas clicáveis (EDVAC e porta) em
# qualquer tamanho de tela.
# ---------------------------------------------------------------------------
ESCALA_X = LARGURA_JANELA / 1312
ESCALA_Y = ALTURA_JANELA / 816


def escalar_retangulo(x, y, largura, altura):
    return pygame.Rect(x * ESCALA_X, y * ESCALA_Y, largura * ESCALA_X, altura * ESCALA_Y)


AREA_EDVAC = escalar_retangulo(380, 195, 325, 460)   # os armários do EDVAC, à esquerda/centro
AREA_PORTA = escalar_retangulo(1130, 330, 160, 320)  # porta do lado direito

# ==============================================================================
# === CÁPSULA DO TEMPO (objeto decorativo do cenário) ===
# ==============================================================================

# ---------------------------------------------------------------------------
# Cápsula do tempo apoiada no chão do lado esquerdo da tela, com a borda
# direita ancorada perto do início do EDVAC (mesmo esquema da Fase 1: a
# borda direita é o ponto fixo, então se ficar larga demais é a borda
# esquerda que passa da tela e é cortada, sem a base sair do lugar).
# ---------------------------------------------------------------------------
imagem_capsula_bruta = pygame.image.load(ASSETS["capsula_do_tempo"]).convert_alpha()
imagem_capsula_original = imagem_capsula_bruta.subsurface(
    imagem_capsula_bruta.get_bounding_rect(min_alpha=10)
).copy()

MARGEM_CAPSULA_EDVAC = 5
ALTURA_CAPSULA_ALVO = 330
_fator_escala_capsula = ALTURA_CAPSULA_ALVO / imagem_capsula_original.get_height()

imagem_capsula = pygame.transform.scale(
    imagem_capsula_original,
    (round(imagem_capsula_original.get_width() * _fator_escala_capsula), ALTURA_CAPSULA_ALVO),
)

CAPSULA_POS_X = AREA_EDVAC.left - MARGEM_CAPSULA_EDVAC - imagem_capsula.get_width()
CAPSULA_POS_Y = ALTURA_JANELA - 20 - imagem_capsula.get_height()  # apoiada no chão

# ==============================================================================
# === CHATBOT (JOHN VON NEUMANN) — VISUAL: ícone, avatar e caixinha ===
# ==============================================================================

# ---------------------------------------------------------------------------
# John von Neumann aparece como um retrato redondo: um ícone pequeno fica
# fixo num canto da tela (clicável, para abrir a conversa livre depois da
# introdução), e um avatar um pouco maior aparece grudado em cima da
# caixinha enquanto a conversa está acontecendo.
# ---------------------------------------------------------------------------
imagem_von_neumann_original = pygame.image.load(ASSETS["von_neumann_retrato"]).convert_alpha()


def recortar_em_circulo(imagem):
    """Recorta uma imagem quadrada em um círculo, usado para deixar o
    retrato de von Neumann redondo."""
    tamanho = imagem.get_size()
    mascara_circulo = pygame.Surface(tamanho, pygame.SRCALPHA)
    pygame.draw.circle(
        mascara_circulo, (255, 255, 255, 255),
        (tamanho[0] // 2, tamanho[1] // 2), tamanho[0] // 2,
    )
    imagem_recortada = imagem.copy()
    imagem_recortada.blit(mascara_circulo, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return imagem_recortada


TAMANHO_ICONE_VON_NEUMANN = 60    # ícone pequeno, fixo num canto da tela
TAMANHO_AVATAR_VON_NEUMANN = 80   # avatar maior, exibido acima da caixinha

imagem_von_neumann_icone = recortar_em_circulo(
    pygame.transform.smoothscale(imagem_von_neumann_original, (TAMANHO_ICONE_VON_NEUMANN, TAMANHO_ICONE_VON_NEUMANN))
)
imagem_von_neumann_avatar = recortar_em_circulo(
    pygame.transform.smoothscale(imagem_von_neumann_original, (TAMANHO_AVATAR_VON_NEUMANN, TAMANHO_AVATAR_VON_NEUMANN))
)

MARGEM_ICONE_VON_NEUMANN = 15
AREA_VON_NEUMANN = pygame.Rect(
    MARGEM_ICONE_VON_NEUMANN, MARGEM_ICONE_VON_NEUMANN, TAMANHO_ICONE_VON_NEUMANN, TAMANHO_ICONE_VON_NEUMANN
)

# ---------------------------------------------------------------------------
# Caixinha de conversa: usa caixa_dialogo_madeira.png como fundo (em vez de
# um retângulo desenhado), redimensionada mantendo a proporção original da
# imagem (677x369). Tamanho e posição definidos aqui porque também são
# usados para calcular até onde o jogador pode digitar sem o texto vazar.
# ---------------------------------------------------------------------------
imagem_caixa_dialogo_original = pygame.image.load(ASSETS["caixa_dialogo_madeira"]).convert_alpha()

CAIXA_VN_LARGURA = 500
CAIXA_VN_ALTURA = round(CAIXA_VN_LARGURA * imagem_caixa_dialogo_original.get_height() / imagem_caixa_dialogo_original.get_width())
MARGEM_CAIXA_VN = 20

imagem_caixa_dialogo = pygame.transform.smoothscale(imagem_caixa_dialogo_original, (CAIXA_VN_LARGURA, CAIXA_VN_ALTURA))

# ---------------------------------------------------------------------------
# "Papel" bege sólido desenhado por cima da madeira, na área central da
# caixa: a foto da madeira tem veios e uma borda entalhada larga, então
# qualquer texto direto sobre ela ficava difícil de ler não importa a cor
# escolhida. Um retângulo liso de cor uniforme por baixo do texto resolve
# isso de vez, com margem generosa (55px) para nunca encostar na moldura
# decorada.
# ---------------------------------------------------------------------------
MARGEM_PAPEL_VN = 55
PAPEL_VN_LARGURA = CAIXA_VN_LARGURA - 2 * MARGEM_PAPEL_VN
PAPEL_VN_ALTURA = CAIXA_VN_ALTURA - 2 * MARGEM_PAPEL_VN
COR_PAPEL_VN = (245, 240, 220)

PADDING_TEXTO_PAPEL_VN = 12  # margem interna do texto dentro do papel
LARGURA_TEXTO_CAIXA_VN = PAPEL_VN_LARGURA - 2 * PADDING_TEXTO_PAPEL_VN

# ==============================================================================
# === MENU DE CONFIGURAÇÕES (engrenagem, moldura, botões) ===
# ==============================================================================

# ---------------------------------------------------------------------------
# Menu de configurações: um ícone de engrenagem fica sempre visível no
# canto superior direito da tela; clicar nele pausa o jogo inteiro e abre
# o menu, usando menu_madeira.png como moldura de fundo.
# ---------------------------------------------------------------------------
imagem_menu_madeira = pygame.transform.smoothscale(
    pygame.image.load(ASSETS["menu_madeira"]).convert_alpha(), (420, 420)
)
MENU_LARGURA, MENU_ALTURA = imagem_menu_madeira.get_size()
MENU_POS_X = (LARGURA_JANELA - MENU_LARGURA) // 2
MENU_POS_Y = (ALTURA_JANELA - MENU_ALTURA) // 2
MENU_CENTRO_X = MENU_POS_X + MENU_LARGURA // 2

CENTRO_ENGRENAGEM = (LARGURA_JANELA - 40, 40)
RAIO_ENGRENAGEM = 16
AREA_ENGRENAGEM = pygame.Rect(0, 0, (RAIO_ENGRENAGEM + 10) * 2, (RAIO_ENGRENAGEM + 10) * 2)
AREA_ENGRENAGEM.center = CENTRO_ENGRENAGEM


def desenhar_icone_engrenagem(superficie, centro, raio, cor=(210, 210, 215)):
    cx, cy = centro
    NUM_DENTES = 8
    for i in range(NUM_DENTES):
        angulo = (2 * math.pi / NUM_DENTES) * i
        dente_x = cx + math.cos(angulo) * raio
        dente_y = cy + math.sin(angulo) * raio
        pygame.draw.circle(superficie, cor, (round(dente_x), round(dente_y)), round(raio * 0.4))
    pygame.draw.circle(superficie, cor, centro, raio)
    pygame.draw.circle(superficie, (35, 35, 40), centro, round(raio * 0.45))  # "furo" do meio


def desenhar_icone_pausa_play(superficie, rect, mostrar_play, cor=(255, 240, 200)):
    """Desenha o ícone de dentro do botão de pausa: duas barrinhas
    verticais (⏸) quando o jogo NÃO está pausado manualmente, ou um
    triângulo (▶) quando já está pausado."""
    cx, cy = rect.center
    if mostrar_play:
        pygame.draw.polygon(superficie, cor, [
            (cx - 8, cy - 12), (cx - 8, cy + 12), (cx + 12, cy),
        ])
    else:
        pygame.draw.rect(superficie, cor, (cx - 10, cy - 12, 6, 24))
        pygame.draw.rect(superficie, cor, (cx + 4, cy - 12, 6, 24))


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

# ==============================================================================
# === ÁREA DO EDVAC E PUZZLE (programa armazenado) ===
# ==============================================================================

# ---------------------------------------------------------------------------
# fase_concluida guarda se o EDVAC já foi energizado (equivalente ao
# "cenário consertado" da Fase 1). Só passa a True quando o jogador monta o
# programa na ordem certa e clica em "Ligar EDVAC" dentro do puzzle.
# ---------------------------------------------------------------------------
fase_concluida = False

# ---------------------------------------------------------------------------
# Instruções do programa, na ORDEM CORRETA. O índice de cada instrução na
# lista já É o endereço de memória correto para ela (0 a 5) — assim, um
# card com id N está no lugar certo quando está dentro do slot N.
# ---------------------------------------------------------------------------
INSTRUCOES_EDVAC = [
    "LOAD A    (carregar valor A)",
    "LOAD B    (carregar valor B)",
    "ADD A, B  (somar A e B)",
    "STORE C   (guardar resultado em C)",
    "PRINT C   (mostrar resultado)",
    "HALT      (parar a maquina)",
]
NUM_ENDERECOS_EDVAC = len(INSTRUCOES_EDVAC)

# ---------------------------------------------------------------------------
# Layout do puzzle: um painel central com uma coluna de slots de memória
# (endereços 0 a 5) à esquerda e os cards embaralhados numa coluna de
# origem à direita.
# ---------------------------------------------------------------------------
PUZZLE_EDVAC_PAINEL = pygame.Rect(0, 0, 860, 500)
PUZZLE_EDVAC_PAINEL.center = (LARGURA_JANELA // 2, ALTURA_JANELA // 2)

SLOT_EDVAC_LARGURA, SLOT_EDVAC_ALTURA = 240, 44
SLOT_EDVAC_GAP = 10
SLOT_EDVAC_ROTULO_LARGURA = 34

SLOTS_EDVAC_X = PUZZLE_EDVAC_PAINEL.left + 50 + SLOT_EDVAC_ROTULO_LARGURA
SLOTS_EDVAC_Y = PUZZLE_EDVAC_PAINEL.top + 110


def rect_slot_edvac(indice):
    return pygame.Rect(
        SLOTS_EDVAC_X,
        SLOTS_EDVAC_Y + indice * (SLOT_EDVAC_ALTURA + SLOT_EDVAC_GAP),
        SLOT_EDVAC_LARGURA, SLOT_EDVAC_ALTURA,
    )


RETANGULOS_SLOTS_EDVAC = [rect_slot_edvac(i) for i in range(NUM_ENDERECOS_EDVAC)]

CARD_EDVAC_LARGURA, CARD_EDVAC_ALTURA = 226, 36
ORIGEM_EDVAC_X = SLOTS_EDVAC_X + SLOT_EDVAC_LARGURA + 70


def rect_origem_edvac(indice):
    """Posição (alinhada com a linha do slot de mesmo índice) de uma das 6
    posições fixas da área de origem, à direita dos slots."""
    slot = RETANGULOS_SLOTS_EDVAC[indice]
    rect = pygame.Rect(0, 0, CARD_EDVAC_LARGURA, CARD_EDVAC_ALTURA)
    rect.center = (ORIGEM_EDVAC_X + CARD_EDVAC_LARGURA // 2, slot.centery)
    return rect


# Cada card (id 0 a 5, igual ao seu endereço correto) começa numa posição
# FIXA e embaralhada na área de origem — a posição não muda enquanto o
# puzzle estiver aberto, então soltar um card fora de um slot sempre o
# devolve para o mesmo lugar.
_ordem_embaralhada_edvac = list(range(NUM_ENDERECOS_EDVAC))
random.shuffle(_ordem_embaralhada_edvac)
POSICOES_ORIGEM_EDVAC = {
    card_id: rect_origem_edvac(posicao).topleft
    for posicao, card_id in enumerate(_ordem_embaralhada_edvac)
}

BOTAO_LIGAR_EDVAC = pygame.Rect(0, 0, 260, 48)
BOTAO_LIGAR_EDVAC.center = (
    PUZZLE_EDVAC_PAINEL.centerx,
    SLOTS_EDVAC_Y + NUM_ENDERECOS_EDVAC * (SLOT_EDVAC_ALTURA + SLOT_EDVAC_GAP) - SLOT_EDVAC_GAP + 45,
)

COR_PAINEL_EDVAC_FUNDO = (24, 22, 32)
COR_PAINEL_EDVAC_BORDA = (255, 220, 80)
COR_SLOT_EDVAC_VAZIO = (45, 45, 60)
COR_SLOT_EDVAC_BORDA = (110, 110, 130)
COR_ROTULO_ENDERECO_EDVAC = (200, 200, 215)
COR_CARD_EDVAC_FUNDO = (238, 232, 212)
COR_CARD_EDVAC_BORDA = (70, 55, 25)
COR_CARD_EDVAC_BORDA_ARRASTANDO = (255, 220, 80)
COR_TEXTO_CARD_EDVAC = (25, 25, 25)
COR_BOTAO_LIGAR_EDVAC_ATIVO = (70, 150, 75)
COR_BOTAO_LIGAR_EDVAC_INATIVO = (70, 70, 80)
COR_BORDA_BOTAO_LIGAR_EDVAC = (30, 60, 30)
COR_MENSAGEM_SUCESSO_EDVAC = (130, 235, 130)
COR_MENSAGEM_ERRO_EDVAC = (235, 110, 100)

# ---------------------------------------------------------------------------
# Estado do puzzle: cada slot guarda o id do card encaixado nele (ou None);
# card_no_slot_edvac é o inverso (card -> slot), útil pra achar rápido onde
# um card está. Um card sem slot (None) está na área de origem.
# ---------------------------------------------------------------------------
puzzle_edvac_aberto = False
puzzle_edvac_resolvido = False
slots_edvac = [None] * NUM_ENDERECOS_EDVAC
card_no_slot_edvac = {card_id: None for card_id in range(NUM_ENDERECOS_EDVAC)}
card_arrastando_edvac = None       # id do card sendo arrastado no momento, ou None
arrasto_offset_edvac = (0, 0)      # distância do canto do card até o cursor, pra ele não "pular" ao pegar
mensagem_validacao_edvac = ""
cor_mensagem_validacao_edvac = (255, 255, 255)


def rect_atual_card_edvac(card_id, mouse_pos=None):
    """Devolve o retângulo onde o card deve ser desenhado agora: seguindo o
    mouse se estiver sendo arrastado, centralizado no slot se já estiver
    encaixado, ou na posição fixa de origem caso contrário."""
    rect = pygame.Rect(0, 0, CARD_EDVAC_LARGURA, CARD_EDVAC_ALTURA)
    if card_arrastando_edvac == card_id and mouse_pos is not None:
        rect.topleft = (mouse_pos[0] - arrasto_offset_edvac[0], mouse_pos[1] - arrasto_offset_edvac[1])
        return rect
    slot_index = card_no_slot_edvac[card_id]
    if slot_index is not None:
        rect.center = RETANGULOS_SLOTS_EDVAC[slot_index].center
        return rect
    rect.topleft = POSICOES_ORIGEM_EDVAC[card_id]
    return rect


def desenhar_card_edvac(superficie, rect, texto, arrastando=False):
    pygame.draw.rect(superficie, COR_CARD_EDVAC_FUNDO, rect, border_radius=6)
    cor_borda = COR_CARD_EDVAC_BORDA_ARRASTANDO if arrastando else COR_CARD_EDVAC_BORDA
    pygame.draw.rect(superficie, cor_borda, rect, width=3 if arrastando else 2, border_radius=6)

    linhas = quebrar_texto(texto, fonte_dialogo_von_neumann, rect.width - 16)
    y = rect.centery - (len(linhas) * ESPACAMENTO_LINHA_DIALOGO_VN) // 2
    for linha in linhas:
        superficie_linha = fonte_dialogo_von_neumann.render(linha, True, COR_TEXTO_CARD_EDVAC)
        superficie.blit(superficie_linha, (rect.centerx - superficie_linha.get_width() // 2, y))
        y += ESPACAMENTO_LINHA_DIALOGO_VN

# ==============================================================================
# === ESTADO DO MENU (aberto/fechado, pausa manual, volume da música) ===
# ==============================================================================
menu_aberto = False
pausado_manual = False
VOLUME_INICIAL_MUSICA = 0.35
volume_musica = VOLUME_INICIAL_MUSICA

# ==============================================================================
# === CHATBOT (VON NEUMANN) — ESTADO DA CONVERSA E INTEGRAÇÃO COM IA ===
# ==============================================================================

# ---------------------------------------------------------------------------
# Dica visual inicial: nos primeiros 5 segundos de jogo, uma seta animada
# aponta para o ícone de von Neumann, indicando que dá pra clicar nele.
# ---------------------------------------------------------------------------
DURACAO_DICA_VON_NEUMANN = 300  # ~5 segundos a 60 quadros por segundo
contador_dica_von_neumann = DURACAO_DICA_VON_NEUMANN

# ---------------------------------------------------------------------------
# A caixinha só aparece quando o jogador clica no ícone de von Neumann —
# nunca sozinha. Assim que abre, mostra uma única fala fixa (sem IA, então
# nunca trava) e já deixa o campo de digitação disponível: tudo que o
# jogador digitar a partir daí é enviado para a IA.
#   0) ETAPA_NAO_INICIADA / ETAPA_PRONTO -> caixinha fechada; clicar no
#      ícone abre e vai direto para ETAPA_LIVRE.
#   1) ETAPA_LIVRE -> fala fixa de saudação (até o jogador mandar a
#      primeira mensagem) + campo de digitação sempre visível. Depois da
#      primeira pergunta, a fala mostrada passa a ser a resposta da IA
#      (ou "pensando..." enquanto espera). Esc fecha a caixinha.
# ---------------------------------------------------------------------------
ETAPA_NAO_INICIADA = "nao_iniciada"
ETAPA_PRONTO = "pronto"
ETAPA_LIVRE = "livre"

etapa_conversa_von_neumann = ETAPA_NAO_INICIADA
caixa_von_neumann_aberta = False  # só abre quando o jogador clica no ícone de von Neumann
texto_digitado_von_neumann = ""   # o que o jogador está digitando na conversa livre
resposta_von_neumann = ""        # última resposta da IA (só usada na conversa livre)
von_neumann_pensando = False     # true enquanto espera a IA responder

FALA_VON_NEUMANN_SAUDACAO = "Olá, viajante! Sou von Neumann. Você está preparado para ligar o EDVAC?"

# Instrução de sistema enviada ao modelo para ele sempre responder no papel
# de von Neumann. A fala de saudação acima é fixa (não passa pela IA); a
# partir da primeira resposta do jogador, tudo vai para a IA.
PROMPT_SISTEMA_VON_NEUMANN = (
    "Você é John von Neumann, matemático, no fim dos anos 1940, em seu "
    "laboratório com a máquina EDVAC. Conversa com um viajante do tempo. "
    "Explique de forma simples a época, o que é o EDVAC e o programa "
    "armazenado, e incentive o viajante a organizar as instruções do "
    "programa na ordem certa para energizar a máquina e sair. Responda "
    "sempre em português, breve (1 a 3 frases), com tom gentil, "
    "confiante e encorajador."
)

# ---------------------------------------------------------------------------
# Modelo usado no Ollama: qwen2.5:0.5b
# ---------------------------------------------------------------------------
MODELO_VON_NEUMANN = "qwen2.5:0.5b"
TIMEOUT_OLLAMA_SEGUNDOS = 30  # testado na prática: uma resposta levou ~16s
cliente_ollama = ollama.Client(timeout=TIMEOUT_OLLAMA_SEGUNDOS)


def perguntar_a_von_neumann(pergunta):
    """Chama o modelo qwen2.5:0.5b (rodando localmente via Ollama) pedindo
    uma resposta como se fosse von Neumann. Roda em uma thread separada
    para não travar a janela do jogo enquanto espera a resposta chegar."""
    global resposta_von_neumann, von_neumann_pensando
    try:
        resultado = cliente_ollama.chat(
            model=MODELO_VON_NEUMANN,
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA_VON_NEUMANN},
                {"role": "user", "content": pergunta},
            ],
        )
        resposta_von_neumann = resultado["message"]["content"].strip()
    except Exception:
        # Cobre timeout, Ollama fora do ar ou qualquer outro erro de conexão.
        resposta_von_neumann = "Von Neumann não pôde responder agora."
    von_neumann_pensando = False


# ==============================================================================
# === FONTES E TEXTO (fontes pixeladas e funções de desenho de texto) ===
# ==============================================================================
ESPACAMENTO_LINHA = 16

fonte = pygame.font.Font(ASSETS["fonte_pixel"], 10)
fonte_grande = pygame.font.Font(ASSETS["fonte_pixel"], 16)
fonte_vitoria = pygame.font.Font(ASSETS["fonte_pixel"], 24)  # usada só na mensagem de vitória na porta
fonte_pausado = pygame.font.Font(ASSETS["fonte_pixel"], 32)  # usada só no texto "PAUSADO" do menu

# Fonte menor, usada só dentro da caixinha de diálogo do von Neumann: a
# moldura de caixa_dialogo_madeira.png tem uma borda decorativa larga, então
# o texto precisa de uma fonte menor que a padrão (10) para caber por
# inteiro na área de madeira útil, sem vazar em cima da moldura.
ESPACAMENTO_LINHA_DIALOGO_VN = 13
fonte_dialogo_von_neumann = pygame.font.Font(ASSETS["fonte_pixel"], 9)


def quebrar_texto(texto, fonte_usada, largura_maxima):
    """Quebra um texto em várias linhas para caber dentro de uma largura
    máxima, usado para exibir a resposta de von Neumann na caixinha."""
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


def desenhar_texto_multilinha(superficie, texto, fonte_usada, cor, x, y, largura_maxima, espacamento=ESPACAMENTO_LINHA, max_linhas=None):
    """Quebra o texto para caber em largura_maxima e desenha uma linha
    embaixo da outra, começando em (x, y). Devolve o y logo depois da
    última linha desenhada, útil para posicionar o que vem a seguir.

    Se max_linhas for informado, corta o texto nesse número de linhas (com
    "..." na última) em vez de deixar vazar para fora da área disponível —
    usado na resposta da IA, que pode vir mais longa do que cabe na
    caixinha."""
    linhas = quebrar_texto(texto, fonte_usada, largura_maxima)
    if max_linhas is not None and len(linhas) > max_linhas:
        linhas = linhas[:max_linhas]
        linhas[-1] = linhas[-1].rstrip() + "..."
    for linha in linhas:
        superficie.blit(fonte_usada.render(linha, True, cor), (x, y))
        y += espacamento
    return y


def desenhar_texto_com_contorno(superficie, texto, fonte_usada, cor_texto, cor_contorno, centro_x, centro_y, espessura=2):
    """Desenha um texto com contorno grosso, pra garantir contraste em cima
    de qualquer fundo, sem precisar de imagem nenhuma."""
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
# === EFEITOS VISUAIS (brilho no EDVAC, seta de dica) ===
# ==============================================================================

# ---------------------------------------------------------------------------
# Feedback visual no EDVAC: desenha um contorno dourado pulsante ao redor
# de AREA_EDVAC quando o mouse está em cima, indicando que é clicável.
# ---------------------------------------------------------------------------
def desenhar_brilho_edvac(superficie, area, tempo_ms):
    pulso = (math.sin(tempo_ms / 200) + 1) / 2
    expansao = round(4 + pulso * 6)
    alpha = round(120 + pulso * 100)

    contorno = area.inflate(expansao * 2, expansao * 2)
    brilho = pygame.Surface(contorno.size, pygame.SRCALPHA)
    pygame.draw.rect(brilho, (255, 220, 80, alpha), brilho.get_rect(), width=4, border_radius=8)
    superficie.blit(brilho, contorno.topleft)


def desenhar_dica_von_neumann(superficie, tempo_ms):
    """Desenha uma seta (linha + ponta triangular) e o texto "Clique
    aqui!" apontando para o ícone de von Neumann, no canto superior
    esquerdo. A seta balança suavemente ao longo da própria diagonal."""
    oscilacao = round(math.sin(tempo_ms / 250) * 8)

    ponta_x = AREA_VON_NEUMANN.right + 18 + oscilacao
    ponta_y = AREA_VON_NEUMANN.bottom + 18 + oscilacao
    base_x = ponta_x + 45
    base_y = ponta_y + 45

    cor_seta = (255, 225, 60)
    pygame.draw.line(superficie, cor_seta, (base_x, base_y), (ponta_x, ponta_y), 5)
    pygame.draw.polygon(superficie, cor_seta, [
        (ponta_x, ponta_y),
        (ponta_x + 16, ponta_y + 4),
        (ponta_x + 4, ponta_y + 16),
    ])

    texto_dica = fonte.render("Clique aqui!", True, cor_seta)
    superficie.blit(texto_dica, (base_x + 8, base_y - 6))


# ==============================================================================
# === TELA DE INTRODUÇÃO (mostrada uma vez, antes do jogo começar) ===
# ==============================================================================
TEXTO_INTRODUCAO = (
    "Ano de 1945. Você chega a um laboratório coberto de válvulas e fios, "
    "onde o EDVAC aguarda desligado. Um cientista observa seus cálculos "
    "no quadro-negro ao fundo..."
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

        tela.fill((12, 10, 18))
        desenhar_texto_multilinha(
            tela, TEXTO_INTRODUCAO, fonte_grande, (230, 230, 230),
            60, ALTURA_JANELA // 2 - 100, LARGURA_JANELA - 120, espacamento=30,
        )

        texto_continuar = fonte.render("Pressione qualquer tecla para começar", True, (170, 170, 170))
        tela.blit(texto_continuar, (LARGURA_JANELA // 2 - texto_continuar.get_width() // 2, ALTURA_JANELA - 60))

        pygame.display.flip()


# ==============================================================================
# === SONS (música de fundo em loop e som de clique) ===
# ==============================================================================
pygame.mixer.music.load(ASSETS["musica_fundo"])
pygame.mixer.music.set_volume(volume_musica)
pygame.mixer.music.play(-1)  # -1 = toca em loop infinito

som_clique = pygame.mixer.Sound(ASSETS["som_clique"])

tela_introducao()

# ==============================================================================
# === LOOP PRINCIPAL DO JOGO ===
# ==============================================================================
rodando = True
while rodando:
    relogio.tick(60)
    personagem_andou = False

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

        # ---------------------------------------------------------------
        # --- EVENTOS: MENU DE CONFIGURAÇÕES (engrenagem e botões) ---
        # ---------------------------------------------------------------
        if evento.type == pygame.MOUSEBUTTONDOWN:
            if not menu_aberto and not puzzle_edvac_aberto and AREA_ENGRENAGEM.collidepoint(evento.pos):
                som_clique.play()
                menu_aberto = True

            elif menu_aberto:
                if BOTAO_PAUSA.collidepoint(evento.pos):
                    pausado_manual = not pausado_manual
                elif BOTAO_VOLUME_MENOS.collidepoint(evento.pos):
                    volume_musica = max(0.0, round(volume_musica - 0.1, 2))
                    pygame.mixer.music.set_volume(volume_musica)
                elif BOTAO_VOLUME_MAIS.collidepoint(evento.pos):
                    volume_musica = min(1.0, round(volume_musica + 0.1, 2))
                    pygame.mixer.music.set_volume(volume_musica)
                elif BOTAO_CONTINUAR.collidepoint(evento.pos):
                    menu_aberto = False
                    pausado_manual = False
                elif BOTAO_SAIR.collidepoint(evento.pos):
                    rodando = False

            elif puzzle_edvac_aberto:
                # -----------------------------------------------------------
                # --- EVENTOS: PUZZLE DO EDVAC (pegar um card ou ligar) ---
                # -----------------------------------------------------------
                if BOTAO_LIGAR_EDVAC.collidepoint(evento.pos) and all(s is not None for s in slots_edvac):
                    som_clique.play()
                    primeiro_errado = next(
                        (i for i in range(NUM_ENDERECOS_EDVAC) if slots_edvac[i] != i), None
                    )
                    if primeiro_errado is None:
                        mensagem_validacao_edvac = "Programa executado com sucesso!"
                        cor_mensagem_validacao_edvac = COR_MENSAGEM_SUCESSO_EDVAC
                        puzzle_edvac_resolvido = True
                        fase_concluida = True
                        fundo_atual = fundo_ligado
                    else:
                        mensagem_validacao_edvac = f"ERRO: execução travou no endereço {primeiro_errado}"
                        cor_mensagem_validacao_edvac = COR_MENSAGEM_ERRO_EDVAC
                else:
                    # Pega o card clicado (se houver), de cima pra baixo na
                    # ordem dos endereços e depois na área de origem.
                    for card_id in range(NUM_ENDERECOS_EDVAC):
                        rect_card = rect_atual_card_edvac(card_id)
                        if rect_card.collidepoint(evento.pos):
                            som_clique.play()
                            card_arrastando_edvac = card_id
                            arrasto_offset_edvac = (evento.pos[0] - rect_card.x, evento.pos[1] - rect_card.y)
                            slot_de_origem = card_no_slot_edvac[card_id]
                            if slot_de_origem is not None:
                                slots_edvac[slot_de_origem] = None
                                card_no_slot_edvac[card_id] = None
                            break

            else:
                # -----------------------------------------------------------
                # --- EVENTOS: EDVAC (clique na máquina) ---
                # Abre o puzzle de organizar o programa na memória.
                # -----------------------------------------------------------
                if not fase_concluida and not caixa_von_neumann_aberta:
                    if AREA_EDVAC.collidepoint(evento.pos):
                        som_clique.play()
                        puzzle_edvac_aberto = True
                        mensagem_validacao_edvac = ""

                # -----------------------------------------------------------------
                # --- EVENTOS: CHATBOT VON NEUMANN (clique no ícone) ---
                # -----------------------------------------------------------------
                if (
                    not caixa_von_neumann_aberta
                    and etapa_conversa_von_neumann in (ETAPA_NAO_INICIADA, ETAPA_PRONTO)
                ):
                    if AREA_VON_NEUMANN.collidepoint(evento.pos):
                        som_clique.play()
                        contador_dica_von_neumann = 0  # clicou antes dos 5s: a dica some na hora
                        caixa_von_neumann_aberta = True
                        etapa_conversa_von_neumann = ETAPA_LIVRE
                        texto_digitado_von_neumann = ""
                        resposta_von_neumann = ""
                        von_neumann_pensando = False

        # ---------------------------------------------------------------
        # --- EVENTOS: PUZZLE DO EDVAC (soltar o card arrastado) ---
        # Solta dentro de um slot vazio encaixa o card ali; solto em
        # qualquer outro lugar, o card volta pra área de origem (não faz
        # nada além de limpar o estado de arrasto, já que rect_atual_card_edvac
        # cai automaticamente na posição de origem quando o card não está
        # em nenhum slot).
        # ---------------------------------------------------------------
        if evento.type == pygame.MOUSEBUTTONUP and card_arrastando_edvac is not None:
            slot_alvo = next(
                (i for i in range(NUM_ENDERECOS_EDVAC)
                 if slots_edvac[i] is None and RETANGULOS_SLOTS_EDVAC[i].collidepoint(evento.pos)),
                None,
            )
            if slot_alvo is not None:
                slots_edvac[slot_alvo] = card_arrastando_edvac
                card_no_slot_edvac[card_arrastando_edvac] = slot_alvo
            card_arrastando_edvac = None

        # Enquanto o menu de configurações está aberto, Esc fecha ele.
        if evento.type == pygame.KEYDOWN and menu_aberto:
            if evento.key == pygame.K_ESCAPE:
                menu_aberto = False
                pausado_manual = False

        # Enquanto o puzzle do EDVAC está aberto, Esc fecha ele sem perder o
        # que o jogador já organizou nos slots (fecha só a janela do puzzle).
        if evento.type == pygame.KEYDOWN and puzzle_edvac_aberto:
            if evento.key == pygame.K_ESCAPE:
                puzzle_edvac_aberto = False

        # ---------------------------------------------------------------
        # --- EVENTOS: CHATBOT VON NEUMANN (digitação na caixinha) ---
        # A conversa é toda livre: o jogador digita qualquer coisa (a
        # primeira mensagem ou as próximas) e ela é enviada para a IA numa
        # thread separada, com timeout, para não travar o jogo se o Ollama
        # demorar ou estiver fora do ar. Esc fecha a caixinha a qualquer momento.
        # ---------------------------------------------------------------
        if evento.type == pygame.KEYDOWN and caixa_von_neumann_aberta and not menu_aberto:
            if etapa_conversa_von_neumann == ETAPA_LIVRE:
                if evento.key == pygame.K_ESCAPE:
                    caixa_von_neumann_aberta = False
                    etapa_conversa_von_neumann = ETAPA_PRONTO
                elif evento.key == pygame.K_RETURN:
                    if texto_digitado_von_neumann != "" and not von_neumann_pensando:
                        von_neumann_pensando = True
                        resposta_von_neumann = ""
                        threading.Thread(
                            target=perguntar_a_von_neumann,
                            args=(texto_digitado_von_neumann,),
                            daemon=True,
                        ).start()
                        texto_digitado_von_neumann = ""
                elif evento.key == pygame.K_BACKSPACE:
                    if not von_neumann_pensando:
                        texto_digitado_von_neumann = texto_digitado_von_neumann[:-1]
                elif (
                    not von_neumann_pensando
                    and evento.unicode.isprintable()
                    and fonte_dialogo_von_neumann.size(texto_digitado_von_neumann + evento.unicode)[0] <= LARGURA_TEXTO_CAIXA_VN
                ):
                    texto_digitado_von_neumann += evento.unicode

    # -----------------------------------------------------------------------
    # --- ATUALIZAÇÃO: MOVIMENTO DO PERSONAGEM ---
    # Bloqueado enquanto a caixinha de von Neumann ou o menu estão abertos.
    # -----------------------------------------------------------------------
    if not caixa_von_neumann_aberta and not menu_aberto and not puzzle_edvac_aberto:
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
    # --- ATUALIZAÇÃO: PORTA ---
    # Verifica se o personagem encostou na porta, só depois da fase concluída.
    # -----------------------------------------------------------------------
    retangulo_personagem = pygame.Rect(personagem_pos_x, personagem_pos_y, largura_atual, altura_atual)
    chegou_na_porta = fase_concluida and retangulo_personagem.colliderect(AREA_PORTA)

    # =========================================================================
    # === DESENHO: CENÁRIO, PERSONAGEM E ÍCONES FIXOS ===
    # =========================================================================
    tela.blit(fundo_atual, (0, 0))

    tela.blit(imagem_capsula, (CAPSULA_POS_X, CAPSULA_POS_Y))

    tela.blit(imagem_personagem, (personagem_pos_x, personagem_pos_y))

    # Ícone redondo de von Neumann, fixo num canto da tela; depois da
    # conversa inicial, clicar nele abre a conversa livre.
    tela.blit(imagem_von_neumann_icone, (AREA_VON_NEUMANN.x, AREA_VON_NEUMANN.y))

    desenhar_icone_engrenagem(tela, CENTRO_ENGRENAGEM, RAIO_ENGRENAGEM)

    # =========================================================================
    # === DESENHO: EFEITOS VISUAIS (dica e brilho) ===
    # =========================================================================
    if contador_dica_von_neumann > 0:
        desenhar_dica_von_neumann(tela, pygame.time.get_ticks())
        contador_dica_von_neumann -= 1

    mouse_pos = pygame.mouse.get_pos()
    if (
        not fase_concluida
        and not caixa_von_neumann_aberta
        and not puzzle_edvac_aberto
        and AREA_EDVAC.collidepoint(mouse_pos)
    ):
        desenhar_brilho_edvac(tela, AREA_EDVAC, pygame.time.get_ticks())

    # Mensagem de vitória, com visual de jogo retrô: fonte pixelada grande,
    # texto branco com contorno preto, fundo escuro semitransparente atrás
    # e um pulsar suave na opacidade do fundo.
    if chegou_na_porta:
        TEXTO_VITORIA = "Você concluiu a Fase 6!"
        centro_vitoria_x = LARGURA_JANELA // 2
        centro_vitoria_y = 60

        medida_texto = fonte_vitoria.size(TEXTO_VITORIA)
        largura_fundo_vitoria = medida_texto[0] + 40
        altura_fundo_vitoria = medida_texto[1] + 24

        pulso_vitoria = (math.sin(pygame.time.get_ticks() / 250) + 1) / 2
        alpha_fundo_vitoria = round(140 + pulso_vitoria * 60)

        fundo_vitoria = pygame.Surface((largura_fundo_vitoria, altura_fundo_vitoria), pygame.SRCALPHA)
        fundo_vitoria.fill((0, 0, 0, alpha_fundo_vitoria))
        tela.blit(fundo_vitoria, (
            centro_vitoria_x - largura_fundo_vitoria // 2,
            centro_vitoria_y - altura_fundo_vitoria // 2,
        ))

        desenhar_texto_com_contorno(
            tela, TEXTO_VITORIA, fonte_vitoria, (255, 255, 255), (0, 0, 0),
            centro_vitoria_x, centro_vitoria_y,
        )

    # =========================================================================
    # === DESENHO: CHATBOT VON NEUMANN (caixinha de conversa) ===
    # Usa caixa_dialogo_madeira.png como fundo, com o avatar redondo de von
    # Neumann grudado acima dela, tipo caixa de diálogo de RPG. Fica no
    # canto inferior esquerdo da tela, para deixar o meio da tela livre.
    # =========================================================================
    if caixa_von_neumann_aberta:
        caixa_vn_x = MARGEM_CAIXA_VN
        caixa_vn_y = ALTURA_JANELA - CAIXA_VN_ALTURA - MARGEM_CAIXA_VN

        tela.blit(imagem_caixa_dialogo, (caixa_vn_x, caixa_vn_y))

        avatar_x = caixa_vn_x + CAIXA_VN_LARGURA // 2 - TAMANHO_AVATAR_VON_NEUMANN // 2
        avatar_y = caixa_vn_y - TAMANHO_AVATAR_VON_NEUMANN + 15
        tela.blit(imagem_von_neumann_avatar, (avatar_x, avatar_y))

        # "Papel" bege liso por cima da madeira: todo o texto é desenhado
        # sobre essa área, nunca direto sobre os veios/moldura da foto.
        papel_x = caixa_vn_x + MARGEM_PAPEL_VN
        papel_y = caixa_vn_y + MARGEM_PAPEL_VN
        pygame.draw.rect(tela, COR_PAPEL_VN, (papel_x, papel_y, PAPEL_VN_LARGURA, PAPEL_VN_ALTURA))

        texto_x = papel_x + PADDING_TEXTO_PAPEL_VN

        desenhar_texto_multilinha(
            tela, "John von Neumann", fonte_dialogo_von_neumann, (0, 0, 0),
            texto_x, papel_y + 10, LARGURA_TEXTO_CAIXA_VN, espacamento=ESPACAMENTO_LINHA_DIALOGO_VN,
        )

        # A fala de saudação fixa aparece até o jogador mandar a primeira
        # mensagem; depois disso, mostra a resposta da IA (ou "pensando..."
        # enquanto ela ainda não chegou).
        if von_neumann_pensando:
            fala_von_neumann = "Von Neumann está pensando..."
        else:
            fala_von_neumann = resposta_von_neumann or FALA_VON_NEUMANN_SAUDACAO

        # max_linhas evita que uma resposta longa da IA vaze para fora do
        # papel bege, por cima do campo de digitação e da instrução — o
        # texto é cortado com "..." em vez de vazar.
        desenhar_texto_multilinha(
            tela, fala_von_neumann, fonte_dialogo_von_neumann, (0, 0, 0),
            texto_x, papel_y + 30, LARGURA_TEXTO_CAIXA_VN, espacamento=ESPACAMENTO_LINHA_DIALOGO_VN, max_linhas=6,
        )

        # campo de digitação e texto de ajuda ancorados a uma distância FIXA
        # do TOPO do papel — assim ficam sempre dentro do retângulo bege,
        # independentemente de quantas linhas a fala ocupar. O campo fica
        # sempre visível: a conversa é livre desde a primeira mensagem.
        campo_y = papel_y + 119
        pygame.draw.rect(tela, (255, 255, 255), (texto_x, campo_y, LARGURA_TEXTO_CAIXA_VN, 20))
        pygame.draw.rect(tela, (0, 0, 0), (texto_x, campo_y, LARGURA_TEXTO_CAIXA_VN, 20), 1)
        tela.blit(fonte_dialogo_von_neumann.render(texto_digitado_von_neumann, True, (0, 0, 0)), (texto_x + 4, campo_y + 4))

        desenhar_texto_multilinha(
            tela, "Enter para perguntar, Esc para fechar", fonte_dialogo_von_neumann, (0, 0, 0),
            texto_x, papel_y + 143, LARGURA_TEXTO_CAIXA_VN, espacamento=ESPACAMENTO_LINHA_DIALOGO_VN,
        )

    # =========================================================================
    # === DESENHO: PUZZLE DO EDVAC (memória, cards e botão de ligar) ===
    # Enquanto está aberto, o resto do jogo fica pausado atrás de um fundo
    # escurecido, igual ao menu de configurações.
    # =========================================================================
    if puzzle_edvac_aberto:
        fundo_escurecido_edvac = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA), pygame.SRCALPHA)
        fundo_escurecido_edvac.fill((0, 0, 0, 170))
        tela.blit(fundo_escurecido_edvac, (0, 0))

        pygame.draw.rect(tela, COR_PAINEL_EDVAC_FUNDO, PUZZLE_EDVAC_PAINEL, border_radius=10)
        pygame.draw.rect(tela, COR_PAINEL_EDVAC_BORDA, PUZZLE_EDVAC_PAINEL, width=3, border_radius=10)

        desenhar_texto_com_contorno(
            tela, "EDVAC - Programa Armazenado", fonte_grande, COR_PAINEL_EDVAC_BORDA, (0, 0, 0),
            PUZZLE_EDVAC_PAINEL.centerx, PUZZLE_EDVAC_PAINEL.top + 28,
        )
        texto_instrucao_edvac = fonte.render(
            "Arraste os cards para os enderecos, na ordem certa", True, (210, 210, 220),
        )
        tela.blit(texto_instrucao_edvac, (
            PUZZLE_EDVAC_PAINEL.centerx - texto_instrucao_edvac.get_width() // 2, PUZZLE_EDVAC_PAINEL.top + 55,
        ))

        rotulo_memoria = fonte.render("MEMORIA", True, COR_ROTULO_ENDERECO_EDVAC)
        tela.blit(rotulo_memoria, (SLOTS_EDVAC_X, SLOTS_EDVAC_Y - 22))
        rotulo_instrucoes = fonte.render("INSTRUCOES", True, COR_ROTULO_ENDERECO_EDVAC)
        tela.blit(rotulo_instrucoes, (ORIGEM_EDVAC_X, SLOTS_EDVAC_Y - 22))

        # Slots de memória vazios (o card, se já estiver encaixado, é
        # desenhado depois, por cima, junto com os outros cards).
        for indice, slot_rect in enumerate(RETANGULOS_SLOTS_EDVAC):
            pygame.draw.rect(tela, COR_SLOT_EDVAC_VAZIO, slot_rect, border_radius=6)
            pygame.draw.rect(tela, COR_SLOT_EDVAC_BORDA, slot_rect, width=2, border_radius=6)
            rotulo_endereco = fonte.render(str(indice), True, COR_ROTULO_ENDERECO_EDVAC)
            tela.blit(rotulo_endereco, (
                slot_rect.left - SLOT_EDVAC_ROTULO_LARGURA + 8,
                slot_rect.centery - rotulo_endereco.get_height() // 2,
            ))

        # Cards de instrução: o que está sendo arrastado é desenhado por
        # último, pra ficar sempre por cima dos outros.
        for card_id in range(NUM_ENDERECOS_EDVAC):
            if card_id == card_arrastando_edvac:
                continue
            rect_card = rect_atual_card_edvac(card_id)
            desenhar_card_edvac(tela, rect_card, INSTRUCOES_EDVAC[card_id])
        if card_arrastando_edvac is not None:
            rect_card = rect_atual_card_edvac(card_arrastando_edvac, mouse_pos)
            desenhar_card_edvac(tela, rect_card, INSTRUCOES_EDVAC[card_arrastando_edvac], arrastando=True)

        # Botão "Ligar EDVAC": só fica com a cor "ativa" quando os 6 slots
        # estão preenchidos.
        pronto_para_ligar = all(s is not None for s in slots_edvac)
        cor_botao_ligar = COR_BOTAO_LIGAR_EDVAC_ATIVO if pronto_para_ligar else COR_BOTAO_LIGAR_EDVAC_INATIVO
        pygame.draw.rect(tela, cor_botao_ligar, BOTAO_LIGAR_EDVAC, border_radius=8)
        pygame.draw.rect(tela, COR_BORDA_BOTAO_LIGAR_EDVAC, BOTAO_LIGAR_EDVAC, width=2, border_radius=8)
        texto_botao_ligar = fonte.render("LIGAR EDVAC", True, (255, 255, 255))
        tela.blit(texto_botao_ligar, texto_botao_ligar.get_rect(center=BOTAO_LIGAR_EDVAC.center))

        if mensagem_validacao_edvac:
            texto_msg_edvac = fonte.render(mensagem_validacao_edvac, True, cor_mensagem_validacao_edvac)
            tela.blit(texto_msg_edvac, (
                PUZZLE_EDVAC_PAINEL.centerx - texto_msg_edvac.get_width() // 2, BOTAO_LIGAR_EDVAC.bottom + 14,
            ))

        texto_fechar_edvac = fonte.render("Esc para fechar", True, (170, 170, 180))
        tela.blit(texto_fechar_edvac, (
            PUZZLE_EDVAC_PAINEL.right - texto_fechar_edvac.get_width() - 16, PUZZLE_EDVAC_PAINEL.top + 14,
        ))

    # =========================================================================
    # === DESENHO: MENU DE CONFIGURAÇÕES ===
    # =========================================================================
    if menu_aberto:
        fundo_escurecido = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA), pygame.SRCALPHA)
        fundo_escurecido.fill((0, 0, 0, 150))
        tela.blit(fundo_escurecido, (0, 0))

        tela.blit(imagem_menu_madeira, (MENU_POS_X, MENU_POS_Y))

        desenhar_texto_com_contorno(
            tela, "MENU", fonte_grande, COR_TEXTO_MENU, (60, 30, 10),
            MENU_CENTRO_X, MENU_POS_Y + 50,
        )

        pygame.draw.rect(tela, COR_BOTAO_MENU, BOTAO_PAUSA, border_radius=8)
        pygame.draw.rect(tela, COR_BORDA_BOTAO_MENU, BOTAO_PAUSA, width=2, border_radius=8)
        desenhar_icone_pausa_play(tela, BOTAO_PAUSA, pausado_manual, COR_TEXTO_MENU)

        texto_volume_label = fonte.render("Volume da música", True, COR_TEXTO_MENU)
        tela.blit(texto_volume_label, (MENU_CENTRO_X - texto_volume_label.get_width() // 2, MENU_POS_Y + 165))

        for botao, rotulo in ((BOTAO_VOLUME_MENOS, "-"), (BOTAO_VOLUME_MAIS, "+")):
            pygame.draw.rect(tela, COR_BOTAO_MENU, botao, border_radius=6)
            pygame.draw.rect(tela, COR_BORDA_BOTAO_MENU, botao, width=2, border_radius=6)
            texto_botao = fonte_grande.render(rotulo, True, COR_TEXTO_MENU)
            tela.blit(texto_botao, texto_botao.get_rect(center=botao.center))

        texto_porcentagem = fonte.render(f"{round(volume_musica * 100)}%", True, COR_TEXTO_MENU)
        tela.blit(texto_porcentagem, texto_porcentagem.get_rect(center=(MENU_CENTRO_X, BOTAO_VOLUME_MENOS.centery)))

        for botao, rotulo in ((BOTAO_CONTINUAR, "Continuar (Esc)"), (BOTAO_SAIR, "Sair")):
            pygame.draw.rect(tela, COR_BOTAO_MENU, botao, border_radius=8)
            pygame.draw.rect(tela, COR_BORDA_BOTAO_MENU, botao, width=2, border_radius=8)
            texto_botao = fonte.render(rotulo, True, COR_TEXTO_MENU)
            tela.blit(texto_botao, texto_botao.get_rect(center=botao.center))

        if pausado_manual:
            desenhar_texto_com_contorno(
                tela, "PAUSADO", fonte_pausado, (255, 90, 90), (40, 0, 0),
                LARGURA_JANELA // 2, ALTURA_JANELA // 2,
            )

    pygame.display.flip()

pygame.quit()
sys.exit()

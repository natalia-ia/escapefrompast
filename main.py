"""
Escape Room - Fase 1 (Ábaco)
Jogo básico feito com Pygame: personagem anda pela sala, clica no ábaco
quebrado, resolve uma conta e libera a porta para a próxima fase.
"""

import pygame
import random
import sys

pygame.init()

# ---------------------------------------------------------------------------
# Janela do jogo
# ---------------------------------------------------------------------------
LARGURA_JANELA = 1000
ALTURA_JANELA = 495

tela = pygame.display.set_mode((LARGURA_JANELA, ALTURA_JANELA))
pygame.display.set_caption("Escape Room - Fase do Ábaco")
relogio = pygame.time.Clock()

# ---------------------------------------------------------------------------
# Caminhos das imagens
# Pasta do personagem em uma única variável: para trocar de personagem no
# futuro, basta apontar essa variável para outra pasta com os mesmos nomes
# de arquivo (parado_frente, andando_lado_1, andando_lado_2).
# ---------------------------------------------------------------------------
PASTA_PERSONAGEM = "assets/imagens/personagem/"

CAMINHO_FUNDO_QUEBRADO = "assets/imagens/cenarios/fase_abaco/cenario_abaco_quebrado.png"
CAMINHO_FUNDO_CONSERTADO = "assets/imagens/cenarios/fase_abaco/cenario_abaco_consertado.png"

# ---------------------------------------------------------------------------
# Fundo da cena (redimensionado para caber exatamente na janela)
# ---------------------------------------------------------------------------
fundo_quebrado = pygame.transform.scale(
    pygame.image.load(CAMINHO_FUNDO_QUEBRADO).convert(), (LARGURA_JANELA, ALTURA_JANELA)
)
fundo_consertado = pygame.transform.scale(
    pygame.image.load(CAMINHO_FUNDO_CONSERTADO).convert(), (LARGURA_JANELA, ALTURA_JANELA)
)
fundo_atual = fundo_quebrado

# ---------------------------------------------------------------------------
# Personagem
# As imagens têm proporções (largura x altura) diferentes entre si, então
# aplicamos o MESMO fator de escala a todas, em vez de forçar cada uma numa
# caixa fixa — isso aumenta o personagem sem esticar ou distorcer nenhuma
# das poses.
# ---------------------------------------------------------------------------
ALTURA_PERSONAGEM_ALVO = 260  # altura desejada para a pose parada (era ~170 e ficava pequena)


def carregar_imagem_personagem(nome_arquivo, fator_escala):
    imagem = pygame.image.load(PASTA_PERSONAGEM + nome_arquivo).convert_alpha()
    largura_original, altura_original = imagem.get_size()
    novo_tamanho = (round(largura_original * fator_escala), round(altura_original * fator_escala))
    return pygame.transform.scale(imagem, novo_tamanho)


# fator calculado a partir da imagem parada e reaplicado nas demais, para que
# todas cresçam na mesma proporção (mantendo o tamanho relativo entre poses)
_altura_original_parado = pygame.image.load(PASTA_PERSONAGEM + "personagem_parado_frente.png").get_height()
FATOR_ESCALA_PERSONAGEM = ALTURA_PERSONAGEM_ALVO / _altura_original_parado

imagem_parado = carregar_imagem_personagem("personagem_parado_frente.png", FATOR_ESCALA_PERSONAGEM)
imagens_andando = [
    carregar_imagem_personagem("personagem_andando_lado_1.png", FATOR_ESCALA_PERSONAGEM),
    carregar_imagem_personagem("personagem_andando_lado_2.png", FATOR_ESCALA_PERSONAGEM),
]

# posição inicial: centralizado horizontalmente, em pé sobre o chão.
# Como cada quadro tem um tamanho um pouco diferente, guardamos apenas o
# centro (X) e a altura dos pés (Y) — a caixa exata é calculada a cada
# quadro, de acordo com a imagem exibida naquele momento.
personagem_centro_x = LARGURA_JANELA // 2
PE_PERSONAGEM_Y = ALTURA_JANELA - 20
VELOCIDADE_PERSONAGEM = 4

virado_para_esquerda = False   # usado para espelhar o sprite ao andar p/ esquerda
quadro_animacao = 0            # qual das duas imagens de andar está ativa
contador_animacao = 0          # conta quadros até trocar de imagem de andar

# ---------------------------------------------------------------------------
# Áreas clicáveis/de colisão do cenário.
# As posições foram medidas na imagem original (1456x720) e são escaladas
# automaticamente para o tamanho da janela atual.
# ---------------------------------------------------------------------------
ESCALA_X = LARGURA_JANELA / 1456
ESCALA_Y = ALTURA_JANELA / 720


def escalar_retangulo(x, y, largura, altura):
    return pygame.Rect(x * ESCALA_X, y * ESCALA_Y, largura * ESCALA_X, altura * ESCALA_Y)


AREA_ABACO = escalar_retangulo(315, 280, 210, 170)   # ábaco em cima da mesa
AREA_PORTA = escalar_retangulo(1150, 230, 165, 295)  # porta do lado direito

# ---------------------------------------------------------------------------
# Estado do quebra-cabeça do ábaco
# ---------------------------------------------------------------------------
cenario_consertado = False
caixa_matematica_aberta = False
resposta_digitada = ""

numero_a = 0
numero_b = 0
operador = "+"
resposta_correta = 0


def gerar_nova_conta():
    """Sorteia uma conta simples (soma, subtração ou multiplicação)."""
    global numero_a, numero_b, operador, resposta_correta

    operador = random.choice(["+", "-", "*"])
    numero_a = random.randint(1, 12)
    numero_b = random.randint(1, 12)

    if operador == "-" and numero_a < numero_b:
        numero_a, numero_b = numero_b, numero_a  # evita resposta negativa

    if operador == "+":
        resposta_correta = numero_a + numero_b
    elif operador == "-":
        resposta_correta = numero_a - numero_b
    else:
        resposta_correta = numero_a * numero_b


# ---------------------------------------------------------------------------
# Mensagens temporárias (sucesso / erro) mostradas no topo da tela
# ---------------------------------------------------------------------------
mensagem_atual = ""
tempo_mensagem = 0  # quantos quadros a mensagem ainda deve ficar visível

fonte = pygame.font.SysFont(None, 32)
fonte_grande = pygame.font.SysFont(None, 40)

# ---------------------------------------------------------------------------
# Loop principal do jogo
# ---------------------------------------------------------------------------
rodando = True
while rodando:
    relogio.tick(60)
    personagem_andou = False

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

        # clique do mouse no ábaco abre a caixa da conta matemática
        if evento.type == pygame.MOUSEBUTTONDOWN:
            if not cenario_consertado and not caixa_matematica_aberta:
                if AREA_ABACO.collidepoint(evento.pos):
                    caixa_matematica_aberta = True
                    resposta_digitada = ""
                    gerar_nova_conta()

        # digitação da resposta enquanto a caixa da conta está aberta
        if evento.type == pygame.KEYDOWN and caixa_matematica_aberta:
            if evento.key == pygame.K_RETURN:
                if resposta_digitada != "":
                    if int(resposta_digitada) == resposta_correta:
                        cenario_consertado = True
                        fundo_atual = fundo_consertado
                        caixa_matematica_aberta = False
                        mensagem_atual = "Parabéns! A conta está certa."
                        tempo_mensagem = 120
                    else:
                        mensagem_atual = "Resposta errada, tente de novo!"
                        tempo_mensagem = 90
                        resposta_digitada = ""
                        gerar_nova_conta()
            elif evento.key == pygame.K_BACKSPACE:
                resposta_digitada = resposta_digitada[:-1]
            elif evento.unicode.isdigit():
                resposta_digitada += evento.unicode

    # -----------------------------------------------------------------------
    # Movimento do personagem (bloqueado enquanto a caixa da conta está aberta)
    # -----------------------------------------------------------------------
    if not caixa_matematica_aberta:
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
    # Escolhe a imagem do personagem (parado ou animação de andar)
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

    # mantém o personagem dentro dos limites da tela (usando a largura do quadro atual)
    personagem_centro_x = max(largura_atual // 2, min(personagem_centro_x, LARGURA_JANELA - largura_atual // 2))

    personagem_pos_x = personagem_centro_x - largura_atual // 2
    personagem_pos_y = PE_PERSONAGEM_Y - altura_atual

    # -----------------------------------------------------------------------
    # Verifica se o personagem encostou na porta (só depois do ábaco pronto)
    # -----------------------------------------------------------------------
    retangulo_personagem = pygame.Rect(personagem_pos_x, personagem_pos_y, largura_atual, altura_atual)
    chegou_na_porta = cenario_consertado and retangulo_personagem.colliderect(AREA_PORTA)

    # -----------------------------------------------------------------------
    # Desenho da tela
    # -----------------------------------------------------------------------
    tela.blit(fundo_atual, (0, 0))
    tela.blit(imagem_personagem, (personagem_pos_x, personagem_pos_y))

    if tempo_mensagem > 0:
        texto = fonte_grande.render(mensagem_atual, True, (255, 255, 0))
        tela.blit(texto, (LARGURA_JANELA // 2 - texto.get_width() // 2, 30))
        tempo_mensagem -= 1

    if chegou_na_porta:
        texto_porta = fonte_grande.render("Você passou para a segunda fase!", True, (0, 255, 0))
        tela.blit(texto_porta, (LARGURA_JANELA // 2 - texto_porta.get_width() // 2, 30))

    if caixa_matematica_aberta:
        caixa_largura, caixa_altura = 400, 150
        caixa_x = LARGURA_JANELA // 2 - caixa_largura // 2
        caixa_y = ALTURA_JANELA // 2 - caixa_altura // 2

        pygame.draw.rect(tela, (245, 245, 220), (caixa_x, caixa_y, caixa_largura, caixa_altura))
        pygame.draw.rect(tela, (0, 0, 0), (caixa_x, caixa_y, caixa_largura, caixa_altura), 3)

        texto_conta = fonte.render(f"Quanto é {numero_a} {operador} {numero_b} ?", True, (0, 0, 0))
        tela.blit(texto_conta, (caixa_x + 20, caixa_y + 20))

        pygame.draw.rect(tela, (255, 255, 255), (caixa_x + 20, caixa_y + 70, caixa_largura - 40, 40))
        texto_resposta = fonte.render(resposta_digitada, True, (0, 0, 0))
        tela.blit(texto_resposta, (caixa_x + 25, caixa_y + 78))

        texto_ajuda = fonte.render("Digite a resposta e pressione Enter", True, (80, 80, 80))
        tela.blit(texto_ajuda, (caixa_x + 20, caixa_y + 115))

    pygame.display.flip()

pygame.quit()
sys.exit()

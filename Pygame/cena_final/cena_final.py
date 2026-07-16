"""
Escape Room - Cena Final (Retorno ao presente)
Última cena do jogo, feita com Pygame: o jogador está na sala do portal,
precisa caminhar até a nebulosa que gira dentro dele para voltar à época
atual. Ao tocar na nebulosa, a tela passa por uma transição (um clarão) e
o cenário troca para uma rua da cidade no presente, onde aparece a
palavra "PARABÉNS!" em destaque, com confetes coloridos caindo.

Esta cena não tem quebra-cabeça nem diálogo com IA (diferente das fases
anteriores): é só movimentação livre até a nebulosa e a tela de vitória.
"""

# ==============================================================================
# === CONFIGURAÇÃO INICIAL (imports, janela, caminhos de assets) ===
# ==============================================================================
import math
import os
import random
import sys

import pygame

pygame.init()

# ---------------------------------------------------------------------------
# Monta caminhos de assets a partir da pasta onde este arquivo .py está, em
# vez de depender da pasta de onde o jogo é executado — assim o jogo
# funciona em qualquer computador, mesmo rodando de outro diretório.
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
pygame.display.set_caption("Escape Room - Cena Final")
relogio = pygame.time.Clock()

# ---------------------------------------------------------------------------
# Enquanto o menu de escolha de personagem não fica pronto, essa variável
# permite trocar manualmente qual personagem é carregado no jogo:
# 0 = para rodar com o primeiro personagem, 1 = para o segundo personagem.
# ---------------------------------------------------------------------------
PERSONAGEM_ESCOLHIDO = 1

# ---------------------------------------------------------------------------
# ASSETS: dicionário centralizado com todos os caminhos de imagem/fonte/som
# usados nesta cena, cada um montado com caminho_asset(). Só ter os
# caminhos aqui não impede o jogo de rodar caso algum arquivo esteja
# faltando — isso é tratado pelos "carregadores seguros" logo abaixo.
# ---------------------------------------------------------------------------
ASSETS = {
    "portal_fechado": caminho_asset("assets/imagens/cenarios/cena_final/portal_fechado.png"),
    "nebulosa": caminho_asset("assets/imagens/cenarios/cena_final/nebulosa.png"),
    "presente": caminho_asset("assets/imagens/cenarios/cena_final/presente.png"),
    "fonte_pixel": caminho_asset("assets/fontes/PressStart2P-Regular.ttf"),
    "pasta_personagem_1": caminho_asset("assets/imagens/personagem/"),
    "pasta_personagem_2": caminho_asset("assets/imagens/personagem2/"),
    "musica_fundo": caminho_asset("assets/sons/musica_fundo.ogg"),
    "som_clique": caminho_asset("assets/sons/som_clique.wav"),
}

# ==============================================================================
# === CARREGADORES SEGUROS (nunca travam o jogo por causa de um arquivo) ===
# ==============================================================================
# ---------------------------------------------------------------------------
# Se uma imagem, som ou fonte não for encontrada (nome errado, arquivo
# apagado, pasta movida etc.), o jogo NÃO deve fechar com um erro. Em vez
# disso, essas funções devolvem um "substituto" (um retângulo colorido com
# o nome do arquivo escrito em cima, no caso das imagens) e o jogo continua
# rodando normalmente, só com aquele elemento visualmente diferente.
# ---------------------------------------------------------------------------


def criar_imagem_placeholder(tamanho, caminho_que_faltou, cor_fundo=(200, 40, 40)):
    """Cria uma superfície colorida no lugar de uma imagem que não pôde ser
    carregada, com o caminho do arquivo escrito em cima, para ficar fácil
    de identificar o que está faltando."""
    largura, altura = tamanho
    superficie = pygame.Surface((largura, altura), pygame.SRCALPHA)
    superficie.fill(cor_fundo)
    pygame.draw.rect(superficie, (0, 0, 0), superficie.get_rect(), width=3)

    # Usa a fonte padrão do sistema aqui (não a fonte pixel do jogo), pois a
    # própria fonte pixel também pode estar faltando.
    fonte_aviso = pygame.font.SysFont(None, 16)
    nome_relativo = os.path.relpath(caminho_que_faltou, PASTA_DO_SCRIPT)
    palavras = nome_relativo.replace("\\", "/").split("/")

    y_texto = altura // 2 - (len(palavras) * 16) // 2
    for palavra in palavras:
        texto_renderizado = fonte_aviso.render(palavra, True, (255, 255, 255))
        superficie.blit(texto_renderizado, texto_renderizado.get_rect(centerx=largura // 2, y=y_texto))
        y_texto += 16

    return superficie


def carregar_imagem_segura(caminho, tamanho_padrao=(200, 200), com_alpha=True):
    """Tenta carregar uma imagem; se o arquivo não existir ou estiver
    corrompido, devolve um placeholder colorido no lugar dela."""
    try:
        imagem = pygame.image.load(caminho)
        return imagem.convert_alpha() if com_alpha else imagem.convert()
    except (pygame.error, FileNotFoundError):
        print(f"[AVISO] Não foi possível carregar a imagem: {caminho}")
        return criar_imagem_placeholder(tamanho_padrao, caminho)


def carregar_fonte_segura(caminho, tamanho):
    """Tenta carregar a fonte pixel; se faltar, usa uma fonte padrão do
    sistema no mesmo tamanho, para o texto continuar legível."""
    try:
        return pygame.font.Font(caminho, tamanho)
    except (pygame.error, FileNotFoundError):
        print(f"[AVISO] Não foi possível carregar a fonte: {caminho}")
        return pygame.font.SysFont(None, tamanho)


def carregar_som_seguro(caminho):
    """Tenta carregar um efeito sonoro; se faltar, devolve None (o código
    que toca o som verifica isso antes de chamar .play())."""
    try:
        return pygame.mixer.Sound(caminho)
    except (pygame.error, FileNotFoundError):
        print(f"[AVISO] Não foi possível carregar o som: {caminho}")
        return None


def tocar_musica_de_fundo_segura(caminho, volume):
    """Tenta carregar e tocar a música de fundo em loop; se faltar, o jogo
    simplesmente continua tocando sem música."""
    try:
        pygame.mixer.music.load(caminho)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)  # -1 = toca em loop infinito
    except (pygame.error, FileNotFoundError):
        print(f"[AVISO] Não foi possível carregar a música: {caminho}")


# ==============================================================================
# === CENÁRIO (portal fechado e cidade no presente) ===
# ==============================================================================
# As duas imagens de cenário são redimensionadas para caber exatamente na
# janela do jogo. fundo_atual guarda qual das duas está sendo exibida no
# momento — a cena começa na sala do portal.
imagem_portal_fechado = pygame.transform.scale(
    carregar_imagem_segura(ASSETS["portal_fechado"], tamanho_padrao=(LARGURA_JANELA, ALTURA_JANELA), com_alpha=False),
    (LARGURA_JANELA, ALTURA_JANELA),
)
imagem_presente = pygame.transform.scale(
    carregar_imagem_segura(ASSETS["presente"], tamanho_padrao=(LARGURA_JANELA, ALTURA_JANELA), com_alpha=False),
    (LARGURA_JANELA, ALTURA_JANELA),
)
fundo_atual = imagem_portal_fechado

# ---------------------------------------------------------------------------
# Escala entre a imagem original do cenário (1312x816) e o tamanho da
# janela, usada para posicionar a nebulosa no lugar certo dentro do portal,
# em qualquer tamanho de tela.
# ---------------------------------------------------------------------------
ESCALA_X = LARGURA_JANELA / 1312
ESCALA_Y = ALTURA_JANELA / 816


def escalar_ponto(x, y):
    return (round(x * ESCALA_X), round(y * ESCALA_Y))


# Centro do "buraco" escuro do portal na imagem original, medido olhando
# para a arte de portal_fechado.png.
NEBULOSA_CENTRO = escalar_ponto(675, 390)

# ==============================================================================
# === NEBULOSA (gira continuamente e pulsa, dentro do portal) ===
# ==============================================================================
DIAMETRO_NEBULOSA = 220

imagem_nebulosa_original = pygame.transform.smoothscale(
    carregar_imagem_segura(ASSETS["nebulosa"], tamanho_padrao=(DIAMETRO_NEBULOSA, DIAMETRO_NEBULOSA), com_alpha=True),
    (DIAMETRO_NEBULOSA, DIAMETRO_NEBULOSA),
)

VELOCIDADE_ROTACAO_NEBULOSA = 1.3  # graus somados a cada quadro
angulo_nebulosa = 0.0


def desenhar_nebulosa(superficie, tempo_ms):
    """Desenha a nebulosa girando (pygame.transform.rotate) e pulsando
    (aumentando/diminuindo de tamanho com uma onda seno), sempre
    re-centralizada em NEBULOSA_CENTRO para não "andar" pela tela conforme
    gira (rotate muda o tamanho da superfície retornada)."""
    global angulo_nebulosa
    angulo_nebulosa = (angulo_nebulosa + VELOCIDADE_ROTACAO_NEBULOSA) % 360

    pulso = (math.sin(tempo_ms / 300) + 1) / 2  # oscila suavemente entre 0 e 1
    fator_pulso = 1.0 + pulso * 0.08  # varia entre 100% e 108% do tamanho
    tamanho_pulsando = round(DIAMETRO_NEBULOSA * fator_pulso)

    imagem_pulsando = pygame.transform.smoothscale(imagem_nebulosa_original, (tamanho_pulsando, tamanho_pulsando))
    imagem_rotacionada = pygame.transform.rotate(imagem_pulsando, angulo_nebulosa)

    rect_nebulosa = imagem_rotacionada.get_rect(center=NEBULOSA_CENTRO)
    superficie.blit(imagem_rotacionada, rect_nebulosa)


# Raio (em pixels) usado para saber se o personagem já "tocou" a nebulosa —
# comparado com a distância do meio do corpo do personagem até o centro
# dela, então não precisa ser pixel perfeito com o círculo desenhado.
RAIO_COLISAO_NEBULOSA = 95


def personagem_tocou_nebulosa(centro_x, pe_y, altura_sprite):
    ponto_meio_corpo = (centro_x, pe_y - altura_sprite / 2)
    distancia = math.hypot(ponto_meio_corpo[0] - NEBULOSA_CENTRO[0], ponto_meio_corpo[1] - NEBULOSA_CENTRO[1])
    return distancia <= RAIO_COLISAO_NEBULOSA


# ==============================================================================
# === PERSONAGEM (carregamento dos sprites e movimentação) ===
# ==============================================================================
PASTAS_PERSONAGEM = [
    ASSETS["pasta_personagem_1"],
    ASSETS["pasta_personagem_2"],
]
PASTA_PERSONAGEM = PASTAS_PERSONAGEM[PERSONAGEM_ESCOLHIDO]

# As imagens têm proporções (largura x altura) diferentes entre si, então
# aplicamos o MESMO fator de escala a todas, para o personagem crescer sem
# esticar ou distorcer nenhuma das poses.
ALTURA_PERSONAGEM_ALVO = 260


def carregar_imagem_personagem(nome_arquivo, fator_escala):
    imagem = carregar_imagem_segura(PASTA_PERSONAGEM + nome_arquivo, tamanho_padrao=(160, 330), com_alpha=True)
    largura_original, altura_original = imagem.get_size()
    novo_tamanho = (round(largura_original * fator_escala), round(altura_original * fator_escala))
    return pygame.transform.scale(imagem, novo_tamanho)


_imagem_parado_bruta = carregar_imagem_segura(
    PASTA_PERSONAGEM + "personagem_parado_frente.png", tamanho_padrao=(160, 330), com_alpha=True
)
FATOR_ESCALA_PERSONAGEM = ALTURA_PERSONAGEM_ALVO / _imagem_parado_bruta.get_height()
imagem_parado = pygame.transform.scale(
    _imagem_parado_bruta,
    (round(_imagem_parado_bruta.get_width() * FATOR_ESCALA_PERSONAGEM), ALTURA_PERSONAGEM_ALVO),
)
imagens_andando = [
    carregar_imagem_personagem("personagem_andando_lado_1.png", FATOR_ESCALA_PERSONAGEM),
    carregar_imagem_personagem("personagem_andando_lado_2.png", FATOR_ESCALA_PERSONAGEM),
]

# ---------------------------------------------------------------------------
# Posição, velocidade e limites de movimento do personagem. Diferente das
# fases anteriores (onde ele só andava para os lados), aqui ele se move nas
# quatro direções (setas ou WASD) para conseguir alcançar a nebulosa, que
# fica mais alta na tela, dentro do portal.
# ---------------------------------------------------------------------------
VELOCIDADE_PERSONAGEM = 4
PE_PERSONAGEM_Y_MIN = 240  # não deixa o personagem "subir" para dentro da parede do fundo
PE_PERSONAGEM_Y_MAX = ALTURA_JANELA - 20  # chão da sala

personagem_centro_x = LARGURA_JANELA // 2
personagem_pe_y = PE_PERSONAGEM_Y_MAX  # começa parado no chão, na frente da tela

virado_para_esquerda = False
quadro_animacao = 0
contador_animacao = 0

# ==============================================================================
# === MENSAGEM "VÁ ATÉ A NEBULOSA" (texto chamativo, com brilho pulsante) ===
# ==============================================================================
ESPACAMENTO_LINHA = 16
fonte_mensagem = carregar_fonte_segura(ASSETS["fonte_pixel"], 20)
fonte_vitoria = carregar_fonte_segura(ASSETS["fonte_pixel"], 28)


def desenhar_texto_com_contorno(superficie, texto, fonte_usada, cor_texto, cor_contorno, centro_x, centro_y, espessura=2):
    """Desenha um texto com um contorno grosso ao redor, pra garantir
    contraste em cima de qualquer fundo, sem precisar de imagem nenhuma."""
    superficie_texto = fonte_usada.render(texto, True, cor_texto)
    superficie_contorno = fonte_usada.render(texto, True, cor_contorno)
    rect_texto = superficie_texto.get_rect(center=(centro_x, centro_y))

    for dx in (-espessura, 0, espessura):
        for dy in (-espessura, 0, espessura):
            if dx == 0 and dy == 0:
                continue
            superficie.blit(superficie_contorno, (rect_texto.x + dx, rect_texto.y + dy))

    superficie.blit(superficie_texto, rect_texto)


def desenhar_texto_com_brilho(superficie, texto, fonte_usada, cor_texto, cor_contorno, cor_brilho, centro_x, centro_y, tempo_ms):
    """Desenha um texto com contorno escuro (pra se destacar do fundo) e,
    por baixo, várias cópias levemente deslocadas numa cor clara com
    opacidade pulsante — um "halo" de brilho simples, sem precisar de
    nenhuma imagem ou biblioteca extra."""
    pulso = (math.sin(tempo_ms / 250) + 1) / 2  # oscila suavemente entre 0 e 1
    alpha_brilho = round(60 + pulso * 130)

    superficie_brilho = fonte_usada.render(texto, True, cor_brilho)
    superficie_brilho.set_alpha(alpha_brilho)
    rect_brilho = superficie_brilho.get_rect(center=(centro_x, centro_y))
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
        superficie.blit(superficie_brilho, (rect_brilho.x + dx, rect_brilho.y + dy))

    desenhar_texto_com_contorno(superficie, texto, fonte_usada, cor_texto, cor_contorno, centro_x, centro_y)


TEXTO_MENSAGEM_NEBULOSA = "Vá até a nebulosa para voltar ao presente"


def desenhar_fundo_mensagem(superficie, texto, fonte_usada, centro_x, centro_y):
    """Desenha um retângulo escuro semitransparente atrás do texto, pra ele
    ficar legível em cima de qualquer parte do cenário."""
    medida = fonte_usada.size(texto)
    largura_fundo = medida[0] + 40
    altura_fundo = medida[1] + 24
    fundo = pygame.Surface((largura_fundo, altura_fundo), pygame.SRCALPHA)
    fundo.fill((0, 0, 0, 150))
    superficie.blit(fundo, (centro_x - largura_fundo // 2, centro_y - altura_fundo // 2))


# ==============================================================================
# === TRANSIÇÃO (clarão ao tocar a nebulosa, trocando o cenário) ===
# ==============================================================================
ESTADO_PORTAL = "portal"
ESTADO_TRANSICAO = "transicao"
ESTADO_PRESENTE = "presente"

estado_cena = ESTADO_PORTAL
DURACAO_TRANSICAO = 50  # quadros (~0.8s a 60 quadros por segundo)
contador_transicao = 0
fundo_ja_trocado_na_transicao = False

# ==============================================================================
# === CONFETES (comemoração ao chegar no presente) ===
# ==============================================================================
CORES_CONFETE = [
    (230, 60, 60), (60, 150, 230), (250, 210, 40),
    (60, 200, 120), (200, 80, 220), (250, 140, 40),
]
NUM_CONFETES = 120
confetes = []


def criar_confete_no_topo():
    return {
        "x": random.uniform(0, LARGURA_JANELA),
        "y": random.uniform(-ALTURA_JANELA, 0),
        "vx": random.uniform(-1.0, 1.0),
        "vy": random.uniform(2.0, 5.0),
        "tamanho": random.randint(6, 12),
        "cor": random.choice(CORES_CONFETE),
        "angulo": random.uniform(0, 360),
        "velocidade_giro": random.uniform(-6, 6),
    }


def iniciar_confetes():
    confetes.clear()
    for _ in range(NUM_CONFETES):
        confetes.append(criar_confete_no_topo())


def atualizar_confetes():
    for confete in confetes:
        confete["x"] += confete["vx"]
        confete["y"] += confete["vy"]
        confete["angulo"] = (confete["angulo"] + confete["velocidade_giro"]) % 360
        # Ao sair por baixo da tela, volta pro topo numa posição nova, pra
        # chuva de confete não parar nunca.
        if confete["y"] > ALTURA_JANELA + 20:
            confete["x"] = random.uniform(0, LARGURA_JANELA)
            confete["y"] = random.uniform(-40, -10)


def desenhar_confetes(superficie):
    for confete in confetes:
        tamanho = confete["tamanho"]
        quadrado = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        quadrado.fill(confete["cor"])
        quadrado_girado = pygame.transform.rotate(quadrado, confete["angulo"])
        rect_confete = quadrado_girado.get_rect(center=(confete["x"], confete["y"]))
        superficie.blit(quadrado_girado, rect_confete)


# ==============================================================================
# === SONS (música de fundo em loop e som de clique) ===
# ==============================================================================
VOLUME_MUSICA = 0.35
tocar_musica_de_fundo_segura(ASSETS["musica_fundo"], VOLUME_MUSICA)
som_clique = carregar_som_seguro(ASSETS["som_clique"])


def tocar_som_clique():
    if som_clique is not None:
        som_clique.play()


# ==============================================================================
# === LOOP PRINCIPAL DO JOGO ===
# ==============================================================================
rodando = True
while rodando:
    relogio.tick(60)
    tempo_atual_ms = pygame.time.get_ticks()
    personagem_andou = False

    # -------------------------------------------------------------------
    # --- EVENTOS ---
    # -------------------------------------------------------------------
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            rodando = False

    # -------------------------------------------------------------------
    # --- ATUALIZAÇÃO: MOVIMENTO DO PERSONAGEM (só na sala do portal) ---
    # Aceita tanto as setas quanto WASD, nas quatro direções. Diagonais são
    # normalizadas (divididas por raiz de 2) pra não andar mais rápido na
    # diagonal do que em linha reta.
    # -------------------------------------------------------------------
    if estado_cena == ESTADO_PORTAL:
        teclas = pygame.key.get_pressed()
        direcao_x = 0
        direcao_y = 0
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            direcao_x -= 1
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            direcao_x += 1
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            direcao_y -= 1
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            direcao_y += 1

        if direcao_x != 0 or direcao_y != 0:
            personagem_andou = True
            fator_normalizacao = math.sqrt(2) if (direcao_x != 0 and direcao_y != 0) else 1
            personagem_centro_x += (direcao_x / fator_normalizacao) * VELOCIDADE_PERSONAGEM
            personagem_pe_y += (direcao_y / fator_normalizacao) * VELOCIDADE_PERSONAGEM
            if direcao_x != 0:
                virado_para_esquerda = direcao_x < 0

        personagem_pe_y = max(PE_PERSONAGEM_Y_MIN, min(personagem_pe_y, PE_PERSONAGEM_Y_MAX))

    # -------------------------------------------------------------------
    # --- ATUALIZAÇÃO: ANIMAÇÃO DO PERSONAGEM ---
    # -------------------------------------------------------------------
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
    personagem_pos_y = personagem_pe_y - altura_atual

    # -------------------------------------------------------------------
    # --- ATUALIZAÇÃO: TOQUE NA NEBULOSA (dispara a transição) ---
    # -------------------------------------------------------------------
    if estado_cena == ESTADO_PORTAL:
        if personagem_tocou_nebulosa(personagem_centro_x, personagem_pe_y, altura_atual):
            tocar_som_clique()
            estado_cena = ESTADO_TRANSICAO
            contador_transicao = 0
            fundo_ja_trocado_na_transicao = False

    # -------------------------------------------------------------------
    # --- ATUALIZAÇÃO: TRANSIÇÃO (clarão que troca o cenário na metade) ---
    # -------------------------------------------------------------------
    elif estado_cena == ESTADO_TRANSICAO:
        contador_transicao += 1
        progresso_transicao = contador_transicao / DURACAO_TRANSICAO

        # Troca o fundo (e reposiciona o personagem na nova cena) só uma
        # vez, no meio da transição, quando a tela já está bem clara —
        # assim a troca fica escondida atrás do clarão.
        if progresso_transicao >= 0.5 and not fundo_ja_trocado_na_transicao:
            fundo_atual = imagem_presente
            personagem_centro_x = LARGURA_JANELA // 2
            personagem_pe_y = PE_PERSONAGEM_Y_MAX
            virado_para_esquerda = False
            fundo_ja_trocado_na_transicao = True

        if contador_transicao >= DURACAO_TRANSICAO:
            estado_cena = ESTADO_PRESENTE
            iniciar_confetes()

    # -------------------------------------------------------------------
    # --- ATUALIZAÇÃO: CENA DO PRESENTE (confetes caindo) ---
    # -------------------------------------------------------------------
    elif estado_cena == ESTADO_PRESENTE:
        atualizar_confetes()

    # =====================================================================
    # === DESENHO ===
    # =====================================================================
    tela.blit(fundo_atual, (0, 0))

    if estado_cena == ESTADO_PORTAL:
        desenhar_nebulosa(tela, tempo_atual_ms)
        tela.blit(imagem_personagem, (personagem_pos_x, personagem_pos_y))

        desenhar_fundo_mensagem(tela, TEXTO_MENSAGEM_NEBULOSA, fonte_mensagem, LARGURA_JANELA // 2, 50)
        desenhar_texto_com_brilho(
            tela, TEXTO_MENSAGEM_NEBULOSA, fonte_mensagem,
            (255, 255, 255), (40, 10, 70), (170, 130, 255),
            LARGURA_JANELA // 2, 50, tempo_atual_ms,
        )

    elif estado_cena == ESTADO_TRANSICAO:
        tela.blit(imagem_personagem, (personagem_pos_x, personagem_pos_y))

        # Clarão: sobe a opacidade de um branco até o topo (metade da
        # transição) e depois desce, revelando o novo cenário por trás.
        # Recalculado aqui (em vez de reaproveitar a variável da etapa de
        # atualização) porque no primeiro quadro da transição o estado muda
        # dentro do bloco do ESTADO_PORTAL, então essa variável ainda não
        # teria sido definida neste quadro.
        progresso_visual_transicao = contador_transicao / DURACAO_TRANSICAO
        alpha_clarao = round(255 * math.sin(min(progresso_visual_transicao, 1.0) * math.pi))
        superficie_clarao = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA), pygame.SRCALPHA)
        superficie_clarao.fill((255, 255, 255, alpha_clarao))
        tela.blit(superficie_clarao, (0, 0))

    elif estado_cena == ESTADO_PRESENTE:
        tela.blit(imagem_personagem, (personagem_pos_x, personagem_pos_y))
        desenhar_confetes(tela)

        desenhar_fundo_mensagem(tela, "PARABÉNS!", fonte_vitoria, LARGURA_JANELA // 2, 60)
        desenhar_texto_com_brilho(
            tela, "PARABÉNS!", fonte_vitoria,
            (255, 250, 210), (90, 60, 0), (255, 220, 80),
            LARGURA_JANELA // 2, 60, tempo_atual_ms,
        )

    pygame.display.flip()

pygame.quit()
sys.exit()

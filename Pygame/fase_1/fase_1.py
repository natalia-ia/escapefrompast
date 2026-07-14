"""
Escape Room - Fase 1 (Ábaco)
Jogo básico feito com Pygame: personagem anda pela sala, clica no ábaco
quebrado, resolve uma conta e libera a porta para a próxima fase.
"""
#Explicação da primeira parte do código:
# Foi importado as bibliotecas usadas no jogo: pygame (para criar o jogo),
# O random foi usado para sortear números da conta matemática e sys (para encerrar o programa corretamente ao fechar o jogo).
# Por diante, inicializa o Pygame, é definido o tamanho da janela do jogo,
# é criado a janela com esse tamanho, é definido o título que aparece na barra
# da janela, e é criado um "relógio" que controla quantas vezes por segundo
# o jogo atualiza a tela (60 vezes por segundo, mais à frente no código).
import math
import os
import pygame
import random
import sys
import threading

import ollama

pygame.init()

# ---------------------------------------------------------------------------
# Monta caminhos de assets a partir da pasta onde este arquivo .py está,
# em vez de depender da pasta de onde o jogo é executado. Sem isso, rodar
# o jogo a partir de outra pasta (ex: um diretório acima) faz o Pygame não
# achar as imagens/fontes, porque os caminhos "assets/..." eram relativos
# à pasta atual do terminal, não à pasta do projeto.
# ---------------------------------------------------------------------------
PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))


def caminho_asset(nome_relativo):
    """Monta o caminho absoluto de um asset a partir da pasta 'assets'
    ao lado deste arquivo .py."""
    return os.path.join(PASTA_DO_SCRIPT, nome_relativo)

# ---------------------------------------------------------------------------
# Janela do jogo
# ---------------------------------------------------------------------------
LARGURA_JANELA = 960
ALTURA_JANELA = 600

tela = pygame.display.set_mode((LARGURA_JANELA, ALTURA_JANELA))
pygame.display.set_caption("Escape Room - Fase do Ábaco")
relogio = pygame.time.Clock()

# ---------------------------------------------------------------------------
# Enquanto o menu de escolha de personagem não fica pronto, essa variável
# permite trocar manualmente qual personagem é carregado no jogo:
# 0 = para rodar com o primeiro personagem, 1 = para o segundo personagem.
# ---------------------------------------------------------------------------
PERSONAGEM_ESCOLHIDO = 1

# ---------------------------------------------------------------------------
# ASSETS: dicionário centralizado com TODOS os caminhos de imagem/fonte
# usados no jogo, cada um montado com caminho_asset() a partir da pasta
# onde este arquivo .py está salvo. Em vez de ter caminhos soltos
# espalhados pelo código, tudo fica reunido aqui — para adicionar ou trocar
# um asset, basta mexer neste dicionário.
# ---------------------------------------------------------------------------
ASSETS = {
    "fundo_quebrado": caminho_asset("assets/imagens/cenarios/fase_abaco/cenario_abaco_quebrado.png"),
    "fundo_consertado": caminho_asset("assets/imagens/cenarios/fase_abaco/cenario_abaco_consertado.png"),
    "gerbert_retrato": caminho_asset("assets/imagens/cenarios/fase_abaco/gerbert_retrato.png"),
    "capsula_do_tempo": caminho_asset("assets/imagens/cenarios/fase_abaco/capsula_do_tempo.png"),
    "fonte_pixel": caminho_asset("assets/fontes/PressStart2P-Regular.ttf"),
    "pasta_personagem_1": caminho_asset("assets/imagens/personagem/"),
    "pasta_personagem_2": caminho_asset("assets/imagens/personagem2/"),
    "musica_fundo": caminho_asset("assets/sons/musica_fundo.ogg"),
    "som_clique": caminho_asset("assets/sons/som_clique.wav"),
}

# ---------------------------------------------------------------------------
# Definido os caminhos das pastas/imagens usadas no jogo. A pasta do
# personagem fica guardada em uma única variável, para facilitar trocar
# por outro personagem no futuro.
#
# Em seguida, carrega as duas imagens de cenário (ábaco quebrado e ábaco
# consertado) e é redimensionado cada uma para caber exatamente no tamanho da
# janela do jogo. A variável fundo_atual guarda qual das duas imagens está
# sendo exibida no momento — o jogo começa com o cenário quebrado.
# ---------------------------------------------------------------------------
PASTAS_PERSONAGEM = [
    ASSETS["pasta_personagem_1"],
    ASSETS["pasta_personagem_2"],
]
PASTA_PERSONAGEM = PASTAS_PERSONAGEM[PERSONAGEM_ESCOLHIDO]

# ---------------------------------------------------------------------------
# Fundo da cena (redimensionado para caber exatamente na janela)
# ---------------------------------------------------------------------------
fundo_quebrado = pygame.transform.scale(
    pygame.image.load(ASSETS["fundo_quebrado"]).convert(), (LARGURA_JANELA, ALTURA_JANELA)
)
fundo_consertado = pygame.transform.scale(
    pygame.image.load(ASSETS["fundo_consertado"]).convert(), (LARGURA_JANELA, ALTURA_JANELA)
)
fundo_atual = fundo_quebrado

# ---------------------------------------------------------------------------
# Personagem
# As imagens têm proporções (largura x altura) diferentes entre si, então
# aplicamos o MESMO fator de escala a todas, em vez de forçar cada uma numa
# caixa fixa — isso aumenta o personagem sem esticar ou distorcer nenhuma
# das poses.
# ---------------------------------------------------------------------------
ALTURA_PERSONAGEM_ALVO = 330  # ~27% maior que os 260px anteriores (era ~170 originalmente)


def carregar_imagem_personagem(nome_arquivo, fator_escala):
    imagem = pygame.image.load(PASTA_PERSONAGEM + nome_arquivo).convert_alpha()
    largura_original, altura_original = imagem.get_size()
    novo_tamanho = (round(largura_original * fator_escala), round(altura_original * fator_escala))
    return pygame.transform.scale(imagem, novo_tamanho)


# O fator foi calculado a partir da imagem parada e reaplicado nas demais, para que
# todas cresçam na mesma proporção.
_altura_original_parado = pygame.image.load(PASTA_PERSONAGEM + "personagem_parado_frente.png").get_height()
FATOR_ESCALA_PERSONAGEM = ALTURA_PERSONAGEM_ALVO / _altura_original_parado

imagem_parado = carregar_imagem_personagem("personagem_parado_frente.png", FATOR_ESCALA_PERSONAGEM)
imagens_andando = [
    carregar_imagem_personagem("personagem_andando_lado_1.png", FATOR_ESCALA_PERSONAGEM),
    carregar_imagem_personagem("personagem_andando_lado_2.png", FATOR_ESCALA_PERSONAGEM),
]
#---------------------------------------------------------------------------
# Foi definido a posição inicial e velocidade do personagem, além das
# variáveis que controlam a animação de caminhada (direção, quadro
# atual e contador de troca de quadro).
#----------------------------------------------------------------------------
PE_PERSONAGEM_Y = ALTURA_JANELA - 20
VELOCIDADE_PERSONAGEM = 4
personagem_centro_x = LARGURA_JANELA // 2  # começa parado no centro da janela

virado_para_esquerda = False   # usado para espelhar o sprite ao andar p/ esquerda
quadro_animacao = 0            # qual das duas imagens de andar está ativa
contador_animacao = 0          # conta os quadros até trocar de imagem de andar

# ---------------------------------------------------------------------------
# Foi usado para calcular a escala entre a imagem original do cenário e o tamanho da
# janela, para posicionar corretamente as áreas clicáveis do ábaco e
# da porta em qualquer tamanho de tela.
# ---------------------------------------------------------------------------
ESCALA_X = LARGURA_JANELA / 1456
ESCALA_Y = ALTURA_JANELA / 720


def escalar_retangulo(x, y, largura, altura):
    return pygame.Rect(x * ESCALA_X, y * ESCALA_Y, largura * ESCALA_X, altura * ESCALA_Y)


AREA_ABACO = escalar_retangulo(315, 280, 210, 170)   # ábaco em cima da mesa
AREA_PORTA = escalar_retangulo(1150, 230, 165, 295)  # porta do lado direito

# ---------------------------------------------------------------------------
# Cápsula do tempo: um objeto decorativo do cenário, apoiada no chão do
# lado esquerdo da tela. Usa convert_alpha() para preservar a transparência
# do PNG (diferente do fundo, que usa convert() porque ocupa a tela inteira
# sem partes transparentes).
#
# O arquivo original (2624x1632) tem uma margem transparente enorme ao
# redor do desenho (~66% da imagem é vazio) — isso fazia a cápsula parecer
# pequena mesmo em alturas grandes, porque boa parte da altura/largura
# "gasta" era espaço vazio. get_bounding_rect() encontra o retângulo exato
# do conteúdo visível e recortamos só essa parte antes de redimensionar,
# então toda a altura escolhida vira cápsula de verdade, sem desperdício.
#
# Isso também muda a proporção: sem a margem, o desenho é quase quadrado
# (~1.05:1), bem diferente do 1.6:1 do canvas inteiro.
#
# Posição: a borda DIREITA fica ancorada quase encostando no início do
# ábaco (perto da mesa, sem cobrir o ábaco) — esse é o ponto fixo. A altura
# é definida diretamente (não mais "a máxima que cabe sem cortar"), então
# se ela ficar larga demais para caber inteira, a borda ESQUERDA é que
# passa da tela e é cortada; a base continua apoiada no chão na mesma
# posição, então ela só cresce "para cima".
# ---------------------------------------------------------------------------
imagem_capsula_bruta = pygame.image.load(ASSETS["capsula_do_tempo"]).convert_alpha()
imagem_capsula_original = imagem_capsula_bruta.subsurface(
    imagem_capsula_bruta.get_bounding_rect(min_alpha=10)
).copy()

MARGEM_CAPSULA_ABACO = 5  # folga entre a cápsula e o início do ábaco, pra não encostar "grudado"
ALTURA_CAPSULA_ALVO = 330  # ~18% maior que os 280px anteriores
_fator_escala_capsula = ALTURA_CAPSULA_ALVO / imagem_capsula_original.get_height()

imagem_capsula = pygame.transform.scale(
    imagem_capsula_original,
    (round(imagem_capsula_original.get_width() * _fator_escala_capsula), ALTURA_CAPSULA_ALVO),
)

CAPSULA_POS_X = AREA_ABACO.left - MARGEM_CAPSULA_ABACO - imagem_capsula.get_width()
CAPSULA_POS_Y = ALTURA_JANELA - 20 - imagem_capsula.get_height()  # apoiada no chão

# ---------------------------------------------------------------------------
# Gerbert de Aurillac aparece como um retrato redondo (recortado em círculo
# a partir da imagem original), em vez de solto no cenário: um ícone
# pequeno fica fixo num canto da tela (clicável, para abrir a conversa
# livre depois da introdução), e um avatar um pouco maior aparece grudado
# em cima da caixinha enquanto a conversa está acontecendo — como em jogos
# de RPG com caixa de diálogo.
#
# convert_alpha() já é usado ao carregar a imagem, para preservar
# transparência caso o arquivo tenha canal alfa; hoje o arquivo
# gerbert_retrato.png não tem nenhum pixel transparente (fundo é opaco),
# então o recorte em círculo é o que garante o formato redondo.
# ---------------------------------------------------------------------------
imagem_gerbert_original = pygame.image.load(ASSETS["gerbert_retrato"]).convert_alpha()


def recortar_em_circulo(imagem):
    """Recorta uma imagem quadrada em um círculo, usado para deixar o
    retrato do Gerbert redondo."""
    tamanho = imagem.get_size()
    mascara_circulo = pygame.Surface(tamanho, pygame.SRCALPHA)
    pygame.draw.circle(
        mascara_circulo, (255, 255, 255, 255),
        (tamanho[0] // 2, tamanho[1] // 2), tamanho[0] // 2,
    )
    imagem_recortada = imagem.copy()
    imagem_recortada.blit(mascara_circulo, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return imagem_recortada


TAMANHO_ICONE_GERBERT = 60    # ícone pequeno, fixo num canto da tela
TAMANHO_AVATAR_GERBERT = 80   # avatar maior, exibido acima da caixinha

imagem_gerbert_icone = recortar_em_circulo(
    pygame.transform.smoothscale(imagem_gerbert_original, (TAMANHO_ICONE_GERBERT, TAMANHO_ICONE_GERBERT))
)
imagem_gerbert_avatar = recortar_em_circulo(
    pygame.transform.smoothscale(imagem_gerbert_original, (TAMANHO_AVATAR_GERBERT, TAMANHO_AVATAR_GERBERT))
)

MARGEM_ICONE_GERBERT = 15
AREA_GERBERT = pygame.Rect(
    MARGEM_ICONE_GERBERT, MARGEM_ICONE_GERBERT, TAMANHO_ICONE_GERBERT, TAMANHO_ICONE_GERBERT
)

# Tamanho e posição da caixinha de conversa com o Gerbert, definidos aqui
# (em vez de só dentro do desenho) porque também são usados para calcular
# até onde o jogador pode digitar sem o texto vazar da caixinha.
CAIXA_GERBERT_LARGURA, CAIXA_GERBERT_ALTURA = 320, 225
MARGEM_CAIXA_GERBERT = 20
LARGURA_TEXTO_CAIXA_GERBERT = CAIXA_GERBERT_LARGURA - 30  # largura útil pro texto, descontando as margens

# ---------------------------------------------------------------------------
# Variáveis de estado da atividade da fase: se o cenário foi consertado, se a
# caixa da conta está aberta, a resposta digitada e os dados da conta.
# ---------------------------------------------------------------------------
cenario_consertado = False
caixa_matematica_aberta = False
resposta_digitada = ""

# ---------------------------------------------------------------------------
# Agora é preciso acertar várias contas seguidas para consertar o ábaco, em
# vez de apenas uma. ACERTOS_NECESSARIOS guarda quantas são necessárias e
# acertos_atuais conta quantas o jogador já acertou na tentativa atual.
# ---------------------------------------------------------------------------
ACERTOS_NECESSARIOS = 3
acertos_atuais = 0

# ---------------------------------------------------------------------------
# MELHORIA 3 (contador de tentativas): conta quantas vezes o jogador
# confirmou uma resposta na conta matemática, certa ou errada — só pra dar
# sensação de progresso, não limita nem pune o jogador.
# ---------------------------------------------------------------------------
tentativas_abaco = 0

# ---------------------------------------------------------------------------
# MELHORIA 4 (efeito ao acertar): partículas (pequenas "faíscas") que voam
# a partir do ábaco quando o jogador acerta uma conta, e um flash rápido de
# cor que cobre a tela por alguns quadros. Cada partícula é um dicionário
# com posição, velocidade, vida restante (em quadros) e cor.
# ---------------------------------------------------------------------------
particulas_acerto = []
tempo_flash_acerto = 0  # quantos quadros o flash ainda deve aparecer

# ---------------------------------------------------------------------------
# A caixinha do Gerbert só aparece quando o jogador clica no ícone dele — a
# conversa NÃO abre sozinha no início. A conversa tem duas falas fixas no
# começo (sem IA, então nunca travam) e depois libera uma conversa livre
# opcional usando IA:
#   0) ETAPA_NAO_INICIADA -> estado inicial, caixinha fechada; o primeiro
#      clique no ícone do Gerbert abre a caixinha e começa a apresentação.
#   1) ETAPA_APRESENTACAO -> Gerbert pergunta quem o jogador é/de onde veio;
#      o jogador digita algo e aperta Enter para continuar.
#   2) ETAPA_DICA_ABACO   -> Gerbert avisa sobre o ábaco quebrado; Enter
#      fecha a caixinha e libera o jogo normal.
#   3) ETAPA_PRONTO       -> caixinha fechada, esperando um novo clique no
#      Gerbert para abrir a conversa livre.
#   4) ETAPA_LIVRE        -> conversa livre, usando IA para as respostas.
# ---------------------------------------------------------------------------
ETAPA_NAO_INICIADA = "nao_iniciada"
ETAPA_APRESENTACAO = "apresentacao"
ETAPA_DICA_ABACO = "dica_abaco"
ETAPA_PRONTO = "pronto"
ETAPA_LIVRE = "livre"

etapa_conversa_gerbert = ETAPA_NAO_INICIADA
caixa_gerbert_aberta = False    # só abre quando o jogador clica no ícone do Gerbert
texto_digitado_gerbert = ""     # o que o jogador está digitando no momento
resposta_gerbert = ""           # última resposta da IA (só usada na conversa livre)
gerbert_pensando = False        # true enquanto espera a IA responder

FALA_GERBERT_APRESENTACAO = "Olá, viajante! Quem é você? De onde você veio?"
FALA_GERBERT_DICA_ABACO = (
    "Interessante... Para sair desta época, clique no ábaco ali na mesa "
    "e resolva as contas para consertá-lo. Boa sorte!"
)
FALA_GERBERT_CONVITE_LIVRE = "O que você gostaria de me perguntar?"

# Instrução de sistema enviada ao modelo para ele sempre responder no papel
# do Gerbert. Usada só na conversa livre — as duas primeiras falas são
# fixas e não passam pela IA.
PROMPT_SISTEMA_GERBERT = (
    "Você é Gerbert de Aurillac, um monge medieval estudioso de matemática "
    "e astronomia. Responda sempre em português, de forma breve (1-2 "
    "frases), com tom leve e gentil, adequado para a primeira fase de um "
    "jogo educativo."
)

# ---------------------------------------------------------------------------
# Modelo usado no Ollama: qwen2.5:0.5b é bem menor que o llama3.2, então
# roda mais rápido em computadores com pouca memória disponível.
#
# O cliente usa um tempo limite (timeout) curto: sem isso, se o Ollama não
# estiver rodando ou demorar demais, a chamada fica esperando para sempre e
# trava a caixinha em "Gerbert está pensando...".
# ---------------------------------------------------------------------------
MODELO_GERBERT = "qwen2.5:0.5b"
TIMEOUT_OLLAMA_SEGUNDOS = 30  # testado na prática: uma resposta levou ~16s
cliente_ollama = ollama.Client(timeout=TIMEOUT_OLLAMA_SEGUNDOS)


def perguntar_ao_gerbert(pergunta):
    """Chama o modelo qwen2.5:0.5b (rodando localmente via Ollama) pedindo
    uma resposta como se fosse o Gerbert. Roda em uma thread separada para
    não travar a janela do jogo enquanto espera a resposta chegar."""
    global resposta_gerbert, gerbert_pensando
    try:
        resultado = cliente_ollama.chat(
            model=MODELO_GERBERT,
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA_GERBERT},
                {"role": "user", "content": pergunta},
            ],
        )
        resposta_gerbert = resultado["message"]["content"].strip()
    except Exception:
        # Cobre timeout, Ollama fora do ar ou qualquer outro erro de conexão.
        resposta_gerbert = "Gerbert não pôde responder agora."
    gerbert_pensando = False


def quebrar_texto(texto, fonte, largura_maxima):
    """Quebra um texto em várias linhas para caber dentro de uma largura
    máxima, usado para exibir a resposta do Gerbert na caixinha."""
    palavras = texto.split(" ")
    linhas = []
    linha_atual = ""
    for palavra in palavras:
        linha_testada = (linha_atual + " " + palavra).strip()
        if fonte.size(linha_testada)[0] <= largura_maxima:
            linha_atual = linha_testada
        else:
            if linha_atual:
                linhas.append(linha_atual)
            linha_atual = palavra
    if linha_atual:
        linhas.append(linha_atual)
    return linhas


numero_a = 0
numero_b = 0
operador = "+"
resposta_correta = 0

#-----------------------------------------------------------------------
# Sorteia uma conta matemática (soma, subtração ou multiplicação) com
# números entre 1 e 12, evitando resultado negativo na subtração.
#Decidimos operações mais fáceis por ser a fase 1
#------------------------------------------------------------------------

def gerar_nova_conta():
    """Sorteia uma conta simples (soma, subtração ou multiplicação)."""
    global numero_a, numero_b, operador, resposta_correta

    operador = random.choice(["+", "-", "*"])

    # A multiplicação usa números menores (1 a 6) para o resultado não
    # passar de 36 e continuar simples de calcular de cabeça; soma e
    # subtração seguem com números entre 1 e 12, como já era.
    if operador == "*":
        numero_a = random.randint(1, 6)
        numero_b = random.randint(1, 6)
    else:
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
# Controla as mensagens temporárias na tela (sucesso/erro) e foi usado para definir as
# fontes de texto usadas no jogo.
# ---------------------------------------------------------------------------
mensagem_atual = ""
tempo_mensagem = 0  # quantos quadros a mensagem ainda deve ficar visível

# ---------------------------------------------------------------------------
# Fonte pixelada (estilo jogos retrô) usada em toda a interface do jogo, em
# vez da fonte padrão do sistema. Como cada caractere dessa fonte ocupa bem
# mais espaço que uma fonte comum, os tamanhos são bem menores que antes, e
# os textos mais longos são quebrados em várias linhas (função
# desenhar_texto_multilinha) para nunca vazar para fora das caixinhas.
# ---------------------------------------------------------------------------
ESPACAMENTO_LINHA = 16  # distância vertical entre linhas de texto quebrado

fonte = pygame.font.Font(ASSETS["fonte_pixel"], 10)
fonte_grande = pygame.font.Font(ASSETS["fonte_pixel"], 16)
fonte_vitoria = pygame.font.Font(ASSETS["fonte_pixel"], 24)  # usada só na mensagem de vitória na porta


def desenhar_texto_multilinha(superficie, texto, fonte_usada, cor, x, y, largura_maxima, espacamento=ESPACAMENTO_LINHA):
    """Quebra o texto para caber em largura_maxima e desenha uma linha
    embaixo da outra, começando em (x, y). Devolve o y logo depois da
    última linha desenhada, útil para posicionar o que vem a seguir."""
    for linha in quebrar_texto(texto, fonte_usada, largura_maxima):
        superficie.blit(fonte_usada.render(linha, True, cor), (x, y))
        y += espacamento
    return y


# ---------------------------------------------------------------------------
# Desenha um texto com contorno grosso: renderiza o texto várias vezes na
# cor do contorno, deslocado alguns pixels em cada direção ao redor do
# centro, e por cima desenha o texto de verdade na cor principal — a
# técnica clássica de jogos retrô pra garantir contraste em cima de
# qualquer fundo, sem precisar de imagem nenhuma.
# ---------------------------------------------------------------------------
def desenhar_texto_com_contorno(superficie, texto, fonte_usada, cor_texto, cor_contorno, centro_x, centro_y, espessura=2):
    superficie_texto = fonte_usada.render(texto, True, cor_texto)
    superficie_contorno = fonte_usada.render(texto, True, cor_contorno)
    rect_texto = superficie_texto.get_rect(center=(centro_x, centro_y))

    for dx in (-espessura, 0, espessura):
        for dy in (-espessura, 0, espessura):
            if dx == 0 and dy == 0:
                continue
            superficie.blit(superficie_contorno, (rect_texto.x + dx, rect_texto.y + dy))

    superficie.blit(superficie_texto, rect_texto)


# ---------------------------------------------------------------------------
# MELHORIA 1 (feedback visual no ábaco): desenha um contorno dourado
# pulsante ao redor de AREA_ABACO quando o mouse está em cima, indicando
# que é clicável. Usa uma superfície separada com SRCALPHA porque
# pygame.draw não desenha com transparência direto na tela.
# ---------------------------------------------------------------------------
def desenhar_brilho_abaco(superficie, area, tempo_ms):
    pulso = (math.sin(tempo_ms / 200) + 1) / 2  # oscila suavemente entre 0 e 1
    expansao = round(4 + pulso * 6)             # o contorno "respira" entre 4 e 10px de folga
    alpha = round(120 + pulso * 100)             # e também varia de opacidade (120 a 220)

    contorno = area.inflate(expansao * 2, expansao * 2)
    brilho = pygame.Surface(contorno.size, pygame.SRCALPHA)
    pygame.draw.rect(brilho, (255, 220, 80, alpha), brilho.get_rect(), width=4, border_radius=8)
    superficie.blit(brilho, contorno.topleft)


# ---------------------------------------------------------------------------
# MELHORIA 4 (efeito ao acertar): cria as partículas que "explodem" a
# partir do centro do ábaco e liga o flash de tela, chamada toda vez que o
# jogador acerta uma conta.
# ---------------------------------------------------------------------------
CORES_PARTICULA_ACERTO = [(255, 215, 0), (255, 255, 255), (255, 190, 60)]


def disparar_efeito_acerto():
    global tempo_flash_acerto
    tempo_flash_acerto = 10
    for _ in range(18):
        angulo = random.uniform(0, 2 * math.pi)
        velocidade = random.uniform(1.5, 4)
        particulas_acerto.append({
            "x": float(AREA_ABACO.centerx),
            "y": float(AREA_ABACO.centery),
            "vx": math.cos(angulo) * velocidade,
            "vy": math.sin(angulo) * velocidade,
            "vida": random.randint(20, 40),
            "cor": random.choice(CORES_PARTICULA_ACERTO),
        })


# ---------------------------------------------------------------------------
# MELHORIA 2 (tela de introdução): mostrada uma única vez antes do jogo
# começar, com um texto situando o jogador na história. Fica num loop
# próprio (igual ao loop principal, mas mais simples) até o jogador
# apertar qualquer tecla.
# ---------------------------------------------------------------------------
TEXTO_INTRODUCAO = (
    "Ano 1000. Você acordou numa sala estranha, cercado por pergaminhos "
    "e um velho ábaco quebrado. Alguém te observa das sombras..."
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


# ---------------------------------------------------------------------------
# Sons do jogo: a música de fundo começa a tocar em loop assim que o jogo
# abre, num volume moderado para não atrapalhar; o som de clique é tocado
# nas interações importantes (clicar no ábaco, clicar no Gerbert).
# ---------------------------------------------------------------------------
pygame.mixer.music.load(ASSETS["musica_fundo"])
pygame.mixer.music.set_volume(0.35)
pygame.mixer.music.play(-1)  # -1 = toca em loop infinito

som_clique = pygame.mixer.Sound(ASSETS["som_clique"])

tela_introducao()

# ---------------------------------------------------------------------------
# Loop principal do jogo: roda continuamente a 60 quadros por segundo,
# verificando eventos como clicar no ábaco para
# abrir a caixa da conta matemática.
# ---------------------------------------------------------------------------
rodando = True
while rodando:
    relogio.tick(60)
    personagem_andou = False

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

        if evento.type == pygame.MOUSEBUTTONDOWN:
            if not cenario_consertado and not caixa_matematica_aberta and not caixa_gerbert_aberta:
                if AREA_ABACO.collidepoint(evento.pos):
                    som_clique.play()
                    caixa_matematica_aberta = True
                    resposta_digitada = ""
                    gerar_nova_conta()

            # Clicar no ícone do Gerbert abre a caixinha: da primeira vez,
            # começa a apresentação fixa; nas próximas vezes (depois que a
            # introdução já terminou), abre a conversa livre com a IA.
            if (
                not caixa_matematica_aberta
                and not caixa_gerbert_aberta
                and etapa_conversa_gerbert in (ETAPA_NAO_INICIADA, ETAPA_PRONTO)
            ):
                if AREA_GERBERT.collidepoint(evento.pos):
                    som_clique.play()
                    caixa_gerbert_aberta = True
                    if etapa_conversa_gerbert == ETAPA_NAO_INICIADA:
                        etapa_conversa_gerbert = ETAPA_APRESENTACAO
                    else:
                        etapa_conversa_gerbert = ETAPA_LIVRE
                    texto_digitado_gerbert = ""
                    resposta_gerbert = ""
                    gerbert_pensando = False

        #---------------------------------------------------------------------
        # É analisado a digitação da conta: Enter confirma e verifica se está
        # certa ou errada; Backspace apaga; números são adicionados à
        # resposta.
        #
        # Se acertar, soma 1 ao contador de acertos. Enquanto o contador não
        # chegar em ACERTOS_NECESSARIOS, a caixinha continua aberta e uma
        # nova conta é sorteada na hora, sem resetar o que já foi acertado.
        # Só quando completa as 3 contas seguidas é que o cenário é
        # consertado e a caixinha fecha de vez.
        # Se errar, o comportamento continua o mesmo de antes: mostra a
        # mensagem de erro e sorteia outra conta, mas sem mexer no contador
        # de acertos já feitos.
        if evento.type == pygame.KEYDOWN and caixa_matematica_aberta:
            if evento.key == pygame.K_RETURN:
                if resposta_digitada != "":
                    tentativas_abaco += 1  # MELHORIA 3: conta toda confirmação, certa ou errada
                    if int(resposta_digitada) == resposta_correta:
                        disparar_efeito_acerto()  # MELHORIA 4: partículas + flash
                        acertos_atuais += 1
                        resposta_digitada = ""
                        if acertos_atuais >= ACERTOS_NECESSARIOS:
                            cenario_consertado = True
                            fundo_atual = fundo_consertado
                            caixa_matematica_aberta = False
                            mensagem_atual = "Parabéns! A conta está certa."
                            tempo_mensagem = 120
                        else:
                            gerar_nova_conta()
                    else:
                        mensagem_atual = "Resposta errada, tente de novo!"
                        tempo_mensagem = 90
                        resposta_digitada = ""
                        gerar_nova_conta()
            elif evento.key == pygame.K_BACKSPACE:
                resposta_digitada = resposta_digitada[:-1]
            elif evento.unicode.isdigit():
                resposta_digitada += evento.unicode

        #---------------------------------------------------------------------
        # É analisado a digitação na caixinha do Gerbert. O comportamento
        # muda de acordo com a etapa da conversa:
        if evento.type == pygame.KEYDOWN and caixa_gerbert_aberta:
            if etapa_conversa_gerbert == ETAPA_APRESENTACAO:
                # Primeira fala fixa (sem IA): o jogador digita quem é/de
                # onde veio; Enter só avança para a segunda fala fixa.
                if evento.key == pygame.K_RETURN:
                    if texto_digitado_gerbert != "":
                        texto_digitado_gerbert = ""
                        etapa_conversa_gerbert = ETAPA_DICA_ABACO
                elif evento.key == pygame.K_BACKSPACE:
                    texto_digitado_gerbert = texto_digitado_gerbert[:-1]
                elif evento.unicode.isprintable() and fonte.size(texto_digitado_gerbert + evento.unicode)[0] <= LARGURA_TEXTO_CAIXA_GERBERT:
                    texto_digitado_gerbert += evento.unicode

            elif etapa_conversa_gerbert == ETAPA_DICA_ABACO:
                # Segunda fala fixa (sem IA): só espera Enter para fechar a
                # caixinha e liberar o clique no ábaco.
                if evento.key == pygame.K_RETURN:
                    caixa_gerbert_aberta = False
                    etapa_conversa_gerbert = ETAPA_PRONTO

            elif etapa_conversa_gerbert == ETAPA_LIVRE:
                # Conversa livre (opcional): usa a IA numa thread separada,
                # com timeout, para não travar o jogo se o Ollama demorar ou
                # estiver fora do ar. Esc fecha a caixinha a qualquer momento.
                if evento.key == pygame.K_ESCAPE:
                    caixa_gerbert_aberta = False
                    etapa_conversa_gerbert = ETAPA_PRONTO
                elif evento.key == pygame.K_RETURN:
                    if texto_digitado_gerbert != "" and not gerbert_pensando:
                        gerbert_pensando = True
                        resposta_gerbert = ""
                        threading.Thread(
                            target=perguntar_ao_gerbert,
                            args=(texto_digitado_gerbert,),
                            daemon=True,
                        ).start()
                        texto_digitado_gerbert = ""
                elif evento.key == pygame.K_BACKSPACE:
                    if not gerbert_pensando:
                        texto_digitado_gerbert = texto_digitado_gerbert[:-1]
                elif (
                    not gerbert_pensando
                    and evento.unicode.isprintable()
                    and fonte.size(texto_digitado_gerbert + evento.unicode)[0] <= LARGURA_TEXTO_CAIXA_GERBERT
                ):
                    texto_digitado_gerbert += evento.unicode

    # -----------------------------------------------------------------------
    # Movimento do personagem, bloqueado enquanto a caixa da conta ou a
    # caixinha de conversa com o Gerbert estão abertas
    # -----------------------------------------------------------------------
    if not caixa_matematica_aberta and not caixa_gerbert_aberta:
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
    # Escolha da imagem do personagem 
    # as quais alternam entre os quadros de
    # caminhada se ele andou, ou usa a imagem parada; espelha se estiver
    # virado para a esquerda.
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
    #-----------------------------------------------------------------
    # Para calcular o tamanho e a posição do personagem na tela, mantendo-o
    # dentro dos limites da janela.
    largura_atual, altura_atual = imagem_personagem.get_size()

    
    personagem_centro_x = max(largura_atual // 2, min(personagem_centro_x, LARGURA_JANELA - largura_atual // 2))

    personagem_pos_x = personagem_centro_x - largura_atual // 2
    personagem_pos_y = PE_PERSONAGEM_Y - altura_atual

    # -----------------------------------------------------------------------
    # Verifica se o personagem encostou na porta só depois do ábaco pronto
    # -----------------------------------------------------------------------
    retangulo_personagem = pygame.Rect(personagem_pos_x, personagem_pos_y, largura_atual, altura_atual)
    chegou_na_porta = cenario_consertado and retangulo_personagem.colliderect(AREA_PORTA)

    # -----------------------------------------------------------------------
    # Desenho da tela e do personagem
    # -----------------------------------------------------------------------
    tela.blit(fundo_atual, (0, 0))

    # Cápsula do tempo, parada no chão do cenário.
    tela.blit(imagem_capsula, (CAPSULA_POS_X, CAPSULA_POS_Y))

    tela.blit(imagem_personagem, (personagem_pos_x, personagem_pos_y))

    # Ícone redondo do Gerbert, fixo num canto da tela; depois da conversa
    # inicial, clicar nele abre a conversa livre.
    tela.blit(imagem_gerbert_icone, (AREA_GERBERT.x, AREA_GERBERT.y))

    # -----------------------------------------------------------------------
    # MELHORIA 1: brilho pulsante ao redor do ábaco quando o mouse está em
    # cima dele, só enquanto ele ainda não foi consertado e nenhuma
    # caixinha está aberta (senão o brilho ficaria por baixo delas à toa).
    # -----------------------------------------------------------------------
    mouse_pos = pygame.mouse.get_pos()
    if (
        not cenario_consertado
        and not caixa_matematica_aberta
        and not caixa_gerbert_aberta
        and AREA_ABACO.collidepoint(mouse_pos)
    ):
        desenhar_brilho_abaco(tela, AREA_ABACO, pygame.time.get_ticks())

    # -----------------------------------------------------------------------
    # MELHORIA 4: atualiza e desenha as partículas do efeito de acerto (cada
    # uma anda um pouco e perde "vida"; quando a vida acaba, ela some), e o
    # flash de cor que cobre a tela por alguns quadros logo após acertar.
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
        superficie_flash = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA), pygame.SRCALPHA)
        alpha_flash = round(150 * (tempo_flash_acerto / 10))
        superficie_flash.fill((255, 255, 200, alpha_flash))
        tela.blit(superficie_flash, (0, 0))
        tempo_flash_acerto -= 1

    # -----------------------------------------------------------------------
    # MELHORIA 3: contador de tentativas, num canto discreto (com um fundo
    # semitransparente atrás, só pra ficar legível em cima do cenário).
    # -----------------------------------------------------------------------
    texto_tentativas = fonte.render(f"Tentativas: {tentativas_abaco}", True, (255, 255, 255))
    pos_tentativas_x = LARGURA_JANELA - texto_tentativas.get_width() - 15
    fundo_tentativas = pygame.Surface(
        (texto_tentativas.get_width() + 10, texto_tentativas.get_height() + 6), pygame.SRCALPHA
    )
    fundo_tentativas.fill((0, 0, 0, 120))
    tela.blit(fundo_tentativas, (pos_tentativas_x - 5, 12))
    tela.blit(texto_tentativas, (pos_tentativas_x, 15))

    if tempo_mensagem > 0:
        texto = fonte_grande.render(mensagem_atual, True, (255, 255, 0))
        tela.blit(texto, (LARGURA_JANELA // 2 - texto.get_width() // 2, 30))
        tempo_mensagem -= 1

    # -----------------------------------------------------------------------
    # Mensagem de vitória, com visual de jogo retrô: fonte pixelada grande,
    # texto branco com contorno preto (desenhar_texto_com_contorno), um
    # fundo escuro semitransparente atrás pra destacar do cenário, e um
    # pulsar suave na opacidade do fundo pra chamar atenção sem cansar.
    # -----------------------------------------------------------------------
    if chegou_na_porta:
        TEXTO_VITORIA = "Você passou para a segunda fase!"
        centro_vitoria_x = LARGURA_JANELA // 2
        centro_vitoria_y = 60

        medida_texto = fonte_vitoria.size(TEXTO_VITORIA)
        largura_fundo_vitoria = medida_texto[0] + 40
        altura_fundo_vitoria = medida_texto[1] + 24

        pulso_vitoria = (math.sin(pygame.time.get_ticks() / 250) + 1) / 2  # 0 a 1, suave
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
    #----------------------------------------------------------
    # Desenha a caixa da conta matemática: fundo, texto da conta, campo
    # de resposta e instrução.
    # Deixamos a caixinha mais alta para caber a nova linha que mostra o progresso.
    if caixa_matematica_aberta:
        caixa_largura, caixa_altura = 400, 195
        caixa_x = LARGURA_JANELA // 2 - caixa_largura // 2
        caixa_y = ALTURA_JANELA // 2 - caixa_altura // 2
        largura_texto_caixa = caixa_largura - 40

        pygame.draw.rect(tela, (245, 245, 220), (caixa_x, caixa_y, caixa_largura, caixa_altura))
        pygame.draw.rect(tela, (0, 0, 0), (caixa_x, caixa_y, caixa_largura, caixa_altura), 3)

        desenhar_texto_multilinha(
            tela, f"Quanto é {numero_a} {operador} {numero_b} ?", fonte, (0, 0, 0),
            caixa_x + 20, caixa_y + 15, largura_texto_caixa,
        )

        # Mostra o progresso do jogador nas contas seguidas (ex: "Acertos: 1 de 3").
        desenhar_texto_multilinha(
            tela, f"Acertos: {acertos_atuais} de {ACERTOS_NECESSARIOS}", fonte, (0, 0, 0),
            caixa_x + 20, caixa_y + 45, largura_texto_caixa,
        )

        pygame.draw.rect(tela, (255, 255, 255), (caixa_x + 20, caixa_y + 75, largura_texto_caixa, 34))
        tela.blit(fonte.render(resposta_digitada, True, (0, 0, 0)), (caixa_x + 25, caixa_y + 83))

        desenhar_texto_multilinha(
            tela, "Digite a resposta e pressione Enter", fonte, (80, 80, 80),
            caixa_x + 20, caixa_y + 120, largura_texto_caixa,
        )

    #----------------------------------------------------------
    # Desenha a caixinha de conversa com o Gerbert: fundo, título e a fala
    # atual (fixa nas duas primeiras etapas, ou a resposta da IA/"pensando..."
    # na conversa livre). O campo de digitação só aparece quando o jogador
    # precisa escrever algo.
    #
    # Caixinha compacta, com o avatar redondo do Gerbert grudado acima dela,
    # tipo caixa de diálogo de RPG. Fica no canto inferior esquerdo da tela,
    # em vez de centralizada, para deixar o meio da tela livre (personagem e
    # cenário continuam visíveis durante a conversa).
    #
    # Todos os textos usam desenhar_texto_multilinha, que quebra a linha
    # sozinho quando necessário — assim nenhum texto vaza para fora da
    # caixinha, mesmo com a fonte pixelada ocupando mais espaço por letra.
    if caixa_gerbert_aberta:
        caixa_g_x = MARGEM_CAIXA_GERBERT
        caixa_g_y = ALTURA_JANELA - CAIXA_GERBERT_ALTURA - MARGEM_CAIXA_GERBERT

        pygame.draw.rect(tela, (245, 245, 220), (caixa_g_x, caixa_g_y, CAIXA_GERBERT_LARGURA, CAIXA_GERBERT_ALTURA))
        pygame.draw.rect(tela, (0, 0, 0), (caixa_g_x, caixa_g_y, CAIXA_GERBERT_LARGURA, CAIXA_GERBERT_ALTURA), 3)

        # Avatar redondo "flutuando" por cima do canto superior da caixa,
        # com só uma pontinha por cima da borda (a maior parte fica acima).
        avatar_x = caixa_g_x + CAIXA_GERBERT_LARGURA // 2 - TAMANHO_AVATAR_GERBERT // 2
        avatar_y = caixa_g_y - TAMANHO_AVATAR_GERBERT + 15
        tela.blit(imagem_gerbert_avatar, (avatar_x, avatar_y))

        desenhar_texto_multilinha(
            tela, "Gerbert de Aurillac", fonte, (0, 0, 0),
            caixa_g_x + 15, caixa_g_y + 10, LARGURA_TEXTO_CAIXA_GERBERT,
        )

        if etapa_conversa_gerbert == ETAPA_APRESENTACAO:
            fala_gerbert = FALA_GERBERT_APRESENTACAO
        elif etapa_conversa_gerbert == ETAPA_DICA_ABACO:
            fala_gerbert = FALA_GERBERT_DICA_ABACO
        elif gerbert_pensando:
            fala_gerbert = "Gerbert está pensando..."
        else:
            fala_gerbert = resposta_gerbert or FALA_GERBERT_CONVITE_LIVRE

        desenhar_texto_multilinha(
            tela, fala_gerbert, fonte, (0, 0, 0),
            caixa_g_x + 15, caixa_g_y + 32, LARGURA_TEXTO_CAIXA_GERBERT,
        )

        # O campo de digitação só aparece nas etapas em que o jogador
        # precisa escrever algo (apresentação e conversa livre); na dica do
        # ábaco, ele só precisa apertar Enter para continuar.
        if etapa_conversa_gerbert in (ETAPA_APRESENTACAO, ETAPA_LIVRE):
            campo_y = caixa_g_y + CAIXA_GERBERT_ALTURA - 70
            pygame.draw.rect(tela, (255, 255, 255), (caixa_g_x + 15, campo_y, LARGURA_TEXTO_CAIXA_GERBERT, 22))
            tela.blit(fonte.render(texto_digitado_gerbert, True, (0, 0, 0)), (caixa_g_x + 19, campo_y + 5))

        if etapa_conversa_gerbert == ETAPA_APRESENTACAO:
            texto_ajuda_gerbert = "Digite sua resposta e pressione Enter"
        elif etapa_conversa_gerbert == ETAPA_DICA_ABACO:
            texto_ajuda_gerbert = "Pressione Enter para continuar"
        else:
            texto_ajuda_gerbert = "Enter para perguntar, Esc para fechar"

        desenhar_texto_multilinha(
            tela, texto_ajuda_gerbert, fonte, (80, 80, 80),
            caixa_g_x + 15, caixa_g_y + CAIXA_GERBERT_ALTURA - 40, LARGURA_TEXTO_CAIXA_GERBERT,
        )
    #--------------------------------------------------------------------
    # É para atualizar a tela e, ao final do jogo, encerra o Pygame corretamente.
    pygame.display.flip()

pygame.quit()
sys.exit()

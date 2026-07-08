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
import pygame
import random
import sys
import threading

import ollama

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
# Enquanto o menu de escolha de personagem não fica pronto, essa variável
# permite trocar manualmente qual personagem é carregado no jogo:
# 0 = para rodar com o primeiro personagem, 1 = para o segundo personagem.
# ---------------------------------------------------------------------------
PERSONAGEM_ESCOLHIDO = 1

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
    "assets/imagens/personagem/",
    "assets/imagens/personagem2/",
]
PASTA_PERSONAGEM = PASTAS_PERSONAGEM[PERSONAGEM_ESCOLHIDO]

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
# Retrato do Gerbert de Aurillac, que fica desenhado no canto superior
# esquerdo da tela e, ao ser clicado, abre a caixinha de conversa com ele.
# A imagem é recortada em círculo para ficar com aparência de retrato.
# ---------------------------------------------------------------------------
CAMINHO_RETRATO_GERBERT = "assets/imagens/cenarios/fase_abaco/gerbert_retrato.png"


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


_retrato_gerbert_original = pygame.image.load(CAMINHO_RETRATO_GERBERT).convert_alpha()

TAMANHO_RETRATO_BOTAO = 70    # retrato pequeno, usado como botão no canto da tela
TAMANHO_RETRATO_CAIXA = 90    # retrato maior, usado dentro da caixinha de conversa

imagem_retrato_gerbert_botao = recortar_em_circulo(
    pygame.transform.smoothscale(_retrato_gerbert_original, (TAMANHO_RETRATO_BOTAO, TAMANHO_RETRATO_BOTAO))
)
imagem_retrato_gerbert_caixa = recortar_em_circulo(
    pygame.transform.smoothscale(_retrato_gerbert_original, (TAMANHO_RETRATO_CAIXA, TAMANHO_RETRATO_CAIXA))
)

MARGEM_RETRATO_GERBERT = 15
AREA_RETRATO_GERBERT = pygame.Rect(
    MARGEM_RETRATO_GERBERT, MARGEM_RETRATO_GERBERT, TAMANHO_RETRATO_BOTAO, TAMANHO_RETRATO_BOTAO
)

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
# Estado da caixinha de conversa com o Gerbert de Aurillac: se está aberta,
# a pergunta que o jogador está digitando, a resposta mais recente da IA e
# se o jogo está esperando o modelo terminar de responder.
# ---------------------------------------------------------------------------
caixa_gerbert_aberta = False
pergunta_gerbert = ""
resposta_gerbert = ""
gerbert_pensando = False

# Instrução de sistema enviada ao modelo para ele sempre responder no papel
# do Gerbert, com tom leve e simples, adequado para a primeira fase do jogo.
PROMPT_SISTEMA_GERBERT = (
    "Você é Gerbert de Aurillac, um monge medieval estudioso de matemática e "
    "astronomia, e está conversando com o jogador de um jogo educativo de "
    "escape room, na primeira fase (a fase do ábaco). Responda sempre em "
    "português, em tom leve, simples e gentil, sem nada difícil ou "
    "assustador. Seja breve: no máximo 2 a 3 frases."
)


def perguntar_ao_gerbert(pergunta):
    """Chama o modelo llama3.2 (rodando localmente via Ollama) pedindo uma
    resposta como se fosse o Gerbert. Roda em uma thread separada para não
    travar a janela do jogo enquanto espera a resposta chegar."""
    global resposta_gerbert, gerbert_pensando
    try:
        resultado = ollama.chat(
            model="llama3.2",
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA_GERBERT},
                {"role": "user", "content": pergunta},
            ],
        )
        resposta_gerbert = resultado["message"]["content"].strip()
    except Exception:
        resposta_gerbert = "Desculpe, não consegui pensar em uma resposta agora."
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

fonte = pygame.font.SysFont(None, 32)
fonte_grande = pygame.font.SysFont(None, 40)

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
                    caixa_matematica_aberta = True
                    resposta_digitada = ""
                    gerar_nova_conta()

            # Clicar no retrato do Gerbert abre a caixinha de conversa, desde
            # que nenhuma outra caixinha já esteja aberta.
            if not caixa_matematica_aberta and not caixa_gerbert_aberta:
                if AREA_RETRATO_GERBERT.collidepoint(evento.pos):
                    caixa_gerbert_aberta = True
                    pergunta_gerbert = ""
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
                    if int(resposta_digitada) == resposta_correta:
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
        # É analisado a digitação da pergunta ao Gerbert: Enter envia a
        # pergunta para o modelo (numa thread separada, pra não travar a
        # janela) e mostra "pensando..." até a resposta chegar; Backspace
        # apaga; Esc fecha a caixinha e volta pro jogo normal. Enquanto o
        # modelo está pensando, a digitação fica bloqueada.
        if evento.type == pygame.KEYDOWN and caixa_gerbert_aberta:
            if evento.key == pygame.K_ESCAPE:
                caixa_gerbert_aberta = False
            elif evento.key == pygame.K_RETURN:
                if pergunta_gerbert != "" and not gerbert_pensando:
                    gerbert_pensando = True
                    resposta_gerbert = ""
                    threading.Thread(
                        target=perguntar_ao_gerbert, args=(pergunta_gerbert,), daemon=True
                    ).start()
            elif evento.key == pygame.K_BACKSPACE:
                if not gerbert_pensando:
                    pergunta_gerbert = pergunta_gerbert[:-1]
            elif not gerbert_pensando and evento.unicode.isprintable() and len(pergunta_gerbert) < 60:
                pergunta_gerbert += evento.unicode

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
    tela.blit(imagem_personagem, (personagem_pos_x, personagem_pos_y))

    # Retrato do Gerbert sempre visível no canto superior esquerdo, servindo
    # de botão para abrir a caixinha de conversa.
    tela.blit(imagem_retrato_gerbert_botao, (AREA_RETRATO_GERBERT.x, AREA_RETRATO_GERBERT.y))

    if tempo_mensagem > 0:
        texto = fonte_grande.render(mensagem_atual, True, (255, 255, 0))
        tela.blit(texto, (LARGURA_JANELA // 2 - texto.get_width() // 2, 30))
        tempo_mensagem -= 1

    if chegou_na_porta:
        texto_porta = fonte_grande.render("Você passou para a segunda fase!", True, (0, 255, 0))
        tela.blit(texto_porta, (LARGURA_JANELA // 2 - texto_porta.get_width() // 2, 30))
    #----------------------------------------------------------
    # Desenha a caixa da conta matemática: fundo, texto da conta, campo
    # de resposta e instrução.
    # Deixamos a caixinha mais alta para caber a nova linha que mostra o progresso.
    if caixa_matematica_aberta:
        caixa_largura, caixa_altura = 400, 180
        caixa_x = LARGURA_JANELA // 2 - caixa_largura // 2
        caixa_y = ALTURA_JANELA // 2 - caixa_altura // 2

        pygame.draw.rect(tela, (245, 245, 220), (caixa_x, caixa_y, caixa_largura, caixa_altura))
        pygame.draw.rect(tela, (0, 0, 0), (caixa_x, caixa_y, caixa_largura, caixa_altura), 3)

        texto_conta = fonte.render(f"Quanto é {numero_a} {operador} {numero_b} ?", True, (0, 0, 0))
        tela.blit(texto_conta, (caixa_x + 20, caixa_y + 15))

        # Mostra o progresso do jogador nas contas seguidas (ex: "Acertos: 1 de 3").
        texto_acertos = fonte.render(f"Acertos: {acertos_atuais} de {ACERTOS_NECESSARIOS}", True, (0, 0, 0))
        tela.blit(texto_acertos, (caixa_x + 20, caixa_y + 45))

        pygame.draw.rect(tela, (255, 255, 255), (caixa_x + 20, caixa_y + 85, caixa_largura - 40, 40))
        texto_resposta = fonte.render(resposta_digitada, True, (0, 0, 0))
        tela.blit(texto_resposta, (caixa_x + 25, caixa_y + 93))

        texto_ajuda = fonte.render("Digite a resposta e pressione Enter", True, (80, 80, 80))
        tela.blit(texto_ajuda, (caixa_x + 20, caixa_y + 145))

    #----------------------------------------------------------
    # Desenha a caixinha de conversa com o Gerbert: fundo, retrato ao lado,
    # campo de pergunta e o espaço onde a resposta da IA aparece.
    if caixa_gerbert_aberta:
        caixa_g_largura, caixa_g_altura = 560, 260
        caixa_g_x = LARGURA_JANELA // 2 - caixa_g_largura // 2
        caixa_g_y = ALTURA_JANELA // 2 - caixa_g_altura // 2

        pygame.draw.rect(tela, (245, 245, 220), (caixa_g_x, caixa_g_y, caixa_g_largura, caixa_g_altura))
        pygame.draw.rect(tela, (0, 0, 0), (caixa_g_x, caixa_g_y, caixa_g_largura, caixa_g_altura), 3)

        tela.blit(imagem_retrato_gerbert_caixa, (caixa_g_x + 20, caixa_g_y + 20))

        # O texto (título, pergunta e resposta) fica ao lado do retrato.
        texto_x = caixa_g_x + 20 + TAMANHO_RETRATO_CAIXA + 20
        texto_largura_disponivel = caixa_g_largura - (texto_x - caixa_g_x) - 20

        texto_titulo = fonte.render("Converse com Gerbert de Aurillac", True, (0, 0, 0))
        tela.blit(texto_titulo, (texto_x, caixa_g_y + 15))

        pygame.draw.rect(tela, (255, 255, 255), (texto_x, caixa_g_y + 50, texto_largura_disponivel, 35))
        texto_pergunta = fonte.render(pergunta_gerbert, True, (0, 0, 0))
        tela.blit(texto_pergunta, (texto_x + 5, caixa_g_y + 57))

        # Enquanto o modelo ainda não respondeu, mostra "pensando..."; depois
        # que a resposta chega, ela é quebrada em várias linhas para caber
        # dentro da caixinha.
        posicao_y_resposta = caixa_g_y + 100
        if gerbert_pensando:
            texto_status = fonte.render("Gerbert está pensando...", True, (80, 80, 80))
            tela.blit(texto_status, (texto_x, posicao_y_resposta))
        elif resposta_gerbert:
            for linha in quebrar_texto(resposta_gerbert, fonte, texto_largura_disponivel):
                texto_linha = fonte.render(linha, True, (0, 0, 0))
                tela.blit(texto_linha, (texto_x, posicao_y_resposta))
                posicao_y_resposta += 26

        texto_ajuda_gerbert = fonte.render(
            "Digite sua pergunta, Enter para enviar, Esc para fechar", True, (80, 80, 80)
        )
        tela.blit(texto_ajuda_gerbert, (caixa_g_x + 20, caixa_g_y + caixa_g_altura - 30))
    #--------------------------------------------------------------------
    # É para atualizar a tela e, ao final do jogo, encerra o Pygame corretamente.
    pygame.display.flip()

pygame.quit()
sys.exit()

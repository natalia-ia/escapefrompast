"""
=====================================================================
Fase 8: IBM SYSTEM/360 E A ERA DA MINIATURIZAÇÃO (1960-1975)
=====================================================================
Estrutura baseada na Fase 5 (Z3 e Colossus), reaproveitando:
  - inventario.py     (Inventario, ItemColecionavel)
  - npc_chatbot.py     (NPCChatbot, conectado ao Ollama)
=====================================================================
"""
import os
import sys
import random
import pygame
from inventario import Inventario, ItemColecionavel
from npc_chatbot import NPCChatbot
import audio_fase5
import config_fase5
# =====================================================================
# 1. CONFIGURAÇÕES GERAIS DA JANELA E DO JOGO
# =====================================================================
LARGURA, ALTURA = 960, 600
FPS = 60

# Tempo total da fase, em segundos (fase com mais etapas que a 5,
# por isso 7 minutos - ajuste como preferir).
TEMPO_LIMITE_SEGUNDOS = 7 * 60

# Cores utilitárias (RGB)
BRANCO      = (245, 245, 240)
PRETO       = (15, 15, 15)
CINZA       = (90, 90, 90)
CINZA_CLARO = (180, 180, 180)
VERDE       = (60, 170, 90)
VERMELHO    = (190, 60, 60)
AMARELO_SEPIA = (196, 164, 96)
AZUL_IBM    = (30, 80, 160)    # azul "IBM" para combinar com o tema
CINZA_METAL = (140, 145, 150)  # tom "metálico" da miniaturização

# =====================================================================
# 2. CAMINHOS DOS ASSETS
# =====================================================================
PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))


def caminho_asset(nome_relativo):
    """Monta o caminho absoluto de um asset a partir da pasta 'assets'
    ao lado deste arquivo .py."""
    return os.path.join(PASTA_DO_SCRIPT, nome_relativo)


ASSETS = {
    # Fundo da tela de MENU inicial. Sugestão: 960x600 px.
    # Duas variantes da tela de introdução: dependem de qual personagem
    # foi escolhido na tela "personagens" do menu geral (fundo_intro1 =
    # Personagem 1, fundo_intro2 = Personagem 2), mesmo padrão da Fase 5.
    "fundo_intro1": caminho_asset("assets/fundo_intro_fase8.png"),
    "fundo_intro2": caminho_asset("assets/fundo_intro_fase8_2.png"),

    # Avatar do jogador (mesmos personagens das outras fases).
    "avatar_parado": caminho_asset("assets/personagem_parado.png"),
    "avatar_andando1": caminho_asset("assets/personagem_andando1.png"),
    "avatar_andando2": caminho_asset("assets/personagem_andando2.png"),

    # Segundo personagem selecionável (mesmo padrão das outras fases).
    "avatar2_parado": caminho_asset("assets/personagem2_parado.png"),
    "avatar2_andando1": caminho_asset("assets/personagem2_andando1.png"),
    "avatar2_andando2": caminho_asset("assets/personagem2_andando2.png"),

    # Ícone quadrado do botão de configurações (canto superior direito),
    # desenhado por config_fase5.desenhar_icone().
    "icone_configuracao": caminho_asset("assets/icone_configuracao.png"),

    # Sprite do NPC: engenheiro/técnico da IBM.
    "npc": caminho_asset("assets/engenheiro_ibm.png"),

    # Fundo da CENA 1: escritório/laboratório da IBM, com espaço livre
    # para a impressora. Sugestão: 960x600 px.
    "fundo_cena1": caminho_asset("assets/escritorio_ibm.png"),

    # Sprite da impressora - objeto clicável na Cena 1, mas só ativo
    # depois que o cartão perfurado for encontrado no cofre.
    "impressora": caminho_asset("assets/impressora.png"),

    # Ícone de seta usado na Cena 1 para ir até a Cena 3.
    "seta_direita": caminho_asset("assets/seta_direita.png"),

    # Fundo da CENA 3: a segunda sala, com o cofre na parede, o
    # computador e a cápsula do tempo. Sugestão: 960x600 px.
    "fundo_cena3": caminho_asset("assets/sala_system360.png"),

    # Sprite do cofre na parede - clicável na Cena 3.
    "cofre": caminho_asset("assets/cofre.png"),

    # Sprite do "computador" - só clicável na Cena 3 depois da Cena
    # de Dica 2.
    "computador": caminho_asset("assets/computador_system360.png"),

    # Sprite da cápsula do tempo - alvo fixo na Cena 3, para onde o
    # módulo de compatibilidade deve ser arrastado.
    "capsula_tempo": caminho_asset("assets/capsula_tempo.png"),

    # Sprite do módulo de compatibilidade - some do computador e
    # pode ser arrastado pelo jogador até a cápsula do tempo.
    "modulo_compatibilidade": caminho_asset("assets/modulo_compatibilidade.png"),

    # Fundo da CENA 2: close-up do mostrador/fechadura do cofre, com
    # os 4 quadrados de dígitos desenhados por cima. Sugestão: 960x600.
    "fundo_cena2": caminho_asset("assets/cofre_fechadura.png"),

    # Fundo da CENA DE DICA 1: o cartão perfurado encontrado dentro
    # do cofre (uma imagem só, sem mais nada). Sugestão: 960x600 px.
    "fundo_cena_dica1": caminho_asset("assets/cartao_perfurado_encontrado.png"),

    # Fundo da CENA DA IMPRESSORA: close-up do painel/relatório da
    # impressora, com a sequência embaralhada por cima. 960x600 px.
    "fundo_cena_impressora": caminho_asset("assets/impressora_painel.png"),

    # Fundo da CENA DE DICA 2: imagem única sobre compatibilidade de
    # hardware, com o botão "Voltar" por cima. Sugestão: 960x600 px.
    "fundo_cena_dica2": caminho_asset("assets/dica2_compatibilidade.png"),

    # Telas finais.
    # Duas variantes da tela de vitória, mesma regra do fundo_intro1/2
    # acima (depende do personagem escolhido no menu geral).
    "tela_vitoria1": caminho_asset("assets/vitoria1.png"),
    "tela_vitoria2": caminho_asset("assets/vitoria2.png"),
    "tela_derrota": caminho_asset("assets/derrota.png"),

    # (Opcional) Fonte .ttf de época. Deixe None para usar a padrão.
    "fonte": caminho_asset("assets/fonte_jogo.ttf"),
}
# =====================================================================
# 3. FUNÇÕES AUXILIARES DE CARREGAMENTO (COM PLACEHOLDER AUTOMÁTICO)
# =====================================================================
def carregar_imagem(caminho, tamanho, cor_placeholder, texto_placeholder):
    
    if caminho and os.path.isfile(caminho):
        imagem = pygame.image.load(caminho).convert_alpha()
        return pygame.transform.smoothscale(imagem, tamanho)

    superficie = pygame.Surface(tamanho, pygame.SRCALPHA)
    superficie.fill(cor_placeholder)
    pygame.draw.rect(superficie, PRETO, superficie.get_rect(), width=3)

    fonte = pygame.font.SysFont("arial", 18, bold=True)
    linhas = texto_placeholder.split("\n")
    y = tamanho[1] // 2 - (len(linhas) * 22) // 2
    for linha in linhas:
        texto_render = fonte.render(linha, True, PRETO)
        rect_texto = texto_render.get_rect(center=(tamanho[0] // 2, y))
        superficie.blit(texto_render, rect_texto)
        y += 22
    return superficie


def carregar_fonte(caminho, tamanho):
   
    if caminho and os.path.isfile(caminho):
        return pygame.font.Font(caminho, tamanho)
    return pygame.font.SysFont("georgia", tamanho)


def _parar_audio_seguro():
    """Rede de segurança chamada ao sair da Fase 8 por qualquer caminho
    que não passe pelo painel de configurações (vitória, fechar a
    janela) -- o painel já para a música sozinho em
    config_fase5.abrir_painel_config() quando o jogador escolhe "sair".
    Para música E efeitos em qualquer canal, sem travar se o mixer não
    estiver disponível (mesmo espírito de audio_fase5.parar_tudo() e
    do helper equivalente na Fase 5)."""
    try:
        pygame.mixer.music.stop()
    except pygame.error:
        pass
    try:
        pygame.mixer.stop()
    except pygame.error:
        pass

# =====================================================================
# 4. LÓGICA DOS DESAFIOS
# =====================================================================
# --- Desafio da Cena 2: senha do cofre (4 dígitos) ---
# 1964 = ano em que a IBM lançou o System/360. 
SENHA_COFRE = "1965"

# --- Desafio da Cena da Impressora: reordenar letras e números ---
# CODIGO_IMPRESSORA_CORRETO é a resposta certa. CODIGO_EXIBIDO é a
# mesma sequência só que embaralhada, mostrada na tela para o
# jogador decifrar.
CODIGO_IMPRESSORA_CORRETO = "IBM360"
CODIGO_IMPRESSORA_EXIBIDO = "".join(
    random.sample(CODIGO_IMPRESSORA_CORRETO, len(CODIGO_IMPRESSORA_CORRETO))
)
# Evita o azar de o embaralhamento sortear a própria resposta certa.
while CODIGO_IMPRESSORA_EXIBIDO == CODIGO_IMPRESSORA_CORRETO:
    CODIGO_IMPRESSORA_EXIBIDO = "".join(
        random.sample(CODIGO_IMPRESSORA_CORRETO, len(CODIGO_IMPRESSORA_CORRETO))
    )
# =====================================================================
# 5. CLASSES DE INTERAÇÃO: CAIXA DE TEXTO E COFRE (SENHA POR CLIQUE)
# =====================================================================
class CaixaDeTexto:
    def __init__(self, rect, fonte, tamanho_maximo, modo="letras"):
        self.rect = pygame.Rect(rect)
        self.fonte = fonte
        self.texto = ""
        self.tamanho_maximo = tamanho_maximo
        self.modo = modo  # "letras", "numeros" ou "alfanumerico"
        self.ativa = True

    def tratar_evento(self, evento):
        if not self.ativa or evento.type != pygame.KEYDOWN:
            return False

        if evento.key == pygame.K_RETURN:
            return True
        elif evento.key == pygame.K_BACKSPACE:
            self.texto = self.texto[:-1]
        else:
            tecla = evento.unicode
            if self.modo == "numeros":
                aceita = tecla.isdigit()
            elif self.modo == "alfanumerico":
                aceita = tecla.isalnum()
            else:
                aceita = tecla.isalpha()
            if aceita and len(self.texto) < self.tamanho_maximo:
                self.texto += tecla.upper() if self.modo != "numeros" else tecla
        return False

    def desenhar(self, tela):
        pygame.draw.rect(tela, BRANCO, self.rect, border_radius=6)
        pygame.draw.rect(tela, PRETO, self.rect, width=2, border_radius=6)
        texto_render = self.fonte.render(self.texto, True, PRETO)
        tela.blit(
            texto_render,
            (self.rect.x + 10, self.rect.y + (self.rect.height - texto_render.get_height()) // 2),
        )
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = self.rect.x + 10 + texto_render.get_width() + 2
            pygame.draw.line(
                tela, PRETO,
                (cursor_x, self.rect.y + 8),
                (cursor_x, self.rect.y + self.rect.height - 8), 2,
            )

class CofreSenha:
    """4 quadrados de dígitos lado a lado. NÃO usa teclado: o jogador
    clica na metade de CIMA de um quadrado para aumentar o dígito, na
    metade de BAIXO para diminuir, ou passa o mouse por cima e usa a
    RODINHA do mouse. Assim que os dígitos batem com `senha_correta`,
    `resolvido()` passa a retornar True (a fase 8 verifica isso a
    cada frame e avança sozinha, sem precisar de um botão "OK")."""

    def __init__(self, posicao_inicial, senha_correta, tamanho_caixa=70, espaco=24):
        self.senha_correta = senha_correta
        self.digitos_atuais = [0] * len(senha_correta)
        self.caixas = []
        x, y = posicao_inicial
        for indice in range(len(senha_correta)):
            rect = pygame.Rect(x + indice * (tamanho_caixa + espaco), y, tamanho_caixa, tamanho_caixa)
            self.caixas.append(rect)

    def texto_atual(self):
        return "".join(str(digito) for digito in self.digitos_atuais)

    def resolvido(self):
        return self.texto_atual() == self.senha_correta

    def tratar_clique(self, posicao_mouse):
        """Clique na metade de cima = +1, clique na metade de baixo = -1."""
        for indice, rect in enumerate(self.caixas):
            if rect.collidepoint(posicao_mouse):
                if posicao_mouse[1] < rect.centery:
                    self.digitos_atuais[indice] = (self.digitos_atuais[indice] + 1) % 10
                else:
                    self.digitos_atuais[indice] = (self.digitos_atuais[indice] - 1) % 10
                return True
        return False

    def tratar_scroll(self, posicao_mouse, direcao):
        """direcao: +1 (rodinha para cima) ou -1 (rodinha para baixo)."""
        for indice, rect in enumerate(self.caixas):
            if rect.collidepoint(posicao_mouse):
                self.digitos_atuais[indice] = (self.digitos_atuais[indice] + direcao) % 10
                return True
        return False

    def desenhar(self, tela, fonte):
        for indice, rect in enumerate(self.caixas):
            pygame.draw.rect(tela, BRANCO, rect, border_radius=8)
            pygame.draw.rect(tela, PRETO, rect, width=3, border_radius=8)

            texto_render = fonte.render(str(self.digitos_atuais[indice]), True, PRETO)
            tela.blit(texto_render, texto_render.get_rect(center=rect.center))

            # Setinhas de dica (só visuais - o clique funciona no
            # quadrado inteiro, metade de cima/baixo).
            seta_cima = [
                (rect.centerx - 8, rect.top - 6),
                (rect.centerx + 8, rect.top - 6),
                (rect.centerx, rect.top - 18),
            ]
            seta_baixo = [
                (rect.centerx - 8, rect.bottom + 6),
                (rect.centerx + 8, rect.bottom + 6),
                (rect.centerx, rect.bottom + 18),
            ]
            pygame.draw.polygon(tela, AMARELO_SEPIA, seta_cima)
            pygame.draw.polygon(tela, AMARELO_SEPIA, seta_baixo)

# =====================================================================
# 6. CLASSE: JOGADOR (AVATAR CONTROLÁVEL)
# =====================================================================
class Jogador:
    """Avatar do jogador. Move-se manualmente (teclado) ou
    automaticamente até um destino (ao clicar num objeto interativo).
    Idêntica à classe usada nas outras fases."""

    VELOCIDADE = 4
    INTERVALO_ANIMACAO_MS = 150

    def __init__(self, frame_parado, frames_andando, posicao_inicial):
        self.frame_parado = frame_parado
        self.frames_andando = frames_andando
        self.indice_animacao = 0
        self.tempo_ultimo_frame = pygame.time.get_ticks()

        self.imagem = self.frame_parado
        self.rect = self.imagem.get_rect(topleft=posicao_inicial)
        self.olhando_para_esquerda = False

        self.destino = None
        self.movendo_automaticamente = False

    def mover_ate(self, destino):
        self.destino = destino
        self.movendo_automaticamente = True

    def mover(self, teclas, limites):
        chegou_ao_destino = False

        if self.movendo_automaticamente:
            dx = self._calcular_direcao_para_destino()
            esta_andando = (dx != 0)
            if not esta_andando:
                self.movendo_automaticamente = False
                chegou_ao_destino = True
        else:
            dx = 0
            if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
                dx -= self.VELOCIDADE
            if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
                dx += self.VELOCIDADE
            esta_andando = (dx != 0)

        if dx < 0:
            self.olhando_para_esquerda = True
        elif dx > 0:
            self.olhando_para_esquerda = False

        self.rect.x = max(limites.left, min(self.rect.x + dx, limites.right - self.rect.width))

        self._atualizar_sprite(esta_andando)
        return chegou_ao_destino

    def _calcular_direcao_para_destino(self):
        alvo_x, _ = self.destino
        centro_x, _ = self.rect.center
        delta_x = alvo_x - centro_x

        if abs(delta_x) <= self.VELOCIDADE:
            return 0
        return self.VELOCIDADE if delta_x > 0 else -self.VELOCIDADE

    def _atualizar_sprite(self, esta_andando):
        if not esta_andando:
            imagem_base = self.frame_parado
            self.indice_animacao = 0
        else:
            agora = pygame.time.get_ticks()
            if agora - self.tempo_ultimo_frame >= self.INTERVALO_ANIMACAO_MS:
                self.indice_animacao = (self.indice_animacao + 1) % len(self.frames_andando)
                self.tempo_ultimo_frame = agora
            imagem_base = self.frames_andando[self.indice_animacao]

        if self.olhando_para_esquerda:
            self.imagem = pygame.transform.flip(imagem_base, True, False)
        else:
            self.imagem = imagem_base

    def desenhar(self, tela):
        tela.blit(self.imagem, self.rect)

# =====================================================================
# 7. CLASSE PRINCIPAL: O JOGO
# =====================================================================
class Jogo:
    """Controla o laço principal, a máquina de estados das cenas e o
    cronômetro da fase."""

    MENU = "menu"
    CENA1 = "cena1"
    CENA2 = "cena2"                    # senha do cofre
    CENA_DICA1 = "cena_dica1"          # cartão perfurado encontrado
    CENA3 = "cena3"                    # segunda sala
    CENA_IMPRESSORA = "cena_impressora"  # decodificação
    CENA_DICA2 = "cena_dica2"
    VITORIA = "vitoria"
    DERROTA = "derrota"

    def __init__(self, inventario=None, character_image=None, character_name="Jogador", genero="m"):
        # character_image/character_name/genero seguem o mesmo formato
        # que a Fase 5 já recebe do menu geral (ver Pygame/menu/jogo.py)
        # -- assim o personagem escolhido lá continua o mesmo aqui, em
        # vez desta fase usar sempre o primeiro conjunto de sprites
        # fixo. character_image só é guardado (não usado pra desenhar
        # aqui -- não há retrato grande nesta fase); quem decide o
        # sprite do avatar é `genero`.
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Fase 8 - IBM System/360 (1960-1975)")
        self.relogio = pygame.time.Clock()
        self.character_name = character_name or "Jogador"

        # --- Personagem escolhido na tela "personagens" do menu geral ---
        # "m" -> Personagem 1, "f" -> Personagem 2 (mesma convenção
        # usada pela Fase 5). Qualquer valor inesperado cai em "m", pra
        # esta fase nunca quebrar por causa disso. É a partir de
        # personagem_escolhido que decidimos o fundo de intro e a tela
        # de vitória (o sprite do avatar já usa `genero` direto, ver
        # mais abaixo, perto de "Escolhe o conjunto de sprites").
        self.genero = genero if genero in ("m", "f") else "m"
        self.personagem_escolhido = 1 if self.genero == "m" else 2
        self.character_image = character_image

        # Ícone do botão de configurações (parado / hover, cresce um
        # pouco quando o mouse passa por cima, mesmo efeito da Fase 5) ---
        self.img_config = carregar_imagem(
            ASSETS["icone_configuracao"], (36, 36), CINZA_CLARO, "CONFIG",
        )
        self.img_config_hover = carregar_imagem(
            ASSETS["icone_configuracao"], (42, 42), CINZA_CLARO, "CONFIG",
        )

        # --- Inventário de colecionáveis (compartilhável entre fases) ---
        self.inventario = inventario if inventario is not None else Inventario()

        # --- Fontes ---
        self.fonte_titulo = carregar_fonte(ASSETS["fonte"], 30)
        self.fonte_texto = carregar_fonte(ASSETS["fonte"], 26)
        self.fonte_pequena = carregar_fonte(ASSETS["fonte"], 20)

        # --- Imagens ---
        self.img_fundo_intro1 = carregar_imagem(
            ASSETS["fundo_intro1"], (LARGURA, ALTURA), PRETO, "FUNDO DA INTRO\n(personagem 1)",
        )
        self.img_fundo_intro2 = carregar_imagem(
            ASSETS["fundo_intro2"], (LARGURA, ALTURA), PRETO, "FUNDO DA INTRO\n(personagem 2)",
        )
        # Escolhe a variante certa conforme o personagem escolhido no
        # menu geral (self.personagem_escolhido == 1 ou 2).
        self.img_fundo_intro = (
            self.img_fundo_intro1 if self.personagem_escolhido == 1 else self.img_fundo_intro2
        )
        self.img_fundo_cena1 = carregar_imagem(
            ASSETS["fundo_cena1"], (LARGURA, ALTURA), AZUL_IBM,
            "FUNDO DA CENA 1\n(escritório da IBM)",
        )
        self.img_impressora = carregar_imagem(
            ASSETS["impressora"], (220, 250), CINZA_METAL, "IMPRESSORA",
        )
        self.img_fundo_cena3 = carregar_imagem(
            ASSETS["fundo_cena3"], (LARGURA, ALTURA), (60, 65, 75),
            "FUNDO DA CENA 3\n(segunda sala)",
        )
        self.img_cofre = carregar_imagem(
            ASSETS["cofre"], (150, 260), (80, 80, 85), "COFRE",
        )
        self.img_computador = carregar_imagem(
            ASSETS["computador"], (160, 140), CINZA_METAL, "COMPUTADOR\nSYSTEM/360",
        )
        self.img_capsula_tempo = carregar_imagem(
            ASSETS["capsula_tempo"], (235, 426), (110, 100, 70), "CÁPSULA\nDO TEMPO",
        )
        self.img_modulo = carregar_imagem(
            ASSETS["modulo_compatibilidade"], (90, 60), AMARELO_SEPIA, "MÓDULO",
        )
        self.img_fundo_cena2 = carregar_imagem(
            ASSETS["fundo_cena2"], (LARGURA, ALTURA), (45, 45, 50),
            "FUNDO DA CENA 2\n(fechadura do cofre)",
        )
        self.img_fundo_cena_dica1 = carregar_imagem(
            ASSETS["fundo_cena_dica1"], (LARGURA, ALTURA), (70, 60, 40),
            "FUNDO DA CENA DE\nDICA 1 (cartão perfurado)",
        )
        self.img_fundo_cena_impressora = carregar_imagem(
            ASSETS["fundo_cena_impressora"], (LARGURA, ALTURA), (50, 55, 60),
            "FUNDO DA CENA\nDA IMPRESSORA",
        )
        self.img_fundo_cena_dica2 = carregar_imagem(
            ASSETS["fundo_cena_dica2"], (LARGURA, ALTURA), (40, 60, 70),
            "FUNDO DA CENA DE\nDICA 2 (compatibilidade)",
        )
        self.img_seta_direita = carregar_imagem(
            ASSETS["seta_direita"], (70, 65), (0, 0, 0), "",
        ) if os.path.isfile(ASSETS["seta_direita"]) else None

        self.img_avatar_parado = carregar_imagem(
            ASSETS["avatar_parado"], (138, 288), CINZA, "PARADO",
        )
        self.img_avatar_andando1 = carregar_imagem(
            ASSETS["avatar_andando1"], (138, 288), CINZA, "ANDANDO 1",
        )
        self.img_avatar_andando2 = carregar_imagem(
            ASSETS["avatar_andando2"], (138, 288), CINZA, "ANDANDO 2",
        )
        self.img_avatar2_parado = carregar_imagem(
            ASSETS["avatar2_parado"], (138, 288), (120, 70, 70), "PARADO 2",
        )
        self.img_avatar2_andando1 = carregar_imagem(
            ASSETS["avatar2_andando1"], (138, 288), (120, 70, 70), "ANDANDO 2.1",
        )
        self.img_avatar2_andando2 = carregar_imagem(
            ASSETS["avatar2_andando2"], (138, 288), (120, 70, 70), "ANDANDO 2.2",
        )

        # Escolhe o conjunto de sprites de acordo com o `genero` recebido
        # do menu -- "f" usa o segundo personagem, qualquer outro valor
        # (o padrão "m") usa o primeiro, mesma regra da Fase 5.
        if genero == "f":
            _frame_parado_jogador = self.img_avatar2_parado
            _frames_andando_jogador = [self.img_avatar2_andando1, self.img_avatar2_andando2]
        else:
            _frame_parado_jogador = self.img_avatar_parado
            _frames_andando_jogador = [self.img_avatar_andando1, self.img_avatar_andando2]

        self.jogador = Jogador(
            frame_parado=_frame_parado_jogador,
            frames_andando=_frames_andando_jogador,
            posicao_inicial=(80, ALTURA - 320),
        )

        self.img_npc = carregar_imagem(
            ASSETS["npc"], (155, 280), (60, 90, 130), "ENGENHEIRO\nIBM",
        )

        self.img_vitoria1 = carregar_imagem(
            ASSETS["tela_vitoria1"], (LARGURA, ALTURA), VERDE, "TELA DE VITÓRIA\n(personagem 1)",
        )
        self.img_vitoria2 = carregar_imagem(
            ASSETS["tela_vitoria2"], (LARGURA, ALTURA), VERDE, "TELA DE VITÓRIA\n(personagem 2)",
        )
        # Escolhe a variante certa conforme o personagem escolhido no
        # menu geral (mesma regra usada no fundo_intro acima).
        self.img_vitoria = (
            self.img_vitoria1 if self.personagem_escolhido == 1 else self.img_vitoria2
        )
        self.img_derrota = carregar_imagem(
            ASSETS["tela_derrota"], (LARGURA, ALTURA), VERMELHO, "TELA DE DERROTA",
        )

        # --- Botões do Menu e das telas finais ---
        self.botao_iniciar = pygame.Rect(0, 0, 220, 60)
        self.botao_iniciar.center = (LARGURA - 245, 350)

        self.botao_reiniciar_vitoria = pygame.Rect(0, 0, 260, 60)
        self.botao_reiniciar_vitoria.center = (LARGURA // 2, ALTURA // 2 + 120)

        self.botao_reiniciar_derrota = pygame.Rect(0, 0, 260, 60)
        self.botao_reiniciar_derrota.center = (LARGURA - 300, ALTURA // 2 + 120)

        # --- Elementos de cena ---
        self.limites_sala = pygame.Rect(0, 0, LARGURA, ALTURA)

        # --- Impressora (Cena 1) - só clicável depois do cartão achado ---
        # AJUSTE a posição para onde a impressora aparece no seu fundo.
        self.rect_impressora = self.img_impressora.get_rect(midbottom=(600, ALTURA - 70))
        self.ponto_interacao_impressora = (
            self.rect_impressora.left - 1,
            self.jogador.rect.centery,
        )

        # --- NPC (engenheiro IBM), parado na Cena 1 ---
        self.rect_npc = self.img_npc.get_rect(midleft=(350, ALTURA - 220))

        # --- Chatbot do NPC integrado à IA local (Ollama) ---
        self.npc_chat = NPCChatbot(
            rect_npc=self.rect_npc,
            nome_npc="Engenheiro da IBM",
            contexto_fase=(
                "Você é um engenheiro da IBM, entre 1960 e 1975, dentro de um "
                "jogo de escape room educativo. Responda SOMENTE perguntas "
                "relacionadas à Fase 8: o lançamento do System/360 em 1964, a "
                "padronização de arquitetura de computadores, a miniaturização "
                "com circuitos integrados, e a busca por compatibilidade entre "
                "modelos diferentes. Se o jogador perguntar sobre a senha do "
                "cofre, diga apenas que ela tem relação com o ano em que a "
                "IBM revolucionou a computação com o System/360, sem dizer o "
                "número diretamente. Se o jogador perguntar algo fora desse "
                "tema, responda educadamente que só pode falar sobre esta "
                "fase. Responda sempre em português, em no máximo 3 frases "
                "curtas, sem revelar diretamente a solução dos desafios."
            ),
        )

        # --- Seta de navegação (Cena 1 -> Cena 3) ---
        self.rect_seta_avancar = pygame.Rect(0, 0, 56, 56)
        self.rect_seta_avancar.midright = (LARGURA - 85, ALTURA // 2 + 50)
        self.ponto_interacao_seta = (
            self.rect_seta_avancar.left - 40,
            self.jogador.rect.centery,
        )

        self.proximo_estado_ao_chegar = None

        # --- Cofre (Cena 3) -> abre a Cena 2 ---
        self.rect_cofre = self.img_cofre.get_rect(midright=(180, ALTURA - 315))
        self.ponto_interacao_cofre = (
            max(self.rect_cofre.left - 30, 90),
            self.rect_cofre.bottom - 10,
        )
        self.papel_encontrado = False   # cartão perfurado já coletado?

        # --- Computador (Cena 3) -> libera o módulo de compatibilidade ---
        self.rect_computador = self.img_computador.get_rect(midright=(LARGURA - 330, ALTURA - 275))
        self.ponto_interacao_computador = (
            self.rect_computador.left - 30,
            self.rect_computador.bottom - 10,
        )
        self.dica2_liberada = False      # já viu a Cena de Dica 2?
        self.modulo_liberado = False     # módulo já apareceu p/ arrastar?
        self.modulo_entregue = False     # módulo já foi solto na cápsula?

        # --- Cápsula do tempo (Cena 3) -> alvo do arrasto do módulo ---
        self.rect_capsula = self.img_capsula_tempo.get_rect(bottomleft=(730, ALTURA - 55))

        # --- Módulo de compatibilidade (arrastável, some do computador) ---
        self.rect_modulo_posicao_inicial = self.img_modulo.get_rect(
            midtop=(self.rect_computador.centerx, self.rect_computador.bottom + 10)
        )
        self.rect_modulo = self.rect_modulo_posicao_inicial.copy()
        self.arrastando_modulo = False
        self.offset_arrasto = (0, 0)

        # --- Botão "Voltar" da Cena 3 (-> Cena 1) ---
        self.botao_voltar_cena3 = pygame.Rect(0, 0, 160, 50)
        self.botao_voltar_cena3.bottomleft = (30, ALTURA - 30)

        # --- Cena 2: senha do cofre (4 dígitos, só no mouse) ---
        largura_total_caixas = len(SENHA_COFRE) * 70 + (len(SENHA_COFRE) - 1) * 24
        self.cofre_senha = CofreSenha(
            posicao_inicial=((LARGURA - largura_total_caixas) // 2, 260),
            senha_correta=SENHA_COFRE,
        )

        # --- Botão "Voltar" da Cena de Dica 1 (-> Cena 3) ---
        self.botao_voltar_dica1 = pygame.Rect(0, 0, 160, 50)
        self.botao_voltar_dica1.bottomleft = (30, ALTURA - 30)

        # --- Cena da Impressora: decodificação (resposta alfanumérica) ---
        self.caixa_resposta_impressora = CaixaDeTexto(
            rect=(LARGURA // 2 - 150, 320, 300, 50),
            fonte=self.fonte_texto,
            tamanho_maximo=len(CODIGO_IMPRESSORA_CORRETO),
            modo="alfanumerico",
        )
        self.mensagem_erro_impressora = ""
        self.impressora_resolvida = False
        self.botao_voltar_impressora = pygame.Rect(0, 0, 160, 50)
        self.botao_voltar_impressora.bottomleft = (30, ALTURA - 30)

        # --- Botão "Voltar" da Cena de Dica 2 (-> Cena 1) ---
        self.botao_voltar_dica2 = pygame.Rect(0, 0, 160, 50)
        self.botao_voltar_dica2.bottomleft = (30, ALTURA - 30)

        # --- Ícone de inventário (canto inferior direito, sempre visível) ---
        self.botao_inventario = pygame.Rect(0, 0, 70, 70)
        self.botao_inventario.bottomright = (LARGURA - 20, ALTURA - 20)
        self.mostrar_painel_inventario = False

        # Mapeia o nome de um item colecionável para a imagem mostrada
        # em tela cheia ao clicar nele no painel de inventário. Para o
        # cartão perfurado, usamos a própria imagem de fundo da Cena
        # de Dica 1 - assim, clicar no item reabre "a cena" completa,
        # como foi pedido.
        self.imagens_dos_itens = {
            "Cartão Perfurado do System/360": self.img_fundo_cena_dica1,
            "Módulo de Compatibilidade": self.img_modulo,
        }
        self.item_em_visualizacao = None
        self.botao_fechar_item = pygame.Rect(0, 0, 160, 50)
        self.botao_fechar_item.bottomleft = (30, ALTURA - 30)

        # --- Estado do jogo ---
        self.estado = Jogo.MENU
        self.mensagem_erro = ""
        self.ticks_inicio = None

    # -----------------------------------------------------------------
    # CONTROLE DE TEMPO
    # -----------------------------------------------------------------
    def iniciar_cronometro(self):
        self.ticks_inicio = pygame.time.get_ticks()

    def tempo_restante_segundos(self):
        decorrido_ms = pygame.time.get_ticks() - self.ticks_inicio
        restante = TEMPO_LIMITE_SEGUNDOS - (decorrido_ms // 1000)
        return max(0, restante)

    def desenhar_cronometro(self):
        restante = self.tempo_restante_segundos()
        minutos, segundos = divmod(restante, 60)
        texto = f"{minutos:02d}:{segundos:02d}"
        cor = VERMELHO if restante <= 30 else BRANCO

        fundo_rect = pygame.Rect(LARGURA // 2, 15, 110, 40)
        pygame.draw.rect(self.tela, (0, 0, 0, 150), fundo_rect, border_radius=8)
        render = self.fonte_texto.render(texto, True, cor)
        self.tela.blit(render, render.get_rect(center=fundo_rect.center))

    # -----------------------------------------------------------------
    # TELA: MENU INICIAL
    # -----------------------------------------------------------------
    def desenhar_menu(self):
        self.tela.blit(self.img_fundo_intro, (0, 0))
        titulo = self.fonte_titulo.render("Fase 08 - IBM System/360", True, PRETO)
        self.tela.blit(titulo, titulo.get_rect(center=(LARGURA // 2, 115)))

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_iniciar.collidepoint(mouse_pos) else AMARELO_SEPIA

        pygame.draw.rect(self.tela, cor_botao, self.botao_iniciar, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_iniciar, width=2, border_radius=10)

        texto_botao = self.fonte_texto.render("Iniciar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_iniciar.center))

        instrucao = self.fonte_pequena.render(
            "Clique em Iniciar ou pressione ENTER", True, CINZA_CLARO,
        )
        self.tela.blit(instrucao, instrucao.get_rect(center=(335, 500)))

    # -----------------------------------------------------------------
    # TELA: CENA 1 - ESCRITÓRIO + IMPRESSORA + NPC + SETA
    # -----------------------------------------------------------------
    def desenhar_cena1(self):
        mouse_pos = pygame.mouse.get_pos()

        impressora_esta_ativa = self.papel_encontrado and not self.impressora_resolvida
        sobre_algo_clicavel = (
            (impressora_esta_ativa and self.rect_impressora.collidepoint(mouse_pos))
            or self.rect_seta_avancar.collidepoint(mouse_pos)
        )
        pygame.mouse.set_cursor(
            pygame.SYSTEM_CURSOR_HAND if sobre_algo_clicavel else pygame.SYSTEM_CURSOR_ARROW
        )

        self.tela.blit(self.img_fundo_cena1, (0, 0))

        # A impressora aparece sempre, mas só ganha um contorno de
        # destaque quando estiver realmente clicável.
        self.tela.blit(self.img_impressora, self.rect_impressora)
        if impressora_esta_ativa:
            pygame.draw.rect(self.tela, AMARELO_SEPIA, self.rect_impressora, width=5, border_radius=10)
        elif not self.papel_encontrado:
            # Ainda travada: um pequeno cadeado visual (ajuste/troque à vontade).
            texto_travada = self.fonte_pequena.render("🔒", True, CINZA_CLARO)
            self.tela.blit(texto_travada, texto_travada.get_rect(midbottom=(self.rect_impressora.centerx, self.rect_impressora.top - 4)))

        self.tela.blit(self.img_npc, self.rect_npc)
        self.jogador.desenhar(self.tela)
        self.desenhar_seta_avancar(self.rect_seta_avancar)
        self.desenhar_cronometro()
        self.desenhar_botao_inventario()
        config_fase5.desenhar_icone(self.tela, self.img_config, self.img_config_hover)

        if self.mensagem_erro:
            render_erro = self.fonte_pequena.render(self.mensagem_erro, True, VERMELHO)
            self.tela.blit(render_erro, render_erro.get_rect(center=(LARGURA // 2, ALTURA - 40)))

        # --- Chatbot do NPC: sempre por último, para ficar por cima de tudo ---
        if self.npc_chat.perto_do_jogador(self.jogador.rect) and not self.npc_chat.dialogo_aberto:
            self.npc_chat.desenhar_dica_interacao(self.tela, self.fonte_pequena)
        self.npc_chat.desenhar(self.tela, self.fonte_texto, self.fonte_pequena, LARGURA, ALTURA)

    def desenhar_seta_avancar(self, rect):
        """Desenha a seta de navegação (usa a imagem em
        ASSETS['seta_direita'] se existir; senão, um triângulo simples)."""
        if self.img_seta_direita is not None:
            self.tela.blit(self.img_seta_direita, rect)
            return

        pygame.draw.circle(self.tela, (0, 0, 0), rect.center, rect.width // 2)
        pygame.draw.circle(self.tela, AMARELO_SEPIA, rect.center, rect.width // 2, width=2)
        ponta = (rect.centerx + 12, rect.centery)
        base_superior = (rect.centerx - 8, rect.centery - 14)
        base_inferior = (rect.centerx - 8, rect.centery + 14)
        pygame.draw.polygon(self.tela, AMARELO_SEPIA, [ponta, base_superior, base_inferior])

    def atualizar_cena1(self, teclas):
        if self.npc_chat.dialogo_aberto:
            return
        chegou = self.jogador.mover(teclas, self.limites_sala)
        if chegou and self.proximo_estado_ao_chegar is not None:
            self.mensagem_erro = ""
            proximo = self.proximo_estado_ao_chegar
            self.proximo_estado_ao_chegar = None
            if proximo == Jogo.CENA3:
                self.jogador.rect.topleft = (40, self.jogador.rect.top)
            self.estado = proximo

    # -----------------------------------------------------------------
    # TELA: CENA 3 - SEGUNDA SALA (COFRE + COMPUTADOR + CÁPSULA)
    # -----------------------------------------------------------------
    def desenhar_cena3(self):
        mouse_pos = pygame.mouse.get_pos()
        computador_esta_ativo = self.dica2_liberada and not self.modulo_entregue
        sobre_algo_clicavel = (
            (not self.papel_encontrado and self.rect_cofre.collidepoint(mouse_pos))
            or (computador_esta_ativo and not self.modulo_liberado and self.rect_computador.collidepoint(mouse_pos))
            or (self.modulo_liberado and not self.modulo_entregue and self.rect_modulo.collidepoint(mouse_pos))
        )
        pygame.mouse.set_cursor(
            pygame.SYSTEM_CURSOR_HAND if sobre_algo_clicavel else pygame.SYSTEM_CURSOR_ARROW
        )

        self.tela.blit(self.img_fundo_cena3, (0, 0))
        self.tela.blit(self.img_cofre, self.rect_cofre)
        self.tela.blit(self.img_computador, self.rect_computador)
        self.tela.blit(self.img_capsula_tempo, self.rect_capsula)

        if not self.papel_encontrado:
            pygame.draw.rect(self.tela, AMARELO_SEPIA, self.rect_cofre, width=5, border_radius=10)
        if computador_esta_ativo and not self.modulo_liberado:
            pygame.draw.rect(self.tela, AMARELO_SEPIA, self.rect_computador, width=5, border_radius=10)

        if self.modulo_liberado and not self.modulo_entregue:
            self.tela.blit(self.img_modulo, self.rect_modulo)

        self.jogador.desenhar(self.tela)
        self.desenhar_cronometro()
        self.desenhar_botao_inventario()
        config_fase5.desenhar_icone(self.tela, self.img_config, self.img_config_hover)

        cor_botao = VERDE if self.botao_voltar_cena3.collidepoint(mouse_pos) else AMARELO_SEPIA
        pygame.draw.rect(self.tela, cor_botao, self.botao_voltar_cena3, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_voltar_cena3, width=2, border_radius=10)
        texto_botao = self.fonte_pequena.render("Voltar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_voltar_cena3.center))

        if self.modulo_liberado and not self.modulo_entregue:
            dica = self.fonte_pequena.render(
                "Arraste o módulo até a cápsula do tempo.", True, CINZA_CLARO,
            )
            self.tela.blit(dica, dica.get_rect(center=(LARGURA // 2, 40)))

    def atualizar_cena3(self, teclas):
        if self.arrastando_modulo:
            return
        chegou = self.jogador.mover(teclas, self.limites_sala)
        if chegou and self.proximo_estado_ao_chegar is not None:
            self.mensagem_erro = ""
            self.estado = self.proximo_estado_ao_chegar
            self.proximo_estado_ao_chegar = None

    def iniciar_arrasto_modulo(self, posicao_mouse):
        self.arrastando_modulo = True
        self.offset_arrasto = (
            posicao_mouse[0] - self.rect_modulo.x,
            posicao_mouse[1] - self.rect_modulo.y,
        )

    def atualizar_arrasto_modulo(self, posicao_mouse):
        if self.arrastando_modulo:
            self.rect_modulo.x = posicao_mouse[0] - self.offset_arrasto[0]
            self.rect_modulo.y = posicao_mouse[1] - self.offset_arrasto[1]

    def soltar_modulo(self):
        """Chamado quando o jogador solta o botão do mouse durante o
        arrasto. Se o módulo estiver em cima da cápsula, conclui a
        fase; senão, ele volta para a posição inicial (perto do
        computador) para o jogador tentar de novo."""
        self.arrastando_modulo = False
        if self.rect_modulo.colliderect(self.rect_capsula):
            item_final = ItemColecionavel(
                nome="Módulo de Compatibilidade",
                descricao="O módulo que permitiu a diferentes modelos do System/360 operarem juntos.",
            )
            self.inventario.adicionar(item_final)
            self.modulo_entregue = True
            self.estado = Jogo.VITORIA
        else:
            self.rect_modulo = self.rect_modulo_posicao_inicial.copy()

    # -----------------------------------------------------------------
    # TELA: CENA 2 - SENHA DO COFRE (4 DÍGITOS, SÓ NO MOUSE)
    # -----------------------------------------------------------------
    def desenhar_cena2(self):
        self.tela.blit(self.img_fundo_cena2, (0, 0))
        self.desenhar_cronometro()
        self.desenhar_botao_inventario()
        config_fase5.desenhar_icone(self.tela, self.img_config, self.img_config_hover)

        linha1 = self.fonte_texto.render(
            "Descubra a senha do cofre:", True, BRANCO
        )

        linha2 = self.fonte_texto.render(
            "Dica: Ano Lançamento IBM", True, BRANCO
        )

        # Centralizando cada linha
        rect1 = linha1.get_rect(center=(LARGURA // 2, 160))
        rect2 = linha2.get_rect(center=(LARGURA // 2, 200))  # mais abaixo

        # Desenhando na tela
        self.tela.blit(linha1, rect1)
        self.tela.blit(linha2, rect2)

        self.cofre_senha.desenhar(self.tela, self.fonte_titulo)

        linha1 = self.fonte_pequena.render(
            "Clique em cima do quadrado para aumentar,", True, CINZA_CLARO
        )

        linha2 = self.fonte_pequena.render(
            "embaixo para diminuir (ou use o scroll do mouse).", True, CINZA_CLARO
        )

        rect1 = linha1.get_rect(center=(LARGURA // 2, 400))
        rect2 = linha2.get_rect(center=(LARGURA // 2, 430))  # ajusta o espaçamento

        self.tela.blit(linha1, rect1)
        self.tela.blit(linha2, rect2)

        dica_voltar = self.fonte_pequena.render("ESC para voltar à sala", True, CINZA_CLARO)
        self.tela.blit(dica_voltar, (20, ALTURA - 35))

    def atualizar_cena2(self):
        """Chamada a cada frame enquanto o jogador está na Cena 2:
        verifica se a senha já bate, e se sim, avança sozinha para
        a Cena de Dica 1 - sem precisar de nenhum botão "confirmar"."""
        if self.cofre_senha.resolvido() and not self.papel_encontrado:
            item_papel = ItemColecionavel(
                nome="Cartão Perfurado do System/360",
                descricao="Um cartão perfurado guardado dentro do cofre, essencial para a impressora.",
            )
            self.inventario.adicionar(item_papel)
            self.papel_encontrado = True
            self.estado = Jogo.CENA_DICA1

    # -----------------------------------------------------------------
    # TELA: CENA DE DICA 1 - CARTÃO PERFURADO ENCONTRADO
    # -----------------------------------------------------------------
    def desenhar_cena_dica1(self):
        self.tela.blit(self.img_fundo_cena_dica1, (0, 0))
        self.desenhar_cronometro()
        self.desenhar_botao_inventario()
        config_fase5.desenhar_icone(self.tela, self.img_config, self.img_config_hover)

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_voltar_dica1.collidepoint(mouse_pos) else AMARELO_SEPIA

        pygame.draw.rect(self.tela, cor_botao, self.botao_voltar_dica1, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_voltar_dica1, width=2, border_radius=10)

        texto_botao = self.fonte_pequena.render("Voltar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_voltar_dica1.center))

    # -----------------------------------------------------------------
    # TELA: CENA DA IMPRESSORA - DECODIFICAÇÃO (LETRAS E NÚMEROS)
    # -----------------------------------------------------------------
    def desenhar_cena_impressora(self):
        self.tela.blit(self.img_fundo_cena_impressora, (0, 0))
        self.desenhar_cronometro()
        self.desenhar_botao_inventario()
        config_fase5.desenhar_icone(self.tela, self.img_config, self.img_config_hover)

        titulo = self.fonte_texto.render(
            "Reordene as letras e números do relatório da impressora:", True, AZUL_IBM,
        )
        self.tela.blit(titulo, titulo.get_rect(center=(LARGURA // 2, 180)))

        codigo_exibido = self.fonte_titulo.render(CODIGO_IMPRESSORA_EXIBIDO, True, AMARELO_SEPIA)
        self.tela.blit(codigo_exibido, codigo_exibido.get_rect(center=(LARGURA // 2, 240)))

        self.caixa_resposta_impressora.desenhar(self.tela)

        if self.mensagem_erro_impressora:
            render_erro = self.fonte_pequena.render(self.mensagem_erro_impressora, True, VERMELHO)
            self.tela.blit(render_erro, render_erro.get_rect(center=(LARGURA // 2, 400)))

        dica_voltar = self.fonte_pequena.render("ESC para voltar", True, CINZA_CLARO)
        self.tela.blit(dica_voltar, (20, ALTURA - 35))

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_voltar_impressora.collidepoint(mouse_pos) else AMARELO_SEPIA
        pygame.draw.rect(self.tela, cor_botao, self.botao_voltar_impressora, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_voltar_impressora, width=2, border_radius=10)
        texto_botao = self.fonte_pequena.render("Voltar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_voltar_impressora.center))

    def validar_codigo_impressora(self):
        if self.caixa_resposta_impressora.texto == CODIGO_IMPRESSORA_CORRETO:
            self.impressora_resolvida = True
            self.estado = Jogo.CENA_DICA2
        else:
            self.mensagem_erro_impressora = "Sequência incorreta. Tente novamente!"
            self.caixa_resposta_impressora.texto = ""

    # -----------------------------------------------------------------
    # TELA: CENA DE DICA 2 - IMAGEM + BOTÃO VOLTAR
    # -----------------------------------------------------------------
    def desenhar_cena_dica2(self):
        self.tela.blit(self.img_fundo_cena_dica2, (0, 0))
        self.desenhar_cronometro()
        self.desenhar_botao_inventario()
        config_fase5.desenhar_icone(self.tela, self.img_config, self.img_config_hover)

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_voltar_dica2.collidepoint(mouse_pos) else AMARELO_SEPIA

        pygame.draw.rect(self.tela, cor_botao, self.botao_voltar_dica2, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_voltar_dica2, width=2, border_radius=10)

        texto_botao = self.fonte_pequena.render("Voltar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_voltar_dica2.center))

    # -----------------------------------------------------------------
    # INVENTÁRIO (ícone, painel, e visualização de item)
    # -----------------------------------------------------------------
    def desenhar_botao_inventario(self):
        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_inventario.collidepoint(mouse_pos) else AMARELO_SEPIA

        pygame.draw.rect(self.tela, cor_botao, self.botao_inventario, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_inventario, width=2, border_radius=10)

        texto = self.fonte_pequena.render(str(self.inventario.quantidade()), True, PRETO)
        self.tela.blit(texto, texto.get_rect(center=self.botao_inventario.center))

    def rect_item_no_painel(self, indice):
        """Calcula o retângulo clicável de um item dentro do painel,
        dado seu índice na lista - usado tanto para desenhar quanto
        para detectar o clique, garantindo que os dois combinem."""
        painel_rect = pygame.Rect(0, 0, 400, 300)
        painel_rect.center = (LARGURA // 2, ALTURA // 2)
        y = painel_rect.top + 60 + indice * 30
        return pygame.Rect(painel_rect.left + 15, y - 4, 370, 26)

    def desenhar_painel_inventario(self):
        painel_rect = pygame.Rect(0, 0, 400, 300)
        painel_rect.center = (LARGURA // 2, ALTURA // 2)

        faixa = pygame.Surface(painel_rect.size, pygame.SRCALPHA)
        faixa.fill((20, 20, 20, 230))
        self.tela.blit(faixa, painel_rect.topleft)

        pygame.draw.rect(self.tela, AMARELO_SEPIA, painel_rect, width=3, border_radius=10)

        titulo = self.fonte_texto.render("Itens coletados", True, BRANCO)
        self.tela.blit(titulo, titulo.get_rect(midtop=(painel_rect.centerx, painel_rect.top + 15)))

        if self.inventario.quantidade() == 0:
            vazio = self.fonte_pequena.render("Nenhum item ainda.", True, CINZA_CLARO)
            self.tela.blit(vazio, vazio.get_rect(center=painel_rect.center))
        else:
            for indice, item in enumerate(self.inventario.itens):
                rect_item = self.rect_item_no_painel(indice)
                nome_render = self.fonte_pequena.render(f"- {item.nome}", True, BRANCO)
                self.tela.blit(nome_render, (rect_item.left + 5, rect_item.top + 3))

        dica = self.fonte_pequena.render(
            "Clique num item para vê-lo. Clique no ícone para fechar.", True, CINZA_CLARO,
        )
        self.tela.blit(dica, dica.get_rect(midbottom=(painel_rect.centerx, painel_rect.bottom - 15)))

    def desenhar_visualizacao_item(self):
        imagem = self.imagens_dos_itens.get(self.item_em_visualizacao)
        if imagem is not None:
            fundo = pygame.Surface((LARGURA, ALTURA))
            fundo.fill((15, 15, 15))
            self.tela.blit(fundo, (0, 0))
            self.tela.blit(imagem, imagem.get_rect(center=(LARGURA // 2, ALTURA // 2)))

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_fechar_item.collidepoint(mouse_pos) else AMARELO_SEPIA
        pygame.draw.rect(self.tela, cor_botao, self.botao_fechar_item, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_fechar_item, width=2, border_radius=10)
        texto_botao = self.fonte_pequena.render("Fechar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_fechar_item.center))

    # -----------------------------------------------------------------
    # TELAS FINAIS: VITÓRIA / DERROTA
    # -----------------------------------------------------------------
    def desenhar_vitoria(self):
        self.tela.blit(self.img_vitoria, (0, 0))
        texto = self.fonte_titulo.render("Você concluiu, parabéns!", True, BRANCO)
        sombra = self.fonte_titulo.render("Você concluiu, parabéns!", True, PRETO)
        centro = (LARGURA // 2, ALTURA // 2)
        self.tela.blit(sombra, sombra.get_rect(center=(centro[0] + 2, centro[1] + 2)))
        self.tela.blit(texto, texto.get_rect(center=centro))

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_reiniciar_vitoria.collidepoint(mouse_pos) else AMARELO_SEPIA
        pygame.draw.rect(self.tela, cor_botao, self.botao_reiniciar_vitoria, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_reiniciar_vitoria, width=2, border_radius=10)
        texto_botao = self.fonte_texto.render("Continuar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_reiniciar_vitoria.center))

        self.desenhar_botao_inventario()

    def desenhar_derrota(self):
        self.tela.blit(self.img_derrota, (0, 0))

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_reiniciar_derrota.collidepoint(mouse_pos) else AMARELO_SEPIA

        pygame.draw.rect(self.tela, cor_botao, self.botao_reiniciar_derrota, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_reiniciar_derrota, width=2, border_radius=10)

        texto_botao = self.fonte_texto.render("Tentar novamente", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_reiniciar_derrota.center))

        dica = self.fonte_pequena.render("(ou pressione R)", True, BRANCO)
        self.tela.blit(dica, dica.get_rect(center=(LARGURA - 260, self.botao_reiniciar_derrota.bottom + 25)))

    # -----------------------------------------------------------------
    # REINÍCIO DA FASE
    # -----------------------------------------------------------------
    def reiniciar(self):
        self.jogador.rect.topleft = (80, ALTURA - 300)
        self.npc_chat.fechar_dialogo()
        self.mensagem_erro = ""
        self.mensagem_erro_impressora = ""
        self.caixa_resposta_impressora.texto = ""
        self.impressora_resolvida = False
        self.papel_encontrado = False
        self.dica2_liberada = False
        self.modulo_liberado = False
        self.modulo_entregue = False
        self.arrastando_modulo = False
        self.rect_modulo = self.rect_modulo_posicao_inicial.copy()
        self.cofre_senha.digitos_atuais = [0] * len(SENHA_COFRE)
        self.estado = Jogo.MENU
        self.ticks_inicio = None
        self.proximo_estado_ao_chegar = None

    # -----------------------------------------------------------------
    # LAÇO PRINCIPAL DO JOGO
    # -----------------------------------------------------------------
    def executar(self):
        rodando = True
        while rodando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    rodando = False

                elif evento.type == pygame.KEYDOWN:
                    if self.estado == Jogo.CENA1:
                        if self.npc_chat.dialogo_aberto:
                            self.npc_chat.tratar_evento(evento)
                        elif evento.key == pygame.K_e and self.npc_chat.perto_do_jogador(self.jogador.rect):
                            self.npc_chat.abrir_dialogo()

                    elif self.estado == Jogo.CENA2 and evento.key == pygame.K_ESCAPE:
                        self.estado = Jogo.CENA3

                    elif self.estado == Jogo.CENA_IMPRESSORA:
                        if evento.key == pygame.K_ESCAPE:
                            self.estado = Jogo.CENA1
                        else:
                            enter_pressionado = self.caixa_resposta_impressora.tratar_evento(evento)
                            if enter_pressionado:
                                self.validar_codigo_impressora()

                    elif self.estado in (Jogo.VITORIA, Jogo.DERROTA) and evento.key == pygame.K_r:
                        self.reiniciar()

                elif evento.type == pygame.MOUSEWHEEL:
                    if self.estado == Jogo.CENA2:
                        self.cofre_senha.tratar_scroll(pygame.mouse.get_pos(), evento.y)

                elif evento.type == pygame.MOUSEMOTION:
                    if self.estado == Jogo.CENA3 and self.arrastando_modulo:
                        self.atualizar_arrasto_modulo(evento.pos)

                elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                    if self.estado == Jogo.CENA3 and self.arrastando_modulo:
                        self.soltar_modulo()

                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    # Botão de configurações: sempre acessível em qualquer cena
                    # jogável. O painel É o "jogo pausado" (ver
                    # config_fase5.abrir_painel_config()) — nada do resto do laço
                    # roda enquanto ele está aberto.
                    if self.estado != Jogo.MENU and config_fase5.icone_rect(LARGURA).collidepoint(evento.pos):
                        resultado_config = config_fase5.abrir_painel_config(
                            self.tela, self.relogio, self.img_config, self.img_config_hover,
                        )
                        if resultado_config == "sair":
                            rodando = False
                    elif self.estado == Jogo.MENU and self.botao_iniciar.collidepoint(evento.pos):
                        self.iniciar_cronometro()
                        audio_fase5.iniciar_musica_fundo()
                        self.estado = Jogo.CENA1

                    # Clique na impressora -> só funciona depois do cartão achado
                    elif (
                        self.estado == Jogo.CENA1
                        and self.papel_encontrado
                        and not self.impressora_resolvida
                        and self.rect_impressora.collidepoint(evento.pos)
                    ):
                        self.jogador.mover_ate(self.ponto_interacao_impressora)
                        self.proximo_estado_ao_chegar = Jogo.CENA_IMPRESSORA

                    elif (
                        self.estado == Jogo.CENA1
                        and not self.papel_encontrado
                        and self.rect_impressora.collidepoint(evento.pos)
                    ):
                        self.mensagem_erro = "A impressora parece travada. Encontre o cartão perfurado primeiro."

                    # Clique na seta -> anda até ela e segue para a Cena 3
                    elif self.estado == Jogo.CENA1 and self.rect_seta_avancar.collidepoint(evento.pos):
                        self.jogador.mover_ate(self.ponto_interacao_seta)
                        self.proximo_estado_ao_chegar = Jogo.CENA3

                    # Clique no cofre (Cena 3) -> abre a Cena 2 (senha)
                    elif (
                        self.estado == Jogo.CENA3
                        and not self.papel_encontrado
                        and self.rect_cofre.collidepoint(evento.pos)
                    ):
                        self.jogador.mover_ate(self.ponto_interacao_cofre)
                        self.proximo_estado_ao_chegar = Jogo.CENA2

                    # Clique no computador (Cena 3) -> libera o módulo
                    elif (
                        self.estado == Jogo.CENA3
                        and self.dica2_liberada
                        and not self.modulo_liberado
                        and self.rect_computador.collidepoint(evento.pos)
                    ):
                        self.jogador.mover_ate(self.ponto_interacao_computador)
                        self.modulo_liberado = True

                    # Clique no módulo (Cena 3) -> começa o arrasto
                    elif (
                        self.estado == Jogo.CENA3
                        and self.modulo_liberado
                        and not self.modulo_entregue
                        and self.rect_modulo.collidepoint(evento.pos)
                    ):
                        self.iniciar_arrasto_modulo(evento.pos)

                    # Botão "Voltar" da Cena 3 -> Cena 1
                    elif self.estado == Jogo.CENA3 and self.botao_voltar_cena3.collidepoint(evento.pos):
                        self.jogador.rect.midright = (self.rect_seta_avancar.left - 20, self.jogador.rect.centery)
                        self.estado = Jogo.CENA1

                    # Clique nos quadrados de dígitos, dentro da Cena 2
                    elif self.estado == Jogo.CENA2:
                        self.cofre_senha.tratar_clique(evento.pos)

                    # Botão "Voltar" da Cena de Dica 1 -> Cena 3
                    elif self.estado == Jogo.CENA_DICA1 and self.botao_voltar_dica1.collidepoint(evento.pos):
                        self.estado = Jogo.CENA3

                    # Botão "Voltar" da Cena da Impressora -> Cena 1
                    elif self.estado == Jogo.CENA_IMPRESSORA and self.botao_voltar_impressora.collidepoint(evento.pos):
                        self.estado = Jogo.CENA1

                    # Botão "Voltar" da Cena de Dica 2 -> Cena 1 (libera o computador)
                    elif self.estado == Jogo.CENA_DICA2 and self.botao_voltar_dica2.collidepoint(evento.pos):
                        self.dica2_liberada = True
                        self.estado = Jogo.CENA1

                    # Fechar a visualização de um item (tem prioridade
                    # sobre o resto, já que fica por cima de tudo)
                    elif self.item_em_visualizacao is not None:
                        if self.botao_fechar_item.collidepoint(evento.pos):
                            self.item_em_visualizacao = None

                    # Clique num item dentro do painel de inventário -> visualizar
                    elif self.mostrar_painel_inventario:
                        clicou_em_algum_item = False
                        for indice, item in enumerate(self.inventario.itens):
                            if self.rect_item_no_painel(indice).collidepoint(evento.pos):
                                if item.nome in self.imagens_dos_itens:
                                    self.item_em_visualizacao = item.nome
                                    self.mostrar_painel_inventario = False
                                clicou_em_algum_item = True
                                break
                        if not clicou_em_algum_item and self.botao_inventario.collidepoint(evento.pos):
                            self.mostrar_painel_inventario = False

                    # Clique no ícone do inventário -> abre o painel
                    elif self.estado != Jogo.MENU and self.botao_inventario.collidepoint(evento.pos):
                        self.mostrar_painel_inventario = True

                    elif self.estado == Jogo.VITORIA and self.botao_reiniciar_vitoria.collidepoint(evento.pos):
                        _parar_audio_seguro()
                        return "vitoria"

                    elif self.estado == Jogo.DERROTA and self.botao_reiniciar_derrota.collidepoint(evento.pos):
                        self.reiniciar()

            # --- Cronômetro (vale para todas as cenas jogáveis) ---
            estados_com_cronometro = (
                Jogo.CENA1, Jogo.CENA2, Jogo.CENA_DICA1, Jogo.CENA3,
                Jogo.CENA_IMPRESSORA, Jogo.CENA_DICA2,
            )
            if self.estado in estados_com_cronometro and self.ticks_inicio is not None:
                if self.tempo_restante_segundos() <= 0:
                    self.estado = Jogo.DERROTA

            # --- Atualização de lógica por estado ---
            if self.estado == Jogo.CENA1:
                teclas = pygame.key.get_pressed()
                self.atualizar_cena1(teclas)
            elif self.estado == Jogo.CENA2:
                self.atualizar_cena2()
            elif self.estado == Jogo.CENA3:
                teclas = pygame.key.get_pressed()
                self.atualizar_cena3(teclas)

            # --- Desenho por estado ---
            if self.estado == Jogo.MENU:
                self.desenhar_menu()
            elif self.estado == Jogo.CENA1:
                self.desenhar_cena1()
            elif self.estado == Jogo.CENA2:
                self.desenhar_cena2()
            elif self.estado == Jogo.CENA_DICA1:
                self.desenhar_cena_dica1()
            elif self.estado == Jogo.CENA3:
                self.desenhar_cena3()
            elif self.estado == Jogo.CENA_IMPRESSORA:
                self.desenhar_cena_impressora()
            elif self.estado == Jogo.CENA_DICA2:
                self.desenhar_cena_dica2()
            elif self.estado == Jogo.VITORIA:
                self.desenhar_vitoria()
            elif self.estado == Jogo.DERROTA:
                self.desenhar_derrota()

            if self.mostrar_painel_inventario:
                self.desenhar_painel_inventario()
            if self.item_em_visualizacao is not None:
                self.desenhar_visualizacao_item()

            pygame.display.flip()
            self.relogio.tick(FPS)

        _parar_audio_seguro()
        pygame.quit()
        sys.exit()


# =====================================================================
# 8. PONTO DE ENTRADA DESTA FASE PARA O MENU GERAL
# =====================================================================
def run(character_image=None, character_name=None, genero="m", inventario=None):
    """
    Ponto de entrada da Fase 8, pronto para ser chamado pelo menu geral
    do jogo (Pygame/menu/jogo.py) -- mesmo espírito de `run` na Fase 5
    (fase_5.run), usado como modelo.

    O menu geral já escolhe o personagem na sua própria tela
    "personagens" (setas </>), antes do jogador entrar em qualquer
    fase -- a escolha NÃO acontece aqui dentro da Fase 8. Esta função
    só recebe o resultado dessa escolha e entrega para a classe Jogo:

        modulo.Jogo(
            character_image=CHARACTER_IMAGES.get(self.personagem_index),
            character_name=self.get_personagem_name(self.personagem_index),
            genero="m" if self.personagem_index == 0 else "f",
        ).executar()

    Parâmetros:
        character_image: imagem do personagem vinda do menu geral
            (CHARACTER_IMAGES.get(...)). Guardada em self.character_image
            para uso futuro dentro da fase.
        character_name: nome do personagem escolhido/renomeado no menu
            geral. Guardado em self.character_name.
        genero: "m" (Personagem 1) ou "f" (Personagem 2) -- é a partir
            dele que a Fase 8 decide sozinha qual sprite, fundo de
            intro e tela de vitória usar (ver Jogo.__init__).
        inventario: opcional, para reaproveitar um inventário já
            existente entre fases (mesmo uso que já existia antes).

    Retorno: o mesmo que Jogo.executar() já devolve hoje -- a string
    "vitoria" quando o jogador vence e clica no botão da tela de
    vitória (nada quando a janela é fechada, pois o próprio laço
    encerra o programa nesse caso).
    """
    jogo = Jogo(
        inventario=inventario,
        character_image=character_image,
        character_name=character_name,
        genero=genero,
    )
    return jogo.executar()


def run_padrao():
    """
    Roda a Fase 8 isolada, fora do menu geral, com o Personagem 1 como
    opção padrão (genero="m") -- útil para testar esta fase sozinha
    (ex: `python fase_8.py`) sem precisar abrir o jogo completo nem
    passar por nenhum menu.

    Para testar a variante do Personagem 2 isoladamente, chame
    run(genero="f") em vez desta função.
    """
    return run(genero="m")


# =====================================================================
# 9. PONTO DE ENTRADA DO PROGRAMA (rodando este arquivo sozinho)
# =====================================================================
if __name__ == "__main__":
    run_padrao()

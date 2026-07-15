"""
=====================================================================
Fase 5: Z3 E COLOSSUS (1941-1943)
=====================================================================
"""
import json
import os
import sys
import pygame
from inventario import Inventario, ItemColecionavel
from npc_chatbot import NPCChatbot

# =====================================================================
# 1. CONFIGURAÇÕES GERAIS DA JANELA E DO JOGO
# =====================================================================
LARGURA, ALTURA = 960, 600
FPS = 60

# Tempo total da fase, em segundos (ajuste como preferir - 5 minutos aqui)
TEMPO_LIMITE_SEGUNDOS = 5 * 60

# Cores utilitárias (RGB)
BRANCO      = (245, 245, 240)
PRETO       = (15, 15, 15)
CINZA       = (90, 90, 90)
CINZA_CLARO = (180, 180, 180)
VERDE       = (60, 170, 90)
VERMELHO    = (190, 60, 60)
AMARELO_SEPIA = (196, 164, 96)
AZUL_ACO    = (80, 120, 150)   # tom "metálico" para combinar com o tema
DOURADO_VALVULA = (200, 150, 60)

# =====================================================================
# 2. CAMINHOS DOS ASSETS -> PREENCHA AQUI COM SUAS IMAGENS
# =====================================================================
PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))


def caminho_asset(nome_relativo):
    """Monta o caminho absoluto de um asset a partir da pasta 'assets'
    ao lado deste arquivo .py."""
    return os.path.join(PASTA_DO_SCRIPT, nome_relativo)


# ---------------------------------------------------------------------------
# Progresso (estrelas + tempo) -- mesmo arquivo/formato compartilhado que
# Fase_2/fase2/puzzles/babbage_lovelace.py, Fase_9/puzzle_terminal.py e
# Fase_4/fase4_atual.py já usam: {"estrelas": 1-3, "completo": true,
# "tempo": "MM:SS"} ("tempo" é quanto o jogador LEVOU pra resolver, não
# quanto sobrou no timer). Fica na raiz de Pygame/ (uma pasta acima
# desta, Fase_5/ -> Pygame/), fora de qualquer fase específica -- mesmo
# espírito autocontido do resto do repositório (cada fase grava sua
# própria chave, sem importar de outra).
# ---------------------------------------------------------------------------
_PYGAME_DIR = os.path.dirname(PASTA_DO_SCRIPT)
PROGRESSO_PATH = os.path.join(_PYGAME_DIR, "progresso.json")
PROGRESSO_CHAVE_FASE = "fase_5"


def _carregar_progresso():
    """Lê Pygame/progresso.json inteiro (de todas as fases). Devolve um
    dicionário vazio se o arquivo ainda não existir ou vier corrompido --
    assim a gente nunca trava tentando salvar só porque o arquivo está
    ausente ou malformado."""
    if not os.path.exists(PROGRESSO_PATH):
        return {}
    try:
        with open(PROGRESSO_PATH, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (json.JSONDecodeError, OSError):
        return {}


def _salvar_progresso(estrelas, tempo_formatado):
    """Grava `estrelas` (1 a 3, ver _calcular_estrelas) e
    `tempo_formatado` ("MM:SS", o tempo que o jogador LEVOU) na chave
    PROGRESSO_CHAVE_FASE do progresso.json compartilhado, preservando as
    chaves de outras fases que já estiverem lá.

    Nunca sobrescreve um resultado MELHOR já salvo: se o jogador já tinha
    completado essa fase antes com estrelas >= as de agora E aquele
    registro já tem um tempo salvo, não mexe em nada. Mas se o registro
    antigo só tem {"completo": true} (ex: gravado pelo menu antes desta
    função existir, ver Pygame/menu/jogo.py _marcar_fase_completa) ou tem
    estrelas iguais/melhores sem "tempo", preenche o que falta sem piorar
    a contagem de estrelas já conquistada."""
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


# Limiares de estrelas -- baseados no tempo RESTANTE no timer no instante
# em que o jogador vence (mesmos limiares usados na Fase 2, na Fase 9 e
# na Fase 4, pra estrela significar a mesma coisa em todas as fases).
ESTRELAS_3_TEMPO_MIN = 25  # >= 25s sobrando -> 3 estrelas
ESTRELAS_2_TEMPO_MIN = 15  # 15 a 24s sobrando -> 2 estrelas
# < 15s sobrando -> 1 estrela (ver _calcular_estrelas)


def _calcular_estrelas(tempo_restante):
    """Devolve 1, 2 ou 3 conforme `tempo_restante` (segundos ainda no
    timer quando o jogador venceu) contra os limiares acima. Esta fase
    tem timer (TEMPO_LIMITE_SEGUNDOS), então sempre usa esta conta; uma
    fase sem timer daria 1 estrela fixa por completar (não é o caso
    aqui)."""
    if tempo_restante >= ESTRELAS_3_TEMPO_MIN:
        return 3
    if tempo_restante >= ESTRELAS_2_TEMPO_MIN:
        return 2
    return 1


def _formatar_tempo(segundos):
    """Formata `segundos` (int/float) como "MM:SS"."""
    total = max(0, int(segundos))
    return f"{total // 60:02d}:{total % 60:02d}"


def _parar_audio_seguro():
    """Esta fase não usa pygame.mixer pra nada (sem música/efeito
    próprio) -- mas o menu compartilha o mesmo processo pygame com todas
    as fases, e quem chama esta função ao sair (ver o fim de executar())
    não sabe se algum áudio de outro lugar ainda está tocando. Só uma
    rede de segurança: para música E efeitos em qualquer canal, sem
    travar se o mixer não estiver disponível."""
    try:
        pygame.mixer.music.stop()
    except pygame.error:
        pass
    try:
        pygame.mixer.stop()
    except pygame.error:
        pass


ASSETS = {
    # Fundo da tela de MENU inicial. Sugestão: 960x600 px.
    "fundo_intro": caminho_asset("assets/fundo_intro.png"),

    # Avatar do jogador (mesmo personagem das outras fases, se quiser
    # reaproveitar). Sugestão: 138x288 px, fundo transparente (PNG).
    "avatar_parado": caminho_asset("assets/personagem_parado.png"),
    "avatar_andando1": caminho_asset("assets/personagem_andando1.png"),
    "avatar_andando2": caminho_asset("assets/personagem_andando2.png"),

    # Segundo personagem (o "personagem_mulher/parada" escolhido no
    # menu, ver Pygame/menu/jogo.py) -- os nomes de arquivo aqui eram
    # "personagem2_*" (que não existem em assets/) antes desta correção;
    # os arquivos que realmente existem seguem o mesmo padrão usado nas
    # outras fases (personagem_parada.png / personagem_mulher_andando*).
    "avatar2_parado": caminho_asset("assets/personagem_parada.png"),
    "avatar2_andando1": caminho_asset("assets/personagem_mulher_andando1.png"),
    "avatar2_andando2": caminho_asset("assets/personagem_mulher_andando2.png"),

    # Sprite do NPC: Konrad Zuse, parado no laboratório.
    "npc": caminho_asset("assets/konrad_zuse.png"),

    # Fundo da CENA 1: o laboratório danificado de Zuse, com espaço
    # livre para o relé (pequeno) e o Z3 (grande). Sugestão: 960x600 px.
    "fundo_cena1": caminho_asset("assets/laboratorio_zuse.png"),

    # Sprite do relé queimado - pequeno objeto clicável na Cena 1.
    "rele": caminho_asset("assets/rele_queimado.png"),

    # Sprite do Z3 (o computador de Zuse) - fica na Cena 1, só clicável
    # depois que o relé for encontrado.
    "z3": caminho_asset("assets/z3.png"),

    # Fundo da CENA 2: close-up do painel de circuitos do Z3, queimado,
    # com os pontos de conexão por cima. Sugestão: 960x600 px.
    "fundo_cena2": caminho_asset("assets/z3_circuitos.png"),

    # Fundo da CENA DA DICA 1: fita perfurada remontada + circuito
    # religado (uma imagem só, sem mais nada). Sugestão: 960x600 px.
    "fundo_cena_dica1": caminho_asset("assets/fita_perfurada_remontada.png"),

    # Fundo da CENA 3: a segunda ala do laboratório, onde fica o
    # Colossus. Sugestão: 960x600 px.
    "fundo_cena3": caminho_asset("assets/laboratorio_colossus.png"),

    # Sprite do Colossus - objeto clicável na Cena 3 (mesma posição
    # que o Z3 ocupava na Cena 1).
    "colossus": caminho_asset("assets/colossus.png"),

    # Fundo da CENA 4: close-up do painel do Colossus, com o cálculo
    # a ser resolvido. Sugestão: 960x600 px.
    "fundo_cena4": caminho_asset("assets/colossus_painel.png"),

    # Ícone de seta usado na Cena 1 para ir até a Cena 3. Se o arquivo
    # não existir, um triângulo simples é desenhado no lugar.
    "seta_direita": caminho_asset("assets/seta_direita.png"),

    # Telas finais.
    "tela_vitoria": caminho_asset("assets/vitoria.png"),
    "tela_derrota": caminho_asset("assets/derrota.png"),

    # (Opcional) Fonte .ttf de época. Deixe None para usar a padrão.
    "fonte": caminho_asset("assets/fonte_jogo.ttf"),
}

# =====================================================================
# 3. FUNÇÕES AUXILIARES DE CARREGAMENTO (COM PLACEHOLDER AUTOMÁTICO)
# =====================================================================
def carregar_imagem(caminho, tamanho, cor_placeholder, texto_placeholder):
    """Tenta carregar uma imagem do disco e redimensioná-la. Se o
    arquivo não existir, gera um retângulo colorido com texto no
    lugar, para o jogo continuar funcionando durante os testes."""
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
    """Carrega uma fonte customizada (.ttf) se disponível, ou usa uma
    fonte padrão do sistema como alternativa."""
    if caminho and os.path.isfile(caminho):
        return pygame.font.Font(caminho, tamanho)
    return pygame.font.SysFont("georgia", tamanho)

# =====================================================================
# 4. LÓGICA DOS DESAFIOS
# =====================================================================
# --- Desafio da Cena 2: reconectar os circuitos na ordem correta ---
# Cada rótulo representa um ponto de conexão do painel do Z3. O
# jogador precisa clicar nos pontos na ordem definida em
# ORDEM_CORRETA_CIRCUITO. Troque livremente a ordem (ou os rótulos)
# para mudar o desafio.
RÓTULOS_CIRCUITO = ["A", "B", "C", "D"]
ORDEM_CORRETA_CIRCUITO = ["C", "A", "D", "B"]

# --- Desafio da Cena 4: o cálculo do Colossus ---
# Troque o texto da conta e o resultado esperado à vontade - o
# importante é que EXPRESSAO_CALCULO e RESULTADO_CALCULO combinem.
EXPRESSAO_CALCULO = "7 x 6"
RESULTADO_CALCULO = "42"

# =====================================================================
# 5. CLASSE: CAIXA DE TEXTO (aceita letras OU números, conforme o modo)
# =====================================================================
class CaixaDeTexto:
    """Campo de entrada de texto simples. Use modo='letras' para
    respostas em palavras (A-Z) ou modo='numeros' para respostas
    numéricas (0-9) - é o que a Cena 4 desta fase usa."""

    def __init__(self, rect, fonte, tamanho_maximo, modo="letras"):
        self.rect = pygame.Rect(rect)
        self.fonte = fonte
        self.texto = ""
        self.tamanho_maximo = tamanho_maximo
        self.modo = modo  # "letras" ou "numeros"
        self.ativa = True

    def tratar_evento(self, evento):
        """Processa eventos de teclado. Retorna True quando o jogador
        pressiona ENTER (pedindo para validar a resposta)."""
        if not self.ativa or evento.type != pygame.KEYDOWN:
            return False

        if evento.key == pygame.K_RETURN:
            return True
        elif evento.key == pygame.K_BACKSPACE:
            self.texto = self.texto[:-1]
        else:
            tecla = evento.unicode
            aceita = tecla.isdigit() if self.modo == "numeros" else tecla.isalpha()
            if aceita and len(self.texto) < self.tamanho_maximo:
                self.texto += tecla.upper() if self.modo == "letras" else tecla
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

# =====================================================================
# 5. CLASSE: CAIXA DE TEXTO (aceita letras OU números, conforme o modo)
# =====================================================================
class CaixaDeTexto:
    """Campo de entrada de texto simples. Use modo='letras' para
    respostas em palavras (A-Z) ou modo='numeros' para respostas
    numéricas (0-9) - é o que a Cena 4 desta fase usa."""

    def __init__(self, rect, fonte, tamanho_maximo, modo="letras"):
        self.rect = pygame.Rect(rect)
        self.fonte = fonte
        self.texto = ""
        self.tamanho_maximo = tamanho_maximo
        self.modo = modo  # "letras" ou "numeros"
        self.ativa = True

    def tratar_evento(self, evento):
        """Processa eventos de teclado. Retorna True quando o jogador
        pressiona ENTER (pedindo para validar a resposta)."""
        if not self.ativa or evento.type != pygame.KEYDOWN:
            return False

        if evento.key == pygame.K_RETURN:
            return True
        elif evento.key == pygame.K_BACKSPACE:
            self.texto = self.texto[:-1]
        else:
            tecla = evento.unicode
            aceita = tecla.isdigit() if self.modo == "numeros" else tecla.isalpha()
            if aceita and len(self.texto) < self.tamanho_maximo:
                self.texto += tecla.upper() if self.modo == "letras" else tecla
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
        
# =====================================================================
# 6. CLASSE: JOGADOR (AVATAR CONTROLÁVEL)
# =====================================================================
class Jogador:
    """Avatar do jogador. Move-se manualmente (teclado) ou
    automaticamente até um destino (ao clicar num objeto interativo)."""

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
    CENA2 = "cena2"
    CENA_DICA1 = "cena_dica1"
    CENA3 = "cena3"
    CENA4 = "cena4"
    VITORIA = "vitoria"
    DERROTA = "derrota"

    def __init__(self, inventario=None, character_image=None, character_name="Jogador", genero="m"):
        # character_image/character_name/genero seguem o mesmo formato
        # que fase2.run()/Fase_9.Jogo()/Fase_4.Jogo() já recebem do menu
        # (ver Pygame/menu/jogo.py) -- assim o personagem escolhido lá
        # continua o mesmo aqui, em vez desta fase usar sempre o
        # primeiro conjunto de sprites fixo. character_image só é
        # guardado (não usado pra desenhar aqui -- não há retrato grande
        # nesta fase); quem decide o sprite do avatar é `genero`.
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Fase 5 - Z3 e Colossus (1941-1943)")
        self.relogio = pygame.time.Clock()
        self.character_name = character_name

        # --- Inventário de colecionáveis (compartilhável entre fases) ---
        self.inventario = inventario if inventario is not None else Inventario()

        # --- Fontes ---
        self.fonte_titulo = carregar_fonte(ASSETS["fonte"], 30)
        self.fonte_texto = carregar_fonte(ASSETS["fonte"], 26)
        self.fonte_pequena = carregar_fonte(ASSETS["fonte"], 20)

        # --- Imagens ---
        self.img_fundo_intro = carregar_imagem(
            ASSETS["fundo_intro"], (LARGURA, ALTURA), PRETO, "FUNDO DA INTRO",
        )
        self.img_fundo_cena1 = carregar_imagem(
            ASSETS["fundo_cena1"], (LARGURA, ALTURA), AZUL_ACO,
            "FUNDO DA CENA 1\n(laboratório de Zuse)",
        )
        self.img_rele = carregar_imagem(
            ASSETS["rele"], (60, 60), DOURADO_VALVULA, "RELÉ",
        )
        self.img_z3 = carregar_imagem(
            ASSETS["z3"], (188, 142), CINZA, "Z3",
        )
        self.img_fundo_cena2 = carregar_imagem(
            ASSETS["fundo_cena2"], (LARGURA, ALTURA), (50, 50, 55),
            "FUNDO DA CENA 2\n(painel de circuitos do Z3)",
        )
        self.img_fundo_cena_dica1 = carregar_imagem(
            ASSETS["fundo_cena_dica1"], (LARGURA, ALTURA), (70, 60, 40),
            "FUNDO DA CENA DE\nDICA 1 (fita remontada)",
        )
        self.img_fundo_cena3 = carregar_imagem(
            ASSETS["fundo_cena3"], (LARGURA, ALTURA), (55, 65, 80),
            "FUNDO DA CENA 3\n(ala do Colossus)",
        )
        self.img_colossus = carregar_imagem(
            ASSETS["colossus"], (340, 570), (60, 70, 60), "COLOSSUS",
        )
        self.img_fundo_cena4 = carregar_imagem(
            ASSETS["fundo_cena4"], (LARGURA, ALTURA), (40, 40, 45),
            "FUNDO DA CENA 4\n(painel do Colossus)",
        )
        self.img_seta_direita = carregar_imagem(
            ASSETS["seta_direita"], (60, 60), (0, 0, 0), "",
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
        # (o padrão "m") usa o primeiro, mesma regra da Fase 4.
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
            ASSETS["npc"], (155, 305), (115, 90, 130), "KONRAD\nZUSE",
        )

        self.img_vitoria = carregar_imagem(
            ASSETS["tela_vitoria"], (LARGURA, ALTURA), VERDE, "TELA DE VITÓRIA",
        )
        self.img_derrota = carregar_imagem(
            ASSETS["tela_derrota"], (LARGURA, ALTURA), VERMELHO, "TELA DE DERROTA",
        )

        # --- Botões do Menu e das telas finais ---
        self.botao_iniciar = pygame.Rect(0, 0, 220, 60)
        self.botao_iniciar.center = (LARGURA - 270, 500)

        self.botao_reiniciar_vitoria = pygame.Rect(0, 0, 260, 60)
        self.botao_reiniciar_vitoria.center = (LARGURA // 2, ALTURA // 2 + 120)

        self.botao_reiniciar_derrota = pygame.Rect(0, 0, 260, 60)
        self.botao_reiniciar_derrota.center = (LARGURA - 300, ALTURA // 2 + 120)

        # --- Elementos de cena ---
        self.limites_sala = pygame.Rect(0, 0, LARGURA, ALTURA)

        # --- Relé (Cena 1) - clicável desde o início, vira colecionável ---
        # AJUSTE a posição para onde o relé aparece na sua imagem de fundo.
        self.rect_rele = self.img_rele.get_rect(midbottom=(375, ALTURA - 208))
        self.rele_encontrado = False

        # --- Z3 (Cena 1) - só fica clicável depois do relé encontrado ---
        self.rect_z3 = self.img_z3.get_rect(midright=(LARGURA - 362, ALTURA - 268))
        self.ponto_interacao_z3 = (
            self.rect_z3.left - 40,
            self.rect_z3.bottom - 20,
        )

        # --- NPC (Konrad Zuse), parado na Cena 1 ---
        self.rect_npc = self.img_npc.get_rect(midleft=(700, ALTURA - 220))
        
        # --- Chatbot do NPC (Konrad Zuse) integrado à IA local (Ollama) ---
        self.npc_chat = NPCChatbot(
            rect_npc=self.rect_npc,
            nome_npc="Konrad Zuse",
            contexto_fase=(
                "Você é Konrad Zuse, entre 1941 e 1943, dentro de um jogo de escape "
                "room educativo. Responda SOMENTE perguntas relacionadas à Fase 5: "
                "o computador Z3, o relé eletromecânico queimado, o desafio de "
                "reconectar os circuitos, e o computador Colossus. Se o jogador "
                "perguntar algo fora desse tema, responda educadamente que só pode "
                "falar sobre esta fase. Responda sempre em português, em no máximo "
                "3 frases curtas, sem revelar diretamente a solução dos desafios."
            ),
        )

        # --- Seta de navegação (Cena 1 -> Cena 3) ---
        self.rect_seta_avancar = pygame.Rect(0, 0, 56, 56)
        self.rect_seta_avancar.midright = (LARGURA - 15, ALTURA // 2)
        self.ponto_interacao_seta = (
            self.rect_seta_avancar.left - 40,
            self.jogador.rect.centery,
        )

        self.proximo_estado_ao_chegar = None

        # --- Desafio da Cena 2: pontos de conexão do circuito ---
        # AJUSTE as posições dos nós para coincidir com sua imagem de
        # fundo (fundo_cena2 / z3_circuitos.png).
        self.nos_circuito = {
            "A": pygame.Rect(0, 0, 80, 80),
            "B": pygame.Rect(0, 0, 80, 80),
            "C": pygame.Rect(0, 0, 80, 80),
            "D": pygame.Rect(0, 0, 80, 80),
        }
        self.nos_circuito["A"].center = (220, 260)
        self.nos_circuito["B"].center = (420, 420)
        self.nos_circuito["C"].center = (620, 260)
        self.nos_circuito["D"].center = (780, 420)
        self.progresso_circuito = []       # rótulos já clicados corretamente, em ordem
        self.mensagem_erro_circuito = ""

        # --- Botão "Voltar" da Cena de Dica 1 (-> Cena 1) ---
        self.botao_voltar_dica1 = pygame.Rect(0, 0, 160, 50)
        self.botao_voltar_dica1.bottomleft = (30, ALTURA - 30)

        # --- Botão "Voltar" da Cena 3 (-> Cena 1) ---
        self.botao_voltar_cena3 = pygame.Rect(0, 0, 160, 50)
        self.botao_voltar_cena3.bottomleft = (30, ALTURA - 30)

        # --- Colossus (Cena 3) - mesma posição que o Z3 ocupava na Cena 1 ---
        self.ponto_interacao_colossus = (
            self.rect_z3.left - 40,   # reaproveita a mesma posição x/y de referência
            self.rect_z3.bottom - 20,
        )
        self.rect_colossus = self.img_colossus.get_rect(midright=(LARGURA - 260, ALTURA - 220))
        self.ponto_interacao_colossus = (
            self.rect_colossus.left - 20,
            self.rect_colossus.bottom - 5,
        )

        # --- Cena 4: cálculo do Colossus (resposta numérica) ---
        self.caixa_resposta_cena4 = CaixaDeTexto(
            rect=(LARGURA // 2 - 150, 300, 300, 50),
            fonte=self.fonte_texto,
            tamanho_maximo=len(RESULTADO_CALCULO),
            modo="numeros",
        )
        self.mensagem_erro_cena4 = ""
        self.botao_voltar_cena4 = pygame.Rect(0, 0, 160, 50)
        self.botao_voltar_cena4.bottomleft = (30, ALTURA - 30)

        # --- Ícone de inventário (canto inferior direito, sempre visível) ---
        self.botao_inventario = pygame.Rect(0, 0, 70, 70)
        self.botao_inventario.bottomright = (LARGURA - 20, ALTURA - 20)
        self.mostrar_painel_inventario = False

        # Mapeia o nome de um item colecionável para uma imagem de
        # visualização (mostrada em tela cheia ao clicar no item
        # dentro do painel de inventário). Itens fora deste dicionário
        # simplesmente não fazem nada ao serem clicados no painel.
        self.imagens_dos_itens = {
            "Relé Eletromecânico do Z3": self.img_rele,
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

        fundo_rect = pygame.Rect(LARGURA - 130, 15, 110, 40)
        pygame.draw.rect(self.tela, (0, 0, 0, 150), fundo_rect, border_radius=8)
        render = self.fonte_texto.render(texto, True, cor)
        self.tela.blit(render, render.get_rect(center=fundo_rect.center))

    # -----------------------------------------------------------------
    # TELA: MENU INICIAL
    # -----------------------------------------------------------------
    def desenhar_menu(self):
        self.tela.blit(self.img_fundo_intro, (0, 0))
        titulo = self.fonte_titulo.render("Fase 05 - Z3 e Colossus", True, BRANCO)
        self.tela.blit(titulo, titulo.get_rect(center=(LARGURA - 280, 170)))

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_iniciar.collidepoint(mouse_pos) else AMARELO_SEPIA

        pygame.draw.rect(self.tela, cor_botao, self.botao_iniciar, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_iniciar, width=2, border_radius=10)

        texto_botao = self.fonte_texto.render("Iniciar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_iniciar.center))

        instrucao = self.fonte_pequena.render(
            "Clique em Iniciar ou pressione ENTER", True, CINZA_CLARO,
        )
        self.tela.blit(instrucao, instrucao.get_rect(center=(LARGURA - 270, 550)))

    # -----------------------------------------------------------------
    # TELA: CENA 1 - LABORATÓRIO + RELÉ + Z3 + NPC + SETA
    # -----------------------------------------------------------------
    def desenhar_cena1(self):
        mouse_pos = pygame.mouse.get_pos()

        # O Z3 só reage ao mouse (cursor de mão) depois do relé encontrado
        z3_esta_clicavel = self.rele_encontrado
        sobre_algo_clicavel = (
            self.rect_rele.collidepoint(mouse_pos) and not self.rele_encontrado
        ) or (
            z3_esta_clicavel and self.rect_z3.collidepoint(mouse_pos)
        ) or self.rect_seta_avancar.collidepoint(mouse_pos)

        pygame.mouse.set_cursor(
            pygame.SYSTEM_CURSOR_HAND if sobre_algo_clicavel else pygame.SYSTEM_CURSOR_ARROW
        )

        self.tela.blit(self.img_fundo_cena1, (0, 0))

        # O Z3 aparece sempre (é parte do cenário), mas só ganha um
        # contorno de destaque depois que o relé foi encontrado
        self.tela.blit(self.img_z3, self.rect_z3)
        if self.rele_encontrado:
            pygame.draw.rect(self.tela, AMARELO_SEPIA, self.rect_z3, width=3, border_radius=6)

        # O relé só aparece enquanto não foi coletado
        if not self.rele_encontrado:
            self.tela.blit(self.img_rele, self.rect_rele)
            pygame.draw.rect(self.tela, AMARELO_SEPIA, self.rect_rele, width=3, border_radius=6)

        self.tela.blit(self.img_npc, self.rect_npc)
        self.jogador.desenhar(self.tela)
        self.desenhar_seta_avancar(self.rect_seta_avancar)
        self.desenhar_cronometro()
        self.desenhar_botao_inventario()
        
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
    # TELA: CENA 2 - RECONECTAR OS CIRCUITOS DO Z3
    # -----------------------------------------------------------------
    def desenhar_cena2(self):
        self.tela.blit(self.img_fundo_cena2, (0, 0))
        self.desenhar_cronometro()
        self.desenhar_botao_inventario()

        titulo = self.fonte_texto.render(
            "Reconecte os circuitos na ordem correta:", True, BRANCO,
        )
        self.tela.blit(titulo, titulo.get_rect(center=(LARGURA // 2, 100)))

        # --- Desenha os 4 nós do circuito ---
        for rotulo, rect in self.nos_circuito.items():
            ja_conectado = rotulo in self.progresso_circuito
            cor = VERDE if ja_conectado else AZUL_ACO
            pygame.draw.circle(self.tela, cor, rect.center, rect.width // 2)
            pygame.draw.circle(self.tela, BRANCO, rect.center, rect.width // 2, width=3)
            texto_no = self.fonte_texto.render(rotulo, True, BRANCO)
            self.tela.blit(texto_no, texto_no.get_rect(center=rect.center))

        # --- Progresso (quantos já conectados) ---
        progresso_texto = self.fonte_pequena.render(
            f"Conectados: {len(self.progresso_circuito)}/{len(ORDEM_CORRETA_CIRCUITO)}",
            True, CINZA_CLARO,
        )
        self.tela.blit(progresso_texto, progresso_texto.get_rect(center=(LARGURA // 2, 500)))

        if self.mensagem_erro_circuito:
            render_erro = self.fonte_pequena.render(self.mensagem_erro_circuito, True, VERMELHO)
            self.tela.blit(render_erro, render_erro.get_rect(center=(LARGURA // 2, 530)))

        dica_voltar = self.fonte_pequena.render("ESC para voltar à sala", True, CINZA_CLARO)
        self.tela.blit(dica_voltar, (20, ALTURA - 35))

    def clicar_no_circuito(self, posicao_mouse):
        """Verifica se o clique caiu em algum nó do circuito ainda não
        conectado, e avança (ou reseta) o progresso de acordo com a
        ordem correta. Chamado pelo laço de eventos em CENA2."""
        for rotulo, rect in self.nos_circuito.items():
            if rect.collidepoint(posicao_mouse) and rotulo not in self.progresso_circuito:
                indice_esperado = len(self.progresso_circuito)
                if rotulo == ORDEM_CORRETA_CIRCUITO[indice_esperado]:
                    self.progresso_circuito.append(rotulo)
                    self.mensagem_erro_circuito = ""
                    if len(self.progresso_circuito) == len(ORDEM_CORRETA_CIRCUITO):
                        # Circuito religado! Segue para a Cena de Dica 1.
                        self.estado = Jogo.CENA_DICA1
                else:
                    self.mensagem_erro_circuito = "Conexão errada! O circuito resetou."
                    self.progresso_circuito = []
                break

    # -----------------------------------------------------------------
    # TELA: CENA DA DICA 1 - APENAS IMAGEM + BOTÃO VOLTAR
    # -----------------------------------------------------------------
    def desenhar_cena_dica1(self):
        self.tela.blit(self.img_fundo_cena_dica1, (0, 0))
        self.desenhar_cronometro()
        self.desenhar_botao_inventario()

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_voltar_dica1.collidepoint(mouse_pos) else AMARELO_SEPIA

        pygame.draw.rect(self.tela, cor_botao, self.botao_voltar_dica1, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_voltar_dica1, width=2, border_radius=10)

        texto_botao = self.fonte_pequena.render("Voltar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_voltar_dica1.center))

    # -----------------------------------------------------------------
    # TELA: CENA 3 - ALA DO COLOSSUS
    # -----------------------------------------------------------------
    def desenhar_cena3(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect_colossus.collidepoint(mouse_pos):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        self.tela.blit(self.img_fundo_cena3, (0, 0))
        self.tela.blit(self.img_colossus, self.rect_colossus)
        self.jogador.desenhar(self.tela)
        self.desenhar_cronometro()
        self.desenhar_botao_inventario()

        cor_botao = VERDE if self.botao_voltar_cena3.collidepoint(mouse_pos) else AMARELO_SEPIA
        pygame.draw.rect(self.tela, cor_botao, self.botao_voltar_cena3, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_voltar_cena3, width=2, border_radius=10)
        texto_botao = self.fonte_pequena.render("Voltar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_voltar_cena3.center))

    def atualizar_cena3(self, teclas):
        chegou = self.jogador.mover(teclas, self.limites_sala)
        if chegou and self.proximo_estado_ao_chegar is not None:
            self.mensagem_erro = ""
            self.estado = self.proximo_estado_ao_chegar
            self.proximo_estado_ao_chegar = None

    # -----------------------------------------------------------------
    # TELA: CENA 4 - CÁLCULO DO COLOSSUS (RESPOSTA NUMÉRICA)
    # -----------------------------------------------------------------
    def desenhar_cena4(self):
        self.tela.blit(self.img_fundo_cena4, (0, 0))
        self.desenhar_cronometro()
        self.desenhar_botao_inventario()

        titulo = self.fonte_texto.render(
            "Resolva o cálculo para verificar o Colossus:", True, BRANCO,
        )
        self.tela.blit(titulo, titulo.get_rect(center=(LARGURA // 2, 180)))

        expressao = self.fonte_titulo.render(f"{EXPRESSAO_CALCULO} = ?", True, DOURADO_VALVULA)
        self.tela.blit(expressao, expressao.get_rect(center=(LARGURA // 2, 240)))

        self.caixa_resposta_cena4.desenhar(self.tela)

        if self.mensagem_erro_cena4:
            render_erro = self.fonte_pequena.render(self.mensagem_erro_cena4, True, VERMELHO)
            self.tela.blit(render_erro, render_erro.get_rect(center=(LARGURA // 2, 400)))

        dica_voltar = self.fonte_pequena.render("ESC para voltar", True, CINZA_CLARO)
        self.tela.blit(dica_voltar, (20, ALTURA - 35))

        mouse_pos = pygame.mouse.get_pos()
        cor_botao = VERDE if self.botao_voltar_cena4.collidepoint(mouse_pos) else AMARELO_SEPIA
        pygame.draw.rect(self.tela, cor_botao, self.botao_voltar_cena4, border_radius=10)
        pygame.draw.rect(self.tela, BRANCO, self.botao_voltar_cena4, width=2, border_radius=10)
        texto_botao = self.fonte_pequena.render("Voltar", True, PRETO)
        self.tela.blit(texto_botao, texto_botao.get_rect(center=self.botao_voltar_cena4.center))

    def validar_calculo_colossus(self):
        """Compara a resposta numérica com RESULTADO_CALCULO. Se
        acertar, coleta a peça/sequência final e vai DIRETO para a
        Vitória - sem nenhuma cena intermediária."""
        if self.caixa_resposta_cena4.texto == RESULTADO_CALCULO:
            item_final = ItemColecionavel(
                nome="Sequência Numérica do Colossus",
                descricao="O componente/código que vai reparar a cápsula do tempo.",
            )
            self.inventario.adicionar(item_final)
            self.estado = Jogo.VITORIA
            # Estrelas calculadas com o tempo QUE SOBROU no timer neste
            # instante exato (antes de reiniciar()/um novo cronômetro
            # zerar ticks_inicio) -- mesmo ponto de cálculo que
            # babbage_lovelace.py e fase4_atual.py usam. Não é mostrado
            # nesta tela (ver Pygame/Fase_2/fase2/fase2.py e
            # Pygame/Fase_9/fase9.py, onde as estrelas também só
            # aparecem no mapa, não no final da fase) -- só calculado e
            # salvo aqui.
            tempo_restante = self.tempo_restante_segundos()
            estrelas = _calcular_estrelas(tempo_restante)
            tempo_gasto = TEMPO_LIMITE_SEGUNDOS - tempo_restante
            _salvar_progresso(estrelas, _formatar_tempo(tempo_gasto))
        else:
            self.mensagem_erro_cena4 = "Cálculo incorreto. Tente novamente!"
            self.caixa_resposta_cena4.texto = ""


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
            # Centraliza a imagem do item (que pode ser pequena, tipo
            # o relé) sobre um fundo escuro, em vez de esticá-la
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
        self.caixa_resposta_cena4.texto = ""
        self.mensagem_erro = ""
        self.mensagem_erro_cena4 = ""
        self.mensagem_erro_circuito = ""
        self.progresso_circuito = []
        self.rele_encontrado = False
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
                            self.npc_chat.tratar_evento(evento)          # <-- ADICIONE este bloco todo
                        elif evento.key == pygame.K_e and self.npc_chat.perto_do_jogador(self.jogador.rect):
                            self.npc_chat.abrir_dialogo()

                    elif evento.type == pygame.KEYDOWN:
                        if self.estado == Jogo.CENA2 and evento.key == pygame.K_ESCAPE:
                            self.estado = Jogo.CENA1

                        elif self.estado == Jogo.CENA4:
                            if evento.key == pygame.K_ESCAPE:
                                self.estado = Jogo.CENA3
                            else:
                                enter_pressionado = self.caixa_resposta_cena4.tratar_evento(evento)
                                if enter_pressionado:
                                    self.validar_calculo_colossus()

                    elif self.estado in (Jogo.VITORIA, Jogo.DERROTA) and evento.key == pygame.K_r:
                        self.reiniciar()

                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if self.estado == Jogo.MENU and self.botao_iniciar.collidepoint(evento.pos):
                        self.iniciar_cronometro()
                        self.estado = Jogo.CENA1

                    # Clique no relé -> vira colecionável direto (sem cena própria)
                    elif self.estado == Jogo.CENA1 and not self.rele_encontrado and self.rect_rele.collidepoint(evento.pos):
                        item_rele = ItemColecionavel(
                            nome="Relé Eletromecânico do Z3",
                            descricao="O relé queimado que travava o funcionamento do Z3.",
                        )
                        self.inventario.adicionar(item_rele)
                        self.rele_encontrado = True

                    # Clique no Z3 -> só funciona depois do relé encontrado
                    elif self.estado == Jogo.CENA1 and self.rele_encontrado and self.rect_z3.collidepoint(evento.pos):
                        self.jogador.mover_ate(self.ponto_interacao_z3)
                        self.proximo_estado_ao_chegar = Jogo.CENA2

                    # Clique na seta -> anda até ela e segue para a Cena 3
                    elif self.estado == Jogo.CENA1 and self.rect_seta_avancar.collidepoint(evento.pos):
                        self.jogador.mover_ate(self.ponto_interacao_seta)
                        self.proximo_estado_ao_chegar = Jogo.CENA3

                    # Clique nos nós do circuito, dentro da Cena 2
                    elif self.estado == Jogo.CENA2:
                        self.clicar_no_circuito(evento.pos)

                    # Botão "Voltar" da Cena de Dica 1 -> Cena 1
                    elif self.estado == Jogo.CENA_DICA1 and self.botao_voltar_dica1.collidepoint(evento.pos):
                        self.estado = Jogo.CENA1

                    # Clique no Colossus -> anda até ele e segue para a Cena 4
                    elif self.estado == Jogo.CENA3 and self.rect_colossus.collidepoint(evento.pos):
                        self.jogador.mover_ate(self.ponto_interacao_colossus)
                        self.proximo_estado_ao_chegar = Jogo.CENA4

                    # Botão "Voltar" da Cena 3 -> Cena 1
                    elif self.estado == Jogo.CENA3 and self.botao_voltar_cena3.collidepoint(evento.pos):
                        self.jogador.rect.midright = (self.rect_seta_avancar.left - 20, self.jogador.rect.centery)
                        self.estado = Jogo.CENA1

                    # Botão "Voltar" da Cena 4 -> Cena 3
                    elif self.estado == Jogo.CENA4 and self.botao_voltar_cena4.collidepoint(evento.pos):
                        self.estado = Jogo.CENA3

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
            if self.estado in (Jogo.CENA1, Jogo.CENA2, Jogo.CENA_DICA1, Jogo.CENA3, Jogo.CENA4) and self.ticks_inicio is not None:
                if self.tempo_restante_segundos() <= 0:
                    self.estado = Jogo.DERROTA

            # --- Atualização de lógica por estado ---
            if self.estado == Jogo.CENA1:
                teclas = pygame.key.get_pressed()
                self.atualizar_cena1(teclas)
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
            elif self.estado == Jogo.CENA4:
                self.desenhar_cena4()
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
# 8. PONTO DE ENTRADA DO PROGRAMA
# =====================================================================
if __name__ == "__main__":
    jogo = Jogo()
    jogo.executar()

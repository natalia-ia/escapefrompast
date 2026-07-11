"""
Este arquivo implementa o chatbot da Ada Lovelace na Fase 2: um único
retrato clicável, sobreposto ao canto superior esquerdo do papel/planta na
parede da oficina, que abre uma caixinha de conversa compacta (estilo RPG,
igual à do Gerbert na Fase 1) onde o jogador pode digitar perguntas e
receber respostas geradas pelo modelo qwen2.5:0.5b, rodando localmente via
Ollama, no papel da própria Ada. Ela conhece a lógica do puzzle de
Babbage/Lovelace e pode dar dicas sobre a ordem dos cartões, mas evita
simplesmente entregar a resposta pronta -- a ideia é ajudar sem estragar a
graça do puzzle.

O mesmo retrato/conversa aparece em DOIS lugares: na cena principal da
oficina (fase2.py) e na tela do próprio puzzle (babbage_lovelace.py) -- é
o mesmo objeto AdaChat repassado de um pra outro, então a conversa (e a
posição do ícone) continua igual nos dois.

Mesma estratégia do Gerbert (Fase 1): a chamada ao Ollama roda numa thread
separada, com timeout, para a janela do jogo nunca travar esperando uma
resposta (mesmo se o Ollama não estiver rodando ou demorar demais). Não
precisa de chave de API nem de conexão com a internet -- o modelo roda no
próprio computador.

Este módulo é independente do resto da Fase 2 (só usa `common` para
cores/fontes compartilhadas) -- quem o conecta ao jogo é fase2.py e
babbage_lovelace.py, que chamam os métodos de evento/desenho de AdaChat
nos momentos certos e não deixam o jogador se mover nem interagir com
outros objetos enquanto a conversa está aberta (mesma regra usada pela
caixinha do Gerbert na Fase 1).
"""

import os
import threading

import ollama
import pygame

from . import common

# ---------------------------------------------------------------------------
# Configuração do Ollama
# ---------------------------------------------------------------------------
# qwen2.5:0.5b é o mesmo modelo já usado pelo Gerbert (Fase 1) -- pequeno o
# bastante pra rodar bem em computadores com pouca memória disponível, e
# reaproveitar o mesmo modelo evita ter que baixar um segundo.
MODELO_ADA = "qwen2.5:0.5b"

# Tempo limite (em segundos) que o cliente do Ollama espera antes de
# desistir -- sem isso, se o Ollama não estiver rodando ou demorar demais,
# a chamada ficaria esperando pra sempre e travaria a caixinha em "Ada está
# pensando...". Mesmo valor usado pelo Gerbert (testado na prática: uma
# resposta chegou a levar ~16s).
TIMEOUT_OLLAMA_SEGUNDOS = 30
cliente_ollama = ollama.Client(timeout=TIMEOUT_OLLAMA_SEGUNDOS)

# Instrução de sistema enviada à IA para ela sempre responder no papel da
# Ada Lovelace. Ela sabe que o puzzle pede pra montar um "programa" com
# cartões de instrução (iniciar -> operação matemática -> repetir ->
# imprimir o resultado), mas é orientada a dar dicas em vez de entregar a
# ordem certa de bandeja -- o jogador ainda precisa pensar um pouco.
PROMPT_SISTEMA_ADA = (
    "Você é Ada Lovelace, matemática e escritora, ajudando o jogador a "
    "programar a Máquina Analítica de Charles Babbage. O jogador está "
    "tentando montar, em ordem, os cartões de instrução de um pequeno "
    "programa (algo como: iniciar a máquina, fazer o cálculo matemático, "
    "repetir os passos necessários e por fim imprimir o resultado). Você "
    "pode dar dicas sobre COMO pensar na lógica de um programa (o que "
    "precisa vir antes do quê, e por quê), mas nunca liste a ordem exata "
    "e completa dos cartões, mesmo se o jogador insistir -- prefere "
    "ensinar o raciocínio a entregar a resposta pronta. Responda sempre "
    "em português, de forma breve (1-2 frases), com tom animado, gentil "
    "e didático, adequado a uma fase educativa sobre história da "
    "computação."
)

# ---------------------------------------------------------------------------
# Configuração visual (retrato, ícone, caixinha de conversa)
# ---------------------------------------------------------------------------
# Pasta assets/ da Fase 2 (fase2/assets/, dois níveis acima deste arquivo:
# puzzles/ -> fase2/), mesmo padrão usado em babbage_lovelace.py.
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
CAMINHO_RETRATO_ADA = os.path.join(ASSETS_DIR, "ada_lovelace.png")

# ada_lovelace.png é um retrato de corpo inteiro (1023x1537, bem mais alto
# que largo) -- pra virar um ícone/avatar redondo decente, primeiro
# recortamos só a região do rosto (medida olhando pra imagem original,
# formato x/y/largura/altura), formando um quadrado, e só depois aplicamos
# o recorte circular. Sem esse recorte de rosto, o círculo pequeno
# mostraria o corpo inteiro minúsculo em vez de um retrato reconhecível.
RECORTE_ROSTO_RECT = (250, 0, 450, 450)

# Só existe UM retrato/ícone (nada de um ícone pequeno + um avatar maior
# separado) -- o mesmo círculo é usado como botão fixo na parede e como
# indicador de que a conversa está rolando.
TAMANHO_ICONE = 54

# Posição do ícone: canto superior esquerdo do papel/planta na parede da
# oficina (fase2.PAPER_RECT = Rect(210, 130, 275, 190) -- não importado
# aqui pra não criar dependência circular com fase2.py, só copiado do
# valor de lá). O ícone fica sobreposto à própria planta, como pedido,
# com uma pequena margem pra não ficar "pendurado" pra fora dela.
ICONE_POS = (210 + 8 + TAMANHO_ICONE // 2, 130 + 8 + TAMANHO_ICONE // 2)

# Caixinha de chat: estilo clássico de RPG (tipo Stardew Valley) -- uma
# faixa horizontal na parte INFERIOR da tela inteira, com a caixa de texto
# grande à esquerda e um retrato emoldurado à direita. Todas as medidas
# abaixo foram calibradas visualmente (protótipo renderizado e comparado
# com o personagem/cenário) antes de aplicar de vez.
#
# BAR_ALTURA = 290px é ~44,6% da altura da tela (650px) -- dentro da faixa
# de 35-45% pedida. BAR_LARGURA quase a largura toda (1000 - 2*20 margem).
BAR_LARGURA, BAR_ALTURA = 960, 290
BAR_MARGEM_LATERAL = 20
BAR_MARGEM_INFERIOR = 16

# Espaço entre a caixa de texto e o painel do retrato, e o tamanho do
# painel -- PAINEL_ALTURA (245) é ~1,11x a altura do personagem jogável
# (Jogador/AVATAR_FIT = 220px), ou seja "um pouco maior", como pedido.
GAP_PAINEL = 14
PAINEL_LARGURA, PAINEL_ALTURA = 230, 245
RETRATO_GRANDE_DIAMETRO = 132  # bem maior que o ícone (54px) -- um "close" reconhecível

# Borda do 9-slice da moldura grande (common.LARGE_FRAME) quando usada
# neste tamanho compacto -- bem menor que LARGE_FRAME_BORDER (200,
# calibrado pra telas de puzzle em tela cheia). Com 200 aqui, os cantos
# ornamentados tomariam a caixa inteira; com 36, sobra uma área plana
# generosa no meio pro texto.
TEXTO_BORDA = 36

# Recuo do conteúdo (texto/campo) em relação à borda da moldura -- bem
# maior que a borda em si, porque o ornamento dos cantos "sangra" visualmente
# pra dentro da área plana (testado no protótipo: com um recuo igual à
# borda, as primeiras letras do texto ficavam escondidas atrás do desenho
# do canto).
CONTEUDO_RECUO_X = 74
CONTEUDO_RECUO_Y_TOPO = 42

# Cor do texto sobre a área plana da moldura grande (um tom de pergaminho
# claro) -- precisa ser um marrom escuro pra ler bem, diferente do CREAM
# claro usado no resto da UI (que sumiria num fundo claro).
COR_TEXTO_PERGAMINHO = (45, 32, 20)

# Largura útil pro texto/campo de digitação dentro da caixa esquerda,
# já descontando a moldura grande e o recuo extra do ornamento dos
# cantos (calculada uma vez aqui, reaproveitada no limite de digitação e
# no desenho).
LARGURA_CONTEUDO = (BAR_LARGURA - PAINEL_LARGURA - GAP_PAINEL) - 2 * TEXTO_BORDA - 2 * CONTEUDO_RECUO_X


def _recortar_em_circulo(imagem):
    """Recorta uma imagem quadrada em um círculo -- mesma técnica usada no
    retrato do Gerbert (Fase 1): desenha uma máscara circular branca numa
    superfície transparente e usa BLEND_RGBA_MIN pra "apagar" tudo que
    sobra fora do círculo."""
    tamanho = imagem.get_size()
    mascara = pygame.Surface(tamanho, pygame.SRCALPHA)
    pygame.draw.circle(mascara, (255, 255, 255, 255), (tamanho[0] // 2, tamanho[1] // 2), tamanho[0] // 2)
    recortada = imagem.copy()
    recortada.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return recortada


def _quebrar_texto(texto, fonte, largura_maxima):
    """Quebra `texto` em linhas que cabem em `largura_maxima` pixels --
    mesma lógica usada em fase2._wrap_text e em fase_1.quebrar_texto,
    copiada aqui (em vez de importada) para este módulo não depender de
    nenhum outro arquivo da Fase 2 além de `common`."""
    palavras = texto.split(" ")
    linhas = []
    atual = ""
    for palavra in palavras:
        candidata = f"{atual} {palavra}".strip()
        if fonte.size(candidata)[0] <= largura_maxima:
            atual = candidata
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


class AdaChat:
    """Controla o estado e o desenho da conversa com a Ada Lovelace.

    Guarda: se a caixinha está aberta, o que o jogador está digitando, a
    última resposta recebida e se está esperando a IA responder. Quem usa
    esta classe (fase2.py) só precisa chamar `tratar_clique_no_icone`,
    `tratar_evento_teclado` e `desenhar` nos momentos certos do loop
    principal -- toda a lógica de abrir/fechar/perguntar fica encapsulada
    aqui dentro.
    """

    def __init__(self):
        retrato_original = pygame.image.load(CAMINHO_RETRATO_ADA).convert_alpha()
        rosto = retrato_original.subsurface(pygame.Rect(RECORTE_ROSTO_RECT)).copy()
        self.icone = _recortar_em_circulo(pygame.transform.smoothscale(rosto, (TAMANHO_ICONE, TAMANHO_ICONE)))
        self.icone_rect = self.icone.get_rect(center=ICONE_POS)

        # Retrato maior, mostrado dentro do painel emoldurado da caixinha
        # de chat (mesmo recorte de rosto do ícone, só que numa escala bem
        # maior, pra ficar reconhecível como um "close" de verdade).
        self.retrato_grande = _recortar_em_circulo(pygame.transform.smoothscale(rosto, (RETRATO_GRANDE_DIAMETRO, RETRATO_GRANDE_DIAMETRO)))

        self.aberta = False
        self.texto_digitado = ""
        self.resposta = ""
        self.pensando = False

    def tratar_clique_no_icone(self, pos_virtual):
        """Se `pos_virtual` (já convertido pra coordenadas da tela virtual
        1000x650, igual ao resto dos cliques em fase2.py) cair em cima do
        ícone da Ada, abre a caixinha de conversa. Devolve True se abriu
        (pra quem chamar saber que esse clique já foi tratado e não deve
        ser repassado pra outra coisa)."""
        if not self.aberta and self.icone_rect.collidepoint(pos_virtual):
            self.aberta = True
            self.texto_digitado = ""
            self.resposta = ""
            return True
        return False

    def tratar_evento_teclado(self, evento):
        """Processa um evento KEYDOWN enquanto a caixinha está aberta: ESC
        fecha a conversa, Enter envia a pergunta (numa thread separada,
        sem travar o jogo), Backspace apaga e o resto digita normalmente.
        Só deve ser chamada quando `self.aberta` for True."""
        if evento.key == pygame.K_ESCAPE:
            self.aberta = False
        elif evento.key == pygame.K_RETURN:
            if self.texto_digitado and not self.pensando:
                pergunta = self.texto_digitado
                self.texto_digitado = ""
                self.pensando = True
                self.resposta = ""
                threading.Thread(target=self._perguntar, args=(pergunta,), daemon=True).start()
        elif evento.key == pygame.K_BACKSPACE:
            if not self.pensando:
                self.texto_digitado = self.texto_digitado[:-1]
        elif not self.pensando and evento.unicode.isprintable():
            common.init_fonts()
            if common.FONT_SMALL.size(self.texto_digitado + evento.unicode)[0] <= LARGURA_CONTEUDO:
                self.texto_digitado += evento.unicode

    def _perguntar(self, pergunta):
        """Roda em uma thread separada (chamada por tratar_evento_teclado
        ao apertar Enter): chama o modelo qwen2.5:0.5b (rodando localmente
        via Ollama) pedindo uma resposta como se fosse a Ada, e guarda o
        resultado em `self.resposta`. Mesma abordagem do Gerbert (Fase 1):
        o timeout já embutido em `cliente_ollama` (ver TIMEOUT_OLLAMA_SEGUNDOS
        lá em cima) é suficiente aqui, sem precisar de uma segunda thread
        interna com `threading.Event` como na versão antiga com Gemini.
        """
        try:
            resultado = cliente_ollama.chat(
                model=MODELO_ADA,
                messages=[
                    {"role": "system", "content": PROMPT_SISTEMA_ADA},
                    {"role": "user", "content": pergunta},
                ],
            )
            self.resposta = resultado["message"]["content"].strip()
        except Exception:
            # Cobre timeout, Ollama fora do ar ou qualquer outro erro --
            # mesma filosofia do Gerbert: nunca deixar o jogador travado
            # esperando.
            self.resposta = "Ada não conseguiu responder, tente novamente."
        self.pensando = False

    def desenhar(self, tela, mouse_pos):
        """Desenha o ícone (sempre visível) e, se a conversa estiver
        aberta, a faixa de diálogo estilo RPG clássico (caixa de texto
        grande à esquerda + retrato emoldurado à direita) na parte
        inferior da tela. `mouse_pos` já deve vir convertido pra
        coordenadas da tela virtual, só para destacar o ícone quando o
        mouse passa por cima (efeito de hover)."""
        common.init_fonts()
        common._load_frames()

        hovered = self.icone_rect.collidepoint(mouse_pos) and not self.aberta
        if hovered:
            pygame.draw.circle(tela, common.GOLD, self.icone_rect.center, TAMANHO_ICONE // 2 + 4, width=3)
        tela.blit(self.icone, self.icone_rect)

        if not self.aberta:
            return

        # A faixa inteira fica colada na parte inferior da tela (estilo
        # Stardew Valley), não mais flutuando perto do ícone -- por isso
        # usa tela.get_size() em vez de alguma posição relativa ao ícone.
        largura_tela, altura_tela = tela.get_size()
        bar_rect = pygame.Rect(
            BAR_MARGEM_LATERAL,
            altura_tela - BAR_ALTURA - BAR_MARGEM_INFERIOR,
            BAR_LARGURA,
            BAR_ALTURA,
        )
        texto_rect = pygame.Rect(
            bar_rect.left, bar_rect.top,
            BAR_LARGURA - PAINEL_LARGURA - GAP_PAINEL, BAR_ALTURA,
        )
        painel_rect = pygame.Rect(
            texto_rect.right + GAP_PAINEL, bar_rect.top,
            PAINEL_LARGURA, PAINEL_ALTURA,
        )

        # --- caixa de texto grande (esquerda) ---
        common.nine_slice(tela, common.LARGE_FRAME, texto_rect, TEXTO_BORDA)

        # --- painel do retrato (direita) ---
        common.nine_slice(tela, common.SMALL_PANEL, painel_rect, common.SMALL_PANEL_BORDER)
        tela.blit(
            self.retrato_grande,
            self.retrato_grande.get_rect(center=(painel_rect.centerx, painel_rect.top + painel_rect.height // 2 - 8)),
        )
        nome_surf = common.FONT_MED.render("Ada Lovelace", True, common.GOLD)
        tela.blit(nome_surf, nome_surf.get_rect(center=(painel_rect.centerx, bar_rect.bottom - 22)))

        # --- conteúdo de texto (fala da Ada) ---
        # O recuo (CONTEUDO_RECUO_X/Y) é bem maior que a borda em si, pra
        # não ficar atrás do ornamento dos cantos da moldura -- ver
        # comentário de LARGURA_CONTEUDO mais acima.
        conteudo_x = texto_rect.left + TEXTO_BORDA + CONTEUDO_RECUO_X
        conteudo_y = texto_rect.top + TEXTO_BORDA + CONTEUDO_RECUO_Y_TOPO

        if self.pensando:
            fala = "Ada está pensando..."
        else:
            fala = self.resposta or "O que você gostaria de me perguntar?"

        y = conteudo_y
        for linha in _quebrar_texto(fala, common.FONT_SMALL, LARGURA_CONTEUDO):
            linha_surf = common.FONT_SMALL.render(linha, True, COR_TEXTO_PERGAMINHO)
            tela.blit(linha_surf, (conteudo_x, y))
            y += common.FONT_SMALL.get_height() + 4

        # --- campo de digitação + dica, no rodapé da caixa de texto ---
        campo_h = 26
        campo_y = texto_rect.bottom - TEXTO_BORDA - campo_h - 26
        campo_rect = pygame.Rect(conteudo_x, campo_y, LARGURA_CONTEUDO, campo_h)
        pygame.draw.rect(tela, (250, 245, 230), campo_rect, border_radius=4)
        pygame.draw.rect(tela, COR_TEXTO_PERGAMINHO, campo_rect, width=2, border_radius=4)
        texto_surf = common.FONT_SMALL.render(self.texto_digitado, True, (20, 20, 20))
        tela.blit(texto_surf, (campo_rect.x + 5, campo_rect.y + 5))

        dica_surf = common.FONT_SMALL.render("Enter pergunta, Esc fecha", True, COR_TEXTO_PERGAMINHO)
        tela.blit(dica_surf, (conteudo_x, campo_rect.bottom + 4))

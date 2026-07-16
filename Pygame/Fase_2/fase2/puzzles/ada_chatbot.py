"""
Este arquivo implementa o chatbot da Ada Lovelace na Fase 2: um único
retrato clicável, sobreposto ao canto superior esquerdo do papel/planta na
parede da oficina, que abre uma caixinha de conversa compacta (estilo RPG,
igual à do Gerbert na Fase 1) onde o jogador pode digitar perguntas e
receber respostas geradas pelo modelo qwen2.5:1.5b, rodando localmente via
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
# qwen2.5:1.5b -- trocado do 0.5b (usado pelo Gerbert na Fase 1) depois de
# comparar as duas respostas lado a lado: o 0.5b divagava bastante e às
# vezes respondia sobre qualquer assunto que o jogador perguntasse, mesmo
# fora do tema da fase. O 1.5b ainda é leve (~1GB) mas segue instruções de
# escopo/tamanho bem melhor.
MODELO_ADA = "qwen2.5:1.5b"

# Tempo limite (em segundos) que o cliente do Ollama espera antes de
# desistir -- sem isso, se o Ollama não estiver rodando ou demorar demais,
# a chamada ficaria esperando pra sempre e travaria a caixinha em "Ada está
# pensando...". Mesmo valor usado pelo Gerbert (testado na prática: uma
# resposta chegou a levar ~16s).
TIMEOUT_OLLAMA_SEGUNDOS = 30

# temperature baixa (padrão do Ollama é bem mais alto) deixa as respostas
# mais previsíveis e focadas -- testado na prática: com a temperatura
# padrão, o modelo 1.5b variava entre respostas curtas e ótimas e
# respostas de vários parágrafos fugindo do assunto; com 0.4 ficou
# consistente nas duas coisas, e como bônus respondeu mais rápido (o
# modelo "titubeia" menos e termina de gerar antes).
TEMPERATURE_ADA = 0.4
cliente_ollama = ollama.Client(timeout=TIMEOUT_OLLAMA_SEGUNDOS)

# Instrução de sistema enviada à IA para ela sempre responder no papel da
# Ada Lovelace. Reforçada depois de testes mostrarem que o modelo pequeno
# só respeita bem o escopo (só falar de Babbage/Ada/1800-1840) e o limite
# de tamanho quando as regras vêm bem explícitas e acompanhadas de
# exemplos (few-shot) -- só descrever a regra em prosa não bastava.
PROMPT_SISTEMA_ADA = (
    "Você é Ada Lovelace, matemática e escritora do século XIX, ajudando "
    "o jogador a programar a Máquina Analítica de Charles Babbage numa "
    "fase educativa sobre história da computação (1800-1840).\n\n"
    "REGRAS IMPORTANTES:\n"
    "- Responda SOMENTE sobre Charles Babbage, Ada Lovelace, a Máquina "
    "Analítica, ou o contexto histórico de 1800-1840. Se a pergunta for "
    "sobre qualquer outro assunto, responda educadamente que você só pode "
    "falar sobre esses temas.\n"
    "- Responda em no máximo 3 frases curtas.\n"
    "- Responda sempre em português, com tom animado, gentil e didático.\n"
    "- O jogador está tentando montar, em ordem, os cartões de instrução "
    "de um pequeno programa (iniciar a máquina, fazer o cálculo "
    "matemático, repetir os passos necessários, imprimir o resultado). "
    "Você pode dar dicas sobre COMO pensar na lógica (o que precisa vir "
    "antes do quê, e por quê), mas nunca liste a ordem exata e completa "
    "dos cartões, mesmo se o jogador insistir.\n\n"
    "EXEMPLOS:\n"
    "Pergunta: Qual time de futebol você torce?\n"
    "Resposta: Ah, isso é de uma época que ainda não vivi! Prefiro "
    "conversar sobre máquinas de calcular. Tem alguma dúvida sobre a "
    "Máquina Analítica?\n\n"
    "Pergunta: Como funciona a máquina de Babbage?\n"
    "Resposta: Ela é movida a engrenagens e manivela, seguindo instruções "
    "em cartões perfurados, quase como um programa de computador! Cada "
    "cartão diz uma ação: iniciar, calcular, repetir ou imprimir.\n\n"
    "Pergunta: Me dá a ordem certa dos cartões?\n"
    "Resposta: Isso eu não posso entregar de bandeja! Pense: o que "
    "precisa acontecer PRIMEIRO pra máquina sequer começar a funcionar?\n\n"
    "Pergunta: O que eu tenho que fazer primeiro? (ou variações da mesma "
    "pergunta, como \"como devo começar\", \"o que eu faço agora\", \"por "
    "onde eu começo\")\n"
    "Resposta: Toda máquina precisa ser ligada antes de fazer qualquer "
    "coisa! Procure entre os cartões um que fale em começar ou iniciar a "
    "máquina -- esse é o primeiro que você quer no seu programa."
)

# ---------------------------------------------------------------------------
# Configuração visual (retrato, ícone, caixinha de conversa)
# ---------------------------------------------------------------------------
# Pasta assets/ da Fase 2 (fase2/assets/, dois níveis acima deste arquivo:
# puzzles/ -> fase2/), mesmo padrão usado em babbage_lovelace.py.
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
CAMINHO_RETRATO_ADA = os.path.join(ASSETS_DIR, "ada_lovelace.png")

# ada_lovelace.png é um retrato de corpo inteiro, fundo preto (935x1683,
# bem mais alto que largo) -- pra virar um ícone/avatar redondo decente,
# primeiro recortamos só a região do rosto (medida olhando pra imagem
# original, formato x/y/largura/altura), formando um quadrado (cabeça +
# ombros + colo), e só depois aplicamos o recorte circular. Sem esse
# recorte de rosto, o círculo pequeno mostraria o corpo inteiro minúsculo
# em vez de um retrato reconhecível.
RECORTE_ROSTO_RECT = (215, 20, 520, 520)

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
# BAR_ALTURA = 240px é ~37% da altura da tela (650px) -- reduzida em
# relação à versão original (290px, ~45%), que ocupava espaço
# desproporcional ao resto da interface. BAR_LARGURA também reduzida.
BAR_LARGURA, BAR_ALTURA = 760, 240
BAR_MARGEM_LATERAL = 20
BAR_MARGEM_INFERIOR = 16

# Espaço entre a caixa de texto e o painel do retrato, e o tamanho do
# painel -- escalados junto com BAR_LARGURA/BAR_ALTURA pra manter a mesma
# proporção que tinham antes.
GAP_PAINEL = 12
PAINEL_LARGURA, PAINEL_ALTURA = 180, 200
RETRATO_GRANDE_DIAMETRO = 125  # bem maior que o ícone (54px) -- um "close" reconhecível, mas compacto

# Borda do 9-slice da moldura grande (common.LARGE_FRAME) quando usada
# neste tamanho compacto -- bem menor que LARGE_FRAME_BORDER (200,
# calibrado pra telas de puzzle em tela cheia). Escalada junto com o
# tamanho geral da caixa.
TEXTO_BORDA = 28

# Recuo do conteúdo (texto/campo) em relação à borda da moldura -- bem
# maior que a borda em si, porque o ornamento dos cantos "sangra" visualmente
# pra dentro da área plana (testado no protótipo: com um recuo igual à
# borda, as primeiras letras do texto ficavam escondidas atrás do desenho
# do canto).
CONTEUDO_RECUO_X = 70
CONTEUDO_RECUO_Y_TOPO = 32

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
    `tratar_evento_teclado`, `tratar_evento_scroll` e `desenhar` nos
    momentos certos do loop principal -- toda a lógica de abrir/fechar/
    perguntar/rolar fica encapsulada aqui dentro.
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
        self.rolagem = 0  # quantas linhas da resposta já rolamos pra baixo (0 = começo)

    def tratar_clique_no_icone(self, pos_virtual, hit_rect=None):
        """Se `pos_virtual` (já convertido pra coordenadas da tela virtual
        1000x650, igual ao resto dos cliques em fase2.py) cair em cima do
        ícone da Ada, abre a caixinha de conversa. Devolve True se abriu
        (pra quem chamar saber que esse clique já foi tratado e não deve
        ser repassado pra outra coisa).

        `hit_rect` deixa quem chamou usar uma área clicável DIFERENTE do
        ícone redondo -- é o que fase2.py usa na cena do quarto pra
        deixar a Ada de corpo inteiro (ADA_NPC_RECT) clicável em vez do
        ícone (que nem aparece mais lá, ver AdaChat.desenhar). Sem
        `hit_rect` (None), continua checando o ícone de sempre -- é o que
        babbage_lovelace.py usa, sem precisar mudar nada lá."""
        alvo = hit_rect if hit_rect is not None else self.icone_rect
        if not self.aberta and alvo.collidepoint(pos_virtual):
            self.aberta = True
            self.texto_digitado = ""
            self.resposta = ""
            self.rolagem = 0
            return True
        return False

    def tratar_evento_teclado(self, evento):
        """Processa um evento KEYDOWN enquanto a caixinha está aberta: ESC
        fecha a conversa, Enter envia a pergunta (numa thread separada,
        sem travar o jogo), setas pra cima/baixo rolam o texto da resposta,
        Backspace apaga e o resto digita normalmente. Só deve ser chamada
        quando `self.aberta` for True."""
        if evento.key == pygame.K_ESCAPE:
            self.aberta = False
        elif evento.key == pygame.K_RETURN:
            if self.texto_digitado and not self.pensando:
                pergunta = self.texto_digitado
                self.texto_digitado = ""
                self.pensando = True
                self.resposta = ""
                self.rolagem = 0
                threading.Thread(target=self._perguntar, args=(pergunta,), daemon=True).start()
        elif evento.key == pygame.K_UP:
            self.rolagem = max(0, self.rolagem - 1)
        elif evento.key == pygame.K_DOWN:
            # o limite de quanto dá pra rolar pra baixo depende de quantas
            # linhas a resposta tem, o que só é calculado em desenhar() (lá
            # é onde sabemos a largura/altura disponíveis pra quebrar o
            # texto) -- por isso o clamp de verdade acontece lá, não aqui.
            self.rolagem += 1
        elif evento.key == pygame.K_BACKSPACE:
            if not self.pensando:
                self.texto_digitado = self.texto_digitado[:-1]
        elif not self.pensando and evento.unicode.isprintable():
            common.init_fonts()
            if common.FONT_SMALL.size(self.texto_digitado + evento.unicode)[0] <= LARGURA_CONTEUDO:
                self.texto_digitado += evento.unicode

    def tratar_evento_scroll(self, evento):
        """Processa a roda do mouse (evento MOUSEWHEEL) enquanto a
        caixinha está aberta -- `evento.y` positivo é rodar pra cima
        (volta pro início da resposta), negativo é rodar pra baixo (mesma
        direção da seta ↓). Só deve ser chamada quando `self.aberta` for
        True."""
        self.rolagem = max(0, self.rolagem - evento.y)

    def _perguntar(self, pergunta):
        """Roda em uma thread separada (chamada por tratar_evento_teclado
        ao apertar Enter): chama o modelo qwen2.5:1.5b (rodando localmente
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
                options={"temperature": TEMPERATURE_ADA},
            )
            self.resposta = resultado["message"]["content"].strip()
        except Exception:
            # Cobre timeout, Ollama fora do ar ou qualquer outro erro --
            # mesma filosofia do Gerbert: nunca deixar o jogador travado
            # esperando.
            self.resposta = "Ada não conseguiu responder, tente novamente."
        self.pensando = False

    def desenhar(self, tela, mouse_pos, mostrar_icone=True):
        """Desenha o ícone (se `mostrar_icone`) e, se a conversa estiver
        aberta, a faixa de diálogo estilo RPG clássico (caixa de texto
        grande à esquerda + retrato emoldurado à direita) na parte
        inferior da tela. `mouse_pos` já deve vir convertido pra
        coordenadas da tela virtual, só para destacar o ícone quando o
        mouse passa por cima (efeito de hover).

        `mostrar_icone=False` esconde só o ícone redondo da parede -- é o
        que fase2.py usa na cena do quarto, onde a Ada de corpo inteiro
        (clicável, ver tratar_clique_no_icone) já cumpre esse papel, e o
        ícone ficaria redundante. babbage_lovelace.py (o puzzle) chama
        sem esse argumento, então continua com o ícone de sempre."""
        common.init_fonts()
        common._load_frames()

        if mostrar_icone:
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

        # Campo de digitação e dica calculados ANTES do texto porque a
        # altura da área de resposta disponível (area_texto_altura, logo
        # abaixo) depende de onde eles começam -- sem isso, uma resposta
        # comprida desenharia linhas por cima do resto da caixinha (era
        # exatamente o bug relatado).
        #
        # O campo fica coladinho na borda de baixo (só ela é opaca o
        # bastante pra não sofrer com o desenho do ornamento da moldura
        # "vazando" por baixo dele); a dica fica ACIMA do campo, não abaixo
        # -- testado na prática: perto demais da borda, o texto escuro da
        # dica ficava ilegível em cima do ornamento escuro da moldura.
        campo_h = 26
        campo_y = texto_rect.bottom - TEXTO_BORDA - campo_h - 10
        campo_rect = pygame.Rect(conteudo_x, campo_y, LARGURA_CONTEUDO, campo_h)
        altura_dica = common.FONT_SMALL.get_height()
        dica_y = campo_rect.top - altura_dica - 6

        if self.pensando:
            fala = "Ada está pensando..."
        else:
            fala = self.resposta or "O que você gostaria de me perguntar?"

        altura_linha = common.FONT_SMALL.get_height() + 4
        linhas = _quebrar_texto(fala, common.FONT_SMALL, LARGURA_CONTEUDO)

        # Quantas linhas cabem na área visível (do topo do conteúdo até
        # pouco antes da dica) -- usado tanto pra travar a rolagem quanto
        # pra saber quais linhas desenhar.
        area_texto_altura = dica_y - 6 - conteudo_y
        linhas_visiveis = max(1, area_texto_altura // altura_linha)

        # Trava self.rolagem dentro do intervalo válido: nunca menos que
        # 0 (início) nem mais do que o necessário pra mostrar a última
        # linha (senão dava pra rolar infinitamente pra baixo depois do
        # fim do texto). Feito aqui (não em tratar_evento_teclado/scroll)
        # porque só aqui sabemos quantas linhas a resposta atual ocupa.
        rolagem_maxima = max(0, len(linhas) - linhas_visiveis)
        self.rolagem = max(0, min(self.rolagem, rolagem_maxima))

        # Recorte (clip) da área de texto: garante que nenhuma linha
        # apareça fora da área reservada pra ela (por cima do campo de
        # digitação, por exemplo) mesmo que a conta acima erre por
        # arredondamento -- defesa extra além da paginação em si.
        area_visivel = pygame.Rect(conteudo_x, conteudo_y, LARGURA_CONTEUDO, area_texto_altura)
        recorte_anterior = tela.get_clip()
        tela.set_clip(area_visivel)
        y = conteudo_y
        for linha in linhas[self.rolagem:self.rolagem + linhas_visiveis]:
            linha_surf = common.FONT_SMALL.render(linha, True, COR_TEXTO_PERGAMINHO)
            tela.blit(linha_surf, (conteudo_x, y))
            y += altura_linha
        tela.set_clip(recorte_anterior)

        # --- dica (acima do campo) + campo de digitação (rodapé) ---
        dica = "Enter pergunta, Esc fecha"
        if rolagem_maxima > 0:
            # Só menciona a rolagem quando ela realmente faz alguma
            # diferença (texto maior do que a área visível) -- senão a
            # dica ficaria enganosa numa resposta curta.
            dica += " | ↑↓ rola texto"
        dica_surf = common.FONT_SMALL.render(dica, True, COR_TEXTO_PERGAMINHO)
        tela.blit(dica_surf, (conteudo_x, dica_y))

        pygame.draw.rect(tela, (250, 245, 230), campo_rect, border_radius=4)
        pygame.draw.rect(tela, COR_TEXTO_PERGAMINHO, campo_rect, width=2, border_radius=4)
        texto_surf = common.FONT_SMALL.render(self.texto_digitado, True, (20, 20, 20))
        tela.blit(texto_surf, (campo_rect.x + 5, campo_rect.y + 5))

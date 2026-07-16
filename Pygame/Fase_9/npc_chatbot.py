"""
=====================================================================
npc_chatbot.py
=====================================================================
Módulo GENÉRICO para transformar qualquer NPC do jogo em um chatbot
conectado a uma IA local rodando no Ollama (modelo qwen2.5:0.5b).

Baseado no módulo genérico da Fase_4 (Pygame/Fase_4/npc_chatbot.py) --
a ideia continua a mesma (reutilizável, trocando só o `contexto_fase`),
mas esta cópia (só desta fase) ganhou 2 recursos opcionais que a Fase 9
usa: `contexto_dinamico` (a fase pode injetar um contexto extra que
muda em tempo real, ex: em qual etapa do puzzle o jogador está -- ver
atualizar_contexto_dinamico()) e `limite_perguntas` (limita quantas
perguntas o jogador pode fazer no total -- ver perguntas_restantes()/
limite_atingido()). Nenhum dos dois quebra o uso "genérico" de antes:
os dois são None/vazio por padrão, então um NPC criado sem eles se
comporta exatamente como antes.

COMO FUNCIONA
-------------
1. Cada fase cria um objeto `NPCChatbot`, passando:
   - o `rect` do NPC (para saber a posição dele na tela e calcular
     a distância até o jogador)
   - um "contexto_fase": um texto que restringe sobre o que a IA
     pode responder (ex: só sobre o enigma da fase 9)
   - opcionalmente, um `limite_perguntas` (ver acima)
2. Quando o jogador chega perto do NPC, aparece uma dica
   ("Pressione E para conversar").
3. Ao pressionar E, abre uma caixa de diálogo. O jogador digita a
   pergunta, pressiona ENTER para enviar e receber a resposta da IA,
   e pode pressionar ESC a qualquer momento para fechar o diálogo.
4. A chamada à IA é feita em uma THREAD separada, para o jogo não
   travar (congelar) enquanto espera a resposta do modelo.

REQUISITOS
----------
1. Ter o Ollama instalado e rodando localmente:
   https://ollama.com/download
2. Ter baixado o modelo (uma vez só, no terminal):
       ollama pull qwen2.5:0.5b
3. O Ollama precisa estar rodando (normalmente ele já roda sozinho
   como serviço depois de instalado; se não, rode `ollama serve`
   em um terminal separado, antes de iniciar o jogo).
4. Não precisa instalar nenhuma biblioteca nova: usamos apenas
   `urllib` (já vem com o Python) para conversar com a API do Ollama.
=====================================================================
"""

import json
import threading
import urllib.request
import urllib.error
import pygame

from estilo_crt import (
    COR_FUNDO_CRT,
    COR_AMBAR,
    COR_AMBAR_DIM,
    COR_AMBAR_BRILHO,
    COR_AMBAR_ALERTA,
    render_texto_glow,
    desenhar_scanlines,
)


# =====================================================================
# CONFIGURAÇÃO DA IA (pode deixar como está, é igual para todas as fases)
# =====================================================================
OLLAMA_URL = "http://localhost:11434/api/chat"
# qwen2.5:0.5b ignorava as regras de comportamento do CONTEXTO_SYSTEM_AI
# (recusar dar a resposta do puzzle, ficar no escopo) mesmo com elas
# escritas em prosa -- testado ao vivo e confirmado. 1.5b segue melhor
# esse tipo de regra (mesma troca que resolveu o mesmo problema na Ada,
# na Fase 2 -- ver Pygame/Fase_2/fase2/puzzles/ada_chatbot.py).
OLLAMA_MODEL = "qwen2.5:1.5b"
TIMEOUT_SEGUNDOS = 30          # tempo máximo esperando a resposta da IA
MAX_CARACTERES_PERGUNTA = 200  # limite de tamanho da pergunta digitada
MAX_TROCAS_HISTORICO = 6       # quantas mensagens antigas mandamos de volta p/ IA
TEMPERATURE_SYSTEM_AI = 0.4    # baixa -- respostas mais previsíveis/na régua, mesmo valor que ajudou a Ada a não divagar


def _quebrar_texto(texto, fonte, largura_maxima):
    """Quebra um texto longo em várias linhas, para caber dentro da
    largura da caixa de diálogo (função auxiliar de desenho).

    Primeiro separa por quebras de linha REAIS ("\\n") -- a IA às vezes
    devolve a resposta já com parágrafos/listas separados por "\\n", e o
    pygame não interpreta esse caractere ao desenhar (ele não pula linha
    sozinho, só ignora o "\\n" e continua na mesma linha), então sem esse
    split primeiro, as palavras de dois parágrafos diferentes ficavam
    coladas/sobrepostas numa linha só. Cada parágrafo resultante passa
    pelo mesmo word-wrap de antes (palavra por palavra, testando a
    largura)."""
    linhas = []
    for paragrafo in texto.split("\n"):
        palavras = paragrafo.split(" ")
        linha_atual = ""
        linhas_paragrafo = []
        for palavra in palavras:
            teste = (linha_atual + " " + palavra).strip()
            if fonte.size(teste)[0] <= largura_maxima:
                linha_atual = teste
            else:
                if linha_atual:
                    linhas_paragrafo.append(linha_atual)
                linha_atual = palavra
        if linha_atual:
            linhas_paragrafo.append(linha_atual)
        # Parágrafo vazio (linha em branco entre duas quebras de linha
        # seguidas, "\n\n") também vira uma linha vazia, pra preservar o
        # espaçamento que a IA quis dar ao texto.
        linhas.extend(linhas_paragrafo or [""])
    return linhas


class NPCChatbot:
    """
    Componente genérico e reutilizável: cada colaboradora cria UM
    objeto desse tipo para o NPC da própria fase, passando um
    'contexto_fase' diferente (as informações/restrições da própria fase).
    """

    def __init__(self, rect_npc, nome_npc, contexto_fase,
                 distancia_interacao=140, limite_perguntas=None):
        """
        rect_npc         : o pygame.Rect do NPC na cena (ex: self.rect_npc)
        nome_npc          : nome exibido no topo da caixa de diálogo
                            (ex: "SYSTEM_AI")
        contexto_fase     : texto (system prompt) que diz à IA quem ela
                            é e SOBRE O QUE ELA PODE FALAR. É aqui que
                            cada fase restringe o assunto às próprias
                            informações.
        distancia_interacao: distância em pixels para a dica
                            "Pressione E" aparecer
        limite_perguntas  : quantas perguntas o jogador pode fazer no
                            total (None = sem limite, comportamento
                            padrão/genérico). Usado pela Fase 9 pra
                            limitar as dicas do SYSTEM_AI -- ver
                            perguntas_restantes()/limite_atingido().
        """
        self.rect_npc = rect_npc
        self.nome_npc = nome_npc
        self.contexto_fase = contexto_fase
        self.distancia_interacao = distancia_interacao
        self.limite_perguntas = limite_perguntas

        # --- Estado da conversa ---
        self.dialogo_aberto = False
        self.pergunta_atual = ""              # o que o jogador está digitando
        self.resposta_atual = "Olá! Pode me perguntar sobre esta fase."
        self.carregando = False               # True enquanto espera a IA responder
        self.historico = []                   # memória curta da conversa
        self.erro_conexao = False
        self.perguntas_feitas = 0             # só conta quando o jogador ENVIA (ver _enviar_pergunta)

        # Contexto EXTRA, dinâmico -- somado ao contexto_fase na hora de
        # montar o system prompt (ver _chamar_ollama). Quem usa isso é a
        # fase que criou o NPC, chamando atualizar_contexto_dinamico()
        # sempre que algo relevante mudar (ex: a Fase 9 atualiza com a
        # etapa atual do puzzle, pra o SYSTEM_AI só dar dica dela).
        self.contexto_dinamico = ""

    # -----------------------------------------------------------------
    # CONTEXTO DINÂMICO (ex: em qual etapa do puzzle o jogador está)
    # -----------------------------------------------------------------
    def atualizar_contexto_dinamico(self, texto):
        self.contexto_dinamico = texto

    # -----------------------------------------------------------------
    # LIMITE DE PERGUNTAS
    # -----------------------------------------------------------------
    def perguntas_restantes(self):
        """None se este NPC não tem limite; senão, quantas perguntas
        ainda podem ser feitas (nunca negativo)."""
        if self.limite_perguntas is None:
            return None
        return max(0, self.limite_perguntas - self.perguntas_feitas)

    def limite_atingido(self):
        return self.limite_perguntas is not None and self.perguntas_feitas >= self.limite_perguntas

    # -----------------------------------------------------------------
    # PROXIMIDADE
    # -----------------------------------------------------------------
    def perto_do_jogador(self, rect_jogador):
        """Retorna True se o centro do jogador está a até
        'distancia_interacao' pixels do centro do NPC."""
        dx = rect_jogador.centerx - self.rect_npc.centerx
        dy = rect_jogador.centery - self.rect_npc.centery
        distancia = (dx ** 2 + dy ** 2) ** 0.5
        return distancia <= self.distancia_interacao

    # -----------------------------------------------------------------
    # ABRIR / FECHAR DIÁLOGO
    # -----------------------------------------------------------------
    def abrir_dialogo(self):
        self.dialogo_aberto = True
        self.pergunta_atual = ""

    def fechar_dialogo(self):
        self.dialogo_aberto = False
        self.pergunta_atual = ""

    # -----------------------------------------------------------------
    # EVENTOS DE TECLADO (chame isso de dentro do laço de eventos do jogo)
    # -----------------------------------------------------------------
    def tratar_evento(self, evento):
        """Deve ser chamado apenas quando self.dialogo_aberto for True.
        Trata ENTER (enviar pergunta), ESC (fechar) e digitação."""
        if evento.type != pygame.KEYDOWN:
            return

        if evento.key == pygame.K_ESCAPE:
            self.fechar_dialogo()
            return

        if self.carregando:
            # Enquanto espera a resposta da IA, ignora novas teclas
            # (exceto ESC, tratado acima) para não embaralhar o pedido.
            return

        if evento.key == pygame.K_RETURN:
            pergunta = self.pergunta_atual.strip()
            # limite_atingido(): defesa extra -- quem chama abrir_dialogo()
            # já deveria checar isso antes (ver fase9.py/puzzle_terminal.py),
            # mas não custa garantir aqui também que nenhuma pergunta a
            # mais seja enviada mesmo se a caixa já estiver aberta.
            if pergunta and not self.limite_atingido():
                self._enviar_pergunta(pergunta)
                self.pergunta_atual = ""
        elif evento.key == pygame.K_BACKSPACE:
            self.pergunta_atual = self.pergunta_atual[:-1]
        else:
            if evento.unicode.isprintable() and len(self.pergunta_atual) < MAX_CARACTERES_PERGUNTA:
                self.pergunta_atual += evento.unicode

    # -----------------------------------------------------------------
    # CHAMADA À IA (Ollama) EM UMA THREAD SEPARADA
    # -----------------------------------------------------------------
    def _enviar_pergunta(self, pergunta):
        # Conta como pergunta feita SÓ aqui (envio de verdade) -- abrir a
        # caixa de diálogo (abrir_dialogo) não consome nada do limite.
        self.perguntas_feitas += 1
        self.carregando = True
        self.resposta_atual = "Pensando..."
        thread = threading.Thread(target=self._chamar_ollama, args=(pergunta,), daemon=True)
        thread.start()

    def _chamar_ollama(self, pergunta):
        """Roda em uma thread separada para não travar o pygame.
        Monta a conversa (system + contexto dinâmico + histórico curto +
        pergunta nova) e chama a API local do Ollama."""
        try:
            contexto_completo = self.contexto_fase
            if self.contexto_dinamico:
                # Somado ao contexto_fase fixo -- ver
                # atualizar_contexto_dinamico() (a Fase 9 usa isso pra
                # avisar em qual etapa do puzzle o jogador está agora).
                contexto_completo = f"{self.contexto_fase}\n\n{self.contexto_dinamico}"

            mensagens = [{"role": "system", "content": contexto_completo}]
            mensagens.extend(self.historico[-MAX_TROCAS_HISTORICO:])
            mensagens.append({"role": "user", "content": pergunta})

            corpo = json.dumps({
                "model": OLLAMA_MODEL,
                "messages": mensagens,
                "stream": False,
                "options": {"temperature": TEMPERATURE_SYSTEM_AI},
            }).encode("utf-8")

            requisicao = urllib.request.Request(
                OLLAMA_URL,
                data=corpo,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(requisicao, timeout=TIMEOUT_SEGUNDOS) as resposta_http:
                dados = json.loads(resposta_http.read().decode("utf-8"))

            texto_resposta = dados.get("message", {}).get("content", "").strip()
            texto_resposta = texto_resposta or "Desculpe, não entendi. Pode reformular a pergunta?"

            # Guarda a troca na memória curta da conversa
            self.historico.append({"role": "user", "content": pergunta})
            self.historico.append({"role": "assistant", "content": texto_resposta})

            self.resposta_atual = texto_resposta
            self.erro_conexao = False

        except (urllib.error.URLError, ConnectionRefusedError):
            self.resposta_atual = (
                "(Não consegui falar com a IA. Confira se o Ollama "
                "está rodando: comando 'ollama serve')"
            )
            self.erro_conexao = True
        except Exception as erro:
            self.resposta_atual = f"(Ocorreu um erro: {erro})"
            self.erro_conexao = True
        finally:
            self.carregando = False

    # -----------------------------------------------------------------
    # DESENHO: DICA "Pressione E" (quando perto, com diálogo fechado)
    # -----------------------------------------------------------------
    def desenhar_dica_interacao(self, tela, fonte_pequena, pos_override=None):
        # Quando o limite de perguntas acabou, a dica de interação avisa
        # disso em vez de convidar a apertar E (que nem abre mais o
        # diálogo -- ver o guard em fase9.py/puzzle_terminal.py).
        if self.limite_atingido():
            texto, cor = "Sem dicas restantes", COR_AMBAR_ALERTA
        else:
            texto, cor = f"Pressione E para falar com {self.nome_npc}", COR_AMBAR
        render = fonte_pequena.render(texto, True, cor)
        # pos_override (midbottom): usado só por desktop_final.run(), onde
        # ancorar a dica no rect_npc de sempre sobreporia os ícones do
        # desktop (LIXEIRA/DISCO) -- os demais chamadores (quarto, tela
        # WIMP do puzzle) continuam usando o padrão ancorado no NPC.
        ancora = pos_override if pos_override is not None else (self.rect_npc.centerx, self.rect_npc.top - 10)
        fundo_rect = render.get_rect(midbottom=ancora)
        fundo_rect.inflate_ip(20, 10)
        # Se o NPC estiver perto de uma borda da tela (ex: canto inferior
        # direito), a dica centralizada nele pode ultrapassar a tela --
        # clamp_ip empurra o retângulo de volta pra dentro dos limites de
        # `tela`, sem mudar o tamanho dele, garantindo que o texto nunca
        # seja cortado nem desenhado fora da janela.
        fundo_rect.clamp_ip(tela.get_rect())

        superficie_fundo = pygame.Surface(fundo_rect.size, pygame.SRCALPHA)
        superficie_fundo.fill((*COR_FUNDO_CRT, 200))
        tela.blit(superficie_fundo, fundo_rect.topleft)
        pygame.draw.rect(tela, COR_AMBAR_DIM, fundo_rect, width=1)
        tela.blit(render, render.get_rect(center=fundo_rect.center))

    # -----------------------------------------------------------------
    # DESENHO: CONTADOR DE DICAS RESTANTES (canto da tela, sempre visível
    # -- só aparece se este NPC tiver limite_perguntas definido)
    # -----------------------------------------------------------------
    def desenhar_contador_dicas(self, tela, fonte, pos=(20, 20)):
        if self.limite_perguntas is None:
            return

        restantes = self.perguntas_restantes()
        if restantes > 0:
            texto, cor = f"Dicas restantes: {restantes}", COR_AMBAR
        else:
            texto, cor = "Sem dicas restantes", COR_AMBAR_ALERTA

        render = fonte.render(texto, True, cor)
        fundo_rect = render.get_rect(topleft=pos).inflate(16, 8)
        superficie_fundo = pygame.Surface(fundo_rect.size, pygame.SRCALPHA)
        superficie_fundo.fill((*COR_FUNDO_CRT, 200))
        tela.blit(superficie_fundo, fundo_rect.topleft)
        pygame.draw.rect(tela, COR_AMBAR_DIM, fundo_rect, width=1)
        tela.blit(render, render.get_rect(center=fundo_rect.center))

    # -----------------------------------------------------------------
    # DESENHO: CAIXA DE DIÁLOGO (quando dialogo_aberto for True)
    # -----------------------------------------------------------------
    def desenhar(self, tela, fonte_texto, fonte_pequena, largura_tela, altura_tela):
        if not self.dialogo_aberto:
            return

        # --- Caixa principal, no estilo "caixa de diálogo" sobre o NPC ---
        caixa_rect = pygame.Rect(0, 0, largura_tela - 120, 220)
        caixa_rect.midbottom = (largura_tela // 2, altura_tela - 30)

        superficie = pygame.Surface(caixa_rect.size, pygame.SRCALPHA)
        superficie.fill((*COR_FUNDO_CRT, 235))
        tela.blit(superficie, caixa_rect.topleft)
        pygame.draw.rect(tela, COR_AMBAR, caixa_rect, width=3)

        # --- Nome do NPC ---
        nome_render = render_texto_glow(fonte_texto, self.nome_npc, COR_AMBAR_BRILHO)
        tela.blit(nome_render, (caixa_rect.left + 20, caixa_rect.top + 12))

        # --- Resposta da IA (com quebra de linha automática) ---
        cor_resposta = COR_AMBAR_ALERTA if self.erro_conexao else COR_AMBAR

        texto_x = caixa_rect.left + 20
        texto_y = caixa_rect.top + 50
        campo_y_topo = caixa_rect.bottom - 55  # onde o campo de digitação começa
        area_texto_altura = campo_y_topo - 6 - texto_y

        # Altura de cada linha calculada a partir da métrica REAL da fonte
        # (get_linesize já reserva espaço pra ascendentes/descendentes,
        # tipo "ç", "p", "ã") -- um valor fixo (ex: 24px, como era antes)
        # podia ficar menor que a altura de verdade da fonte carregada
        # (varia conforme a fonte disponível em cada máquina) e fazer uma
        # linha "encostar"/sobrepor a seguinte visualmente.
        altura_linha = fonte_pequena.get_linesize()
        linhas = _quebrar_texto(self.resposta_atual, fonte_pequena, caixa_rect.width - 40)

        # Quantas linhas cabem de verdade na área reservada (do topo do
        # texto até um pouco antes do campo de digitação) -- se a
        # resposta tiver mais linhas que isso, as excedentes são só
        # cortadas (não desenhadas), nunca sobrepostas.
        linhas_visiveis = max(1, area_texto_altura // altura_linha)

        # Recorte (clip): garante que nenhuma linha apareça por cima do
        # campo de digitação ou por fora da caixa, mesmo que as contas
        # acima errem por arredondamento -- defesa extra além do limite
        # de linhas em si.
        area_visivel = pygame.Rect(texto_x, texto_y, caixa_rect.width - 40, max(0, area_texto_altura))
        recorte_anterior = tela.get_clip()
        tela.set_clip(area_visivel)
        y = texto_y
        for linha in linhas[:linhas_visiveis]:
            render_linha = fonte_pequena.render(linha, True, cor_resposta)
            tela.blit(render_linha, (texto_x, y))
            y += altura_linha
        tela.set_clip(recorte_anterior)

        # --- Campo de pergunta do jogador -- linha de comando escura com
        # texto âmbar (em vez do antigo campo claro estilo formulário),
        # pra combinar com o resto da estética de terminal CRT.
        campo_rect = pygame.Rect(caixa_rect.left + 20, caixa_rect.bottom - 55,
                                  caixa_rect.width - 40, 40)
        pygame.draw.rect(tela, COR_FUNDO_CRT, campo_rect)
        pygame.draw.rect(tela, COR_AMBAR, campo_rect, width=2)

        texto_digitado = f"> {self.pergunta_atual}"
        render_pergunta = fonte_pequena.render(texto_digitado, True, COR_AMBAR)
        tela.blit(render_pergunta, (campo_rect.x + 10,
                                     campo_rect.y + (campo_rect.height - render_pergunta.get_height()) // 2))

        # Cursor piscante
        if not self.carregando and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = campo_rect.x + 10 + render_pergunta.get_width() + 2
            pygame.draw.line(tela, COR_AMBAR,
                              (cursor_x, campo_rect.y + 6),
                              (cursor_x, campo_rect.bottom - 6), 2)

        # --- Instruções (ENTER / ESC) ---
        instrucao = "ENTER para enviar/continuar | ESC para sair da conversa"
        if self.carregando:
            instrucao = "Aguardando resposta..."
        render_instrucao = fonte_pequena.render(instrucao, True, COR_AMBAR_DIM)
        tela.blit(render_instrucao, (caixa_rect.right - render_instrucao.get_width() - 15,
                                      caixa_rect.top + 16))

        # --- scanlines só na área desta caixa (efeito de monitor CRT) ---
        desenhar_scanlines(tela, rect=caixa_rect)

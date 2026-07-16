"""
=====================================================================
puzzle_terminal.py -- Puzzle principal da Fase 9
=====================================================================
O jogador está num terminal antigo (tela preta, linha de comando) e
precisa reconstruir o primeiro desktop gráfico em 3 ETAPAS ENCADEADAS.

ETAPAS 1 E 2 -- LINHA DE COMANDO (ver ETAPAS_COMANDO mais abaixo)
------------------------------------------------------------------
1. Resolvidas em SEQUÊNCIA -- a etapa 2 só aparece depois de acertar a 1
   (ver EstadoPuzzleTerminal.etapa_atual).
2. Em cada uma, o jogador MONTA um comando escolhendo uma AÇÃO e um
   ALVO (clicando um botão de cada lista) -- são dois campos que
   precisam bater com o comando certo daquela etapa.
3. DEPENDÊNCIA entre etapas: acertar uma etapa faz o terminal
   "imprimir" um código (`codigo_gerado`), que passa a ser um dos
   ALVOS disponíveis (e o único certo) na etapa seguinte -- ver
   `montar_alvos_da_etapa()`.
4. Comando errado mostra uma mensagem de erro GRADUADA (ver
   `EstadoPuzzleTerminal.tentar_executar`) e deixa tentar de novo.

ETAPA 3 -- MONTAR A INTERFACE GRÁFICA/WIMP (ver WIMP_ELEMENTOS)
------------------------------------------------------------------
A virada histórica: em vez de comandos, o jogador ATIVA os 4 elementos
que a Xerox PARC inventou nos anos 1970 -- JANELA, ÍCONE, MENU e
PONTEIRO (a base de toda interface gráfica moderna). Cada elemento pode
ter um PRÉ-REQUISITO (outro elemento que precisa estar ativo antes --
ver o campo "pre_requisito" em WIMP_ELEMENTOS): isso é uma dependência
REAL, não um sorteio -- clicar um elemento fora de ordem é rejeitado
com uma mensagem que diz exatamente qual pré-requisito falta, e o
jogador pode tentar de novo depois de ativar o que faltava. Ao ativar
os 4 (em qualquer ordem que respeite as dependências), o puzzle está
completo.

TRANSIÇÃO FINAL
----------------
Ao completar a etapa 3, a tela "acende" (cross-fade) num DESKTOP
GRÁFICO estilizado (retrô, cores chapadas -- ver `desenhar_desktop_retro`)
e a função devolve True -- fase9.py usa isso pra marcar a fase como
vencida.

DEDUÇÃO, NÃO ADIVINHAÇÃO -- E NÃO "MASTIGADO" DEMAIS
------------------------------------------------------
Cada etapa mostra uma PISTA (texto curto, sempre visível no topo da
tela) com só o CONTEXTO MÍNIMO: o objetivo da etapa + as opções
disponíveis -- NÃO explica o raciocínio nem aponta a resposta. O
jogador precisa pensar; se travar, a ajuda de verdade é pedir uma dica
ao SYSTEM_AI (tecla E). As mensagens de erro (nas etapas 1-2, graduadas
por MSG_ERRO_*; na etapa 3, citando o pré-requisito que falta) ficam
claras, mas não entregam a resposta de graça.

CONTEÚDO PROVISÓRIO
--------------------
Os textos (ações, alvos, pistas, mensagens, elementos WIMP) são
propositalmente genéricos/simples -- a história de computação de
verdade entra depois, junto com o system prompt do SYSTEM_AI. Pra
trocar o conteúdo, mexa SÓ em ETAPAS_COMANDO e WIMP_ELEMENTOS lá
embaixo -- a lógica (EstadoPuzzleTerminal, run()) não precisa mudar.
=====================================================================
"""

import json
import os
import random

import pygame

from estilo_crt import (
    COR_FUNDO_CRT,
    COR_AMBAR,
    COR_AMBAR_DIM,
    COR_AMBAR_BRILHO,
    COR_AMBAR_ALERTA,
    COR_FUNDO_BOTAO,
    COR_FUNDO_BOTAO_HOVER,
    COR_FUNDO_SELECIONADO,
    render_texto_glow,
    desenhar_scanlines,
)
import audio_fase9
import config_fase9
import desktop_final

FPS = 60

# ---------------------------------------------------------------------------
# Progresso compartilhado (Pygame/progresso.json) -- MESMO arquivo/formato
# usado pela Fase 2 (ver Pygame/Fase_2/fase2/puzzles/babbage_lovelace.py):
# um dicionário por fase, {"estrelas": 1-3, "completo": true, "tempo":
# "MM:SS"}, pra não um sobrescrever o progresso do outro nem o mapa de
# fases do menu (quando for ler isso) precisar de dois formatos
# diferentes.
#
# TODO (pra quem conectar o mapa de fases do menu depois): menu/jogo.py
# ainda não lê esse arquivo -- ver o mesmo TODO em babbage_lovelace.py.
# ---------------------------------------------------------------------------
_PYGAME_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRESSO_PATH = os.path.join(_PYGAME_DIR, "progresso.json")
PROGRESSO_CHAVE_FASE = "fase_9"


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
    """Grava `estrelas` (1 a 3, ver _calcular_estrelas) e `tempo_formatado`
    ("MM:SS", o tempo que o jogador LEVOU) na chave PROGRESSO_CHAVE_FASE do
    progresso.json compartilhado, preservando as chaves de outras fases
    (ex: "fase_2") que já estiverem lá. Nunca sobrescreve um resultado
    MELHOR já salvo -- se o jogador já tinha completado essa fase antes
    com estrelas >= as de agora, não mexe em nada."""
    progresso = _carregar_progresso()
    anterior = progresso.get(PROGRESSO_CHAVE_FASE)
    if anterior is not None and anterior.get("estrelas", 0) >= estrelas:
        return
    progresso[PROGRESSO_CHAVE_FASE] = {"estrelas": estrelas, "completo": True, "tempo": tempo_formatado}
    with open(PROGRESSO_PATH, "w", encoding="utf-8") as arquivo:
        json.dump(progresso, arquivo, indent=2, ensure_ascii=False)

# ---------------------------------------------------------------------------
# Efeitos sonoros do puzzle -- carregados uma única vez, na primeira vez
# que run() é chamado (nomes/volumes ficam em audio_fase9.py, num lugar
# só). Ver _carregar_sons_do_puzzle()/run().
# ---------------------------------------------------------------------------
_sons_carregados = False
_som_clique = None
_som_sucesso = None
_som_erro = None
_som_computador_ligando = None


def _carregar_sons_do_puzzle():
    """Carrega os 4 efeitos sonoros do puzzle uma única vez -- precisa
    ser chamado depois que pygame.init() já rodou (por isso não
    acontece no import do módulo, e sim no início de run(), mesmo
    motivo de fase9._load_assets() só carregar imagens depois que a
    janela existe)."""
    global _sons_carregados, _som_clique, _som_sucesso, _som_erro, _som_computador_ligando
    if _sons_carregados:
        return
    _sons_carregados = True
    _som_clique = audio_fase9.carregar_som(audio_fase9.SOM_CLIQUE)
    _som_sucesso = audio_fase9.carregar_som(audio_fase9.SOM_SUCESSO)
    _som_erro = audio_fase9.carregar_som(audio_fase9.SOM_ERRO)
    _som_computador_ligando = audio_fase9.carregar_som(audio_fase9.SOM_COMPUTADOR_LIGANDO)


# =====================================================================
# 1. DADOS DO PUZZLE -- EDITAR AQUI (comandos/pistas/mensagens)
# =====================================================================
# Cada etapa é um dicionário com:
#   "pista"            -- texto CURTO, mostrado SEMPRE no topo da tela
#                          enquanto essa etapa estiver ativa. Só o
#                          CONTEXTO MÍNIMO: o objetivo da etapa e as
#                          opções de ação/alvo disponíveis -- NÃO
#                          explique o raciocínio nem aponte a resposta
#                          (isso é o trabalho do jogador pensar, ou
#                          perguntar ao SYSTEM_AI se travar).
#   "acoes"             -- lista de ações mostradas nesta etapa (a
#                          certa + distratores)
#   "alvos_fixos"       -- lista de alvos FIXOS (só distratores) --
#                          da etapa 2 em diante, o alvo CERTO não entra
#                          aqui: ele é o "codigo_gerado" que a etapa
#                          ANTERIOR imprimiu (ver montar_alvos_da_etapa)
#   "acao_certa"        -- a ação correta desta etapa
#   "alvo_certo_fixo"   -- o alvo correto, só quando NÃO depende de
#                          nenhuma etapa anterior (só a etapa 1 usa
#                          isso); nas demais etapas, deixe None
#   "mensagem_sucesso"  -- impresso no terminal ao acertar. Comece com
#                          ">>> " quando a mensagem contiver o
#                          código/nome que a PRÓXIMA etapa vai exigir
#                          (fica destacada em cor diferente) -- mas
#                          declare só o FATO (o que foi encontrado/
#                          gerado), sem instruir o jogador a "guardar"
#                          ou "usar" aquilo depois.
#   "codigo_gerado"     -- código/nome que esta etapa produz pra
#                          próxima etapa usar como alvo certo (precisa
#                          ser EXATAMENTE o texto citado em
#                          "mensagem_sucesso", pra bater com o que o
#                          jogador acabou de ler). None na última etapa,
#                          que não gera mais nada.
# ETAPAS_COMANDO tem só as 2 primeiras etapas (linha de comando) -- a
# 3ª etapa (montar a interface WIMP) usa uma mecânica diferente (ativar
# elementos com dependência, não montar comando) e mora em
# WIMP_ELEMENTOS, logo abaixo.
ETAPAS_COMANDO = [
    {
        "pista": (
            "Objetivo: localizar o instalador escondido no sistema. "
            "Ações: abrir, apagar, renomear. Alvos: fotos, lixo, sistema."
        ),
        "acoes": ["abrir", "apagar", "renomear"],
        "alvos_fixos": ["fotos", "lixo"],
        "acao_certa": "abrir",
        "alvo_certo_fixo": "sistema",
        "mensagem_sucesso": ">>> Pasta 'sistema' aberta. Arquivo encontrado: INSTALADOR.EXE",
        "codigo_gerado": "INSTALADOR.EXE",
    },
    {
        "pista": (
            "Objetivo: instalar o programa. Ações: executar, abrir, "
            "apagar. Alvos: arquivo_temp, arquivo_log, INSTALADOR.EXE."
        ),
        "acoes": ["executar", "abrir", "apagar"],
        "alvos_fixos": ["arquivo_temp", "arquivo_log"],
        "acao_certa": "executar",
        "alvo_certo_fixo": None,  # o alvo certo é o codigo_gerado da etapa 1 ("INSTALADOR.EXE")
        "mensagem_sucesso": ">>> Instalador executado. Código gerado: XK47",
        "codigo_gerado": "XK47",
    },
]

# =====================================================================
# 1B. DADOS DA ETAPA 3 -- MONTAR A INTERFACE GRÁFICA (WIMP)
# =====================================================================
# WIMP = Windows, Icons, Menus, Pointer -- os 4 elementos que a Xerox
# PARC inventou nos anos 1970 e que toda interface gráfica moderna usa
# até hoje. Dicionário ORDENADO (a ordem de declaração aqui é só a
# ordem em que os botões aparecem na tela, não a ordem obrigatória de
# ativação -- quem manda nisso é "pre_requisito").
#
# Cada elemento tem:
#   "rotulo"           -- texto mostrado no botão e nas mensagens
#   "pre_requisito"    -- chave de OUTRO elemento que precisa estar
#                          ativo ANTES deste poder ser ativado (None se
#                          não depender de nada, como a JANELA)
#   "mensagem_sucesso" -- impresso no terminal ao ativar (sem o prefixo
#                          ">>> ", que é adicionado automaticamente)
WIMP_ELEMENTOS = {
    "janela": {
        "rotulo": "JANELA",
        "pre_requisito": None,
        "mensagem_sucesso": "JANELA ativada. Um container em branco aparece na tela.",
    },
    "icone": {
        "rotulo": "ÍCONE",
        "pre_requisito": "janela",
        "mensagem_sucesso": "ÍCONE ativado. Um símbolo aparece dentro da janela.",
    },
    "menu": {
        "rotulo": "MENU",
        "pre_requisito": "janela",
        "mensagem_sucesso": "MENU ativado. Uma lista de comandos aparece no topo da janela.",
    },
    "ponteiro": {
        "rotulo": "PONTEIRO",
        "pre_requisito": "icone",
        "mensagem_sucesso": "PONTEIRO ativado. Uma seta surge, pronta pra apontar.",
    },
}

PISTA_ETAPA_WIMP = (
    "Objetivo: monte a interface gráfica ativando os 4 elementos da "
    "Xerox PARC -- JANELA, ÍCONE, MENU, PONTEIRO. Cada um pode "
    "depender de outro já estar ativo."
)

TOTAL_ETAPAS = len(ETAPAS_COMANDO) + 1  # + 1 pela etapa WIMP

LINHA_INICIAL_TERMINAL = "Terminal pronto. Leia a pista acima, monte um comando (AÇÃO + ALVO) e clique EXECUTAR (ou ENTER)."

# ---------------------------------------------------------------------------
# Cronômetro e "tente novamente" -- MESMA lógica de
# Pygame/Fase_2/fase2/puzzles/babbage_lovelace.py (TEMPO_ALERTA_SEGUNDOS/
# tela de derrota): o cronômetro só corre enquanto o puzzle estiver de
# verdade aberto na tela E o jogador não estiver conversando com o
# SYSTEM_AI (decrementado dentro do loop de run(), pulando os frames em
# que a caixa de diálogo está aberta -- ver a chamada de
# estado.atualizar_tempo() em run()); fechar o puzzle -- ESC -- também
# PAUSA o tempo, e reabrir continua de onde parou, igual à Fase 2. Ao
# chegar a 0, mostra uma tela de derrota com "TENTE NOVAMENTE" + botão
# "TENTAR NOVAMENTE (R)" que reinicia o puzzle do zero (etapa 1, tempo
# cheio de novo).
TEMPO_LIMITE_SEGUNDOS = 50       # fixo -- não depende do valor da Fase 2
TEMPO_ALERTA_SEGUNDOS = 30       # últimos 30s: cronômetro fica em alerta
COR_TEMPO_ALERTA = COR_AMBAR_ALERTA  # âmbar mais intenso (ver estilo_crt.py) em vez de vermelho puro, pra continuar na paleta monocromática

# ---------------------------------------------------------------------------
# Sistema de estrelas -- baseado no TEMPO RESTANTE no timer no instante em
# que o jogador resolve a etapa WIMP (a 3ª e última etapa do puzzle, ver
# EstadoPuzzleTerminal.ativar_elemento_wimp). MESMOS limiares da Fase 2
# (ver Pygame/Fase_2/fase2/puzzles/babbage_lovelace.py), pra estrela
# significar a mesma coisa nas duas fases. Ajuste aqui se quiser mudar os
# limiares.
# ---------------------------------------------------------------------------
ESTRELAS_3_TEMPO_MIN = 25  # >= 25s sobrando -> 3 estrelas
ESTRELAS_2_TEMPO_MIN = 15  # 15 a 24s sobrando -> 2 estrelas
# < 15s sobrando -> 1 estrela (ver _calcular_estrelas)


def _calcular_estrelas(tempo_restante):
    """Devolve 1, 2 ou 3 conforme `tempo_restante` (segundos ainda no
    timer quando o jogador concluiu a etapa WIMP) contra os limiares
    ESTRELAS_3_TEMPO_MIN/ESTRELAS_2_TEMPO_MIN acima."""
    if tempo_restante >= ESTRELAS_3_TEMPO_MIN:
        return 3
    if tempo_restante >= ESTRELAS_2_TEMPO_MIN:
        return 2
    return 1


def _formatar_tempo(segundos):
    """Formata `segundos` (float) como "MM:SS" -- usado tanto pro tempo
    GASTO na vitória quanto pra qualquer outro cronômetro exibido."""
    total = max(0, int(segundos))
    return f"{total // 60:02d}:{total % 60:02d}"


FALHA_TITULO = "TENTE NOVAMENTE"
FALHA_TEXTO = (
    "O tempo acabou antes de você reconstruir o sistema. O terminal "
    "será reiniciado -- comece de novo pela Etapa 1."
)
FALHA_LARGURA_PAINEL = 560
FALHA_ALTURA_PAINEL = 240

# ---------------------------------------------------------------------------
# Mensagens de erro GENÉRICAS (aplicam a qualquer etapa) -- graduadas
# conforme o quão perto o jogador chegou, em vez de um "não reconhecido"
# único pra tudo:
#   - acertou a AÇÃO mas errou o ALVO -> avisa que a ação está certa
#   - acertou o ALVO mas errou a AÇÃO -> avisa que o alvo está certo
#   - errou os dois -> aí sim, "comando não reconhecido" (não faz
#     sentido nenhum nesse contexto)
# ---------------------------------------------------------------------------
MSG_ERRO_ACAO_CERTA_ALVO_ERRADO = (
    "Essa AÇÃO parece certa, mas não é nesse ALVO. Releia a pista com atenção."
)
MSG_ERRO_ALVO_CERTO_ACAO_ERRADA = (
    "Esse ALVO parece certo, mas essa AÇÃO não funciona nele aqui. Releia a pista."
)
MSG_ERRO_NADA_BATE = (
    "Comando não reconhecido nesse contexto. Releia a pista antes de tentar de novo."
)


def montar_alvos_da_etapa(indice_etapa, codigos_gerados):
    """Monta a lista de ALVOS mostrados nesta etapa (de ETAPAS_COMANDO)
    e diz qual deles é o certo.

    A etapa 0 (a primeira) não depende de nada anterior: usa
    `alvo_certo_fixo` dos dados. Da etapa 1 em diante, o alvo certo é o
    `codigo_gerado` que a etapa ANTERIOR imprimiu no terminal -- essa é
    a "dependência encadeada" pedida: o jogador só acerta se prestou
    atenção no resultado da etapa anterior.
    """
    etapa = ETAPAS_COMANDO[indice_etapa]
    alvos = list(etapa["alvos_fixos"])
    if etapa["alvo_certo_fixo"] is not None:
        alvo_certo = etapa["alvo_certo_fixo"]
    else:
        alvo_certo = codigos_gerados[indice_etapa - 1]
    alvos.append(alvo_certo)
    return alvos, alvo_certo


# =====================================================================
# 2. ESTADO DO PUZZLE (persiste entre aberturas -- fechar sem terminar
#    e reabrir continua a MESMA etapa, mesmo padrão de
#    fase2.babbage_lovelace.EstadoPuzzle)
# =====================================================================
class EstadoPuzzleTerminal:
    """Guarda em que etapa o jogador está (0/1 = comando, 2 = WIMP), os
    códigos já descobertos, o log do terminal e a seleção atual.
    Criado uma única vez em fase9.py e repassado por parâmetro pra
    run(), assim fechar essa tela (ESC) sem terminar e reabrir clicando
    no computador de novo continua exatamente de onde parou."""

    def __init__(self):
        # Só vira True depois que a etapa WIMP é concluída E a animação
        # de "tela acendendo" já tocou uma vez -- ver o tratamento de
        # "estado.concluido and not estado.no_desktop_final" em run().
        # Fora do reiniciar() de propósito: uma vez True, nunca mais
        # deveria voltar a False (reiniciar() só é chamado num "TENTAR
        # NOVAMENTE" depois de uma derrota, que nunca acontece depois
        # que o WIMP já foi concluído -- ver o guard em
        # atualizar_tempo()).
        self.no_desktop_final = False
        # Resultado (estrelas + tempo) da resolução -- só ganham valor no
        # momento exato em que a etapa WIMP é concluída (ver
        # ativar_elemento_wimp mais abaixo). fase9.py lê os dois pra
        # desenhar a tela de vitória. Fora de reiniciar() de propósito,
        # mesmo espírito de no_desktop_final logo acima.
        self.estrelas_conquistadas = None
        self.tempo_formatado = None
        self.reiniciar()

    def reiniciar(self):
        """Reinicia o puzzle do zero: etapa 1, nenhum código descoberto,
        cronômetro cheio de novo. Chamado na criação do objeto E toda
        vez que o jogador clica "TENTAR NOVAMENTE (R)" depois que o
        tempo acaba -- mesmo papel de
        babbage_lovelace.EstadoPuzzle.reiniciar() na Fase 2."""
        self.etapa_atual = 0
        self.codigos_gerados = []
        self.concluido = False
        self.derrotado = False
        self.tempo_restante = float(TEMPO_LIMITE_SEGUNDOS)
        self.linhas_terminal = [LINHA_INICIAL_TERMINAL]
        self._preparar_etapa_atual()

    def atualizar_tempo(self, dt, conversando_com_system_ai=False):
        """Decrementa o cronômetro -- só conta enquanto o jogador ainda
        está jogando de verdade: nem venceu, nem já está na tela de
        derrota, nem está com a caixa de conversa do SYSTEM_AI aberta
        (`conversando_com_system_ai` -- o tempo que o Ollama leva pra
        responder não deveria contra o jogador). Como isso só é chamado
        de dentro do loop de run() (nunca fora dele), fechar a tela do
        puzzle sem resolver também PAUSA o cronômetro -- reabrir
        continua de onde parou. Tudo isso é o mesmo espírito do
        cronômetro de babbage_lovelace.run() na Fase 2, só com a pausa
        extra durante a conversa (que a Fase 2 não tem, porque a Ada lá
        usa um retrato clicável, não uma tecla dedicada como o SYSTEM_AI)."""
        if self.concluido or self.derrotado or conversando_com_system_ai:
            return
        self.tempo_restante = max(0.0, self.tempo_restante - dt)
        if self.tempo_restante <= 0:
            self.derrotado = True

    def em_etapa_wimp(self):
        """True quando a etapa atual é a 3ª (montar a interface
        gráfica) -- as duas primeiras (0 e 1) são de comando."""
        return self.etapa_atual >= len(ETAPAS_COMANDO)

    def pista_atual(self):
        """Texto da pista a mostrar, seja etapa de comando ou a WIMP."""
        if self.em_etapa_wimp():
            return PISTA_ETAPA_WIMP
        return ETAPAS_COMANDO[self.etapa_atual]["pista"]

    def _preparar_etapa_atual(self):
        """Prepara o estado específico da etapa que acabou de começar:
        sorteia a ORDEM em que ação/alvo aparecem (etapas de comando) ou
        zera os elementos WIMP já ativados (etapa 3) -- feito só UMA VEZ
        ao entrar na etapa, não a cada frame."""
        if self.em_etapa_wimp():
            self.elementos_ativados = []
            return

        etapa = ETAPAS_COMANDO[self.etapa_atual]
        self.acoes_disponiveis = list(etapa["acoes"])
        random.shuffle(self.acoes_disponiveis)
        self.alvos_disponiveis, self.alvo_certo_atual = montar_alvos_da_etapa(
            self.etapa_atual, self.codigos_gerados
        )
        random.shuffle(self.alvos_disponiveis)
        self.acao_selecionada = None
        self.alvo_selecionada = None

    def etapa_atual_dados(self):
        # Atalho pra pegar o dicionário (ação/alvo/pista) da etapa de
        # comando em que o jogador está agora -- só faz sentido chamar
        # fora da etapa WIMP (ver em_etapa_wimp()), quem chama já garante
        # isso antes.
        return ETAPAS_COMANDO[self.etapa_atual]

    def reembaralhar_opcoes(self):
        """Reembaralha a ordem dos botões de AÇÃO/ALVO da etapa atual --
        chamado toda vez que a tela do puzzle é ABERTA (não só na
        primeira vez que a etapa é alcançada, que já embaralha sozinha
        em _preparar_etapa_atual): assim, se o jogador fechar e reabrir
        sem resolver, a resposta certa não continua sempre no mesmo
        botão -- ele precisa LER as opções de novo, não decorar a
        posição. Não faz nada na etapa WIMP (não há posições pra
        decorar lá, é só dependência)."""
        if self.em_etapa_wimp():
            return
        random.shuffle(self.acoes_disponiveis)
        random.shuffle(self.alvos_disponiveis)

    def tentar_executar(self):
        """(Etapas 0/1 -- comando) Confere o comando (ação + alvo)
        escolhido contra o certo desta etapa. Acertou: registra o
        sucesso, guarda o `codigo_gerado` (se houver) e avança pra
        próxima etapa. Errou: registra uma mensagem de erro GRADUADA
        (ver MSG_ERRO_* no topo do arquivo -- diz se a ação ou o alvo já
        estavam certos, em vez de só "errado") e limpa a seleção, pra
        tentar de novo -- TODO: no futuro, pode-se somar aqui alguma
        penalidade (ex: perder uma "estrela", como o puzzle da Fase 2
        faz)."""
        etapa = self.etapa_atual_dados()

        if self.acao_selecionada is None or self.alvo_selecionada is None:
            self.linhas_terminal.append("> Escolha uma AÇÃO e um ALVO antes de executar.")
            return False

        comando_texto = f"{self.acao_selecionada} {self.alvo_selecionada}"
        self.linhas_terminal.append(f"C:\\> {comando_texto}")

        acao_ok = self.acao_selecionada == etapa["acao_certa"]
        alvo_ok = self.alvo_selecionada == self.alvo_certo_atual
        acertou = acao_ok and alvo_ok

        if acertou:
            self.linhas_terminal.append(etapa["mensagem_sucesso"])
            if etapa["codigo_gerado"] is not None:
                self.codigos_gerados.append(etapa["codigo_gerado"])
            self.etapa_atual += 1
            self._preparar_etapa_atual()
        else:
            # Mensagem GRADUADA: se um dos dois campos já estava certo,
            # diz isso explicitamente (ajuda o jogador a corrigir só o
            # outro campo, em vez de recomeçar do zero) -- só cai no
            # "não reconhecido" quando NADA bate.
            if acao_ok and not alvo_ok:
                self.linhas_terminal.append(MSG_ERRO_ACAO_CERTA_ALVO_ERRADO)
            elif alvo_ok and not acao_ok:
                self.linhas_terminal.append(MSG_ERRO_ALVO_CERTO_ACAO_ERRADA)
            else:
                self.linhas_terminal.append(MSG_ERRO_NADA_BATE)
            self.acao_selecionada = None
            self.alvo_selecionada = None

        return acertou

    def tentar_ativar_elemento(self, chave):
        """(Etapa 2/WIMP) Tenta ativar um elemento (janela/icone/menu/
        ponteiro). Só funciona se o PRÉ-REQUISITO desse elemento (se
        houver) já estiver ativo -- essa é a dependência real da etapa:
        cada elemento só liga depois do que ele precisa. Fora de ordem,
        registra uma mensagem dizendo EXATAMENTE qual pré-requisito
        falta (não é um "errado" genérico) e não muda nada, pra tentar
        de novo depois de resolver a dependência. Quando os 4 elementos
        estiverem ativos, marca `concluido = True`."""
        elemento = WIMP_ELEMENTOS[chave]

        if chave in self.elementos_ativados:
            self.linhas_terminal.append(f"{elemento['rotulo']} já está ativo.")
            return False

        pre_requisito = elemento["pre_requisito"]
        if pre_requisito is not None and pre_requisito not in self.elementos_ativados:
            rotulo_pre = WIMP_ELEMENTOS[pre_requisito]["rotulo"]
            self.linhas_terminal.append(
                f"{elemento['rotulo']} precisa de {rotulo_pre} já ativo. Ative {rotulo_pre} primeiro."
            )
            return False

        self.elementos_ativados.append(chave)
        self.linhas_terminal.append(f">>> {elemento['mensagem_sucesso']}")

        if len(self.elementos_ativados) == len(WIMP_ELEMENTOS):
            self.concluido = True
        return True


def contexto_dinamico_etapa(estado):
    """Monta o texto de contexto DINÂMICO (ver
    npc_chatbot.NPCChatbot.atualizar_contexto_dinamico) que avisa o
    SYSTEM_AI em qual etapa do puzzle o jogador está agora e qual é o
    objetivo dela -- sem isso, o chatbot não sabia diferenciar etapa 1
    de etapa 3 e podia comentar coisas de etapas futuras/passadas.
    Chamado toda vez antes de mandar uma pergunta (ver run() e
    fase9.Jogo.executar())."""
    numero_etapa = estado.etapa_atual + 1
    return (
        f"CONTEXTO ATUAL DO JOGADOR: ele está na ETAPA {numero_etapa} de "
        f"{TOTAL_ETAPAS} agora. {estado.pista_atual()} Dê dicas SOMENTE "
        f"sobre esta etapa -- NUNCA fale sobre as etapas seguintes, "
        f"mesmo que o jogador pergunte diretamente sobre elas."
    )


# =====================================================================
# 3. UI AUXILIAR (botão clicável simples, autocontido -- Fase 9 ainda
#    não tem um common.py próprio como a Fase 2)
# =====================================================================
class _Botao:
    """Retângulo clicável com texto, destacado quando o mouse passa por
    cima (`hover`) ou quando está `selecionado` (usado pelas listas de
    AÇÃO/ALVO, pra mostrar qual opção o jogador já escolheu)."""

    def __init__(self, rect, texto):
        self.rect = pygame.Rect(rect)
        self.texto = texto
        self.hover = False

    def atualizar_hover(self, mouse_pos):
        # Chamado todo frame com a posição atual do mouse, pra saber se
        # deve desenhar o botão "aceso" (COR_AMBAR) ou apagado (COR_AMBAR_DIM).
        self.hover = self.rect.collidepoint(mouse_pos)

    def clicado(self, evento):
        # True se este evento é um clique do botão esquerdo dentro da
        # área do botão -- mesmo teste usado em common.Button.clicked na
        # Fase 2.
        return (
            evento.type == pygame.MOUSEBUTTONDOWN
            and evento.button == 1
            and self.rect.collidepoint(evento.pos)
        )

    def desenhar(self, tela, fonte, selecionado=False):
        # `selecionado` tem prioridade sobre `hover` (usado pelas listas
        # de AÇÃO/ALVO pra manter destacada a opção que o jogador já
        # escolheu, mesmo com o mouse em cima de outro botão).
        if selecionado:
            cor_fundo, cor_borda, cor_texto = COR_FUNDO_SELECIONADO, COR_AMBAR_BRILHO, COR_AMBAR_BRILHO
        elif self.hover:
            cor_fundo, cor_borda, cor_texto = COR_FUNDO_BOTAO_HOVER, COR_AMBAR, COR_AMBAR
        else:
            cor_fundo, cor_borda, cor_texto = COR_FUNDO_BOTAO, COR_AMBAR_DIM, COR_AMBAR_DIM

        pygame.draw.rect(tela, cor_fundo, self.rect)
        pygame.draw.rect(tela, cor_borda, self.rect, width=2)
        texto_surf = fonte.render(self.texto, True, cor_texto)
        tela.blit(texto_surf, texto_surf.get_rect(center=self.rect.center))


def _rects_coluna(x, y_topo, quantidade, largura=260, altura=44, gap=12):
    """Gera `quantidade` retângulos empilhados verticalmente a partir de
    (x, y_topo) -- usado pra montar as colunas de botões de AÇÃO/ALVO
    sem repetir a conta pra cada uma."""
    return [pygame.Rect(x, y_topo + i * (altura + gap), largura, altura) for i in range(quantidade)]


def _rects_linha_centralizada(largura_tela, y_topo, quantidade, largura_botao=210, altura=56, gap=20):
    """Gera `quantidade` retângulos lado a lado, centralizados
    horizontalmente na tela -- usado pelos 4 botões WIMP da etapa 3 (uma
    fileira só, em vez de duas colunas como nas etapas de comando)."""
    total = quantidade * largura_botao + (quantidade - 1) * gap
    x0 = (largura_tela - total) // 2
    return [pygame.Rect(x0 + i * (largura_botao + gap), y_topo, largura_botao, altura) for i in range(quantidade)]


def _quebrar_texto(texto, fonte, largura_maxima):
    """Quebra `texto` em linhas que cabem em `largura_maxima` pixels --
    mesma lógica usada em fase9._wrap_text e em
    npc_chatbot._quebrar_texto, duplicada aqui (autocontido, mesmo
    padrão do resto do repositório) porque a PISTA agora pode ter várias
    frases e precisa quebrar em múltiplas linhas."""
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


# =====================================================================
# 4. TELA FINAL -- DESKTOP GRÁFICO ESTILIZADO (retrô, anos 80)
# =====================================================================
# Referência visual: Xerox Star / GEM / primeiros sistemas gráficos --
# fundo liso (sem gradiente), janelas com barra de título + botão
# quadrado de fechar, ícones com rótulo, barra de menu no topo e um
# ponteiro de mouse. NÃO é interativo, é só a tela de "vitória visual"
# mostrando que os 4 elementos WIMP foram reconstruídos.
DESKTOP_BG = (150, 165, 185)
DESKTOP_BARRA_MENU = (230, 230, 225)
DESKTOP_BARRA_MENU_TEXTO = (20, 20, 20)
DESKTOP_JANELA_FUNDO = (235, 235, 230)
DESKTOP_JANELA_BORDA = (20, 20, 20)
DESKTOP_JANELA_TITULO = (40, 60, 120)
DESKTOP_JANELA_TITULO_TEXTO = (245, 245, 240)
DESKTOP_ICONE_COR = (210, 190, 90)


def _desenhar_janela_retro(tela, rect, titulo, fonte_titulo):
    """Uma "janela" simples: retângulo com borda + barra de título
    (com um botão quadrado de fechar, estilo GEM/Xerox Star -- só
    decorativo, não é clicável nesta tela de vitória)."""
    pygame.draw.rect(tela, DESKTOP_JANELA_FUNDO, rect)
    pygame.draw.rect(tela, DESKTOP_JANELA_BORDA, rect, width=2)

    barra_rect = pygame.Rect(rect.left, rect.top, rect.width, 26)
    pygame.draw.rect(tela, DESKTOP_JANELA_TITULO, barra_rect)
    pygame.draw.rect(tela, DESKTOP_JANELA_BORDA, barra_rect, width=2)
    titulo_surf = fonte_titulo.render(titulo, True, DESKTOP_JANELA_TITULO_TEXTO)
    tela.blit(titulo_surf, (barra_rect.left + 8, barra_rect.top + 5))

    fechar_rect = pygame.Rect(barra_rect.right - 22, barra_rect.top + 4, 18, 18)
    pygame.draw.rect(tela, DESKTOP_JANELA_FUNDO, fechar_rect)
    pygame.draw.rect(tela, DESKTOP_JANELA_BORDA, fechar_rect, width=2)


def _desenhar_icone_retro(tela, pos, rotulo, fonte_rotulo, cor_rotulo):
    """Um "ícone": quadrado sólido + rótulo embaixo (estética chapada,
    sem sombra/gradiente, igual às interfaces gráficas originais)."""
    icone_rect = pygame.Rect(0, 0, 40, 34)
    icone_rect.center = pos
    pygame.draw.rect(tela, DESKTOP_ICONE_COR, icone_rect)
    pygame.draw.rect(tela, DESKTOP_JANELA_BORDA, icone_rect, width=2)
    rotulo_surf = fonte_rotulo.render(rotulo, True, cor_rotulo)
    tela.blit(rotulo_surf, rotulo_surf.get_rect(midtop=(pos[0], icone_rect.bottom + 2)))


def _desenhar_ponteiro_retro(tela, pos):
    """Um ponteiro de mouse simples (seta), estilo bitmap monocromático
    dos anos 80 -- só um polígono preenchido de branco com contorno
    preto, sem antialiasing."""
    x, y = pos
    pontos = [
        (x, y), (x, y + 17), (x + 4, y + 13), (x + 8, y + 20),
        (x + 11, y + 18), (x + 7, y + 11), (x + 13, y + 11),
    ]
    pygame.draw.polygon(tela, (255, 255, 255), pontos)
    pygame.draw.polygon(tela, (0, 0, 0), pontos, width=1)


def desenhar_desktop_retro(tela, largura, altura):
    """Desenha a tela final: o desktop gráfico "reconstruído", num
    estilo retrô/anos 80 (ver comentário da seção acima). Chamada tanto
    por _animar_tela_acendendo() (na transição) quanto por
    fase9.Jogo._desenhar_desktop() (enquanto o estado ficar em DESKTOP),
    pra o visual ficar consistente antes e depois da transição.

    TODO: depois que essa tela aparecer, a fase deveria seguir pra sala
    da máquina do tempo (como a Fase 2 faz -- ver fase2._fade_transition
    em Pygame/Fase_2/fase2/fase2.py); por enquanto ela só fica parada
    aqui (ver TODO em fase9.Jogo.executar()).
    """
    fonte_menu = pygame.font.SysFont("consolas", 15, bold=True)
    fonte_titulo_janela = pygame.font.SysFont("consolas", 14, bold=True)
    fonte_rotulo_icone = pygame.font.SysFont("consolas", 12)
    fonte_mensagem = pygame.font.SysFont("consolas", 20, bold=True)

    tela.fill(DESKTOP_BG)

    # --- barra de menu, no topo ---
    barra_menu_rect = pygame.Rect(0, 0, largura, 28)
    pygame.draw.rect(tela, DESKTOP_BARRA_MENU, barra_menu_rect)
    pygame.draw.rect(tela, DESKTOP_JANELA_BORDA, barra_menu_rect, width=2)
    tela.blit(fonte_menu.render("Arquivo   Editar   Exibir   Ajuda", True, DESKTOP_BARRA_MENU_TEXTO), (16, 6))

    # --- duas janelas (uma com um ícone dentro -- o ícone "precisa" da
    # janela pra existir, igual à dependência da etapa 3) ---
    janela1 = pygame.Rect(70, 70, 380, 260)
    _desenhar_janela_retro(tela, janela1, "PROGRAMA.EXE", fonte_titulo_janela)
    _desenhar_icone_retro(tela, (janela1.left + 70, janela1.top + 110), "DADOS", fonte_rotulo_icone, (20, 20, 20))

    janela2 = pygame.Rect(500, 130, 300, 200)
    _desenhar_janela_retro(tela, janela2, "SISTEMA", fonte_titulo_janela)

    # --- ícones soltos no desktop (fora de janelas, como de costume) ---
    _desenhar_icone_retro(tela, (largura - 90, altura - 170), "LIXEIRA", fonte_rotulo_icone, (255, 255, 255))
    _desenhar_icone_retro(tela, (largura - 90, altura - 100), "DISCO", fonte_rotulo_icone, (255, 255, 255))

    # --- mensagem curta de conclusão ---
    mensagem_surf = fonte_mensagem.render("Desktop gráfico reconstruído!", True, (255, 255, 255))
    fundo_msg = mensagem_surf.get_rect(center=(largura // 2, altura - 40)).inflate(30, 16)
    pygame.draw.rect(tela, (20, 20, 20), fundo_msg, border_radius=6)
    pygame.draw.rect(tela, (255, 255, 255), fundo_msg, width=2, border_radius=6)
    tela.blit(mensagem_surf, mensagem_surf.get_rect(center=fundo_msg.center))

    # --- ponteiro do mouse, por cima de tudo ---
    _desenhar_ponteiro_retro(tela, (largura // 2 + 80, altura // 2 - 40))


def _animar_tela_acendendo(tela, relogio, largura, altura, duracao=1.6):
    """Cross-fade do terminal preto pro desktop gráfico estilizado
    (desenhar_desktop_retro) -- mesmo espírito de fase2._fade_transition
    (Pygame/Fase_2/fase2/fase2.py), só que autocontido aqui (não
    depende de nenhuma imagem "antes" pronta, só desenha o quadro final
    uma vez e faz o preto sumir por cima dele)."""
    quadro_final = pygame.Surface((largura, altura))
    desenhar_desktop_retro(quadro_final, largura, altura)

    passos = max(1, int(duracao * FPS))
    for i in range(passos):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
        relogio.tick(FPS)

        progresso = (i + 1) / passos
        quadro = quadro_final.copy()
        véu_preto = pygame.Surface((largura, altura))
        véu_preto.fill(COR_FUNDO_CRT)
        véu_preto.set_alpha(int(255 * (1 - progresso)))  # começa opaco (preto) e vai sumindo
        quadro.blit(véu_preto, (0, 0))

        tela.blit(quadro, (0, 0))
        pygame.display.flip()


# =====================================================================
# 5. LOOP PRINCIPAL DO PUZZLE
# =====================================================================
def run(tela, relogio, npc_chat, estado, largura, altura):
    """Roda o loop do puzzle até o jogador fechar (ESC, antes de
    terminar) ou concluir as 3 etapas. Devolve True se concluiu (fase9.py
    usa isso pra saber que deve seguir pro desktop), ou False se saiu
    sem terminar.

    `tela`/`relogio` são os MESMOS objetos do loop principal da Fase 9
    (mesmo padrão de babbage_lovelace.run() na Fase 2) -- só
    "emprestados" por um tempo. `npc_chat` é o mesmo NPCChatbot (SYSTEM_AI)
    já criado em fase9.py, pra o jogador poder pedir dica sem perder o
    histórico da conversa. `estado` é o EstadoPuzzleTerminal (também
    criado uma vez em fase9.py), que é o que permite fechar essa tela
    sem terminar e retomar a mesma etapa depois.

    "Concluir as 3 etapas" só libera o desktop final -- a fase só
    termina de verdade quando o jogador também decifra o código de
    ativação escondido lá (ver desktop_final.py). Por isso o valor
    devolvido pode ser True (código certo, fase9.py segue pra sala da
    máquina do tempo), False (saiu sem terminar -- de QUALQUER etapa,
    inclusive do desktop final) ou a string "sair" (escolheu SAIR no
    painel de configurações -- fase9.py encerra a fase inteira).
    """
    _carregar_sons_do_puzzle()

    if estado.no_desktop_final:
        # Já concluiu as 3 etapas numa aberta anterior e fechou o
        # desktop final sem decifrar o código -- pula direto pra lá de
        # novo (sem refazer nenhuma etapa nem tocar a animação de "tela
        # acendendo" outra vez).
        resultado_desktop = desktop_final.run(
            tela, relogio, npc_chat, largura, altura,
            _som_clique, _som_sucesso, _som_erro,
        )
        if resultado_desktop == "sair":
            return "sair"
        return bool(resultado_desktop)

    fonte_titulo = pygame.font.SysFont("consolas", 24, bold=True)
    fonte_etapa = pygame.font.SysFont("consolas", 15, bold=True)
    fonte_pista = pygame.font.SysFont("consolas", 17)
    fonte_terminal = pygame.font.SysFont("consolas", 17)
    fonte_botao = pygame.font.SysFont("consolas", 16, bold=True)
    fonte_rotulo = pygame.font.SysFont("consolas", 16, bold=True)
    fonte_hint = pygame.font.SysFont("consolas", 15)
    fonte_tempo = pygame.font.SysFont("consolas", 22, bold=True)

    # --- geometria horizontal (fixa) ---
    coluna_acao_x = 90
    coluna_alvo_x = largura - 90 - 260
    botao_fechar_rect = pygame.Rect(largura - 150, 20, 110, 36)
    fechar_btn = _Botao(botao_fechar_rect, "FECHAR (ESC)")

    # Cronômetro no canto superior direito -- mesmo estilo/posição da
    # Fase 2 (ver babbage_lovelace.run(), topright=(width-50, 44)), só
    # deslocado um pouco mais pra dentro (largura-165 em vez de
    # largura-50) porque a Fase 9 já tem o botão FECHAR bem naquele
    # canto (a Fase 2 põe o botão de fechar embaixo, não ali).
    tempo_pos_topright = (largura - 165, 20)

    # Botão "TENTAR NOVAMENTE (R)" da tela de derrota -- mesmo texto do
    # botão da Fase 2 (ver babbage_lovelace.run(), retry_btn).
    retry_rect = pygame.Rect(0, 0, 280, 50)
    retry_rect.center = (largura // 2, altura // 2 + FALHA_ALTURA_PAINEL // 2 - 55)
    retry_btn = _Botao(retry_rect, "TENTAR NOVAMENTE (R)")

    # --- geometria vertical: a PISTA agora pode ter várias linhas (o
    # texto virá mais longo, com informação suficiente pra deduzir o
    # comando -- ver ETAPAS). Pra um texto mais comprido NUNCA empurrar
    # as colunas de botões/botão executar pra fora da tela (ou por cima
    # deles), só a caixa do terminal (no meio) é flexível: ela ocupa o
    # espaço que sobrar entre o fim da pista e o topo (FIXO) das
    # colunas. Se a pista crescer, a caixa do terminal fica mais baixa
    # (mostra menos linhas de histórico) -- nunca invade o resto do
    # layout.
    PISTA_TOPO_Y = 74
    PISTA_LARGURA_MAXIMA = largura - 160
    COLUNAS_Y_TOPO = 340
    TERMINAL_ALTURA_MINIMA = 60
    botao_executar_rect = pygame.Rect(largura // 2 - 100, 520, 200, 46)

    # Embaralha AÇÃO/ALVO de novo toda vez que a tela é aberta (não só
    # na primeira vez que a etapa é alcançada) -- ver
    # EstadoPuzzleTerminal.reembaralhar_opcoes().
    estado.reembaralhar_opcoes()

    concluido_agora = False
    saiu_da_fase = False  # True se o jogador escolheu SAIR no painel de config (ver o tratamento de MOUSEBUTTONDOWN mais abaixo) -- diferente de fechar o puzzle sem terminar (rodando=False sem isso), que só volta pro QUARTO (ver fase9.Jogo.executar())
    rodando = True
    while rodando:
        dt = relogio.tick(FPS) / 1000
        mouse_pos = pygame.mouse.get_pos()

        # Cronômetro: só decrementa enquanto ainda dá pra jogar (não
        # concluído, não já na tela de derrota, não conversando com o
        # SYSTEM_AI -- ver EstadoPuzzleTerminal.atualizar_tempo()). É
        # essa chamada estar DENTRO do loop (nunca fora dele) que faz o
        # tempo pausar quando o jogador fecha o puzzle sem resolver,
        # igual à Fase 2; o `npc_chat.dialogo_aberto` aqui é o que pausa
        # também enquanto a caixa de conversa estiver aberta (inclusive
        # esperando a resposta do Ollama).
        estado.atualizar_tempo(dt, conversando_com_system_ai=npc_chat.dialogo_aberto)
        if estado.derrotado and npc_chat.dialogo_aberto:
            # A Fase 2 não mostra o chat da Ada na tela de derrota (o
            # foco fica no aviso + botão de tentar de novo) -- mesma
            # regra aqui, força fechar se tiver aberto bem na hora que
            # o tempo acabou.
            npc_chat.fechar_dialogo()

        em_wimp = estado.em_etapa_wimp()
        pista_texto = estado.pista_atual()

        # SYSTEM_AI precisa saber em qual etapa o jogador está AGORA pra
        # só dar dica dela (não adiantar etapas futuras) -- atualizado
        # todo frame (é só montar uma string, barato) porque a etapa
        # pode mudar a qualquer momento (ao acertar um comando/ativar o
        # último elemento WIMP).
        npc_chat.atualizar_contexto_dinamico(contexto_dinamico_etapa(estado))

        # Layout vertical desta etapa: a caixa do terminal ocupa o
        # espaço FLEXÍVEL entre o fim da pista (que pode ter mais ou
        # menos linhas, dependendo do texto) e o topo FIXO das colunas
        # de botões (COLUNAS_Y_TOPO) -- ver comentário acima. Assim uma
        # pista mais longa nunca empurra os botões/botão executar pra
        # fora do lugar, só encolhe a caixa do terminal.
        linhas_pista = _quebrar_texto(pista_texto, fonte_pista, PISTA_LARGURA_MAXIMA)
        altura_linha_pista = fonte_pista.get_linesize()
        terminal_topo = PISTA_TOPO_Y + len(linhas_pista) * altura_linha_pista + 14
        colunas_y_topo = COLUNAS_Y_TOPO
        terminal_altura = max(TERMINAL_ALTURA_MINIMA, (colunas_y_topo - 40) - terminal_topo)
        terminal_rect = pygame.Rect(60, terminal_topo, largura - 120, terminal_altura)

        # Botões desta etapa: nas etapas 0/1 (comando) são duas colunas
        # AÇÃO/ALVO; na etapa 2 (WIMP) é uma fileira só com os 4
        # elementos -- ver estado.em_etapa_wimp().
        if em_wimp:
            chaves_wimp = list(WIMP_ELEMENTOS.keys())
            botoes_wimp = [
                _Botao(r, WIMP_ELEMENTOS[chave]["rotulo"]) for r, chave in zip(
                    _rects_linha_centralizada(largura, colunas_y_topo, len(chaves_wimp)),
                    chaves_wimp,
                )
            ]
            botoes_acao, botoes_alvo = [], []
        else:
            botoes_wimp, chaves_wimp = [], []
            botoes_acao = [
                _Botao(r, texto) for r, texto in zip(
                    _rects_coluna(coluna_acao_x, colunas_y_topo, len(estado.acoes_disponiveis)),
                    estado.acoes_disponiveis,
                )
            ]
            botoes_alvo = [
                _Botao(r, texto) for r, texto in zip(
                    _rects_coluna(coluna_alvo_x, colunas_y_topo, len(estado.alvos_disponiveis)),
                    estado.alvos_disponiveis,
                )
            ]
        for botao in botoes_acao + botoes_alvo + botoes_wimp + [fechar_btn, retry_btn]:
            botao.atualizar_hover(mouse_pos)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            elif evento.type == pygame.KEYDOWN:
                if npc_chat.dialogo_aberto:
                    # Com a conversa aberta, todo o teclado é dela --
                    # SYSTEM_AI continua disponível pra dar dicas
                    # durante o puzzle (mesmo padrão da Ada na Fase 2).
                    npc_chat.tratar_evento(evento)
                elif evento.key == pygame.K_r and estado.derrotado:
                    # Atalho de teclado pro botão "TENTAR NOVAMENTE" --
                    # mesma ação de clicar nele (mesmo atalho R da Fase 2).
                    estado.reiniciar()
                elif estado.derrotado:
                    # Na tela de derrota, só R (acima) e ESC (abaixo)
                    # fazem sentido -- nem E nem ENTER têm o que fazer
                    # aqui (mesma regra da Fase 2: a tela de derrota não
                    # interage com o resto do puzzle).
                    if evento.key == pygame.K_ESCAPE:
                        rodando = False
                elif evento.key == pygame.K_e and not estado.concluido and not npc_chat.limite_atingido():
                    npc_chat.abrir_dialogo()
                elif evento.key == pygame.K_RETURN and not estado.concluido and not em_wimp:
                    # ENTER só faz sentido nas etapas de comando (montar
                    # ação+alvo); na etapa WIMP cada clique já ativa o
                    # elemento na hora, não tem "comando" pra confirmar.
                    audio_fase9.tocar_som(_som_sucesso if estado.tentar_executar() else _som_erro)
                elif evento.key == pygame.K_ESCAPE and not estado.concluido:
                    rodando = False

            elif (
                evento.type == pygame.MOUSEBUTTONDOWN
                and evento.button == 1
                and not npc_chat.dialogo_aberto
                and not estado.concluido
            ):
                if config_fase9.engrenagem_rect(largura).collidepoint(evento.pos):
                    # Botão de configurações: acessível em qualquer
                    # etapa do puzzle, inclusive na tela de derrota --
                    # checado ANTES do resto (inclusive antes do "só o
                    # retry reage" da tela de derrota, logo abaixo), pra
                    # sempre funcionar não importa a etapa. O painel É o
                    # "jogo pausado" (ver config_fase9.abrir_painel_config()).
                    resultado_config = config_fase9.abrir_painel_config(tela, relogio, largura, altura)
                    if resultado_config == "sair":
                        saiu_da_fase = True
                        rodando = False
                    continue

                if estado.derrotado:
                    # Na tela de derrota só o botão de reiniciar reage a
                    # clique -- os botões de comando/WIMP nem são
                    # desenhados aqui, então não faz sentido checá-los
                    # (mesma regra do puzzle da Fase 2).
                    if retry_btn.clicado(evento):
                        estado.reiniciar()
                    continue

                if fechar_btn.clicado(evento):
                    rodando = False
                    continue

                clicou_em_botao = False
                if em_wimp:
                    for chave, botao in zip(chaves_wimp, botoes_wimp):
                        if botao.clicado(evento):
                            estado.tentar_ativar_elemento(chave)
                            clicou_em_botao = True
                            break
                else:
                    for texto_acao, botao in zip(estado.acoes_disponiveis, botoes_acao):
                        if botao.clicado(evento):
                            estado.acao_selecionada = texto_acao
                            clicou_em_botao = True
                            audio_fase9.tocar_som(_som_clique)
                            break
                    if not clicou_em_botao:
                        for texto_alvo, botao in zip(estado.alvos_disponiveis, botoes_alvo):
                            if botao.clicado(evento):
                                estado.alvo_selecionada = texto_alvo
                                clicou_em_botao = True
                                audio_fase9.tocar_som(_som_clique)
                                break

                    if not clicou_em_botao and botao_executar_rect.collidepoint(evento.pos):
                        audio_fase9.tocar_som(_som_sucesso if estado.tentar_executar() else _som_erro)

        # --- desenho ---
        tela.fill(COR_FUNDO_CRT)

        titulo_surf = render_texto_glow(fonte_titulo, "TERMINAL -- RECONSTRUINDO O DESKTOP", COR_AMBAR)
        tela.blit(titulo_surf, titulo_surf.get_rect(midtop=(largura // 2, 24)))

        etapa_label = render_texto_glow(fonte_etapa, f"ETAPA {estado.etapa_atual + 1}/{TOTAL_ETAPAS}", COR_AMBAR_DIM)
        tela.blit(etapa_label, etapa_label.get_rect(midtop=(largura // 2, 54)))

        # --- cronômetro: mesmo estilo da Fase 2 (MM:SS, fica em alerta
        # nos últimos TEMPO_ALERTA_SEGUNDOS) -- some na tela de derrota
        # (dá lugar ao painel "TENTE NOVAMENTE") e quando já concluído.
        if not estado.derrotado and not estado.concluido:
            minutos = int(estado.tempo_restante) // 60
            segundos = int(estado.tempo_restante) % 60
            cor_tempo = COR_TEMPO_ALERTA if estado.tempo_restante <= TEMPO_ALERTA_SEGUNDOS else COR_AMBAR
            tempo_surf = render_texto_glow(fonte_tempo, f"{minutos:02d}:{segundos:02d}", cor_tempo)
            tela.blit(tempo_surf, tempo_surf.get_rect(topright=tempo_pos_topright))

        if estado.derrotado:
            # --- tela de derrota: painel "TENTE NOVAMENTE" + botão --
            # mesmo espírito da tela de derrota da Fase 2 (balão de
            # texto + botão "TENTAR NOVAMENTE (R)"), só sem o retrato de
            # personagem (o SYSTEM_AI não tem um sprite/retrato próprio
            # como a Ada da Fase 2 tem).
            painel_rect = pygame.Rect(0, 0, FALHA_LARGURA_PAINEL, FALHA_ALTURA_PAINEL)
            painel_rect.center = (largura // 2, altura // 2 - 10)
            pygame.draw.rect(tela, COR_FUNDO_CRT, painel_rect)
            pygame.draw.rect(tela, COR_AMBAR, painel_rect, width=3)

            titulo_falha_surf = render_texto_glow(fonte_titulo, FALHA_TITULO, COR_AMBAR_ALERTA)
            tela.blit(titulo_falha_surf, titulo_falha_surf.get_rect(midtop=(painel_rect.centerx, painel_rect.top + 22)))

            linhas_falha = _quebrar_texto(FALHA_TEXTO, fonte_pista, painel_rect.width - 60)
            altura_linha_falha = fonte_pista.get_linesize()
            y_falha = painel_rect.top + 70
            for linha in linhas_falha:
                linha_falha_surf = fonte_pista.render(linha, True, COR_AMBAR)
                tela.blit(linha_falha_surf, linha_falha_surf.get_rect(midtop=(painel_rect.centerx, y_falha)))
                y_falha += altura_linha_falha

            retry_btn.desenhar(tela, fonte_botao)
        else:
            # --- pista: SEMPRE visível enquanto a etapa estiver ativa
            # (não é só uma linha do log que pode rolar pra fora de
            # vista) -- dá o contexto mínimo (objetivo + opções), sem
            # entregar a resposta.
            y_pista = PISTA_TOPO_Y
            for linha in linhas_pista:
                linha_surf = fonte_pista.render(linha, True, COR_AMBAR)
                tela.blit(linha_surf, linha_surf.get_rect(midtop=(largura // 2, y_pista)))
                y_pista += altura_linha_pista

            # --- caixa do terminal: log das últimas linhas, estilo prompt ---
            pygame.draw.rect(tela, COR_FUNDO_CRT, terminal_rect)
            pygame.draw.rect(tela, COR_AMBAR, terminal_rect, width=2)

            # As mensagens (principalmente as de sucesso, mais longas)
            # podem não caber inteiras na largura da caixa -- quebra
            # cada linha LÓGICA do log em uma ou mais linhas VISUAIS
            # antes de desenhar, senão o texto vaza pra fora da caixa.
            # Todas as linhas visuais que vierem de uma linha lógica
            # destacada (">>> ...") mantêm o destaque.
            linhas_expandidas = []
            for linha in estado.linhas_terminal:
                destaque = linha.startswith(">>>")
                for sub_linha in _quebrar_texto(linha, fonte_terminal, terminal_rect.width - 28):
                    linhas_expandidas.append((sub_linha, destaque))

            # Quantas linhas cabem de verdade na altura (FLEXÍVEL) da
            # caixa nesta etapa -- nunca um número fixo, senão o texto
            # vazaria por BAIXO da caixa quando ela ficar mais baixa
            # (pista mais longa) ou quando o log tiver várias mensagens
            # longas já quebradas em 2+ linhas visuais (era o bug antes
            # desta correção).
            altura_linha = fonte_terminal.get_linesize()
            linhas_que_cabem = max(1, (terminal_rect.height - 20) // altura_linha)
            linhas_visiveis = linhas_expandidas[-linhas_que_cabem:]

            # Recorte (clip): defesa extra, igual à caixa de diálogo do
            # SYSTEM_AI (ver npc_chatbot.py) -- garante que nada
            # apareça por fora da caixa mesmo se as contas acima
            # errarem por arredondamento.
            area_visivel = pygame.Rect(terminal_rect.left + 10, terminal_rect.top + 6,
                                        terminal_rect.width - 20, terminal_rect.height - 12)
            recorte_anterior = tela.get_clip()
            tela.set_clip(area_visivel)
            y = terminal_rect.top + 10
            for texto_linha, destaque in linhas_visiveis:
                if destaque:
                    linha_surf = render_texto_glow(fonte_terminal, texto_linha, COR_AMBAR_BRILHO)
                else:
                    linha_surf = fonte_terminal.render(texto_linha, True, COR_AMBAR)
                tela.blit(linha_surf, (terminal_rect.left + 14, y))
                y += altura_linha
            tela.set_clip(recorte_anterior)
            # cursor piscante na última linha (só estética, mesmo
            # padrão do placeholder de fase9._desenhar_terminal)
            if pygame.time.get_ticks() % 1000 < 500 and not estado.concluido:
                ultima_largura = fonte_terminal.size(linhas_visiveis[-1][0])[0] if linhas_visiveis else 0
                cursor_x = terminal_rect.left + 14 + ultima_largura + 4
                cursor_y = y - altura_linha
                pygame.draw.line(tela, COR_AMBAR, (cursor_x, cursor_y), (cursor_x, cursor_y + altura_linha - 4), 2)

            if em_wimp:
                # --- fileira de botões WIMP (etapa 3) ---
                rotulo_wimp = fonte_rotulo.render("ELEMENTOS", True, COR_AMBAR)
                tela.blit(rotulo_wimp, rotulo_wimp.get_rect(midtop=(largura // 2, colunas_y_topo - 26)))
                for chave, botao in zip(chaves_wimp, botoes_wimp):
                    botao.desenhar(tela, fonte_botao, selecionado=(chave in estado.elementos_ativados))
            else:
                # --- colunas de AÇÃO / ALVO (etapas 0/1) ---
                rotulo_acao = fonte_rotulo.render("AÇÃO", True, COR_AMBAR)
                tela.blit(rotulo_acao, (coluna_acao_x, colunas_y_topo - 26))
                for texto_acao, botao in zip(estado.acoes_disponiveis, botoes_acao):
                    botao.desenhar(tela, fonte_botao, selecionado=(texto_acao == estado.acao_selecionada))

                rotulo_alvo = fonte_rotulo.render("ALVO", True, COR_AMBAR)
                tela.blit(rotulo_alvo, (coluna_alvo_x, colunas_y_topo - 26))
                for texto_alvo, botao in zip(estado.alvos_disponiveis, botoes_alvo):
                    botao.desenhar(tela, fonte_botao, selecionado=(texto_alvo == estado.alvo_selecionada))

                # --- comando montado até agora + botão executar (só faz
                # sentido nas etapas de comando -- na WIMP cada clique já
                # ativa na hora, não tem nada pra "executar" à parte) ---
                texto_comando = f"Comando: {estado.acao_selecionada or '???'} {estado.alvo_selecionada or '???'}"
                comando_surf = fonte_pista.render(texto_comando, True, COR_AMBAR)
                tela.blit(comando_surf, comando_surf.get_rect(midtop=(largura // 2, botao_executar_rect.top - 30)))

                hover_executar = botao_executar_rect.collidepoint(mouse_pos)
                pygame.draw.rect(tela, COR_FUNDO_BOTAO_HOVER if hover_executar else COR_FUNDO_BOTAO, botao_executar_rect)
                pygame.draw.rect(tela, COR_AMBAR, botao_executar_rect, width=2)
                executar_texto = fonte_botao.render("EXECUTAR (ENTER)", True, COR_AMBAR_BRILHO if hover_executar else COR_AMBAR)
                tela.blit(executar_texto, executar_texto.get_rect(center=botao_executar_rect.center))

            if not estado.concluido:
                fechar_btn.desenhar(tela, fonte_hint)
                if npc_chat.limite_atingido():
                    texto_hint_ia = "Sem dicas restantes -- resolva sozinho a partir daqui"
                else:
                    texto_hint_ia = "Pressione E para pedir uma dica ao SYSTEM_AI"
                hint_surf = fonte_hint.render(texto_hint_ia, True, COR_AMBAR)
                tela.blit(hint_surf, (30, altura - 30))

        # --- scanlines por cima de todo o conteúdo do puzzle (efeito de
        # monitor CRT) -- desenhado ANTES do contador/caixa do SYSTEM_AI
        # pra essa caixa (quando aberta) ficar nítida por cima, com seu
        # próprio efeito de scanlines só na área dela (ver npc_chatbot.py).
        desenhar_scanlines(tela)

        # --- contador "Dicas restantes: N", sempre visível (mesmo
        # depois de concluído, só como registro) ---
        npc_chat.desenhar_contador_dicas(tela, fonte_hint)

        # --- SYSTEM_AI (dica) por cima de tudo, igual à Ada na Fase 2 ---
        npc_chat.desenhar(tela, fonte_pista, fonte_hint, largura, altura)

        # --- botão de configurações: sempre visível, em qualquer etapa
        # do puzzle (inclusive na tela de derrota) ---
        config_fase9.desenhar_engrenagem(tela, largura, mouse_pos)

        pygame.display.flip()

        # Conclusão das 3 etapas: dispara a animação de "a tela acende"
        # e entra DIRETO no desktop final interativo (não devolve True
        # ainda -- feito FORA do loop de eventos, só depois de já ter
        # desenhado o frame com a mensagem de sucesso da 3ª etapa, senão
        # o jogador nunca chegaria a ver o texto "Desktop gráfico
        # ativado!" antes da tela mudar).
        if estado.concluido and not estado.no_desktop_final:
            # Calcula e salva o resultado final (estrelas + tempo) só
            # aqui, no momento exato em que a etapa WIMP é dada como
            # concluída. estado.tempo_restante já está "congelado" desde
            # que concluido virou True (atualizar_tempo() para de
            # decrementar assim que concluido/derrotado), então o valor
            # aqui é exatamente o tempo que sobrava quando o jogador
            # terminou.
            estado.estrelas_conquistadas = _calcular_estrelas(estado.tempo_restante)
            tempo_gasto = TEMPO_LIMITE_SEGUNDOS - estado.tempo_restante
            estado.tempo_formatado = _formatar_tempo(tempo_gasto)
            _salvar_progresso(estado.estrelas_conquistadas, estado.tempo_formatado)

            audio_fase9.tocar_som(_som_computador_ligando)
            _animar_tela_acendendo(tela, relogio, largura, altura)
            estado.no_desktop_final = True

            resultado_desktop = desktop_final.run(
                tela, relogio, npc_chat, largura, altura,
                _som_clique, _som_sucesso, _som_erro,
            )
            if resultado_desktop == "sair":
                saiu_da_fase = True
            elif resultado_desktop:
                concluido_agora = True
            rodando = False
            # "continue" (em vez de deixar o loop cair no próximo "while
            # rodando") pra NÃO redesenhar mais uma vez a tela da etapa
            # WIMP (já concluída) por cima do que o desktop_final.run()
            # acabou de mostrar -- senão o jogador veria um flash de
            # volta pro terminal bem antes da transição de vitória.
            continue

    if saiu_da_fase:
        # Sinal especial (string, não bool) pra fase9.Jogo.executar()
        # saber que deve encerrar a FASE INTEIRA (não só voltar pro
        # QUARTO como faria um ESC/FECHAR normal) -- ver o tratamento de
        # "sair" logo depois da chamada a run() lá.
        return "sair"
    return concluido_agora

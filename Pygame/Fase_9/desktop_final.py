"""
=====================================================================
desktop_final.py -- mini-puzzle interativo do "desktop final" da Fase 9
=====================================================================
Depois que o jogador resolve as 3 etapas do terminal (ver
puzzle_terminal.py), a tela "acende" num desktop gráfico retrô. Antes,
essa tela era só uma imagem estática (desenhar_desktop_retro, ainda em
puzzle_terminal.py, usada na animação de transição). Este arquivo torna
esse desktop DE VERDADE INTERATIVO: o jogador precisa navegar pelo
menu (Arquivo/Editar/Exibir/Ajuda) e pelos ícones DADOS/DISCO -- cada
um com 3 subpastas -- pra achar as duas PARTES do código de ativação da
máquina do tempo, escondidas em arquivos .dat, e digitá-las juntas
(XK47) na janela PROGRAMA.EXE.

Chamado por puzzle_terminal.run() assim que a etapa WIMP é concluída
(ver o bloco "if estado.concluido" lá) -- este módulo tem seu PRÓPRIO
loop (mesmo padrão de puzzle_terminal.run()/fase9._run_intro()) e só
devolve o controle quando o jogador digita o código certo (True), sai
sem terminar (False, ESC com nenhuma janela aberta) ou escolhe SAIR no
painel de configurações ("sair").

CONTEÚDO (menus/pastas/arquivos/pistas) -- tudo na seção 1 logo abaixo,
separado da lógica (seções 2+), pra editar o texto sem precisar mexer
no resto.
=====================================================================
"""

import pygame

import audio_fase9
import config_fase9

FPS = 60

# Resolução fixa desta fase (mesma de fase9.LARGURA/ALTURA) -- usada só
# pra limitar (clamp) a posição das janelas que se abrem, pra nunca
# nascerem cortadas fora da tela.
LARGURA_TELA = 960
ALTURA_TELA = 600

# =====================================================================
# 1. CONTEÚDO -- EDITAR AQUI (menus, pastas, arquivos, pistas)
# =====================================================================
CODIGO_CORRETO = "XK47"  # as duas partes juntas (codigo_parte1.dat + codigo_parte2.dat)

PISTA_MESTRE = (
    "O código de ativação foi dividido em duas partes e armazenado em "
    "locais diferentes do sistema."
)

# Cada item de menu: rotulo (texto do botão), acao ("abrir_dados" ou
# "mensagem"), texto (só usado quando acao="mensagem") e id (único,
# evita abrir duas janelinhas iguais se o jogador clicar 2x).
MENU_ARQUIVO = [
    {"id": "arquivo_abrir", "rotulo": "Abrir pasta", "acao": "abrir_dados", "texto": None},
    {"id": "arquivo_prop", "rotulo": "Propriedades", "acao": "mensagem", "texto": "Sistema operacional v1.0"},
    {"id": "arquivo_sair", "rotulo": "Sair", "acao": "mensagem", "texto": "Impossível sair. A máquina do tempo aguarda."},
]
MENU_EDITAR = [
    {"id": "editar_desfazer", "rotulo": "Desfazer", "acao": "mensagem", "texto": "Nada para desfazer. Você ainda não fez nada de errado."},
    {"id": "editar_copiar", "rotulo": "Copiar", "acao": "mensagem", "texto": "Ctrl+C ainda não foi inventado neste sistema."},
    {"id": "editar_colar", "rotulo": "Colar", "acao": "mensagem", "texto": "Área de transferência vazia, como sempre."},
]
MENU_EXIBIR = [
    {"id": "exibir_icones", "rotulo": "Ícones grandes", "acao": "mensagem", "texto": "Os ícones já estão no maior tamanho que a memória permite."},
    {"id": "exibir_atualizar", "rotulo": "Atualizar", "acao": "mensagem", "texto": "Tela atualizada. Nada mudou."},
    {"id": "exibir_cores", "rotulo": "Cores", "acao": "mensagem", "texto": "16 cores disponíveis. Escolha com sabedoria."},
]

# Pastas: cada chave é o NOME da subpasta (mostrado na listagem); cada
# valor é a lista de arquivos dentro dela. Um arquivo com "parte": 1 ou
# 2 é uma das duas partes do código (ver CODIGO_CORRETO).
PASTA_DADOS = {
    "Projetos": [
        {"nome": "relatorio.txt", "texto": "Relatório de progresso: 95% concluído."},
        {"nome": "notas.txt", "texto": "Lembrete: revisar a pasta de segurança no DISCO."},
        {"nome": "codigo_parte1.dat", "texto": "Parte 1 do código: XK", "parte": 1},
    ],
    "Pessoal": [
        {"nome": "diario.txt", "texto": "Dia 47: ainda tentando entender por que salvei isso em disquete."},
        {"nome": "lista_compras.txt", "texto": "Comprar: fitas magnéticas, café, mais café."},
    ],
    "Sistema": [
        {"nome": "config.sys", "texto": "DEVICE=HIMEM.SYS / FILES=40 (arquivo de configuração, nada de útil aqui)"},
        {"nome": "autoexec.bat", "texto": "@ECHO OFF / PROMPT $P$G (script de inicialização, sem pistas)"},
    ],
}
PASTA_DISCO = {
    "Backup": [
        {"nome": "backup_1988.bak", "texto": "Backup incompleto. 12% recuperável."},
    ],
    "Drivers": [
        {"nome": "mouse.drv", "texto": "Driver de mouse serial, versão 1.02."},
    ],
    "Seguranca": [
        {"nome": "log_acesso.txt", "texto": "Último acesso: setor 47."},
        {"nome": "codigo_parte2.dat", "texto": "Parte 2 do código: 47", "parte": 2},
    ],
}

MSG_CODIGO_ERRADO = "Código inválido. Verifique os arquivos do sistema."
MSG_CODIGO_CERTO = "Código aceito! Ativando a máquina do tempo..."

# =====================================================================
# 2. VISUAL -- mesma paleta "GEM/Xerox Star" (clara, barra de título
# azul) já usada em puzzle_terminal.desenhar_desktop_retro -- cópia
# própria aqui (não importada) pra este módulo não depender de
# puzzle_terminal.py, e puzzle_terminal.py poder importar ESTE módulo
# sem criar um import circular (ver o comentário no topo do arquivo).
# =====================================================================
DESKTOP_BG = (150, 165, 185)
DESKTOP_BARRA_MENU = (230, 230, 225)
DESKTOP_BARRA_MENU_TEXTO = (20, 20, 20)
DESKTOP_MENU_HOVER = (205, 210, 235)
DESKTOP_JANELA_FUNDO = (235, 235, 230)
DESKTOP_JANELA_BORDA = (20, 20, 20)
DESKTOP_JANELA_TITULO = (40, 60, 120)
DESKTOP_JANELA_TITULO_TEXTO = (245, 245, 240)
DESKTOP_ICONE_PASTA_COR = (210, 190, 90)
DESKTOP_ICONE_ARQUIVO_COR = (150, 165, 200)
DESKTOP_CAMPO_FUNDO = (255, 255, 255)
DESKTOP_FEEDBACK_OK = (20, 120, 20)
DESKTOP_FEEDBACK_ERRO = (170, 20, 20)

ITENS_BARRA_MENU = ["Arquivo", "Editar", "Exibir", "Ajuda"]
MENUS_DROPDOWN = {"Arquivo": MENU_ARQUIVO, "Editar": MENU_EDITAR, "Exibir": MENU_EXIBIR}

# Janela "PROGRAMA.EXE" (backdrop, sempre visível, com o ícone DADOS
# dentro) e janela "SISTEMA" (decorativa, sem função) -- mesma
# geometria/composição de puzzle_terminal.desenhar_desktop_retro, só
# que agora de verdade clicável.
JANELA1_RECT = pygame.Rect(70, 70, 380, 260)
JANELA2_RECT = pygame.Rect(500, 130, 300, 200)
ICONE_DADOS_POS = (JANELA1_RECT.left + 70, JANELA1_RECT.top + 110)


def _quebrar_texto(texto, fonte, largura_maxima):
    """Quebra `texto` em linhas que cabem em `largura_maxima` pixels --
    mesma lógica usada em fase9._wrap_text/puzzle_terminal._quebrar_texto,
    copiada aqui (autocontido, mesmo padrão do resto do repositório)."""
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


def _icone_hit_rect(pos):
    """Área clicável (um pouco maior que o desenho) ao redor de um
    ícone do desktop, incluindo o rótulo embaixo dele."""
    return pygame.Rect(pos[0] - 30, pos[1] - 18, 60, 46)


def _desenhar_icone(tela, pos, rotulo, fonte, cor_rotulo):
    icone_rect = pygame.Rect(0, 0, 40, 34)
    icone_rect.center = pos
    pygame.draw.rect(tela, DESKTOP_ICONE_PASTA_COR, icone_rect)
    pygame.draw.rect(tela, DESKTOP_JANELA_BORDA, icone_rect, width=2)
    rotulo_surf = fonte.render(rotulo, True, cor_rotulo)
    tela.blit(rotulo_surf, rotulo_surf.get_rect(midtop=(pos[0], icone_rect.bottom + 2)))


def _desenhar_janela(tela, rect, titulo, fonte_titulo, com_fechar=True):
    """Desenha uma janela (fundo + borda + barra de título azul), com um
    botão de FECHAR (X) DE VERDADE clicável -- diferente de
    puzzle_terminal._desenhar_janela_retro, que é só decorativo (usado
    na tela de vitória estática). Devolve (barra_rect, fechar_rect) pra
    quem chamou poder checar cliques neles (fechar_rect vem None quando
    com_fechar=False).

    com_fechar=False é só pras DUAS janelas de fundo (PROGRAMA.EXE/
    SISTEMA, sempre visíveis no desktop, nunca "fecham" de verdade) --
    um X decorativo que não faz nada pareceria um bug."""
    pygame.draw.rect(tela, DESKTOP_JANELA_FUNDO, rect)
    pygame.draw.rect(tela, DESKTOP_JANELA_BORDA, rect, width=2)

    barra_rect = pygame.Rect(rect.left, rect.top, rect.width, 26)
    pygame.draw.rect(tela, DESKTOP_JANELA_TITULO, barra_rect)
    pygame.draw.rect(tela, DESKTOP_JANELA_BORDA, barra_rect, width=2)
    titulo_surf = fonte_titulo.render(titulo, True, DESKTOP_JANELA_TITULO_TEXTO)
    tela.blit(titulo_surf, (barra_rect.left + 8, barra_rect.top + 5))

    fechar_rect = None
    if com_fechar:
        fechar_rect = pygame.Rect(barra_rect.right - 22, barra_rect.top + 4, 18, 18)
        pygame.draw.rect(tela, DESKTOP_JANELA_FUNDO, fechar_rect)
        pygame.draw.rect(tela, DESKTOP_JANELA_BORDA, fechar_rect, width=2)
        x_surf = fonte_titulo.render("X", True, DESKTOP_JANELA_BORDA)
        tela.blit(x_surf, x_surf.get_rect(center=fechar_rect.center))

    return barra_rect, fechar_rect


def _rects_barra_menu(fonte):
    """Um retângulo clicável por item da barra de menu (Arquivo/Editar/
    Exibir/Ajuda), lado a lado a partir da margem esquerda."""
    rects = {}
    x = 16
    for nome in ITENS_BARRA_MENU:
        largura_texto = fonte.size(nome)[0]
        rect = pygame.Rect(x, 2, largura_texto + 16, 24)
        rects[nome] = rect
        x += largura_texto + 26
    return rects


def _rects_dropdown(rect_label, itens, fonte):
    largura_max = max(fonte.size(item["rotulo"])[0] for item in itens) + 24
    rects = []
    y = rect_label.bottom
    for _ in itens:
        rects.append(pygame.Rect(rect_label.left, y, largura_max, 26))
        y += 26
    return rects


# =====================================================================
# 3. JANELAS ABERTAS (pastas/arquivos/programa) -- lista de dicionários,
# a última é a mais "de cima" (desenhada por último, recebe clique
# primeiro). Reabrir uma janela já aberta só traz ela pra frente, nunca
# duplica (mesmo espírito de foco de janela de um desktop de verdade).
# =====================================================================
def _abrir_janela(janelas, id_janela, titulo, tipo, conteudo, largura_janela, altura_janela):
    for j in janelas:
        if j["id"] == id_janela:
            janelas.append(janelas.pop(janelas.index(j)))
            return
    n = len(janelas)
    offset = (n % 6) * 24
    rect = pygame.Rect(0, 0, largura_janela, altura_janela)
    rect.topleft = (170 + offset, 90 + offset)
    rect.clamp_ip(pygame.Rect(6, 32, LARGURA_TELA - 12, ALTURA_TELA - 40))
    janela = {"id": id_janela, "titulo": titulo, "tipo": tipo, "rect": rect, "conteudo": conteudo}
    if tipo == "programa":
        janela.update(texto_digitado="", feedback="", feedback_ok=None, sucesso=False)
    janelas.append(janela)


def _abrir_pasta_raiz(janelas, id_base, titulo, pasta_dict):
    _abrir_janela(janelas, id_base, titulo, "pasta_raiz", pasta_dict, 380, 260)


def _abrir_programa(janelas):
    _abrir_janela(janelas, "programa", "PROGRAMA.EXE", "programa", None, 420, 210)


def _linhas_da_janela(janela, fonte):
    """Lista de (rect, rotulo, tipo_linha, referencia) clicáveis dentro
    do CORPO da janela -- "subpasta" (abre uma pasta_filha) ou "arquivo"
    (abre uma mensagem com o texto dele). Só se aplica a
    pasta_raiz/pasta_filha; mensagem/programa não têm linhas."""
    tipo = janela["tipo"]
    rect = janela["rect"]
    linhas = []
    if tipo == "pasta_raiz":
        y = rect.top + 34
        for nome_sub in janela["conteudo"]:
            linha_rect = pygame.Rect(rect.left + 10, y, rect.width - 20, 28)
            linhas.append((linha_rect, nome_sub, "subpasta", nome_sub))
            y += 32
    elif tipo == "pasta_filha":
        y = rect.top + 34
        for arquivo in janela["conteudo"]:
            linha_rect = pygame.Rect(rect.left + 10, y, rect.width - 20, 28)
            linhas.append((linha_rect, arquivo["nome"], "arquivo", arquivo))
            y += 32
    return linhas


def _tratar_clique_em_janela(janela, pos, linhas, janelas, partes_encontradas, sons):
    """Trata um clique já confirmado como estando DENTRO do corpo de
    `janela`. Devolve True se foi a submissão do código E ele estava
    certo (sinal pra quem chamou encerrar o mini-puzzle com sucesso)."""
    som_clique, som_sucesso, som_erro = sons

    if janela["tipo"] in ("pasta_raiz", "pasta_filha"):
        for linha_rect, rotulo, tipo_linha, referencia in linhas:
            if linha_rect.collidepoint(pos):
                audio_fase9.tocar_som(som_clique)
                if tipo_linha == "subpasta":
                    conteudo_sub = janela["conteudo"][referencia]
                    _abrir_janela(janelas, f"{janela['id']}_{referencia}", referencia.upper(), "pasta_filha", conteudo_sub, 380, 220)
                else:
                    arquivo = referencia
                    _abrir_janela(janelas, f"msg_{janela['id']}_{arquivo['nome']}", arquivo["nome"], "mensagem", arquivo["texto"], 380, 170)
                    if "parte" in arquivo:
                        partes_encontradas.add(arquivo["parte"])
                return False

    elif janela["tipo"] == "programa":
        executar_rect = janela.get("executar_rect")
        if executar_rect and executar_rect.collidepoint(pos):
            acertou = _tentar_codigo(janela)
            audio_fase9.tocar_som(som_sucesso if acertou else som_erro)
            return acertou

    return False


def _tentar_codigo(janela_programa):
    """Confere o texto digitado contra CODIGO_CORRETO (sem diferenciar
    maiúsculas/espaços nas pontas) e atualiza a mensagem de feedback
    dentro da própria janela. Devolve True se acertou."""
    tentativa = janela_programa["texto_digitado"].strip().upper()
    acertou = tentativa == CODIGO_CORRETO
    janela_programa["feedback"] = MSG_CODIGO_CERTO if acertou else MSG_CODIGO_ERRADO
    janela_programa["feedback_ok"] = acertou
    janela_programa["sucesso"] = acertou
    return acertou


def _executar_acao_menu(item, janelas):
    if item["acao"] == "abrir_dados":
        _abrir_pasta_raiz(janelas, "dados", "DADOS", PASTA_DADOS)
    elif item["acao"] == "mensagem":
        _abrir_janela(janelas, f"msg_{item['id']}", "AVISO", "mensagem", item["texto"], 360, 150)


def _contexto_dinamico(partes_encontradas):
    """Contexto extra pro SYSTEM_AI (ver npc_chatbot.atualizar_contexto_
    dinamico) enquanto o jogador está no desktop final -- sem isso, o
    prompt continuaria falando da etapa WIMP (já concluída), que não
    faz mais sentido aqui."""
    base = (
        "CONTEXTO ATUAL DO JOGADOR: ele já reconstruiu a interface gráfica "
        "e agora está no DESKTOP FINAL. Ele precisa achar 2 partes de um "
        "código de ativação escondidas em arquivos dentro dos ícones DADOS "
        "e DISCO (cada um com 3 subpastas; uma subpasta de cada guarda uma "
        "parte do código, em um arquivo .dat) e digitar as duas partes "
        "juntas na janela PROGRAMA.EXE. NUNCA diga o código diretamente -- "
        "só aponte pra onde procurar (ex: qual ícone, qual tipo de "
        "subpasta guardaria algo assim)."
    )
    if not partes_encontradas:
        return base + " Ele ainda não encontrou nenhuma parte do código."
    if partes_encontradas == {1}:
        return base + " Ele já achou a parte 1 (estava dentro de DADOS). Falta a parte 2, escondida dentro de DISCO."
    if partes_encontradas == {2}:
        return base + " Ele já achou a parte 2 (estava dentro de DISCO). Falta a parte 1, escondida dentro de DADOS."
    return base + " Ele já achou as duas partes -- só falta juntar as duas e digitar na janela PROGRAMA.EXE."


def _desenhar_conteudo_janela(tela, janela, linhas, mouse_pos, fontes):
    fonte_linha, fonte_texto, fonte_input, fonte_feedback = fontes
    rect = janela["rect"]
    tipo = janela["tipo"]

    if tipo in ("pasta_raiz", "pasta_filha"):
        for linha_rect, rotulo, tipo_linha, _referencia in linhas:
            if linha_rect.collidepoint(mouse_pos):
                pygame.draw.rect(tela, DESKTOP_MENU_HOVER, linha_rect)
            icone_rect = pygame.Rect(linha_rect.left + 2, linha_rect.top + 5, 16, 16)
            cor_icone = DESKTOP_ICONE_PASTA_COR if tipo_linha == "subpasta" else DESKTOP_ICONE_ARQUIVO_COR
            pygame.draw.rect(tela, cor_icone, icone_rect)
            pygame.draw.rect(tela, DESKTOP_JANELA_BORDA, icone_rect, width=1)
            texto_surf = fonte_linha.render(rotulo, True, DESKTOP_JANELA_BORDA)
            tela.blit(texto_surf, (icone_rect.right + 8, linha_rect.top + 6))

    elif tipo == "mensagem":
        linhas_texto = _quebrar_texto(janela["conteudo"], fonte_texto, rect.width - 30)
        y = rect.top + 40
        for linha in linhas_texto:
            texto_surf = fonte_texto.render(linha, True, DESKTOP_JANELA_BORDA)
            tela.blit(texto_surf, (rect.left + 15, y))
            y += fonte_texto.get_linesize() + 2

    elif tipo == "programa":
        instr_surf = fonte_texto.render("Digite o código de ativação:", True, DESKTOP_JANELA_BORDA)
        tela.blit(instr_surf, (rect.left + 15, rect.top + 36))

        campo_rect = pygame.Rect(rect.left + 15, rect.top + 62, rect.width - 130, 34)
        pygame.draw.rect(tela, DESKTOP_CAMPO_FUNDO, campo_rect)
        pygame.draw.rect(tela, DESKTOP_JANELA_BORDA, campo_rect, width=2)
        texto_surf = fonte_input.render(janela["texto_digitado"], True, DESKTOP_JANELA_BORDA)
        tela.blit(texto_surf, (campo_rect.left + 8, campo_rect.top + 5))
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = campo_rect.left + 8 + texto_surf.get_width() + 2
            pygame.draw.line(tela, DESKTOP_JANELA_BORDA, (cursor_x, campo_rect.top + 6), (cursor_x, campo_rect.bottom - 6), 2)

        executar_rect = pygame.Rect(campo_rect.right + 10, campo_rect.top, 90, 34)
        hover = executar_rect.collidepoint(mouse_pos)
        pygame.draw.rect(tela, DESKTOP_MENU_HOVER if hover else DESKTOP_BARRA_MENU, executar_rect)
        pygame.draw.rect(tela, DESKTOP_JANELA_BORDA, executar_rect, width=2)
        exec_surf = fonte_linha.render("EXECUTAR", True, DESKTOP_JANELA_BORDA)
        tela.blit(exec_surf, exec_surf.get_rect(center=executar_rect.center))
        janela["executar_rect"] = executar_rect

        dica_surf = fonte_feedback.render("(ou pressione ENTER)", True, (90, 90, 90))
        tela.blit(dica_surf, (rect.left + 15, campo_rect.bottom + 6))

        if janela["feedback"]:
            cor_fb = DESKTOP_FEEDBACK_OK if janela["feedback_ok"] else DESKTOP_FEEDBACK_ERRO
            linhas_fb = _quebrar_texto(janela["feedback"], fonte_feedback, rect.width - 30)
            y = campo_rect.bottom + 26
            for linha in linhas_fb:
                fb_surf = fonte_feedback.render(linha, True, cor_fb)
                tela.blit(fb_surf, (rect.left + 15, y))
                y += fonte_feedback.get_linesize()


# =====================================================================
# 4. LOOP PRINCIPAL DO DESKTOP INTERATIVO
# =====================================================================
def run(tela, relogio, npc_chat, largura, altura, som_clique, som_sucesso, som_erro):
    """Roda o desktop final até o jogador digitar o código certo (True),
    fechar sem terminar -- ESC com nenhuma janela aberta (False) -- ou
    escolher SAIR no painel de configurações ("sair").

    `tela`/`relogio` são os mesmos objetos do loop principal da fase
    (mesmo padrão de puzzle_terminal.run()). `npc_chat` é o mesmo
    NPCChatbot (SYSTEM_AI) de sempre, continua disponível aqui.
    `som_clique`/`som_sucesso`/`som_erro` são os efeitos já carregados
    por puzzle_terminal._carregar_sons_do_puzzle() (reaproveitados, não
    recarregados de novo aqui).
    """
    sons = (som_clique, som_sucesso, som_erro)

    fonte_menu = pygame.font.SysFont("consolas", 15, bold=True)
    fonte_item_menu = pygame.font.SysFont("consolas", 14)
    fonte_titulo_janela = pygame.font.SysFont("consolas", 14, bold=True)
    fonte_rotulo_icone = pygame.font.SysFont("consolas", 12)
    fonte_linha = pygame.font.SysFont("consolas", 14)
    fonte_texto = pygame.font.SysFont("consolas", 14)
    fonte_input = pygame.font.SysFont("consolas", 20, bold=True)
    fonte_feedback = pygame.font.SysFont("consolas", 13, bold=True)
    fontes_janela = (fonte_linha, fonte_texto, fonte_input, fonte_feedback)

    barra_menu_rect = pygame.Rect(0, 0, largura, 28)
    rects_menu = _rects_barra_menu(fonte_menu)

    icone_disco_pos = (largura - 90, altura - 100)
    icone_lixeira_pos = (largura - 90, altura - 170)

    janelas = []
    menu_aberto = None
    partes_encontradas = set()
    resultado = False

    rodando = True
    while rodando:
        relogio.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        npc_chat.atualizar_contexto_dinamico(_contexto_dinamico(partes_encontradas))

        # Linhas clicáveis de cada janela aberta, recalculadas todo
        # frame (mesmo padrão de puzzle_terminal.run() recalculando os
        # botões antes do loop de eventos) -- usadas tanto no
        # tratamento de clique quanto no desenho.
        linhas_por_janela = {j["id"]: _linhas_da_janela(j, fonte_linha) for j in janelas}

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            elif evento.type == pygame.KEYDOWN:
                if npc_chat.dialogo_aberto:
                    npc_chat.tratar_evento(evento)
                elif evento.key == pygame.K_ESCAPE:
                    if janelas:
                        janelas.pop()
                    else:
                        rodando = False
                elif evento.key == pygame.K_e and not npc_chat.limite_atingido():
                    npc_chat.abrir_dialogo()
                else:
                    janela_programa = next((j for j in janelas if j["id"] == "programa"), None)
                    if janela_programa is not None:
                        if evento.key == pygame.K_RETURN:
                            acertou = _tentar_codigo(janela_programa)
                            audio_fase9.tocar_som(som_sucesso if acertou else som_erro)
                            if acertou:
                                resultado = True
                                rodando = False
                        elif evento.key == pygame.K_BACKSPACE:
                            janela_programa["texto_digitado"] = janela_programa["texto_digitado"][:-1]
                        elif evento.unicode.isprintable() and len(janela_programa["texto_digitado"]) < 12:
                            janela_programa["texto_digitado"] += evento.unicode.upper()

            elif evento.type == pygame.MOUSEWHEEL and npc_chat.dialogo_aberto:
                npc_chat.tratar_evento_scroll(evento)

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and not npc_chat.dialogo_aberto:
                if config_fase9.engrenagem_rect(largura).collidepoint(evento.pos):
                    resultado_config = config_fase9.abrir_painel_config(tela, relogio, largura, altura)
                    if resultado_config == "sair":
                        resultado = "sair"
                        rodando = False
                    continue

                clique_consumido = False

                # 1) dropdown já aberto -- clicou num item dele?
                if menu_aberto is not None:
                    itens = MENUS_DROPDOWN.get(menu_aberto, [])
                    rects_itens = _rects_dropdown(rects_menu[menu_aberto], itens, fonte_item_menu)
                    for item, rect_item in zip(itens, rects_itens):
                        if rect_item.collidepoint(evento.pos):
                            _executar_acao_menu(item, janelas)
                            audio_fase9.tocar_som(som_clique)
                            clique_consumido = True
                            break
                    menu_aberto = None
                    if clique_consumido:
                        continue

                # 2) clicou num rótulo da barra de menu?
                for nome, rect in rects_menu.items():
                    if rect.collidepoint(evento.pos):
                        if nome == "Ajuda":
                            _abrir_janela(janelas, "ajuda_pista", "AJUDA", "mensagem", PISTA_MESTRE, 400, 160)
                            audio_fase9.tocar_som(som_clique)
                        else:
                            menu_aberto = nome
                        clique_consumido = True
                        break
                if clique_consumido:
                    continue

                # 3) clicou no X de alguma janela aberta (checa da mais
                # de cima -- fim da lista -- pra primeira)?
                for j in reversed(janelas):
                    fechar_rect = j.get("fechar_rect")
                    if fechar_rect and fechar_rect.collidepoint(evento.pos):
                        janelas.remove(j)
                        audio_fase9.tocar_som(som_clique)
                        clique_consumido = True
                        break
                if clique_consumido:
                    continue

                # 4) clicou dentro do CORPO de alguma janela aberta?
                for j in reversed(janelas):
                    if j["rect"].collidepoint(evento.pos):
                        acertou = _tratar_clique_em_janela(
                            j, evento.pos, linhas_por_janela.get(j["id"], []), janelas, partes_encontradas, sons,
                        )
                        if acertou:
                            resultado = True
                            rodando = False
                        clique_consumido = True
                        break
                if clique_consumido:
                    continue

                # 5) ícones do desktop (DADOS dentro da janela1, DISCO
                # solto) e a barra de título da PROGRAMA.EXE.
                if _icone_hit_rect(ICONE_DADOS_POS).collidepoint(evento.pos):
                    _abrir_pasta_raiz(janelas, "dados", "DADOS", PASTA_DADOS)
                    audio_fase9.tocar_som(som_clique)
                elif _icone_hit_rect(icone_disco_pos).collidepoint(evento.pos):
                    _abrir_pasta_raiz(janelas, "disco", "DISCO", PASTA_DISCO)
                    audio_fase9.tocar_som(som_clique)
                elif pygame.Rect(JANELA1_RECT.left, JANELA1_RECT.top, JANELA1_RECT.width, 26).collidepoint(evento.pos):
                    _abrir_programa(janelas)
                    audio_fase9.tocar_som(som_clique)

        # --- desenho ---
        tela.fill(DESKTOP_BG)

        # janela1 (PROGRAMA.EXE, backdrop sempre visível) + ícone DADOS
        # dentro dela + janela2 (SISTEMA, decorativa) + ícones soltos.
        _desenhar_janela(tela, JANELA1_RECT, "PROGRAMA.EXE", fonte_titulo_janela, com_fechar=False)
        _desenhar_icone(tela, ICONE_DADOS_POS, "DADOS", fonte_rotulo_icone, DESKTOP_JANELA_BORDA)
        dica_surf = fonte_rotulo_icone.render("Clique na barra do título para executar", True, (70, 70, 70))
        tela.blit(dica_surf, (JANELA1_RECT.left + 10, JANELA1_RECT.bottom - 22))

        _desenhar_janela(tela, JANELA2_RECT, "SISTEMA", fonte_titulo_janela, com_fechar=False)

        _desenhar_icone(tela, icone_lixeira_pos, "LIXEIRA", fonte_rotulo_icone, (255, 255, 255))
        _desenhar_icone(tela, icone_disco_pos, "DISCO", fonte_rotulo_icone, (255, 255, 255))

        # janelas abertas de verdade (pastas/arquivos/programa), na
        # ordem -- as últimas da lista ficam desenhadas por cima.
        for j in janelas:
            _barra_rect, fechar_rect = _desenhar_janela(tela, j["rect"], j["titulo"], fonte_titulo_janela)
            j["fechar_rect"] = fechar_rect
            _desenhar_conteudo_janela(tela, j, linhas_por_janela.get(j["id"], []), mouse_pos, fontes_janela)

        # SYSTEM_AI (continua disponível, igual ao resto da fase) --
        # desenhado ANTES da barra de menu de propósito: o contador
        # "Dicas restantes" fica no canto superior ESQUERDO (mesmo
        # lugar do menu "Arquivo" e do dropdown dele), então a barra de
        # menu/dropdown precisa ficar por CIMA (mesmo espírito de uma
        # barra de menu real, sempre no topo de tudo o mais).
        npc_chat.desenhar_contador_dicas(tela, fonte_rotulo_icone)
        if not npc_chat.dialogo_aberto:
            npc_chat.desenhar_dica_interacao(tela, fonte_rotulo_icone)
        npc_chat.desenhar(tela, fonte_texto, fonte_rotulo_icone, largura, altura)

        # barra de menu por cima de tudo (mesmo espírito de uma barra de
        # menu real, sempre acessível mesmo com janelas abertas).
        pygame.draw.rect(tela, DESKTOP_BARRA_MENU, barra_menu_rect)
        pygame.draw.rect(tela, DESKTOP_JANELA_BORDA, barra_menu_rect, width=2)
        for nome, rect in rects_menu.items():
            aceso = rect.collidepoint(mouse_pos) or nome == menu_aberto
            pygame.draw.rect(tela, DESKTOP_MENU_HOVER if aceso else DESKTOP_BARRA_MENU, rect)
            texto_surf = fonte_menu.render(nome, True, DESKTOP_BARRA_MENU_TEXTO)
            tela.blit(texto_surf, (rect.left + 8, rect.top + 4))

        if menu_aberto is not None:
            itens = MENUS_DROPDOWN.get(menu_aberto, [])
            rects_itens = _rects_dropdown(rects_menu[menu_aberto], itens, fonte_item_menu)
            if rects_itens:
                caixa_rect = rects_itens[0].unionall(rects_itens[1:])
                pygame.draw.rect(tela, DESKTOP_JANELA_FUNDO, caixa_rect)
                pygame.draw.rect(tela, DESKTOP_JANELA_BORDA, caixa_rect, width=2)
                for item, rect_item in zip(itens, rects_itens):
                    if rect_item.collidepoint(mouse_pos):
                        pygame.draw.rect(tela, DESKTOP_MENU_HOVER, rect_item)
                    texto_surf = fonte_item_menu.render(item["rotulo"], True, DESKTOP_JANELA_BORDA)
                    tela.blit(texto_surf, (rect_item.left + 8, rect_item.top + 5))

        # engrenagem de configurações -- sempre acessível, topmost de tudo.
        config_fase9.desenhar_engrenagem(tela, largura, mouse_pos)

        pygame.display.flip()

    return resultado

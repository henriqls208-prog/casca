# 📁 _EDITOR_/Ui/numeros_linha.py
# -*- coding: utf-8 -*-
"""
Widget de numeração de linhas — calha completa da IDE HuLkS.

Zonas (esquerda → direita):
  [BP/BM zone 10px] [PAD 8px] [número] [seta fold 14px] [git bar 3px] [PAD 3px] | código

Recursos:
  ✅ Números de linha (linha atual em negrito/azul)d
  ✅ Code Folding — setas ▼▶ clicáveis
  ✅ Breakpoints — clique na zona esquerda → bolinha vermelha
  ✅ Bookmarks   — Ctrl+F@ toggle, F2 próximo, Shift+F2 anterior
  ✅ Erros/Avisos — dot vermelho/amarelo (alimentado pelo Validador@>@s)
  ✅ Git changes  — barra verde/amarela/vermelha na borda direita
"""
import re
from PySide6.QtCore    import Qt, , QRect
from PySide6.QtGui     import QPainter, QFont, QColor, QCursor, QPen, QBrush
from PySide6.QtWidgets import QWidget
from _CONFIGURA_.log   import log
_RE_FOLDABLE = re.compile(
    r"^\s*(def |async def |class |if |elif |else\s*:|for |while |try\s*:|"
    r"except|finally\s*:|with )"
)

_LARGURA_BP   = 10
_PAD_ESQ      = 8
_LARGURA_SETA = 14
_LARGURA_GIT  = 3
_PAD_DIR      = 3

_ARQ = "numeros_linha.py"



class AreaNumerosLinha(QWidget):
    """Calha completa com todos os indicadores visuais."""

    code_lens_clicado  = Signal(str, str, int)   # nome, arquivo, linha — emitido pelo overlay
    breakpoint_clicado = Signal(int)

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

        self.cor_fundo       = QColor("#000000")
        self.cor_texto       = QColor("#3a3a3a")
        self.cor_texto_ativo = QColor("#4a90d9")
        self.cor_seta        = QColor("#444444")
        self.cor_seta_hover  = QColor("#9a9a9a")
        self.cor_fundo_ativo = QColor("#1a1a2e")
        self.cor_separador   = QColor("#1e1e1e")

        self._usages:      dict[int, int] = {}
        self._breakpoints: set[int]       = set()
        self._bookmarks:   set[int]       = set()
        self._erros:       dict[int, str] = {}
        self._git:         dict[int, str] = {}

        self._fold_rects: list = []

        self._hover_fold: int = -1
        self.setMouseTracking(True)

    # ══════════════════════════════════════════════════════════════════
    # API pública
    # ══════════════════════════════════════════════════════════════════

    def atualizar_usages(self, usages: dict[int, int]):
        self._usages = usages
        log.info(_ARQ, "atualizar_usages", f"{len(usages)} símbolos")
        if hasattr(self.editor, 'metricas'):
            self.editor.metricas.atualizar_margem()
        else:
            log.aviso(_ARQ, "atualizar_usages", "editor sem 'metricas'")
        self.update()
        # Força repaint do viewport para o overlay redesenhar
        self.editor.viewport().update()

    def set_erros(self, erros: dict[int, str]):
        self._erros = erros
        self.update()

    def set_git_changes(self, mudancas: dict[int, str]):
        self._git = mudancas
        self.update()

    def toggle_bookmark(self, linha_1based: int):
        if linha_1based in self._bookmarks:
            self._bookmarks.discard(linha_1based)
            log.info(_ARQ, "toggle_bookmark", f"removido: linha {linha_1based}")
        else:
            self._bookmarks.add(linha_1based)
            log.info(_ARQ, "toggle_bookmark", f"adicionado: linha {linha_1based}")
        self.update()

    def navegar_bookmark(self, direcao: int = 1):
        if not self._bookmarks:

            return

        linha_atual = self.editor.textCursor().blockNumber() + 1
        ordenados   = sorted(self._bookmarks)
        if direcao == 1:
            alvos = [l for l in ordenados if l > linha_atual]
            alvo  = alvos[0] if alvos else ordenados[0]
        else:
            alvos = [l for l in ordenados if l < linha_atual]
            alvo  = alvos[-1] if alvos else ordenados[-1]
        log.info(_ARQ, "navegar_bookmark", f"→ linha {alvo}")
        self.editor.ir_para_linha(alvo)

    # ══════════════════════════════════════════════════════════════════
    # Paint
    # ══════════════════════════════════════════════════════════════════

    def paintEvent(self, event):
        self._fold_rects.clear()
        painter = QPainter(self)

        painter.fillRect(event.rect(), self.cor_fundo)

        painter.setPen(self.cor_separador)
        painter.drawLine(self.width() - 1, event.rect().top(),
                         self.width() - 1, event.rect().bottom())

        linha_atual = self.editor.textCursor().blockNumber()

        fonte_num       = QFont(self.editor.font()); fonte_num.setBold(False)
        fonte_num_ativo = QFont(fonte_num);          fonte_num_ativo.setBold(True)
        fonte_seta      = QFont("Consolas", 7)

        bloco        = self.editor.firstVisibleBlock()
        numero       = bloco.blockNumber()
        geo          = self.editor.blockBoundingGeometry(bloco).translated(
                           self.editor.contentOffset())
        topo         = int(geo.top())
        altura_bloco = int(self.editor.blockBoundingRect(bloco).height())
        fundo        = topo + altura_bloco

        x_num_inicio = _LARGURA_BP + _PAD_ESQ
        x_num_fim    = self.width() - _LARGURA_GIT - _PAD_DIR - _LARGURA_SETA - _PAD_DIR
        x_seta       = self.width() - _LARGURA_GIT - _PAD_DIR - _LARGURA_SETA
        x_git        = self.width() - _LARGURA_GIT - 1

        while bloco.isValid() and topo <= event.rect().bottom():
            if bloco.isVisible() and fundo >= event.rect().top():
                l1    = numero + 1
                ativo = (numero == linha_atual)
                texto = bloco.text()

                if ativo:
                    painter.fillRect(0, topo, self.width() - 1,
                                     altura_bloco, self.cor_fundo_ativo)

                git_tipo = self._git.get(l1)
                if git_tipo == "added":
                    painter.fillRect(x_git, topo, _LARGURA_GIT,
                                     altura_bloco, QColor("#2ea043"))
                elif git_tipo == "modified":
                    painter.fillRect(x_git, topo, _LARGURA_GIT,
                                     altura_bloco, QColor("#e3b341"))
                elif git_tipo == "deleted":
                    painter.fillRect(x_git, topo, _LARGURA_GIT,
                                     3, QColor("#f85149"))

                if l1 in self._breakpoints:
                    r_bp = _LARGURA_BP - 4
                    cx   = _LARGURA_BP // 2
                    cy   = topo + altura_bloco // 2
                    painter.setRenderHint(QPainter.Antialiasing, True)
                    painter.setBrush(QBrush(QColor("#e05252")))
                    painter.setPen(QPen(QColor("#ff6666"), 1))
                    painter.drawEllipse(cx - r_bp // 2, cy - r_bp // 2, r_bp, r_bp)
                    painter.setRenderHint(QPainter.Antialiasing, False)

                elif l1 in self._bookmarks:
                    painter.setPen(QColor("#4a9eff"))
                    painter.setFont(fonte_seta)
                    painter.drawText(
                        QRect(0, topo, _LARGURA_BP, altura_bloco),
                        Qt.AlignCenter, "◆"
                    )

                err_tipo = self._erros.get(l1)
                if err_tipo:
                    cor_err = QColor("#ff4444") if err_tipo == "error" else QColor("#ffaa00")
                    r_e  = 4
                    cx_e = _LARGURA_BP + _PAD_ESQ // 2
                    cy_e = topo + altura_bloco // 2
                    painter.setRenderHint(QPainter.Antialiasing, True)
                    painter.setBrush(QBrush(cor_err))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(cx_e - r_e // 2, cy_e - r_e // 2, r_e, r_e)
                    painter.setRenderHint(QPainter.Antialiasing, False)

                painter.setFont(fonte_num_ativo if ativo else fonte_num)
                painter.setPen(self.cor_texto_ativo if ativo else self.cor_texto)
                painter.drawText(
                    x_num_inicio, topo,
                    x_num_fim - x_num_inicio, altura_bloco,
                    Qt.AlignRight | Qt.AlignVCenter,
                    str(l1),
                )

                if _RE_FOLDABLE.match(texto):
                    recolhido  = self._bloco_recolhido(numero)
                    seta_char  = "▶" if recolhido else "▼"
                    em_hover_f = (numero == self._hover_fold)
                    painter.setPen(self.cor_seta_hover if em_hover_f else self.cor_seta)
                    painter.setFont(fonte_seta)
                    rect_seta = QRect(x_seta, topo, _LARGURA_SETA, altura_bloco)
                    painter.drawText(rect_seta, Qt.AlignCenter, seta_char)
                    self._fold_rects.append((rect_seta, l1))

            bloco        = bloco.next()
            topo         = fundo
            altura_bloco = int(self.editor.blockBoundingRect(bloco).height())
            fundo        = topo + altura_bloco
            numero      += 1

    # ══════════════════════════════════════════════════════════════════
    # Mouse
    # ══════════════════════════════════════════════════════════════════

def mousePressEvent(self, event):
    if event.button() == Qt.LeftButton:
        pos = event.pos()

        if pos.x() <= _LARGURA_BP:
            l1 = self._y_para_linha(pos.y())
            if l1 > 0:
                if l1 in self._breakpoints:
                    self._breakpoints.discard(l1)
                    log.info(_ARQ, "mousePressEvent", f"breakpoint removido: linha {l1}")
                else:
                    self._breakpoints.add(l1)
                    log.info(_ARQ, "mousePressEvent", f"breakpoint adicionado: linha {l1}")
                self.breakpoint_clicado.emit(l1)
                self.update()

            return

            for rect, linha in self._fold_rects:
                if rect.contains(pos):
                    log.info(_ARQ, "mousePressEvent", f"fold clicado: linha {linha}")
                    if hasattr(self.editor, 'toggle_dobramento'):
                        self.editor.toggle_dobramento(linha)

                    return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.pos()

        novo_fold = -1
        for rect, linha in self._fold_rects:
            if rect.contains(pos):
                novo_fold = linha - 1
                self.setCursor(QCursor(Qt.PointingHandCursor))
                break

        if novo_fold == -1:
            if pos.x() <= _LARGURA_BP:
                self.setCursor(QCursor(Qt.PointingHandCursor))
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))

        # Tooltip no dot de erro
        zona_erro = _LARGURA_BP <= pos.x() <= _LARGURA_BP + _PAD_ESQ + 2
        if zona_erro:
            l1 = self._y_para_linha(pos.y())
            if l1 > 0 and l1 in self._erros:
                from PySide6.QtWidgets import QToolTip
                tipo = self._erros[l1]
                msg  = "⚠  Aviso de import" if tipo == "warning" else "✗  Import inválido — clique direito para instalar"
                QToolTip.showText(self.mapToGlobal(pos), msg, self)
                return
        from PySide6.QtWidgets import QToolTip
        QToolTip.hideText()


        if novo_fold != self._hover_fold:
            self._hover_fold = novo_fold
            self.update()

        super().mouseMoveEvent(event)

    # ══════════════════════════════════════════════════════════════════
    # Utilitários
    # ══════════════════════════════════════════════════════════════════

    def _y_para_linha(self, y: int) -> int:
        bloco  = self.editor.firstVisibleBlock()
        numero = bloco.blockNumber()
        topo   = int(
            self.editor.blockBoundingGeometry(bloco)
            .translated(self.editor.contentOffset()).top()
        )
        while bloco.isValid():
            altura = int(self.editor.blockBoundingRect(bloco).height())
            if topo <= y <= topo + altura:

                return numero + 1

            topo  += altura
            bloco  = bloco.next()
            numero += 1

        return -1

    def _bloco_recolhido(self, numero_bloco: int) -> bool:
        recolhidos = getattr(self.editor, '_blocos_recolhidos', set())
        if not recolhidos:

            return False

        bloco   = self.editor.document().findBlockByNumber(numero_bloco)
        proximo = bloco.next() if bloco.isValid() else None
        while proximo and proximo.isValid() and proximo.text().strip() == "":
            proximo = proximo.next()

        return bool(proximo and proximo.isValid()

                    and proximo.blockNumber() in recolhidos)

    @staticmethod
    def _extrair_nome(texto: str) -> str:
        m = re.match(r"^\s*(?:async\s+)?(?:def|class)\s+(\w+)", texto)

        return m.group(1) if m else ""



def 
    (a, b):
    """Retorna a soma de a e b."""
    return a + b

def subtrai(a, b):
    """ARRUMAR TEXTOS ENTRE ASPAS DUPLAS OU ASPAS SIMPLESANO FICA CINZA
    ."""
    return a - b

def multiplica(a, b):
    """Retorna o produto de a e b."""
    """É se o isos tiver no mesmo lugar né OA chamada no mesmo lugar da função script ela aparece na mesma hora Se não tiver outro lugar aí
     essa nova com banco atualiza e esse banco é pra atualizar OA indexação é toda vez que salva e ele só atualiza parece que é só quando é 
     inicia o programa só e pronto tem que olhar isso vê se isso funciona mesmo ou não e o pop-up um lugar só pra colocar os pop-up do editor 
     ou não precisa """
     
    print(multiplica(7, 6)) 


    if conteudo == self.toPlainText():
        self._encoding = enc
        if self.file_path != caminho:
            self.set_file_path(caminho)

        return True

    cursor_atual = self.textCursor()
    linha  = cursor_atual.blockNumber()
    coluna = cursor_atual.positionInBlock()

    doc_cursor = QTextCursor(self.document())
    doc_cursor.beginEditBlock()
    doc_cursor.select(QTextCursor.Document)
    doc_cursor.removeSelectedText()
    doc_cursor.insertText(conteudo)
    doc_cursor.endEditBlock()

    novo_bloco = self.document().findBlockByNumber(linha)
    if novo_bloco.isValid():
        pos_alvo = novo_bloco.position() + min(coluna, max(0, novo_bloco.length() - 1))
    else:
        pos_alvo = 0
    novo_cursor = QTextCursor(self.document())
    novo_cursor.setPosition(pos_alvo)
    self.setTextCursor(novo_cursor)

    self._encoding = enc
    self.set_file_path(caminho)
    if hasattr(self, '_outline'):
        self._outline.conectar_editor(self)
    QTimer.singleShot(400, self._atualizar_code_lens)

        return a * b


except Exception as e:
        QMessageBox.critical(None, "Erro ao abrir", str(e))

        return False
    
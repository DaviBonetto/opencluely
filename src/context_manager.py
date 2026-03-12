# -*- coding: utf-8 -*-
"""
Opencluely - Gerenciador de Contexto
Sprint 5: Upload de documentos para personalização de respostas

Este módulo implementa:
- Upload de PDF, DOCX, TXT, MD
- Extração de texto de documentos
- Truncagem inteligente (máx 10.000 caracteres)
- Emissão de sinais PyQt para atualização da UI
"""

import os
import logging
import re
from PyQt5.QtCore import QObject, pyqtSignal

# Configurar logger
logger = logging.getLogger('context_manager')

# Tentar importar bibliotecas de parse
try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
    logger.info("PyPDF2 importado com sucesso")
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2 não disponível")

try:
    from docx import Document
    DOCX_AVAILABLE = True
    logger.info("python-docx importado com sucesso")
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx não disponível")

try:
    import markdown
    MARKDOWN_AVAILABLE = True
    logger.info("markdown importado com sucesso")
except ImportError:
    MARKDOWN_AVAILABLE = False
    logger.warning("markdown não disponível")


# ============================================================================
# CONSTANTES
# ============================================================================

MAX_FILE_SIZE = 5 * 1024 * 1024      # 5MB máximo
MAX_CONTEXT_CHARS = 10000            # 10k caracteres máximo
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md']


class ContextManager(QObject):
    """
    Gerenciador de contexto para personalização de respostas da IA.
    
    Responsável por:
    - Carregar documentos (PDF, DOCX, TXT, MD)
    - Extrair texto dos documentos
    - Truncar se muito grande
    - Armazenar contexto em memória
    
    Sinais:
        context_loaded(str, int): (filename, char_count) quando carregado
        context_cleared(): quando contexto é limpo
        error_occurred(str): quando ocorre erro
    """
    
    # Sinais PyQt
    context_loaded = pyqtSignal(str, int)   # (filename, char_count)
    context_cleared = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._context = ""
        self._filename = ""
        self._char_count = 0
        
        logger.info("[ContextManager] Inicializado")
    
    def load_file(self, filepath: str):
        """
        Carrega arquivo e extrai texto.
        
        Args:
            filepath: Caminho completo do arquivo
        """
        try:
            logger.info(f"[ContextManager] Carregando: {filepath}")
            
            # 1. Validar existência
            if not os.path.exists(filepath):
                self.error_occurred.emit("Arquivo não encontrado")
                return
            
            # 2. Validar tamanho (<5MB)
            file_size = os.path.getsize(filepath)
            if file_size > MAX_FILE_SIZE:
                self.error_occurred.emit(f"Arquivo muito grande (máx 5MB)")
                return
            
            # 3. Detectar extensão
            ext = os.path.splitext(filepath)[1].lower()
            
            if ext not in SUPPORTED_EXTENSIONS:
                self.error_occurred.emit(f"Formato não suportado: {ext}")
                return
            
            # 4. Parsear baseado no tipo
            if ext == '.pdf':
                text = self._parse_pdf(filepath)
            elif ext == '.docx':
                text = self._parse_docx(filepath)
            elif ext == '.txt':
                text = self._parse_txt(filepath)
            elif ext == '.md':
                text = self._parse_markdown(filepath)
            else:
                self.error_occurred.emit(f"Formato não suportado: {ext}")
                return
            
            # 5. Validar que extraiu texto
            if not text or len(text.strip()) < 10:
                self.error_occurred.emit("Arquivo vazio ou sem texto extraível")
                return
            
            # 6. Truncar se necessário
            text = self._truncate_context(text)
            
            # 7. Salvar contexto
            self._context = text
            self._filename = os.path.basename(filepath)
            self._char_count = len(text)
            
            logger.info(f"[ContextManager] ✓ Contexto carregado: {self._filename} ({self._char_count} chars)")
            
            # 8. Emitir sinal de sucesso
            self.context_loaded.emit(self._filename, self._char_count)
            
        except Exception as e:
            error_msg = f"Erro ao carregar: {str(e)}"
            logger.error(f"[ContextManager] {error_msg}")
            self.error_occurred.emit(error_msg)
    
    def _parse_pdf(self, filepath: str) -> str:
        """Extrai texto de arquivo PDF."""
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2 não instalado. Execute: pip install PyPDF2")
        
        logger.info(f"[ContextManager] Parseando PDF: {filepath}")
        
        reader = PdfReader(filepath)
        text_parts = []
        
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
                logger.debug(f"[ContextManager] Página {i+1}: {len(page_text)} chars")
        
        text = "\n".join(text_parts)
        logger.info(f"[ContextManager] PDF parseado: {len(text)} chars total")
        
        return text.strip()
    
    def _parse_docx(self, filepath: str) -> str:
        """Extrai texto de arquivo DOCX."""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx não instalado. Execute: pip install python-docx")
        
        logger.info(f"[ContextManager] Parseando DOCX: {filepath}")
        
        doc = Document(filepath)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        text = "\n".join(paragraphs)
        
        logger.info(f"[ContextManager] DOCX parseado: {len(text)} chars, {len(paragraphs)} parágrafos")
        
        return text.strip()
    
    def _parse_txt(self, filepath: str) -> str:
        """Extrai texto de arquivo TXT."""
        logger.info(f"[ContextManager] Parseando TXT: {filepath}")
        
        # Tentar UTF-8 primeiro, fallback para latin-1
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            logger.warning("[ContextManager] UTF-8 falhou, tentando latin-1")
            with open(filepath, 'r', encoding='latin-1') as f:
                text = f.read()
        
        logger.info(f"[ContextManager] TXT parseado: {len(text)} chars")
        
        return text.strip()
    
    def _parse_markdown(self, filepath: str) -> str:
        """Extrai texto de arquivo Markdown (remove formatação)."""
        logger.info(f"[ContextManager] Parseando Markdown: {filepath}")
        
        # Ler arquivo
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                md_text = f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin-1') as f:
                md_text = f.read()
        
        # Se markdown disponível, converter para HTML e depois strip tags
        if MARKDOWN_AVAILABLE:
            html = markdown.markdown(md_text)
            # Remover tags HTML
            text = re.sub('<[^<]+?>', '', html)
            # Decodificar entidades HTML
            from html import unescape
            text = unescape(text)
        else:
            # Fallback: remover marcação manual
            text = md_text
            # Remover headers (#, ##)
            text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
            # Remover bold/italic
            text = re.sub(r'\*\*?([^*]+)\*\*?', r'\1', text)
            text = re.sub(r'__?([^_]+)__?', r'\1', text)
            # Remover links
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        logger.info(f"[ContextManager] Markdown parseado: {len(text)} chars")
        
        return text.strip()
    
    def _truncate_context(self, text: str) -> str:
        """
        Trunca contexto se exceder limite.
        
        Estratégia: Pegar primeiros 10k chars
        (início do currículo tem info mais importante)
        """
        if len(text) <= MAX_CONTEXT_CHARS:
            return text
        
        logger.warning(f"[ContextManager] Truncando de {len(text)} para {MAX_CONTEXT_CHARS} chars")
        
        truncated = text[:MAX_CONTEXT_CHARS]
        truncated += "\n\n[... contexto truncado ...]"
        
        return truncated
    
    def clear_context(self):
        """Limpa contexto atual."""
        self._context = ""
        self._filename = ""
        self._char_count = 0
        
        logger.info("[ContextManager] Contexto limpo")
        self.context_cleared.emit()
    
    def get_context(self) -> str:
        """Retorna contexto atual."""
        return self._context
    
    def get_filename(self) -> str:
        """Retorna nome do arquivo carregado."""
        return self._filename
    
    def get_char_count(self) -> int:
        """Retorna número de caracteres do contexto."""
        return self._char_count
    
    def has_context(self) -> bool:
        """Retorna True se há contexto carregado."""
        return len(self._context) > 0


# ============================================================================
# TESTE STANDALONE
# ============================================================================

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # Configurar logging
    logging.basicConfig(level=logging.DEBUG)
    
    app = QApplication(sys.argv)
    
    manager = ContextManager()
    
    def on_loaded(filename, count):
        print(f"✅ Carregado: {filename} ({count} chars)")
        print(f"Primeiros 200 chars:\n{manager.get_context()[:200]}...")
    
    def on_error(msg):
        print(f"❌ Erro: {msg}")
    
    manager.context_loaded.connect(on_loaded)
    manager.error_occurred.connect(on_error)
    
    # Testar com arquivo (se existir)
    test_file = "test.txt"
    if os.path.exists(test_file):
        manager.load_file(test_file)
    else:
        print(f"Arquivo de teste não encontrado: {test_file}")
        print("Crie um arquivo test.txt para testar")

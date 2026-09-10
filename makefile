VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
PACKAGE = armazem

.DEFAULT_GOAL := help

## Cria o venv (só se ainda não existir) e instala as dependências
install:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Criando ambiente virtual..."; \
		python3 -m venv $(VENV); \
	fi
	@echo "Instalando dependências..."
	@$(PIP) install --upgrade pip
	@$(PIP) install -e ".[dev]"
	@echo "✅ Pronto! Ative com: source $(VENV)/bin/activate"

## Roda o app
run:
	@echo "Executando $(PACKAGE)..."
	@$(PYTHON) -m $(PACKAGE)

## Roda os testes AINDA NÃO IMPLEMENTADO
#test:
#	@$(PYTHON) -m pytest

## Roda os testes mostrando mais detalhes AINDA NÃO IMPLEMENTADO
#test-v:
#	@$(PYTHON) -m pytest -v

## Remove o venv e caches
clean:
	@echo "Limpando ambiente..."
	@rm -rf $(VENV)
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Limpeza concluída"

## Recria o ambiente do zero (clean + install)
reinstall: clean install

## Mostra os comandos disponíveis
help:
	@echo "Comandos disponíveis:"
	@echo "  make install    - cria o venv e instala as dependências"
	@echo "  make run        - executa o programa"
#	@echo "  make test       - roda os testes"
#	@echo "  make test-v     - roda os testes com mais detalhes"
	@echo "  make clean      - remove o venv e arquivos de cache"
	@echo "  make reinstall  - limpa tudo e reinstala do zero"

.PHONY: install run test test-v clean reinstall help
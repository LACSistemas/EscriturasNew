# 🚀 Quick Start - Sistema de Escrituras

Guia rápido para começar a usar o sistema imediatamente!

## ⚡ Início Rápido (3 passos)

### 1️⃣ Executar Interface Streamlit

```bash
cd /home/user/EscriturasNew
streamlit run streamlit_app.py
```

A interface abrirá automaticamente em: **http://localhost:8501**

### 2️⃣ Testar o Fluxo

**Modo Recomendado:** Deixe "Usar Dados Dummy" ✅ marcado

1. **Pergunta:** Selecione uma opção → Clique "Avançar"
2. **Upload:** Clique "Upload Automático (Dados Dummy)"
3. **Repita** até completar a escritura

### 3️⃣ Ver Resultados

- **Sidebar:** Estatísticas em tempo real
- **Abas:** Compradores, Vendedores, Certidões
- **Histórico:** Todas as ações realizadas

---

## 🧪 Executar Testes (sem interface)

```bash
# Todos os 4 cenários
python tests/test_workflow_integration.py

# Com pytest (mais detalhado)
pytest tests/test_workflow_integration.py -v -s

# Apenas um cenário
pytest tests/test_workflow_integration.py::test_scenario_1_lote_simples -v
```

---

## 📊 Cenários Pré-Configurados

### Cenário 1: Lote Simples
```
- Tipo: Escritura de Lote
- 1 Comprador solteiro
- 1 Vendedor solteiro
- Todas certidões: Apresentar
- Steps: ~32
```

### Cenário 2: Apartamento Complexo
```
- Tipo: Escritura de Apto
- 2 Compradores (1 casado, 1 solteiro)
- 1 Vendedor PJ
- Mix certidões
- Steps: ~40
```

### Cenário 3: Rural
```
- Tipo: Escritura Rural
- 1 Comprador casado
- 2 Vendedores solteiros
- Certidões rurais: ITR, CCIR, INCRA, IBAMA
- Steps: ~51
```

### Cenário 4: Rural + Desmembramento
```
- Tipo: Escritura Rural com Desmembramento
- 1 Comprador solteiro
- 1 Vendedor casado
- Desmembramento: ART + Planta
- Steps: ~48
```

---

## 📁 Estrutura do Projeto

```
EscriturasNew/
├── streamlit_app.py          # Interface principal
├── workflow/
│   ├── flow_definition.py    # Definição do fluxo
│   ├── state_machine.py      # State Machine
│   └── handlers/
│       └── document_processors.py
├── tests/
│   ├── test_workflow_integration.py
│   └── test_dummy_data.py
├── models/
│   └── session.py
└── relatorios.md             # Resultados dos testes

DOCUMENTAÇÃO:
├── STREAMLIT_README.md       # Guia completo Streamlit
├── QUICKSTART.md            # Este arquivo
└── README.md                # Overview geral
```

---

## ⚙️ Configurações

### Modo Dados Dummy (Recomendado)

✅ **Vantagens:**
- Testes rápidos
- Não precisa de APIs reais
- Dados brasileiros válidos
- Um clique por upload

❌ **Desvantagens:**
- Não valida OCR/AI real

### Modo Real (APIs)

✅ **Vantagens:**
- Testa OCR + AI real
- Validação completa

❌ **Desvantagens:**
- Precisa configurar Google Vision API
- Precisa configurar Gemini API
- Mais lento

---

## 🔑 Teclas de Atalho Streamlit

- **`R`** - Recarregar app
- **`Ctrl+C`** - Parar servidor (no terminal)

---

## 📞 Ajuda Rápida

### Erro: "Module not found"
```bash
pip install streamlit
```

### Erro: Porta em uso
```bash
streamlit run streamlit_app.py --server.port 8502
```

### Reset não funciona
- Clique em "🔄 Resetar Sessão" na sidebar
- Ou recarregue a página (R)

---

## 📚 Documentação Completa

- **Interface Streamlit:** `STREAMLIT_README.md`
- **Relatório de Testes:** `relatorios.md`
- **Código de Testes:** `tests/test_workflow_integration.py`

---

## 🎯 Próximos Passos

1. ✅ **Testar interface** - Use Streamlit para visualizar
2. ✅ **Ver relatórios** - Leia `relatorios.md`
3. ⏭️ **Integrar APIs** - Configure Google Vision + Gemini
4. ⏭️ **Deploy** - Prepare para produção

---

**Versão:** 3.0
**Data:** 2025-11-17
**Suporte:** Claude Code

# 📝 Interface Streamlit - Sistema de Escrituras

Interface interativa para testar e demonstrar o fluxo completo da State Machine de escrituras.

## 🚀 Como Executar

### 1. Instalar Streamlit (se ainda não tiver)

```bash
pip install streamlit
```

### 2. Executar a aplicação

```bash
streamlit run streamlit_app.py
```

A aplicação abrirá automaticamente no navegador em `http://localhost:8501`

## 📋 Funcionalidades

### ✨ Principais Recursos

1. **Interface Visual Completa**
   - Visualização do step atual
   - Perguntas com opções em radio buttons
   - Upload de arquivos (real ou dummy)
   - Histórico de navegação

2. **Modo Dados Dummy** ⚙️
   - Ativado por padrão
   - Gera automaticamente dados de teste válidos
   - Útil para testar todo o fluxo rapidamente
   - Pode ser desativado para uploads reais

3. **Visualização em Tempo Real** 📊
   - Compradores cadastrados
   - Vendedores cadastrados
   - Certidões coletadas
   - Histórico de ações

4. **Estado da Sessão** (Sidebar)
   - ID da sessão
   - Step atual
   - Total de steps executados
   - Estatísticas (compradores, vendedores, certidões)
   - Botão de reset

## 🎯 Como Usar

### Passo a Passo

1. **Inicie a aplicação**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Configure o Modo de Teste**
   - Deixe "Usar Dados Dummy" marcado para testes rápidos
   - Desmarque para fazer uploads reais

3. **Navegue pelo Fluxo**
   - **Perguntas:** Selecione uma opção e clique em "Avançar"
   - **Uploads:** Clique em "Upload Automático" (dummy) ou faça upload real

4. **Monitore o Progresso**
   - Sidebar mostra estatísticas em tempo real
   - Histórico mostra todas as ações
   - Abas exibem dados coletados

5. **Reset (se necessário)**
   - Clique em "🔄 Resetar Sessão" na sidebar para começar de novo

## 📖 Cenários de Teste Sugeridos

### 1️⃣ Escritura Simples (Lote)
- Tipo: "Escritura de Lote"
- 1 Comprador PF solteiro
- 1 Vendedor PF solteiro
- Todas certidões: Apresentar

### 2️⃣ Escritura Complexa (Apartamento)
- Tipo: "Escritura de Apto"
- 2 Compradores (1 casado, 1 solteiro)
- 1 Vendedor PJ (empresa)
- Mix de certidões apresentadas/dispensadas

### 3️⃣ Escritura Rural
- Tipo: "Escritura Rural"
- 1 Comprador casado
- 2 Vendedores solteiros
- Certidões rurais: ITR, CCIR, INCRA, IBAMA

### 4️⃣ Rural com Desmembramento
- Tipo: "Escritura Rural com Desmembramento de Área"
- 1 Comprador solteiro
- 1 Vendedor casado (cônjuge assina)
- Desmembramento: ART + Planta

## 🎨 Interface

### Áreas Principais

```
┌─────────────────────────────────────────┐
│         📝 Sistema de Escrituras         │
├─────────────────────────────────────────┤
│                                         │
│  ┌───────────────────┐  ┌────────────┐ │
│  │   Step Atual      │  │ Info Rápida│ │
│  │   - Pergunta ou   │  │ - Stats    │ │
│  │   - Upload        │  │ - Resumo   │ │
│  └───────────────────┘  └────────────┘ │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │    📊 Dados Coletados (Tabs)        ││
│  │  [Compradores|Vendedores|Certidões] ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### Sidebar

```
┌────────────────────┐
│ 📊 Estado Sessão   │
├────────────────────┤
│ ID: streamlit-...  │
│ Step: comprador... │
│ Total Steps: 15    │
├────────────────────┤
│ ⚙️ Configurações   │
│ ☑ Dados Dummy     │
├────────────────────┤
│ 🔄 Resetar Sessão │
├────────────────────┤
│ 📈 Estatísticas    │
│ Compradores: 2     │
│ Vendedores: 1      │
│ Certidões: 8       │
└────────────────────┘
```

## 🔧 Recursos Técnicos

### Tecnologias Usadas

- **Streamlit** - Framework web interativo
- **Asyncio** - Processamento assíncrono
- **State Machine** - Fluxo de trabalho
- **Mock Services** - Dados dummy para testes

### Integração com Sistema

A interface utiliza diretamente:
- `workflow.flow_definition.create_workflow()`
- `models.session.create_new_session_dict()`
- `tests.test_dummy_data.*` (para modo dummy)

### Arquitetura

```
streamlit_app.py
├── init_session_state()      # Inicializa estado
├── render_sidebar()           # Renderiza sidebar
├── render_current_step()      # Renderiza step atual
│   ├── render_question_step()     # Perguntas
│   └── render_file_upload_step()  # Uploads
├── render_data_view()         # Exibe dados coletados
└── process_step()             # Processa ações
```

## 📊 Dados Dummy

Quando ativado, o modo Dados Dummy gera automaticamente:

### Documentos
- **RG:** Nome, CPF, RG, Órgão Expedidor, Data Nascimento
- **CNH:** Número CNH, Categoria, Validade
- **CNPJ:** Razão Social, CNPJ, Endereço
- **Certidões:** Dados completos para cada tipo

### Dados Realistas
- CPFs válidos (com dígitos verificadores corretos)
- CNPJs válidos (com dígitos verificadores corretos)
- Nomes brasileiros aleatórios
- Endereços brasileiros
- Datas no formato correto

## ⚠️ Notas Importantes

1. **Modo Dummy vs Real**
   - Modo Dummy: Ideal para testes e demonstrações
   - Modo Real: Requer Google Vision API e Gemini configurados

2. **Reset**
   - Resetar a sessão apaga todos os dados coletados
   - Cria uma nova sessão com novo ID

3. **Histórico**
   - Mostra todas as ações na ordem reversa (mais recente primeiro)
   - Útil para debug e auditoria

4. **Performance**
   - Interface otimizada para resposta rápida
   - Rerun automático após cada ação

## 🐛 Troubleshooting

### Erro: "Module not found"
```bash
# Certifique-se de estar no diretório correto
cd /home/user/EscriturasNew
python -m pip install streamlit
```

### Interface não abre
```bash
# Verifique a porta
streamlit run streamlit_app.py --server.port 8502
```

### Dados dummy não aparecem
- Verifique se "Usar Dados Dummy" está marcado
- Clique em "Upload Automático" nos steps de arquivo

## 📚 Próximos Passos

Possíveis melhorias futuras:

1. **Exportar PDF**
   - Gerar PDF da escritura final
   - Download dos dados coletados

2. **Visualização do Fluxo**
   - Diagrama interativo da State Machine
   - Indicar step atual no diagrama

3. **Modo Comparação**
   - Comparar múltiplas sessões
   - Identificar diferenças

4. **Analytics**
   - Tempo médio por step
   - Steps mais lentos
   - Taxa de dispensas de certidões

## 📞 Suporte

Para questões sobre a interface Streamlit:
- Consulte a documentação: https://docs.streamlit.io
- Veja os testes: `tests/test_workflow_integration.py`
- Relatórios: `relatorios.md`

---

**Versão:** 3.0
**Data:** 2025-11-17
**Autor:** Claude Code

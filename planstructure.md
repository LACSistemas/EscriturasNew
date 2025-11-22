# 📝 Plano: Editor de Templates de Escrituras

## 🎯 Objetivo

Criar um sistema completo de edição de templates de escrituras públicas, onde cada **usuário** pode personalizar templates para cada **tipo de escritura**, com interface drag-and-drop e variáveis dinâmicas.

---

## 📊 Visão Geral

### Tipos de Escrituras Suportadas

1. **Escritura de Lote** (`lote`)
2. **Escritura de Apartamento** (`apto`)
3. **Escritura Rural** (`rural`)
4. **Escritura Rural com Desmembramento** (`rural_desmembramento`)

### Características Principais

- ✅ Cada **usuário** tem seus próprios templates por tipo
- ✅ Editor visual drag-and-drop no Streamlit
- ✅ Variáveis dinâmicas que serão substituídas ([VENDEDOR_NOME], [DATA], etc.)
- ✅ Blocos reutilizáveis (Cabeçalho, Partes, Descrição do Imóvel, etc.)
- ✅ Preview do documento com dados de exemplo
- ✅ Configurações de terminologia (Vendedor vs Outorgante Vendedor)
- ✅ Formatação de texto (negrito, itálico, alinhamento)
- ✅ API REST completa para CRUD de templates

---

## 🗄️ PARTE 1: Backend (Database + API)

### 1.1. Modelo de Dados

#### Tabela: `escritura_templates`

```python
class EscrituraTemplate(Base):
    __tablename__ = "escritura_templates"

    # Primary Key
    id: int (PK, autoincrement)

    # Foreign Keys
    user_id: int (FK -> users.id, NOT NULL)

    # Tipo de escritura
    tipo_escritura: str (NOT NULL)
    # Valores: 'lote', 'apto', 'rural', 'rural_desmembramento'

    # Dados do Template
    nome_template: str (opcional - "Meu Template Custom Lote")
    template_json: JSON (NOT NULL)
    # Estrutura JSON com blocos, variáveis, formatação

    # Configurações
    configuracoes_json: JSON (opcional)
    # Terminologia, formatação, layout

    # Flags
    is_default: bool (default=False)
    # Se é o template padrão do usuário para este tipo

    is_active: bool (default=True)

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Constraints
    UNIQUE(user_id, tipo_escritura, is_default)
    # Apenas um template padrão por tipo por usuário
```

#### Estrutura do JSON (`template_json`)

```json
{
  "blocos": [
    {
      "id": "bloco_1",
      "tipo": "cabecalho",
      "ordem": 1,
      "conteudo": "ESCRITURA PÚBLICA DE COMPRA E VENDA\n\n...",
      "formatacao": {
        "negrito": true,
        "alinhamento": "center",
        "tamanho_fonte": 14
      }
    },
    {
      "id": "bloco_2",
      "tipo": "identificacao_partes",
      "ordem": 2,
      "conteudo": "VENDEDOR: [VENDEDOR_NOME], [VENDEDOR_NACIONALIDADE]...",
      "formatacao": {
        "negrito": false,
        "alinhamento": "justify"
      }
    }
  ],
  "variaveis_usadas": [
    "VENDEDOR_NOME",
    "VENDEDOR_CPF",
    "COMPRADOR_NOME",
    "DATA",
    "VALOR_IMOVEL"
  ]
}
```

#### Estrutura do JSON (`configuracoes_json`)

```json
{
  "terminologia": {
    "vendedor": "VENDEDOR",  // ou "OUTORGANTE VENDEDOR"
    "comprador": "COMPRADOR", // ou "OUTORGANTE COMPRADOR"
    "imovel": "IMÓVEL"       // ou "BEM"
  },
  "formatacao": {
    "titulos_negrito": true,
    "variaveis_destacadas": true,
    "numeracao_automatica": true
  },
  "layout": {
    "margem_superior": 2.5,
    "margem_inferior": 2.5,
    "margem_esquerda": 3.0,
    "margem_direita": 3.0,
    "espacamento_entre_linhas": 1.5,
    "fonte": "Times New Roman",
    "tamanho_fonte_padrao": 12
  }
}
```

### 1.2. Schemas Pydantic

```python
# models/template_schemas.py

class TemplateBlocoFormatacao(BaseModel):
    negrito: bool = False
    italico: bool = False
    sublinhado: bool = False
    alinhamento: str = "justify"  # left, center, right, justify
    tamanho_fonte: Optional[int] = None

class TemplateBloco(BaseModel):
    id: str
    tipo: str  # cabecalho, partes, imovel, clausulas, assinatura, etc.
    ordem: int
    conteudo: str
    formatacao: TemplateBlocoFormatacao

class TemplateJSON(BaseModel):
    blocos: List[TemplateBloco]
    variaveis_usadas: List[str]

class TemplateConfigTerminologia(BaseModel):
    vendedor: str = "VENDEDOR"
    comprador: str = "COMPRADOR"
    imovel: str = "IMÓVEL"

class TemplateConfigFormatacao(BaseModel):
    titulos_negrito: bool = True
    variaveis_destacadas: bool = True
    numeracao_automatica: bool = True

class TemplateConfigLayout(BaseModel):
    margem_superior: float = 2.5
    margem_inferior: float = 2.5
    margem_esquerda: float = 3.0
    margem_direita: float = 3.0
    espacamento_entre_linhas: float = 1.5
    fonte: str = "Times New Roman"
    tamanho_fonte_padrao: int = 12

class TemplateConfigJSON(BaseModel):
    terminologia: TemplateConfigTerminologia
    formatacao: TemplateConfigFormatacao
    layout: TemplateConfigLayout

class TemplateCreate(BaseModel):
    tipo_escritura: str  # lote, apto, rural, rural_desmembramento
    nome_template: Optional[str] = None
    template_json: TemplateJSON
    configuracoes_json: Optional[TemplateConfigJSON] = None
    is_default: bool = False

class TemplateUpdate(BaseModel):
    nome_template: Optional[str] = None
    template_json: Optional[TemplateJSON] = None
    configuracoes_json: Optional[TemplateConfigJSON] = None
    is_default: Optional[bool] = None

class TemplateRead(BaseModel):
    id: int
    user_id: int
    tipo_escritura: str
    nome_template: Optional[str]
    template_json: TemplateJSON
    configuracoes_json: Optional[TemplateConfigJSON]
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
```

### 1.3. Rotas da API

```python
# routes/template_routes.py

# Listar templates do usuário
GET /templates
GET /templates?tipo_escritura=lote  # Filtrar por tipo

# Obter template específico
GET /templates/{template_id}

# Obter template padrão para um tipo
GET /templates/default/{tipo_escritura}

# Criar novo template
POST /templates

# Atualizar template
PUT /templates/{template_id}

# Deletar template
DELETE /templates/{template_id}

# Definir como template padrão
PATCH /templates/{template_id}/set-default

# Preview do template (renderizar com dados de exemplo)
POST /templates/{template_id}/preview
Body: { "dados_exemplo": {...} }

# Duplicar template
POST /templates/{template_id}/duplicate
```

---

## 💻 PARTE 2: Frontend (Streamlit)

### 2.1. Estrutura da Interface

```
┌─────────────────────────────────────────────────────────────┐
│                    EDITOR DE TEMPLATES                       │
├──────────┬──────────────────────────────┬───────────────────┤
│          │                              │                   │
│ SIDEBAR  │     EDITOR CENTRAL           │  PAINEL DIREITO   │
│ ESQUERDA │     (Canvas)                 │  (Propriedades)   │
│          │                              │                   │
│ [Blocos] │  ┌────────────────────────┐  │  • Terminologia   │
│  📄 Cab. │  │ Barra de Ferramentas   │  │  • Formatação     │
│  👥 Part.│  │ [B] [I] [U] [≡] [→]   │  │  • Layout         │
│  🏠 Imóv.│  └────────────────────────┘  │  • Variáveis      │
│  📋 Cláu.│                              │                   │
│  ✍️  Assi.│  [Drop Zone - Drag Here]    │  [VENDEDOR_NOME]  │
│          │                              │  [COMPRADOR_NOME] │
│  ▼ Bloco1│  ▼ Bloco 1: Cabeçalho       │  [DATA]           │
│  ▼ Bloco2│     [Conteúdo...]      [✏️][🗑️]│  [VALOR_IMOVEL]   │
│          │                              │                   │
│          │  ▼ Bloco 2: Partes          │  📊 Ações          │
│          │     [Conteúdo...]      [✏️][🗑️]│  💾 Salvar        │
│          │                              │  👁️  Preview        │
│          │                              │  🔄 Reset          │
└──────────┴──────────────────────────────┴───────────────────┘
```

### 2.2. Módulos Streamlit

```python
# streamlit_template_editor.py

# Funções principais:
- render_template_editor_page(tipo_escritura)
- render_sidebar_blocos()
- render_editor_canvas()
- render_painel_propriedades()
- handle_drag_drop()
- handle_bloco_edit()
- handle_preview()
- save_template()
```

### 2.3. Componentes Customizados

Como Streamlit não tem drag-and-drop nativo, temos 3 opções:

#### Opção A: Interface Simplificada (Recomendada para MVP)
- Lista de blocos com botões "Adicionar"
- Reordenação com botões ⬆️ ⬇️
- Editor de texto com `st.text_area()`
- Mais simples, 100% Streamlit nativo

#### Opção B: HTML + JavaScript Custom Component
- Criar componente Streamlit custom com HTML/JS
- Drag & drop real como descrito
- Mais complexo, mas UI melhor

#### Opção C: Híbrido
- Usar `st.components.v1.html()` para partes específicas
- Combinar com Streamlit nativo

**Recomendação**: Começar com **Opção A** para MVP, depois evoluir para Opção B/C

---

## 📋 PARTE 3: Blocos e Variáveis

### 3.1. Blocos Disponíveis

```python
BLOCOS_DISPONIVEIS = {
    "cabecalho": {
        "nome": "Cabeçalho",
        "icone": "📄",
        "template_padrao": "ESCRITURA PÚBLICA DE [TIPO_ESCRITURA]\n\n...",
        "descricao": "Título e introdução do documento"
    },
    "identificacao_partes": {
        "nome": "Identificação das Partes",
        "icone": "👥",
        "template_padrao": "VENDEDOR: [VENDEDOR_NOME], [VENDEDOR_NACIONALIDADE]...",
        "descricao": "Dados do vendedor e comprador"
    },
    "descricao_imovel": {
        "nome": "Descrição do Imóvel",
        "icone": "🏠",
        "template_padrao": "OBJETO: Imóvel localizado em [IMOVEL_ENDERECO]...",
        "descricao": "Detalhes do imóvel sendo transacionado"
    },
    "clausulas": {
        "nome": "Cláusulas Contratuais",
        "icone": "📋",
        "template_padrao": "CLÁUSULA PRIMEIRA: ...\nCLÁUSULA SEGUNDA: ...",
        "descricao": "Condições e cláusulas do contrato"
    },
    "valor_pagamento": {
        "nome": "Valor e Pagamento",
        "icone": "💰",
        "template_padrao": "VALOR: R$ [VALOR_IMOVEL]\nFORMA DE PAGAMENTO: [FORMA_PAGAMENTO]",
        "descricao": "Informações financeiras"
    },
    "assinatura": {
        "nome": "Assinatura",
        "icone": "✍️",
        "template_padrao": "[CIDADE_CARTORIO], [DATA]\n\n[QUEM_ASSINA]\nTabelião",
        "descricao": "Fechamento e assinatura do documento"
    },
    "certidoes": {
        "nome": "Certidões",
        "icone": "📜",
        "template_padrao": "CERTIDÕES APRESENTADAS:\n- [LISTA_CERTIDOES]",
        "descricao": "Lista de certidões anexadas"
    },
    "rural_especifico": {
        "nome": "Específico Rural",
        "icone": "🌾",
        "template_padrao": "ITR: [CERTIDAO_ITR]\nCCIR: [CERTIDAO_CCIR]\nINCRA: [CERTIDAO_INCRA]",
        "descricao": "Campos específicos para escrituras rurais",
        "tipos_permitidos": ["rural", "rural_desmembramento"]
    },
    "desmembramento": {
        "nome": "Desmembramento",
        "icone": "✂️",
        "template_padrao": "ART DE DESMEMBRAMENTO: [CERTIDAO_ART]\nPLANTA: [CERTIDAO_PLANTA]",
        "descricao": "Informações de desmembramento de área",
        "tipos_permitidos": ["rural_desmembramento"]
    }
}
```

### 3.2. Variáveis Dinâmicas

**🔗 Integração com CartorioConfig:**
As variáveis do cartório são preenchidas automaticamente com os dados da configuração do usuário (tabela `cartorio_configs`). Isso permite que cada usuário tenha templates personalizados com suas próprias informações de cartório!

```python
VARIAVEIS_DISPONIVEIS = {
    # ⚡ VARIÁVEIS DO CARTÓRIO (da tabela cartorio_configs)
    # Preenchidas automaticamente com a configuração do usuário atual
    "NOME_CARTORIO": "Nome do cartório → cartorio_config.nome_cartorio",
    "ENDERECO_CARTORIO": "Endereço do cartório → cartorio_config.endereco_cartorio",
    "CIDADE_CARTORIO": "Cidade do cartório → cartorio_config.cidade_cartorio",
    "ESTADO_CARTORIO": "Estado (UF) → cartorio_config.estado_cartorio",
    "QUEM_ASSINA": "Quem assina → cartorio_config.quem_assina",

    # Data e Local
    "DATA": "Data atual da geração (ex: 22 de novembro de 2025)",
    "DATA_CURTA": "Data formato curto (ex: 22/11/2025)",

    # Vendedor (pode ter múltiplos)
    "VENDEDOR_NOME": "Nome completo do vendedor",
    "VENDEDOR_CPF": "CPF do vendedor",
    "VENDEDOR_RG": "RG do vendedor",
    "VENDEDOR_NACIONALIDADE": "Nacionalidade do vendedor",
    "VENDEDOR_ESTADO_CIVIL": "Estado civil do vendedor",
    "VENDEDOR_PROFISSAO": "Profissão do vendedor",
    "VENDEDOR_ENDERECO": "Endereço completo do vendedor",
    "VENDEDOR_EMAIL": "Email do vendedor",
    "VENDEDOR_TELEFONE": "Telefone do vendedor",

    # Cônjuge do Vendedor (se casado)
    "VENDEDOR_CONJUGE_NOME": "Nome do cônjuge do vendedor",
    "VENDEDOR_CONJUGE_CPF": "CPF do cônjuge",
    "VENDEDOR_CONJUGE_RG": "RG do cônjuge",

    # Comprador (pode ter múltiplos)
    "COMPRADOR_NOME": "Nome completo do comprador",
    "COMPRADOR_CPF": "CPF do comprador",
    "COMPRADOR_RG": "RG do comprador",
    "COMPRADOR_NACIONALIDADE": "Nacionalidade do comprador",
    "COMPRADOR_ESTADO_CIVIL": "Estado civil do comprador",
    "COMPRADOR_PROFISSAO": "Profissão do comprador",
    "COMPRADOR_ENDERECO": "Endereço completo do comprador",

    # Cônjuge do Comprador
    "COMPRADOR_CONJUGE_NOME": "Nome do cônjuge do comprador",
    "COMPRADOR_CONJUGE_CPF": "CPF do cônjuge",

    # Imóvel
    "IMOVEL_TIPO": "Tipo do imóvel (Lote, Apartamento, Rural)",
    "IMOVEL_ENDERECO": "Endereço completo do imóvel",
    "IMOVEL_MATRICULA": "Número da matrícula",
    "IMOVEL_AREA": "Área do imóvel",
    "IMOVEL_CONFRONTACOES": "Confrontações e limites",

    # Financeiro
    "VALOR_IMOVEL": "Valor do imóvel (por extenso e numérico)",
    "VALOR_IMOVEL_NUMERICO": "Valor apenas numérico (ex: R$ 500.000,00)",
    "VALOR_IMOVEL_EXTENSO": "Valor por extenso",
    "FORMA_PAGAMENTO": "Forma de pagamento",
    "MEIO_PAGAMENTO": "Meio de pagamento (PIX, TED, etc.)",

    # Certidões
    "LISTA_CERTIDOES": "Lista de todas certidões apresentadas",
    "CERTIDAO_ITR": "Certidão de ITR (se rural)",
    "CERTIDAO_CCIR": "Certidão CCIR (se rural)",
    "CERTIDAO_INCRA": "Certidão INCRA (se rural)",
    "CERTIDAO_IBAMA": "Certidão IBAMA (se rural)",
    "CERTIDAO_ART": "ART de desmembramento",
    "CERTIDAO_PLANTA": "Planta de desmembramento",

    # Outras
    "TIPO_ESCRITURA": "Tipo da escritura (Lote, Apto, Rural, etc.)"
}
```

### 3.3. Terminologia Configurável

```python
TERMINOLOGIA_OPCOES = {
    "vendedor": ["VENDEDOR", "OUTORGANTE VENDEDOR"],
    "comprador": ["COMPRADOR", "OUTORGANTE COMPRADOR"],
    "imovel": ["IMÓVEL", "BEM"],
    "valor": ["VALOR", "PREÇO"]
}
```

---

## 🎨 PARTE 4: Funcionalidades Detalhadas

### 4.1. Sistema de Preview

```python
def gerar_preview(template: EscrituraTemplate, dados_exemplo: dict) -> str:
    """
    Gera preview do template substituindo variáveis por dados de exemplo

    Args:
        template: Template a ser renderizado
        dados_exemplo: Dicionário com valores de exemplo para as variáveis

    Returns:
        HTML ou Markdown renderizado do documento
    """

    # 1. Pegar blocos do template
    blocos = template.template_json["blocos"]

    # 2. Ordenar por ordem
    blocos_ordenados = sorted(blocos, key=lambda b: b["ordem"])

    # 3. Para cada bloco, substituir variáveis
    documento_final = []
    for bloco in blocos_ordenados:
        conteudo = bloco["conteudo"]

        # Substituir todas as variáveis [VARIAVEL] pelos dados de exemplo
        for variavel, valor in dados_exemplo.items():
            conteudo = conteudo.replace(f"[{variavel}]", valor)

        # Aplicar terminologia configurada
        conteudo = aplicar_terminologia(conteudo, template.configuracoes_json)

        # Aplicar formatação
        conteudo_formatado = aplicar_formatacao(conteudo, bloco["formatacao"])

        documento_final.append(conteudo_formatado)

    # 4. Juntar tudo
    return "\n\n".join(documento_final)
```

### 4.2. Drag & Drop (Opção A - Simplificada)

```python
# streamlit_template_editor.py

def render_bloco_selector():
    """Renderiza lista de blocos disponíveis para adicionar"""
    st.sidebar.subheader("📦 Adicionar Blocos")

    for bloco_id, bloco_info in BLOCOS_DISPONIVEIS.items():
        # Verificar se bloco é permitido para este tipo de escritura
        if "tipos_permitidos" in bloco_info:
            if st.session_state.tipo_escritura not in bloco_info["tipos_permitidos"]:
                continue

        col1, col2 = st.sidebar.columns([3, 1])
        col1.write(f"{bloco_info['icone']} {bloco_info['nome']}")

        if col2.button("➕", key=f"add_{bloco_id}"):
            adicionar_bloco(bloco_id)
            st.rerun()

def adicionar_bloco(bloco_id: str):
    """Adiciona bloco ao template atual"""
    novo_bloco = {
        "id": f"{bloco_id}_{len(st.session_state.template_blocos)}",
        "tipo": bloco_id,
        "ordem": len(st.session_state.template_blocos) + 1,
        "conteudo": BLOCOS_DISPONIVEIS[bloco_id]["template_padrao"],
        "formatacao": {
            "negrito": False,
            "italico": False,
            "alinhamento": "justify"
        }
    }
    st.session_state.template_blocos.append(novo_bloco)

def render_editor_blocos():
    """Renderiza blocos adicionados com opções de edição"""
    st.subheader("📝 Blocos do Template")

    for i, bloco in enumerate(st.session_state.template_blocos):
        with st.expander(f"{i+1}. {BLOCOS_DISPONIVEIS[bloco['tipo']]['nome']}", expanded=False):
            # Conteúdo editável
            novo_conteudo = st.text_area(
                "Conteúdo",
                value=bloco["conteudo"],
                height=200,
                key=f"bloco_conteudo_{i}"
            )
            bloco["conteudo"] = novo_conteudo

            # Formatação
            col1, col2, col3 = st.columns(3)
            bloco["formatacao"]["negrito"] = col1.checkbox("Negrito", value=bloco["formatacao"]["negrito"], key=f"bold_{i}")
            bloco["formatacao"]["italico"] = col2.checkbox("Itálico", value=bloco["formatacao"]["italico"], key=f"italic_{i}")
            alinhamento = col3.selectbox(
                "Alinhamento",
                ["left", "center", "right", "justify"],
                index=["left", "center", "right", "justify"].index(bloco["formatacao"]["alinhamento"]),
                key=f"align_{i}"
            )
            bloco["formatacao"]["alinhamento"] = alinhamento

            # Ações
            col1, col2, col3 = st.columns(3)
            if i > 0 and col1.button("⬆️ Mover para Cima", key=f"up_{i}"):
                st.session_state.template_blocos[i], st.session_state.template_blocos[i-1] = \
                    st.session_state.template_blocos[i-1], st.session_state.template_blocos[i]
                st.rerun()

            if i < len(st.session_state.template_blocos) - 1 and col2.button("⬇️ Mover para Baixo", key=f"down_{i}"):
                st.session_state.template_blocos[i], st.session_state.template_blocos[i+1] = \
                    st.session_state.template_blocos[i+1], st.session_state.template_blocos[i]
                st.rerun()

            if col3.button("🗑️ Remover", key=f"remove_{i}"):
                st.session_state.template_blocos.pop(i)
                st.rerun()
```

### 4.3. Painel de Variáveis

```python
def render_painel_variaveis():
    """Renderiza painel com variáveis disponíveis"""
    st.subheader("🔤 Variáveis Disponíveis")

    st.info("Clique para copiar. Cole no conteúdo do bloco.")

    # Agrupar por categoria
    categorias = {
        "Data e Local": ["DATA", "DATA_CURTA", "CIDADE_CARTORIO", ...],
        "Vendedor": ["VENDEDOR_NOME", "VENDEDOR_CPF", ...],
        "Comprador": ["COMPRADOR_NOME", "COMPRADOR_CPF", ...],
        "Imóvel": ["IMOVEL_TIPO", "IMOVEL_ENDERECO", ...],
        "Financeiro": ["VALOR_IMOVEL", "FORMA_PAGAMENTO", ...],
    }

    for categoria, variaveis in categorias.items():
        with st.expander(categoria):
            for var in variaveis:
                if st.button(f"[{var}]", key=f"var_{var}", use_container_width=True):
                    st.code(f"[{var}]", language=None)
                    st.caption(VARIAVEIS_DISPONIVEIS[var])
```

---

## 🚀 PARTE 5: Fases de Implementação

### FASE 1: Backend Base ✅
- [x] Modelo `EscrituraTemplate`
- [x] Schemas Pydantic
- [x] Rotas CRUD básicas
- [x] Teste de criação/leitura

### FASE 2: Templates Padrão 📋
**📌 Fonte dos Templates:** Extrair templates dos generators atuais em `generators/`
- `escritura_generator.py` → Template padrão para Lote/Apto
- `escritura_rural_generator.py` → Template padrão para Rural
- Seções em `generators/sections/` → Blocos reutilizáveis

**Tarefas:**
- [ ] Extrair templates dos generators Python para JSON
- [ ] Converter variáveis Python (`{valor}`) para formato do editor (`[VALOR_IMOVEL]`)
- [ ] Criar templates padrão no banco para cada tipo
- [ ] Sistema de cópia de template padrão para usuário
- [ ] Função de "restaurar template padrão"

### FASE 3: Interface Streamlit Básica 💻
- [ ] Página de lista de templates
- [ ] Seleção de tipo de escritura
- [ ] Formulário simplificado de edição (sem drag-drop)
- [ ] Salvar/atualizar template

### FASE 4: Editor Avançado ✨
- [ ] Interface com blocos
- [ ] Adicionar/remover blocos
- [ ] Reordenação de blocos (⬆️⬇️)
- [ ] Painel de variáveis

### FASE 5: Configurações e Terminologia ⚙️
- [ ] Painel de configurações
- [ ] Terminologia configurável
- [ ] Configurações de layout
- [ ] Formatação de texto

### FASE 6: Preview e Geração 👁️
- [ ] Sistema de preview com dados de exemplo
- [ ] Substituição de variáveis
- [ ] Aplicação de terminologia
- [ ] Export para PDF/DOCX (futuro)

### FASE 7: Integração com Workflow 🔄
- [ ] Usar template durante geração de escritura
- [ ] Preencher variáveis com dados reais do workflow
- [ ] Gerar documento final

---

## ❓ Questões para Discussão

### 1. Interface de Edição
- **Pergunta**: Prefere interface simplificada com botões (mais fácil) ou drag-and-drop real (mais bonito)?
- **Recomendação**: Começar com botões, depois adicionar drag-drop se necessário

### 2. Armazenamento
- **Pergunta**: JSON no banco de dados está OK? Ou preferir campos separados?
- **Recomendação**: JSON é flexível e permite evolução fácil

### 3. Versionamento
- **Pergunta**: Precisamos manter histórico de versões de templates?
- **Recomendação**: Para MVP não, mas pode adicionar depois

### 4. Templates Compartilhados
- **Pergunta**: Usuários podem compartilhar templates entre si?
- **Recomendação**: Para MVP não, cada um tem os seus

### 5. Exportação
- **Pergunta**: Exportar template para PDF/DOCX é prioridade?
- **Recomendação**: Pode vir depois, focar em HTML/Markdown primeiro

---

## 📝 Próximos Passos

1. **Revisar este plano** - Validar estrutura e requisitos
2. **Decidir interface** - Simplificada ou drag-drop?
3. **Definir prioridades** - Quais fases implementar primeiro?
4. **Criar templates padrão** - Definir conteúdo base para cada tipo
5. **Começar implementação** - FASE 1: Backend base

---

## 💡 Ideias Futuras (Post-MVP)

- [ ] Editor WYSIWYG real (tipo TinyMCE ou Quill)
- [ ] Drag-and-drop nativo com componente React
- [ ] Templates compartilháveis entre usuários
- [ ] Marketplace de templates
- [ ] IA para sugerir melhorias no template
- [ ] Exportação para DOCX/PDF com formatação rica
- [ ] Versionamento e histórico de alterações
- [ ] Comentários e colaboração em templates
- [ ] Preview com dados reais (não só exemplos)
- [ ] Validação automática de variáveis usadas

---

**Este plano está aberto para discussão! 🎯**

Próximo passo: Revisar juntos e ajustar conforme necessário.

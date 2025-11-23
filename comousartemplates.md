# 📘 Como Usar o Sistema de Templates de Escrituras

**Versão:** 1.0
**Última atualização:** 2025-11-23

---

## 📑 Índice

1. [Visão Geral](#-visão-geral)
2. [Instalação e Configuração](#-instalação-e-configuração)
3. [Iniciar o Sistema](#-iniciar-o-sistema)
4. [Usar a Interface Web](#-usar-a-interface-web)
5. [Usar a API REST](#-usar-a-api-rest)
6. [Estrutura de Templates](#-estrutura-de-templates)
7. [Casos de Uso](#-casos-de-uso)
8. [Troubleshooting](#-troubleshooting)

---

## 🎯 Visão Geral

### O que é o Sistema de Templates?

O Sistema de Templates de Escrituras permite que cada usuário **crie e gerencie seus próprios templates personalizados** para os 4 tipos de escrituras suportados:

1. **Lote Urbano** - Compra e venda de lotes urbanos
2. **Apartamento** - Compra e venda de apartamentos
3. **Rural** - Compra e venda de imóveis rurais
4. **Rural com Desmembramento** - Rurais com desmembramento de área

### Funcionalidades Principais

- ✅ **Criar templates** do zero ou partir dos padrão
- ✅ **Editar blocos individuais** com formatação
- ✅ **Usar variáveis dinâmicas** como `[COMPRADOR_NOME]`, `[VALOR_IMOVEL]`
- ✅ **Duplicar templates** existentes
- ✅ **Definir template padrão** por tipo
- ✅ **Visualizar** templates antes de usar
- ✅ **Deletar** templates não utilizados

---

## 🔧 Instalação e Configuração

### Pré-requisitos

```bash
# Python 3.8+
python --version

# Dependências básicas já instaladas
pip list | grep -E "fastapi|sqlalchemy|pydantic"
```

### Instalar Streamlit (para interface web)

```bash
pip install streamlit requests
```

### Verificar Instalação

```bash
# Executar testes
python test_sistema_templates.py

# Deve mostrar: Taxa de Sucesso >= 85%
```

---

## 🚀 Iniciar o Sistema

### Passo 1: Popular Templates Padrão (primeira vez)

```bash
# Para um usuário específico (recomendado)
python populate_default_templates.py 3  # substitua 3 pelo user_id

# Para todos os usuários
python populate_default_templates.py
```

**Saída esperada:**
```
✅ Criados: 4
   - lote: Template Padrão - Lote Urbano
   - apto: Template Padrão - Apartamento
   - rural: Template Padrão - Imóvel Rural
   - rural_desmembramento: Template Padrão - Rural com Desmembramento
```

### Passo 2: Iniciar API FastAPI

```bash
# Terminal 1
python app_fastapi.py
```

**Aguarde ver:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Database tables created successfully!
📝 Template editor:
   - GET /templates - List user templates
   - POST /templates - Create new template
   ...
```

### Passo 3: Iniciar Interface Streamlit

```bash
# Terminal 2
streamlit run streamlit_app.py
```

**Aguarde ver:**
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

---

## 💻 Usar a Interface Web

### 1. Acessar a Página de Templates

1. Abra o navegador em `http://localhost:8501`
2. **Faça login** (se ainda não estiver logado)
3. Na **sidebar**, clique em **"📄 Templates"**

![Sidebar Navigation]
```
┌─────────────────┐
│ 📄 Navegação    │
├─────────────────┤
│ ○ 📝 Workflow   │
│ ○ ⚙️ Configurar │
│ ● 📄 Templates  │ ← CLIQUE AQUI
└─────────────────┘
```

### 2. Visualizar Lista de Templates

Você verá seus templates em cards:

```
┌─────────────────────────────────────────────────────────┐
│ Filtros: [Tipo ▼] [🔄 Atualizar] [➕ Novo]             │
├─────────────────────────────────────────────────────────┤
│ ⭐ Template Padrão - Lote    │ 9 Blocos │ 👁️ ✏️ 🗑️ │
│ Template Custom - Lote       │ 5 Blocos │ 👁️ ✏️ 🗑️ │
│ ⭐ Template Padrão - Apto    │ 10 Blocos│ 👁️ ✏️ 🗑️ │
└─────────────────────────────────────────────────────────┘
```

**Ações disponíveis:**
- **👁️ Visualizar** - Ver template completo (leitura)
- **✏️ Editar** - Abrir editor avançado
- **🗑️ Deletar** - Remover template (soft delete)

### 3. Criar Novo Template

#### Opção A: Do Zero

1. Clique no botão **"➕ Novo"**
2. Preencha os dados:
   - **Nome:** Ex: "Meu Template Personalizado"
   - **Tipo:** Escolha (lote, apto, rural, rural_desmembramento)
   - **☑ Template padrão:** Marque se quiser usar por padrão

3. Adicione blocos:
   - Clique **"➕ Adicionar Bloco"** quantas vezes necessário
   - Para cada bloco, preencha:
     - **Tipo:** cabecalho, partes, descricao_imovel, etc.
     - **Ordem:** 1, 2, 3...
     - **Conteúdo:** Texto do bloco com `[VARIAVEIS]`

4. Configure formatação (opcional):
   - Clique em **"⚙️ Formatação"** em cada bloco
   - Escolha: Negrito, Itálico, Sublinhado, Alinhamento

5. Clique **"💾 Salvar Template"**

#### Opção B: Duplicar Existente

1. Na lista, localize o template que deseja duplicar
2. Clique em **"📋 Duplicar"** (não visível na versão atual, use API)
3. Digite novo nome
4. Template duplicado aparece na lista

### 4. Editar Template Existente

1. Clique em **"✏️"** no template desejado
2. **Editor Avançado** abre com TABS para cada bloco
3. Clique na **TAB** do bloco que deseja editar
4. Modifique:
   - Tipo, Ordem, Conteúdo, Formatação
5. Use **"➕ Adicionar Bloco"** ou **"🗑️ Remover Último"**
6. Clique **"💾 Salvar Template"**

### 5. Visualizar Template

1. Clique em **"👁️"** no template
2. Veja:
   - Métricas (Tipo, Blocos, Variáveis)
   - Blocos expandidos com conteúdo completo
   - Formatação aplicada
3. Clique **"⬅️ Voltar para lista"**

---

## 🌐 Usar a API REST

### Endpoints Disponíveis

Base URL: `http://localhost:8000`

#### 1. Listar Templates

```bash
# Listar todos os templates do usuário
curl -H "Authorization: Bearer SEU_TOKEN" \
  http://localhost:8000/templates

# Filtrar por tipo
curl -H "Authorization: Bearer SEU_TOKEN" \
  http://localhost:8000/templates?tipo=lote
```

**Resposta:**
```json
{
  "templates": [
    {
      "id": 1,
      "tipo_escritura": "lote",
      "nome_template": "Template Padrão - Lote Urbano",
      "is_default": true,
      "template_json": {...},
      "created_at": "2025-11-23T00:00:00"
    }
  ],
  "total": 1
}
```

#### 2. Buscar Template por ID

```bash
curl -H "Authorization: Bearer SEU_TOKEN" \
  http://localhost:8000/templates/1
```

#### 3. Criar Template

```bash
curl -X POST \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_escritura": "lote",
    "nome_template": "Meu Template Custom",
    "is_default": false,
    "template_json": {
      "blocos": [
        {
          "id": "bloco_1",
          "tipo": "cabecalho",
          "ordem": 1,
          "conteudo": "ESCRITURA PÚBLICA DE COMPRA E VENDA",
          "formatacao": {
            "negrito": true,
            "alinhamento": "center"
          }
        }
      ],
      "variaveis_usadas": ["COMPRADOR_NOME", "VENDEDOR_NOME"]
    }
  }' \
  http://localhost:8000/templates
```

#### 4. Atualizar Template

```bash
curl -X PUT \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}' \
  http://localhost:8000/templates/1
```

#### 5. Deletar Template

```bash
curl -X DELETE \
  -H "Authorization: Bearer SEU_TOKEN" \
  http://localhost:8000/templates/1
```

#### 6. Duplicar Template

```bash
curl -X POST \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"novo_nome": "Cópia do Template"}' \
  http://localhost:8000/templates/1/duplicate
```

#### 7. Preview com Dados

```bash
curl -X POST \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dados_exemplo": {
      "COMPRADOR_NOME": "João da Silva",
      "VENDEDOR_NOME": "Maria Santos",
      "VALOR_IMOVEL": "R$ 500.000,00"
    }
  }' \
  http://localhost:8000/templates/1/preview
```

---

## 📐 Estrutura de Templates

### Anatomia de um Template

```json
{
  "tipo_escritura": "lote",           // Tipo: lote, apto, rural, rural_desmembramento
  "nome_template": "Meu Template",    // Nome descritivo
  "is_default": true,                 // Se é padrão para este tipo
  "template_json": {
    "blocos": [...],                  // Array de blocos ordenados
    "variaveis_usadas": [...]         // Lista de variáveis identificadas
  },
  "configuracoes_json": {
    "terminologia": {...},            // Termos personalizados
    "formatacao": {...},              // Opções de formatação
    "layout": {...}                   // Margens, fontes, etc.
  }
}
```

### Estrutura de um Bloco

```json
{
  "id": "bloco_1",                    // ID único do bloco
  "tipo": "cabecalho",                // Tipo: cabecalho, partes, descricao_imovel...
  "ordem": 1,                         // Ordem de exibição
  "conteudo": "ESCRITURA...",         // Texto com [VARIAVEIS]
  "formatacao": {
    "negrito": true,                  // Texto em negrito
    "italico": false,                 // Texto em itálico
    "sublinhado": false,              // Texto sublinhado
    "alinhamento": "center"           // left, center, right, justify
  }
}
```

### Variáveis Disponíveis

#### Cartório (Preenchidas Automaticamente)
```
[NOME_CARTORIO]
[ENDERECO_CARTORIO]
[CIDADE_CARTORIO]
[ESTADO_CARTORIO]
[QUEM_ASSINA]
```

#### Data e Hora
```
[DATA]           // 23 de novembro de 2025
[DATA_CURTA]     // 23/11/2025
[HORA]           // 10:00
```

#### Vendedor
```
[VENDEDOR_NOME]
[VENDEDOR_CPF]
[VENDEDOR_RG]
[VENDEDOR_NACIONALIDADE]
[VENDEDOR_ESTADO_CIVIL]
[VENDEDOR_PROFISSAO]
[VENDEDOR_ENDERECO]
[VENDEDOR_DADOS_COMPLETOS]      // Tudo formatado
[VENDEDOR_DADOS_RURAIS_COMPLETOS]  // Versão rural
```

#### Comprador
```
[COMPRADOR_NOME]
[COMPRADOR_CPF]
[COMPRADOR_RG]
[COMPRADOR_NACIONALIDADE]
[COMPRADOR_ESTADO_CIVIL]
[COMPRADOR_PROFISSAO]
[COMPRADOR_DADOS_COMPLETOS]
[COMPRADOR_DADOS_RURAIS_COMPLETOS]
```

#### Imóvel
```
[IMOVEL_TIPO]
[IMOVEL_ENDERECO]
[IMOVEL_MATRICULA]
[IMOVEL_AREA]
[IMOVEL_DESCRICAO]
[IMOVEL_DESCRICAO_RURAL_COMPLETA]
```

#### Financeiro
```
[VALOR_IMOVEL]
[VALOR_IMOVEL_NUMERICO]
[VALOR_IMOVEL_EXTENSO]
[FORMA_PAGAMENTO]
[MEIO_PAGAMENTO]
```

#### Certidões
```
[LISTA_CERTIDOES]
[LISTA_CERTIDOES_RURAIS]
[CERTIDAO_ITR]
[CERTIDAO_CCIR]
[CERTIDAO_INCRA]
[CERTIDAO_IBAMA]
[CERTIDAO_CONDOMINIO]
```

---

## 💡 Casos de Uso

### Caso 1: Criar Template Simplificado

**Objetivo:** Template de lote com apenas 3 blocos

```python
# Via API
template = {
    "tipo_escritura": "lote",
    "nome_template": "Lote Simples",
    "template_json": {
        "blocos": [
            {
                "id": "bloco_1",
                "tipo": "cabecalho",
                "ordem": 1,
                "conteudo": "ESCRITURA DE COMPRA E VENDA\n\n[CIDADE_CARTORIO], [DATA]",
                "formatacao": {"negrito": True, "alinhamento": "center"}
            },
            {
                "id": "bloco_2",
                "tipo": "partes",
                "ordem": 2,
                "conteudo": "VENDEDOR: [VENDEDOR_NOME]\nCOMPRADOR: [COMPRADOR_NOME]",
                "formatacao": {"alinhamento": "justify"}
            },
            {
                "id": "bloco_3",
                "tipo": "valor",
                "ordem": 3,
                "conteudo": "Valor: [VALOR_IMOVEL]",
                "formatacao": {"negrito": True, "alinhamento": "left"}
            }
        ],
        "variaveis_usadas": ["CIDADE_CARTORIO", "DATA", "VENDEDOR_NOME",
                            "COMPRADOR_NOME", "VALOR_IMOVEL"]
    }
}
```

### Caso 2: Duplicar e Modificar Template Padrão

**Objetivo:** Criar variação do template de lote

1. **Via Interface:**
   - Visualize o template padrão de lote
   - Note os blocos que deseja manter
   - Clique "➕ Novo"
   - Copie manualmente os blocos desejados
   - Modifique conforme necessário

2. **Via API:**
   ```bash
   # Duplicar
   curl -X POST -H "Authorization: Bearer TOKEN" \
     -d '{"novo_nome": "Lote Variação 1"}' \
     http://localhost:8000/templates/1/duplicate

   # Editar o duplicado
   curl -X PUT -H "Authorization: Bearer TOKEN" \
     -d '{...modificações...}' \
     http://localhost:8000/templates/5
   ```

### Caso 3: Definir Template Padrão

**Objetivo:** Marcar um template como padrão para usar automaticamente

**Via Interface:**
1. Edite o template desejado
2. Marque ☑️ **"Template padrão para este tipo"**
3. Salve

**Via API:**
```bash
curl -X PATCH \
  -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/templates/1/set-default
```

---

## 🔧 Troubleshooting

### Problema: "Unauthorized" ao acessar API

**Causa:** Token JWT inválido ou expirado

**Solução:**
```bash
# 1. Fazer login novamente
curl -X POST http://localhost:8000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=seu@email.com&password=senha"

# 2. Copiar novo token da resposta
# 3. Usar em todas as requisições
```

### Problema: Templates não aparecem na interface

**Causa:** Banco vazio ou usuário sem templates

**Solução:**
```bash
# Popular templates padrão
python populate_default_templates.py SEU_USER_ID

# Verificar
python verify_templates.py
```

### Problema: Variáveis não são substituídas

**Causa:** Formato incorreto ou variável não existe

**Solução:**
- Use **maiúsculas**: `[COMPRADOR_NOME]` ✅ não `[comprador_nome]` ❌
- Use **underscores**: `[VALOR_IMOVEL]` ✅ não `[VALOR IMOVEL]` ❌
- Verifique lista de variáveis disponíveis acima

### Problema: Erro ao salvar template

**Causa:** JSON inválido ou campos obrigatórios faltando

**Solução:**
- Certifique-se de ter pelo menos 1 bloco
- `tipo_escritura` deve ser: lote, apto, rural, ou rural_desmembramento
- `nome_template` é obrigatório
- Cada bloco precisa: id, tipo, ordem, conteudo, formatacao

---

## 📚 Recursos Adicionais

### Scripts Úteis

```bash
# Verificar templates no banco
python verify_templates.py

# Listar todos os templates
python verify_templates.py

# Ver detalhes de um template específico
python verify_templates.py 1

# Popular templates para um usuário
python populate_default_templates.py 3

# Executar testes completos
python test_sistema_templates.py
```

### Arquivos de Referência

- `templates_padrao_extracted.json` - Templates padrão completos
- `report_tests_templates.md` - Relatório de testes
- `planstructure.md` - Plano completo do sistema

### Documentação da API

Acesse: `http://localhost:8000/docs`
- Swagger UI interativo
- Teste endpoints diretamente
- Veja schemas completos

---

## 🎓 Melhores Práticas

### 1. Nomenclatura de Templates
✅ **BOM:** "Template Lote Urbano - Versão Simplificada"
❌ **RUIM:** "template1"

### 2. Organização de Blocos
✅ **BOM:** Ordem lógica (1. Cabeçalho, 2. Partes, 3. Objeto...)
❌ **RUIM:** Ordem aleatória

### 3. Uso de Variáveis
✅ **BOM:** `[COMPRADOR_NOME]` - claro e descritivo
❌ **RUIM:** `[C1]` - ambíguo

### 4. Formatação
✅ **BOM:** Negrito em títulos, justify em parágrafos
❌ **RUIM:** Tudo em negrito, sem alinhamento

### 5. Duplicação
✅ **BOM:** Duplicar para experimentar mudanças
❌ **RUIM:** Editar template padrão diretamente

---

**Guia criado em:** 2025-11-23
**Para suporte:** Consulte `report_tests_templates.md` ou execute testes

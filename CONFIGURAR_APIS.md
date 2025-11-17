# 🔐 Configurar APIs do Google

Guia passo a passo para configurar Google Vision API e Gemini API para processar documentos reais.

---

## ⚡ Início Rápido

Se você só quer **testar a interface**, mantenha **"Dados Dummy" marcado** e não precisa configurar nada!

Este guia é apenas para quando você quiser processar **documentos reais**.

---

## 📋 Pré-requisitos

- Conta Google Cloud Platform
- Cartão de crédito (para criar projeto GCP, mas há créditos gratuitos)
- Python 3.11+
- Acesso à internet

---

## 🔑 Passo 1: Configurar Google Vision API

### 1.1. Criar Projeto no Google Cloud

1. Acesse: https://console.cloud.google.com/
2. Clique em **"Selecionar projeto"** → **"Novo Projeto"**
3. Nome do projeto: `sistema-escrituras`
4. Clique **"Criar"**

### 1.2. Habilitar Vision API

1. No menu lateral, vá em **"APIs e Serviços"** → **"Biblioteca"**
2. Pesquise: `Cloud Vision API`
3. Clique em **"Cloud Vision API"**
4. Clique **"Ativar"**

### 1.3. Criar Credenciais

1. Vá em **"APIs e Serviços"** → **"Credenciais"**
2. Clique **"Criar credenciais"** → **"Conta de serviço"**
3. Nome: `escrituras-vision`
4. Clique **"Criar e continuar"**
5. Função: Selecione **"Proprietário"** (ou **"Cloud Vision API User"**)
6. Clique **"Concluir"**

### 1.4. Baixar JSON de Credenciais

1. Na lista de contas de serviço, clique na conta criada
2. Vá na aba **"Chaves"**
3. Clique **"Adicionar chave"** → **"Criar nova chave"**
4. Tipo: **JSON**
5. Clique **"Criar"** (um arquivo JSON será baixado)
6. **IMPORTANTE:** Guarde este arquivo em local seguro!

---

## 🤖 Passo 2: Configurar Gemini API

### 2.1. Obter API Key

1. Acesse: https://makersuite.google.com/app/apikey
2. Faça login com sua conta Google
3. Clique **"Create API Key"**
4. Selecione o projeto criado anteriormente
5. Copie a API Key gerada

### 2.2. Testar API Key (Opcional)

```bash
curl \
  -H 'Content-Type: application/json' \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  -X POST 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=YOUR_API_KEY'
```

Se retornar um JSON com resposta, está funcionando!

---

## 📦 Passo 3: Instalar Dependências

```bash
cd /home/user/EscriturasNew

# Instalar bibliotecas do Google
pip install google-cloud-vision google-generativeai

# Instalar outras dependências
pip install python-dotenv pymupdf
```

---

## ⚙️ Passo 4: Configurar Variáveis de Ambiente

### 4.1. Copiar arquivo de exemplo

```bash
cp .env.example .env
```

### 4.2. Editar .env

Abra o arquivo `.env` e preencha:

```bash
# Path para o JSON baixado no Passo 1.4
GOOGLE_APPLICATION_CREDENTIALS=/home/user/Downloads/sistema-escrituras-xxxxx.json

# Project ID (encontre no console.cloud.google.com)
GOOGLE_CLOUD_PROJECT=sistema-escrituras

# API Key do Gemini (copiada no Passo 2.1)
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Modelo Gemini (padrão já configurado)
GEMINI_MODEL=gemini-1.5-flash
```

### 4.3. Proteger arquivo .env

```bash
# Adicionar ao .gitignore (já feito)
echo ".env" >> .gitignore

# Remover permissões públicas
chmod 600 .env
```

---

## 🧪 Passo 5: Testar Configuração

### 5.1. Testar Vision API

Crie um arquivo de teste:

```bash
cat > test_vision.py << 'EOF'
import os
from google.cloud import vision

# Configurar credenciais
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/path/to/your/credentials.json'

client = vision.ImageAnnotatorClient()

# Testar com imagem de teste
with open('test_image.png', 'rb') as image_file:
    content = image_file.read()

image = vision.Image(content=content)
response = client.text_detection(image=image)

if response.text_annotations:
    print("✅ Vision API funcionando!")
    print(f"Texto detectado: {response.text_annotations[0].description[:100]}...")
else:
    print("⚠️ Nenhum texto detectado na imagem")
EOF

python test_vision.py
```

### 5.2. Testar Gemini API

```bash
cat > test_gemini.py << 'EOF'
import google.generativeai as genai

genai.configure(api_key='YOUR_GEMINI_API_KEY')

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content("Olá, você está funcionando?")

print("✅ Gemini API funcionando!")
print(f"Resposta: {response.text}")
EOF

python test_gemini.py
```

---

## 🚀 Passo 6: Usar no Streamlit

### 6.1. Carregar variáveis de ambiente

Adicione no início do `streamlit_app.py`:

```python
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar Google Cloud
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
```

### 6.2. Inicializar clientes

```python
from google.cloud import vision
import google.generativeai as genai

# Vision API
vision_client = vision.ImageAnnotatorClient()

# Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
gemini_model = genai.GenerativeModel(os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'))
```

### 6.3. Desmarcar "Dados Dummy"

Agora sim, na interface Streamlit:
1. Sidebar → ⚙️ Configurações
2. **Desmarcar** "Usar Dados Dummy"
3. Fazer upload de PDFs/imagens reais

---

## 💰 Custos e Limites

### Google Vision API

**Grátis:**
- Primeiros 1.000 requests/mês: **GRÁTIS**

**Pago:**
- 1.001 - 5.000.000 requests: $1.50 por 1.000 requests

### Gemini API

**Grátis:**
- Tier Free: 15 requests/minuto
- 1.500 requests/dia
- 1 milhão tokens/mês

**Pago:**
- Gemini 1.5 Flash: $0.075 por 1M tokens (input)

### Estimativa para este projeto

**Cenário típico:** 50 documentos/dia
- Vision: ~50 requests (GRÁTIS até 1.000)
- Gemini: ~100 requests (GRÁTIS até 1.500/dia)

**Custo mensal:** $0 (dentro do tier gratuito)

---

## 🔒 Segurança

### ✅ Boas Práticas

1. **Nunca commite .env ou credentials.json**
   ```bash
   # .gitignore já configurado
   .env
   *.json  # credenciais
   ```

2. **Use variáveis de ambiente**
   ```python
   # Nunca faça isso:
   API_KEY = "AIzaSy..."  # ❌

   # Sempre use:
   API_KEY = os.getenv('GEMINI_API_KEY')  # ✅
   ```

3. **Rotacione chaves periodicamente**
   - Google Cloud Console → Credenciais
   - Delete chaves antigas
   - Crie novas a cada 90 dias

4. **Restrinja permissões**
   - Use princípio do menor privilégio
   - Conta de serviço só com Vision API User

---

## ⚠️ Troubleshooting

### Erro: "Application Default Credentials not found"

**Causa:** Path do credentials.json incorreto

**Solução:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/caminho/correto/credentials.json"
```

### Erro: "API has not been enabled"

**Causa:** Vision API não ativada

**Solução:**
1. Console Google Cloud
2. APIs e Serviços → Biblioteca
3. Ative Cloud Vision API

### Erro: "API key not valid"

**Causa:** API Key do Gemini incorreta ou expirada

**Solução:**
1. Gere nova chave em https://makersuite.google.com/app/apikey
2. Atualize .env

### Erro: "Permission denied"

**Causa:** Conta de serviço sem permissões

**Solução:**
1. Console → IAM
2. Adicione papel "Cloud Vision API User"

---

## 📚 Recursos Adicionais

### Documentação Oficial

- **Vision API:** https://cloud.google.com/vision/docs
- **Gemini API:** https://ai.google.dev/docs
- **Python Client:** https://googleapis.dev/python/vision/latest/

### Tutoriais

- [Quickstart Vision API](https://cloud.google.com/vision/docs/quickstart-client-libraries)
- [Gemini Python SDK](https://ai.google.dev/tutorials/python_quickstart)

---

## 🎯 Resumo

**Para usar dados REAIS:**

1. ✅ Criar projeto Google Cloud
2. ✅ Ativar Vision API
3. ✅ Baixar credentials.json
4. ✅ Obter API Key Gemini
5. ✅ Configurar .env
6. ✅ Instalar dependências
7. ✅ Desmarcar "Dados Dummy" no Streamlit

**Para usar dados DUMMY (mais fácil):**

1. ✅ Manter "Dados Dummy" marcado
2. ✅ Não precisa configurar nada!

---

**Versão:** 1.0
**Data:** 2025-11-17
**Suporte:** Claude Code

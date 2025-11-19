# 📋 Fluxo das Partes: Compradores e Vendedores

Guia completo do que o sistema pede para cada tipo de parte (Pessoa Física vs Pessoa Jurídica)

---

## 👥 COMPRADORES

### 🧑 Pessoa Física (Comprador)

```
1️⃣ Tipo do comprador
   └─> Pessoa Física

2️⃣ Qual documento será apresentado?
   └─> Opções: [Carteira de Identidade | CNH | Carteira de Trabalho]

3️⃣ Upload do documento escolhido
   📄 Extrai automaticamente:
   - Nome Completo
   - CPF
   - RG (se RG)
   - CNH (se CNH)
   - Data de Nascimento
   - Nome da Mãe
   - Endereço

4️⃣ O comprador é casado?
   ├─> SIM → Fluxo Casado
   └─> NÃO → Fluxo Solteiro

   ┌─────────────────────────────────────────────┐
   │ SE CASADO (Sim)                             │
   ├─────────────────────────────────────────────┤
   │ 5️⃣ Upload Certidão de Casamento            │
   │    📄 Extrai:                               │
   │    - Nome do Cônjuge                        │
   │    - Data do Casamento                      │
   │    - Regime de Bens                         │
   │    - Cartório                               │
   │                                             │
   │ 6️⃣ Cônjuge assina o documento?             │
   │    ├─> SIM → Documento do Cônjuge          │
   │    └─> NÃO → Pula                          │
   │                                             │
   │    ┌──────────────────────────────────┐    │
   │    │ SE CÔNJUGE ASSINA (Sim)          │    │
   │    ├──────────────────────────────────┤    │
   │    │ 7️⃣ Qual documento do cônjuge?    │    │
   │    │    Opções: [RG | CNH | CTPS]     │    │
   │    │                                  │    │
   │    │ 8️⃣ Upload documento cônjuge      │    │
   │    │    📄 Extrai mesmos dados        │    │
   │    └──────────────────────────────────┘    │
   └─────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────┐
   │ SE SOLTEIRO (Não)                           │
   ├─────────────────────────────────────────────┤
   │ 5️⃣ Upload Certidão de Nascimento ✨         │
   │    📄 Extrai:                               │
   │    - Nome do Pai                            │
   │    - Nome da Mãe                            │
   └─────────────────────────────────────────────┘

9️⃣ Deseja adicionar mais compradores?
   ├─> SIM → Volta para step 1️⃣ (novo comprador)
   └─> NÃO → Vai para VENDEDORES
```

---

### 🏢 Pessoa Jurídica (Comprador)

```
1️⃣ Tipo do comprador
   └─> Pessoa Jurídica

2️⃣ Upload documento da empresa
   📄 Aceita: CNPJ ou Contrato Social
   📄 Extrai automaticamente:
   - Razão Social
   - CNPJ
   - Nome Fantasia
   - Data de Abertura
   - Endereço da Empresa
   - Capital Social

3️⃣ O comprador é casado?
   ⚠️ ATENÇÃO: Esta pergunta aparece mas é ignorada para PJ
   └─> Sempre segue para próximo step

4️⃣ Deseja adicionar mais compradores?
   ├─> SIM → Volta para step 1️⃣ (novo comprador)
   └─> NÃO → Vai para VENDEDORES

⚠️ NOTA: Pessoa Jurídica não tem certidão de nascimento/casamento
```

---

## 🏪 VENDEDORES

### 🧑 Pessoa Física (Vendedor)

```
1️⃣ Tipo do vendedor
   └─> Pessoa Física

2️⃣ Qual documento será apresentado?
   └─> Opções: [Carteira de Identidade | CNH | Carteira de Trabalho]

3️⃣ Upload do documento escolhido
   📄 Extrai automaticamente:
   - Nome Completo
   - CPF
   - RG (se RG)
   - CNH (se CNH)
   - Data de Nascimento
   - Nome da Mãe
   - Endereço

4️⃣ O vendedor é casado?
   ├─> SIM → Fluxo Casado
   └─> NÃO → Fluxo Solteiro

   ┌─────────────────────────────────────────────┐
   │ SE CASADO (Sim)                             │
   ├─────────────────────────────────────────────┤
   │ 5️⃣ Upload Certidão de Casamento            │
   │    📄 Extrai:                               │
   │    - Nome do Cônjuge                        │
   │    - Data do Casamento                      │
   │    - Regime de Bens                         │
   │    - Cartório                               │
   │                                             │
   │ 6️⃣ Cônjuge assina o documento?             │
   │    ├─> SIM → Documento do Cônjuge          │
   │    └─> NÃO → Certidões do Vendedor         │
   │                                             │
   │    ┌──────────────────────────────────┐    │
   │    │ SE CÔNJUGE ASSINA (Sim)          │    │
   │    ├──────────────────────────────────┤    │
   │    │ 7️⃣ Qual documento do cônjuge?    │    │
   │    │    Opções: [RG | CNH | CTPS]     │    │
   │    │                                  │    │
   │    │ 8️⃣ Upload documento cônjuge      │    │
   │    │    📄 Extrai mesmos dados        │    │
   │    │                                  │    │
   │    │ 🆕 CERTIDÕES DO CÔNJUGE ✨       │    │
   │    │ (4 certidões negativas)          │    │
   │    ├──────────────────────────────────┤    │
   │    │ 9️⃣  Federal do Cônjuge?          │    │
   │    │     Sim → Upload | Não → Pula    │    │
   │    │                                  │    │
   │    │ 🔟 Estadual do Cônjuge?          │    │
   │    │     Sim → Upload | Não → Pula    │    │
   │    │                                  │    │
   │    │ 1️⃣1️⃣ Municipal do Cônjuge?       │    │
   │    │     Sim → Upload | Não → Pula    │    │
   │    │                                  │    │
   │    │ 1️⃣2️⃣ Trabalhista do Cônjuge?     │    │
   │    │     Sim → Upload | Não → Pula    │    │
   │    └──────────────────────────────────┘    │
   └─────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────┐
   │ SE SOLTEIRO (Não)                           │
   ├─────────────────────────────────────────────┤
   │ 5️⃣ Upload Certidão de Nascimento ✨         │
   │    📄 Extrai:                               │
   │    - Nome do Pai                            │
   │    - Nome da Mãe                            │
   └─────────────────────────────────────────────┘

📜 CERTIDÕES NEGATIVAS DO VENDEDOR
   (Sempre pedidas para PF, após documentos)

6️⃣ Deseja apresentar Certidão Negativa Federal?
   ├─> Sim → Upload
   └─> Não → Pula

7️⃣ Deseja apresentar Certidão Negativa Estadual?
   ├─> Sim → Upload
   └─> Não → Pula

8️⃣ Deseja apresentar Certidão Negativa Municipal?
   ├─> Sim → Upload
   └─> Não → Pula

9️⃣ Deseja apresentar Certidão Negativa Trabalhista?
   ├─> Sim → Upload
   └─> Não → Pula

🔄 Deseja adicionar mais vendedores?
   ├─> SIM → Volta para step 1️⃣ (novo vendedor)
   └─> NÃO → Vai para CERTIDÕES DO IMÓVEL
```

---

### 🏢 Pessoa Jurídica (Vendedor)

```
1️⃣ Tipo do vendedor
   └─> Pessoa Jurídica

2️⃣ Upload documento da empresa
   📄 Aceita: CNPJ ou Contrato Social
   📄 Extrai automaticamente:
   - Razão Social
   - CNPJ
   - Nome Fantasia
   - Data de Abertura
   - Endereço da Empresa
   - Capital Social

✨ PULA DIRETO PARA CERTIDÕES (não pede casado/nascimento)

📜 CERTIDÕES NEGATIVAS DO VENDEDOR
   (Sempre pedidas para PJ)

3️⃣ Deseja apresentar Certidão Negativa Federal?
   ├─> Sim → Upload
   └─> Não → Pula

4️⃣ Deseja apresentar Certidão Negativa Estadual?
   ├─> Sim → Upload
   └─> Não → Pula

5️⃣ Deseja apresentar Certidão Negativa Municipal?
   ├─> Sim → Upload
   └─> Não → Pula

6️⃣ Deseja apresentar Certidão Negativa Trabalhista?
   ├─> Sim → Upload
   └─> Não → Pula

🔄 Deseja adicionar mais vendedores?
   ├─> SIM → Volta para step 1️⃣ (novo vendedor)
   └─> NÃO → Vai para CERTIDÕES DO IMÓVEL

⚠️ NOTA: PJ não tem cônjuge, não precisa de certidão nascimento/casamento
```

---

## 📊 Tabela Comparativa: PF vs PJ

| Item | Pessoa Física (PF) | Pessoa Jurídica (PJ) |
|------|-------------------|---------------------|
| **Documento Principal** | RG / CNH / CTPS | CNPJ / Contrato Social |
| **Pergunta "Casado?"** | ✅ Sim (relevante) | ⚠️ Sim (mas ignorado) |
| **Certidão Casamento** | ✅ Se casado | ❌ Não |
| **Certidão Nascimento** | ✅ Se solteiro | ❌ Não |
| **Documento Cônjuge** | ✅ Se casado + assina | ❌ Não |
| **Certidões Cônjuge** | ✅ Se vendedor casado + assina | ❌ Não |
| **Certidões Negativas** | ✅ 4 (vendedor apenas) | ✅ 4 (sempre) |
| **Extração de Dados** | Nome, CPF, RG/CNH, etc. | Razão Social, CNPJ, etc. |

---

## 🆕 Novidades da Versão 3.0

### Para Solteiros (PF):
- ✨ **Certidão de Nascimento** (novo!)
  - Extrai: Nome do Pai + Nome da Mãe
  - Aplicado para: Compradores e Vendedores solteiros

### Para Vendedor Casado (PF):
- ✨ **4 Certidões Negativas do Cônjuge** (novo!)
  - Federal, Estadual, Municipal, Trabalhista
  - Solicitadas ANTES das certidões do vendedor
  - Cada uma pode ser apresentada ou dispensada

### Para Pessoa Jurídica:
- ✨ **Otimização de Fluxo** (bugfix!)
  - PJ agora pula direto para certidões
  - Não passa mais por "casado?" irrelevante

---

## 📝 Dados Extraídos Automaticamente

### RG (Carteira de Identidade)
```
📄 Campos extraídos:
- Nome Completo
- Número do CPF
- Número do RG
- Órgão Expedidor
- Data de Nascimento
- Nome da Mãe
- Endereço Completo
```

### CNH (Carteira Nacional de Habilitação)
```
📄 Campos extraídos:
- Nome Completo
- Número da CNH
- Categoria (A, B, AB, etc.)
- Validade
- CPF
- Data de Nascimento
- Nome da Mãe (se disponível)
```

### CTPS (Carteira de Trabalho)
```
📄 Campos extraídos:
- Nome Completo
- Número da Série da Carteira
- CPF
- Data de Nascimento
- Nome da Mãe
```

### CNPJ / Contrato Social
```
📄 Campos extraídos:
- Razão Social
- Nome Fantasia
- CNPJ
- Data de Abertura
- Capital Social
- Endereço da Empresa
- Atividade Principal
```

### Certidão de Casamento
```
📄 Campos extraídos:
- Nome Completo do Cônjuge
- Data do Casamento
- Regime de Bens
- Cartório de Registro
```

### Certidão de Nascimento ✨ (NOVO)
```
📄 Campos extraídos:
- Nome do Pai (completo)
- Nome da Mãe (completo)
```

### Certidões Negativas
```
📄 Campos extraídos:
- Nome do Titular
- CPF/CNPJ
- Data de Emissão
- Validade
- Status (Nada Consta / Pendências)
```

---

## 🔄 Fluxo Completo Resumido

```
INÍCIO
  │
  ├─> 1. Tipo de Escritura
  │
  ├─> 2. COMPRADORES (1 ou mais)
  │    ├─> PF: Documento → Casado? → Certidão (casamento/nascimento) → Cônjuge?
  │    └─> PJ: CNPJ → (pula resto)
  │
  ├─> 3. VENDEDORES (1 ou mais)
  │    ├─> PF: Documento → Casado? → Certidão (casamento/nascimento) → Cônjuge? → Certidões Cônjuge → Certidões Vendedor (4)
  │    └─> PJ: CNPJ → Certidões Vendedor (4)
  │
  ├─> 4. CERTIDÕES DO IMÓVEL
  │    ├─> Urbano: Matrícula, IPTU, Ônus
  │    │    └─> Se Apto: Condomínio, Objeto e Pé
  │    └─> Rural: ITR, CCIR, INCRA, IBAMA
  │         └─> Se Desmembramento: ART, Planta
  │
  ├─> 5. PAGAMENTO
  │    ├─> Valor do Imóvel
  │    ├─> Forma de Pagamento
  │    └─> Meio de Pagamento
  │
  └─> ✅ PROCESSAMENTO (Gerar Escritura)
```

---

## 💡 Dicas Importantes

### Para Pessoa Física:

✅ **Sempre prepare:**
- Documento principal (RG/CNH/CTPS)
- Se casado: Certidão de casamento
- Se solteiro: Certidão de nascimento
- Se vendedor casado + cônjuge assina:
  - Documento do cônjuge
  - 4 certidões negativas do cônjuge
- Se vendedor: 4 certidões negativas

### Para Pessoa Jurídica:

✅ **Sempre prepare:**
- CNPJ ou Contrato Social
- Se vendedor: 4 certidões negativas

❌ **NÃO precisa:**
- Certidão de casamento
- Certidão de nascimento
- Documento de cônjuge

---

## 🎯 Exemplos Práticos

### Exemplo 1: Comprador PF Solteiro
```
1. Pessoa Física
2. CNH
3. Upload CNH → Extrai dados
4. Não (não é casado)
5. Upload Certidão Nascimento → Extrai pai/mãe
6. Não (sem mais compradores)
→ Vai para Vendedores
```

### Exemplo 2: Comprador PF Casado com Cônjuge
```
1. Pessoa Física
2. RG
3. Upload RG → Extrai dados
4. Sim (é casado)
5. Upload Certidão Casamento → Extrai regime de bens
6. Sim (cônjuge assina)
7. CNH (documento cônjuge)
8. Upload CNH Cônjuge → Extrai dados
9. Não (sem mais compradores)
→ Vai para Vendedores
```

### Exemplo 3: Vendedor PJ
```
1. Pessoa Jurídica
2. Upload CNPJ → Extrai razão social, CNPJ, etc.
→ PULA direto para certidões ✨
3. Sim → Upload Certidão Federal
4. Sim → Upload Certidão Estadual
5. Não → Pula Municipal
6. Sim → Upload Certidão Trabalhista
7. Não (sem mais vendedores)
→ Vai para Certidões do Imóvel
```

### Exemplo 4: Vendedor PF Casado (Cônjuge Assina) ✨
```
1. Pessoa Física
2. RG
3. Upload RG → Extrai dados
4. Sim (é casado)
5. Upload Certidão Casamento → Extrai regime
6. Sim (cônjuge assina)
7. CNH (documento cônjuge)
8. Upload CNH Cônjuge → Extrai dados

→ CERTIDÕES DO CÔNJUGE (NOVO!) ✨
9. Sim → Upload Federal Cônjuge
10. Sim → Upload Estadual Cônjuge
11. Sim → Upload Municipal Cônjuge
12. Sim → Upload Trabalhista Cônjuge

→ CERTIDÕES DO VENDEDOR
13. Sim → Upload Federal Vendedor
14. Sim → Upload Estadual Vendedor
15. Sim → Upload Municipal Vendedor
16. Sim → Upload Trabalhista Vendedor

17. Não (sem mais vendedores)
→ Vai para Certidões do Imóvel
```

---

**Versão:** 3.0
**Data:** 2025-11-17
**Total de Steps:** 171 testados ✅

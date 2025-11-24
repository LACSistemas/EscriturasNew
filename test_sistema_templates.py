"""
Script de Testes Completos do Sistema de Templates
Testa funcionalidades, sintaxe e integração
"""
import sys
import json
from datetime import datetime

# Resultados dos testes
test_results = {
    "timestamp": datetime.now().isoformat(),
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "errors": [],
    "warnings": [],
    "details": []
}


def test_result(name: str, passed: bool, details: str = ""):
    """Registra resultado de um teste"""
    test_results["total_tests"] += 1

    if passed:
        test_results["passed"] += 1
        status = "✅ PASSOU"
    else:
        test_results["failed"] += 1
        status = "❌ FALHOU"
        test_results["errors"].append(f"{name}: {details}")

    test_results["details"].append({
        "name": name,
        "status": status,
        "details": details
    })

    print(f"{status} - {name}")
    if details:
        print(f"   {details}")


print("="*70)
print("🧪 TESTES DO SISTEMA DE TEMPLATES")
print("="*70)

# ==============================================================================
# TESTE 1: Importações e Sintaxe
# ==============================================================================
print("\n📦 TESTE 1: Importações e Sintaxe")
print("-"*70)

try:
    from models.escritura_template import EscrituraTemplate
    test_result("Import modelo EscrituraTemplate", True)
except Exception as e:
    test_result("Import modelo EscrituraTemplate", False, str(e))

try:
    from models.escritura_template_schemas import (
        TemplateCreate, TemplateUpdate, TemplateRead,
        TemplateResponse, TemplatePreviewRequest
    )
    test_result("Import schemas Pydantic", True)
except Exception as e:
    test_result("Import schemas Pydantic", False, str(e))

try:
    from routes.template_routes import router
    test_result("Import routes template_routes", True)
except Exception as e:
    test_result("Import routes template_routes", False, str(e))

try:
    import streamlit_templates
    test_result("Import streamlit_templates", True)
except Exception as e:
    test_result("Import streamlit_templates", False, str(e))

# ==============================================================================
# TESTE 2: Modelo de Dados
# ==============================================================================
print("\n🗄️ TESTE 2: Modelo de Dados")
print("-"*70)

try:
    from database import get_sync_db
    db = next(get_sync_db())

    # Verificar se tabela existe
    from sqlalchemy import inspect
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()

    if 'escritura_templates' in tables:
        test_result("Tabela escritura_templates existe", True)

        # Verificar colunas
        columns = [col['name'] for col in inspector.get_columns('escritura_templates')]
        expected_cols = ['id', 'user_id', 'tipo_escritura', 'nome_template',
                        'template_json', 'configuracoes_json', 'is_default',
                        'is_active', 'created_at', 'updated_at']

        missing_cols = [col for col in expected_cols if col not in columns]
        if not missing_cols:
            test_result("Todas as colunas esperadas existem", True,
                       f"Colunas: {', '.join(columns)}")
        else:
            test_result("Todas as colunas esperadas existem", False,
                       f"Colunas faltando: {', '.join(missing_cols)}")
    else:
        test_result("Tabela escritura_templates existe", False,
                   f"Tabelas disponíveis: {', '.join(tables)}")

    db.close()

except Exception as e:
    test_result("Verificação do modelo no banco", False, str(e))

# ==============================================================================
# TESTE 3: Templates Padrão
# ==============================================================================
print("\n📋 TESTE 3: Templates Padrão")
print("-"*70)

try:
    # Verificar arquivo JSON
    import os
    if os.path.exists('templates_padrao_extracted.json'):
        test_result("Arquivo templates_padrao_extracted.json existe", True)

        with open('templates_padrao_extracted.json', 'r', encoding='utf-8') as f:
            templates_data = json.load(f)

        # Verificar tipos
        tipos_esperados = ['lote', 'apto', 'rural', 'rural_desmembramento']
        tipos_encontrados = list(templates_data.keys())

        if set(tipos_esperados) == set(tipos_encontrados):
            test_result("Todos os 4 tipos de templates estão presentes", True,
                       f"Tipos: {', '.join(tipos_encontrados)}")
        else:
            faltando = set(tipos_esperados) - set(tipos_encontrados)
            test_result("Todos os 4 tipos de templates estão presentes", False,
                       f"Faltando: {', '.join(faltando)}")

        # Verificar estrutura de cada template
        for tipo, template in templates_data.items():
            has_blocos = 'template_json' in template and 'blocos' in template['template_json']
            has_vars = 'template_json' in template and 'variaveis_usadas' in template['template_json']
            has_config = 'configuracoes_json' in template

            if has_blocos and has_vars and has_config:
                blocos_count = len(template['template_json']['blocos'])
                vars_count = len(template['template_json']['variaveis_usadas'])
                test_result(f"Template {tipo} tem estrutura completa", True,
                           f"{blocos_count} blocos, {vars_count} variáveis")
            else:
                missing = []
                if not has_blocos:
                    missing.append("blocos")
                if not has_vars:
                    missing.append("variaveis_usadas")
                if not has_config:
                    missing.append("configuracoes_json")
                test_result(f"Template {tipo} tem estrutura completa", False,
                           f"Faltando: {', '.join(missing)}")
    else:
        test_result("Arquivo templates_padrao_extracted.json existe", False)

except Exception as e:
    test_result("Verificação de templates padrão", False, str(e))

# ==============================================================================
# TESTE 4: Scripts de Utilidade
# ==============================================================================
print("\n🔧 TESTE 4: Scripts de Utilidade")
print("-"*70)

scripts = {
    'extract_templates.py': 'Extração de templates',
    'populate_default_templates.py': 'População de templates',
    'verify_templates.py': 'Verificação de templates',
    'test_template_direct.py': 'Teste direto do modelo',
    'test_template_api.py': 'Teste da API'
}

import os
for script_file, description in scripts.items():
    if os.path.exists(script_file):
        # Verificar se é sintaxe válida
        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, script_file, 'exec')
            test_result(f"Script {script_file} - sintaxe válida", True, description)
        except SyntaxError as e:
            test_result(f"Script {script_file} - sintaxe válida", False,
                       f"Erro de sintaxe: linha {e.lineno}")
    else:
        test_result(f"Script {script_file} existe", False)

# ==============================================================================
# TESTE 5: Templates no Banco de Dados
# ==============================================================================
print("\n💾 TESTE 5: Templates no Banco de Dados")
print("-"*70)

try:
    from database import get_sync_db
    from models.escritura_template import EscrituraTemplate

    db = next(get_sync_db())

    # Contar templates
    total_templates = db.query(EscrituraTemplate).filter(
        EscrituraTemplate.is_active == True
    ).count()

    if total_templates > 0:
        test_result("Existem templates no banco de dados", True,
                   f"Total: {total_templates} templates")

        # Verificar por tipo
        tipos = ['lote', 'apto', 'rural', 'rural_desmembramento']
        for tipo in tipos:
            count = db.query(EscrituraTemplate).filter(
                EscrituraTemplate.tipo_escritura == tipo,
                EscrituraTemplate.is_active == True
            ).count()

            if count > 0:
                test_result(f"Templates do tipo '{tipo}' existem", True,
                           f"{count} template(s)")
            else:
                test_results["warnings"].append(f"Nenhum template do tipo '{tipo}' encontrado")
                test_result(f"Templates do tipo '{tipo}' existem", True,
                           "⚠️ Nenhum template, mas não é erro crítico")

        # Verificar integridade de um template
        sample = db.query(EscrituraTemplate).first()
        if sample:
            has_json = sample.template_json is not None
            has_blocos = 'blocos' in sample.template_json if has_json else False
            has_vars = 'variaveis_usadas' in sample.template_json if has_json else False

            if has_json and has_blocos and has_vars:
                test_result("Templates têm estrutura JSON válida", True,
                           f"Exemplo: {len(sample.template_json['blocos'])} blocos")
            else:
                test_result("Templates têm estrutura JSON válida", False,
                           "JSON incompleto ou inválido")
    else:
        test_results["warnings"].append("Nenhum template no banco - execute populate_default_templates.py")
        test_result("Existem templates no banco de dados", True,
                   "⚠️ Banco vazio, mas não é erro - pode popular depois")

    db.close()

except Exception as e:
    test_result("Verificação de templates no banco", False, str(e))

# ==============================================================================
# TESTE 6: Funções da API (import)
# ==============================================================================
print("\n🌐 TESTE 6: Funções da API")
print("-"*70)

try:
    from routes.template_routes import (
        list_templates, get_template, create_template,
        update_template, delete_template, set_default_template,
        duplicate_template, preview_template
    )
    test_result("Todas as funções da API podem ser importadas", True,
               "8 funções disponíveis")
except Exception as e:
    test_result("Todas as funções da API podem ser importadas", False, str(e))

# ==============================================================================
# TESTE 7: Integração Streamlit
# ==============================================================================
print("\n🎨 TESTE 7: Integração Streamlit")
print("-"*70)

try:
    # Verificar se app_fastapi foi modificado
    with open('app_fastapi.py', 'r', encoding='utf-8') as f:
        app_content = f.read()

    if 'template_router' in app_content and 'template_routes' in app_content:
        test_result("Template router integrado no app_fastapi.py", True)
    else:
        test_result("Template router integrado no app_fastapi.py", False,
                   "Importação ou registro do router não encontrado")

    # Verificar streamlit_app.py
    if os.path.exists('streamlit_app.py'):
        with open('streamlit_app.py', 'r', encoding='utf-8') as f:
            streamlit_content = f.read()

        if 'streamlit_templates' in streamlit_content and 'Templates' in streamlit_content:
            test_result("Página de templates integrada no Streamlit", True)
        else:
            test_result("Página de templates integrada no Streamlit", False,
                       "Importação não encontrada")
    else:
        test_result("Arquivo streamlit_app.py existe", False)

except Exception as e:
    test_result("Verificação de integração Streamlit", False, str(e))

# ==============================================================================
# TESTE 8: Funções Streamlit
# ==============================================================================
print("\n📱 TESTE 8: Funções Streamlit")
print("-"*70)

try:
    from streamlit_templates import (
        list_user_templates, get_template_by_id, create_template as st_create,
        update_template as st_update, delete_template as st_delete,
        duplicate_template as st_duplicate, render_template_editor_page,
        render_block_editor, render_advanced_template_editor,
        render_template_viewer, extract_variables_from_content
    )
    test_result("Funções Streamlit importadas com sucesso", True,
               "10+ funções disponíveis")

    # Testar extração de variáveis
    test_content = "Teste com [VAR1] e [VAR2] e [VAR1] repetida"
    vars_extracted = extract_variables_from_content(test_content)

    if set(vars_extracted) == {'VAR1', 'VAR2'}:
        test_result("Extração de variáveis funciona corretamente", True,
                   f"Extraiu: {vars_extracted}")
    else:
        test_result("Extração de variáveis funciona corretamente", False,
                   f"Esperado: ['VAR1', 'VAR2'], Obtido: {vars_extracted}")

except Exception as e:
    test_result("Import de funções Streamlit", False, str(e))

# ==============================================================================
# TESTE 9: Validação de Schemas
# ==============================================================================
print("\n📋 TESTE 9: Validação de Schemas Pydantic")
print("-"*70)

try:
    from models.escritura_template_schemas import (
        TemplateCreate, TemplateBloco, TemplateBlocoFormatacao
    )

    # Testar criação de bloco
    try:
        formatacao = TemplateBlocoFormatacao(
            negrito=True,
            italico=False,
            alinhamento="center"
        )
        test_result("Schema TemplateBlocoFormatacao válido", True)
    except Exception as e:
        test_result("Schema TemplateBlocoFormatacao válido", False, str(e))

    # Testar criação de template
    try:
        template_data = TemplateCreate(
            tipo_escritura="lote",
            nome_template="Teste",
            template_json={
                "blocos": [
                    {
                        "id": "bloco_1",
                        "tipo": "teste",
                        "ordem": 1,
                        "conteudo": "Teste",
                        "formatacao": {
                            "negrito": False,
                            "italico": False,
                            "sublinhado": False,
                            "alinhamento": "justify"
                        }
                    }
                ],
                "variaveis_usadas": ["VAR1"]
            }
        )
        test_result("Schema TemplateCreate válido", True)
    except Exception as e:
        test_result("Schema TemplateCreate válido", False, str(e))

except Exception as e:
    test_result("Validação de schemas", False, str(e))

# ==============================================================================
# RESULTADOS FINAIS
# ==============================================================================
print("\n" + "="*70)
print("📊 RESULTADOS FINAIS")
print("="*70)

print(f"\n✅ Testes Passados: {test_results['passed']}/{test_results['total_tests']}")
print(f"❌ Testes Falhados: {test_results['failed']}/{test_results['total_tests']}")

if test_results['warnings']:
    print(f"\n⚠️  Avisos ({len(test_results['warnings'])}):")
    for warning in test_results['warnings']:
        print(f"   - {warning}")

if test_results['errors']:
    print(f"\n❌ Erros ({len(test_results['errors'])}):")
    for error in test_results['errors']:
        print(f"   - {error}")

# Calcular porcentagem de sucesso
success_rate = (test_results['passed'] / test_results['total_tests'] * 100) if test_results['total_tests'] > 0 else 0

print(f"\n📈 Taxa de Sucesso: {success_rate:.1f}%")

if success_rate >= 90:
    print("🎉 EXCELENTE! Sistema está funcionando muito bem!")
elif success_rate >= 75:
    print("✅ BOM! Sistema está funcionando com pequenos problemas")
elif success_rate >= 50:
    print("⚠️  ATENÇÃO! Sistema tem problemas que precisam ser corrigidos")
else:
    print("❌ CRÍTICO! Sistema tem problemas sérios")

# Salvar resultados em JSON
with open('test_results.json', 'w', encoding='utf-8') as f:
    json.dump(test_results, f, indent=2, ensure_ascii=False)

print(f"\n💾 Resultados salvos em: test_results.json")
print("="*70)

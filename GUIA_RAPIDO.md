# 🚀 Guia Rápido - Sistema NFSe Arapiraca

## ⚡ Início Rápido

### 1. Configuração Básica
```python
# config.py - Edite com seus dados
PRESTADOR_CNPJ = "12345678000195"  # ← SEU CNPJ AQUI
PRESTADOR_IM = "123456"            # ← SUA INSCRIÇÃO MUNICIPAL
CODIGO_MUNICIPIO = "2700102"       # Arapiraca (não alterar)

# Para TESTE (recomendado inicialmente)
SKIP_SIGNATURE = True       # Pula assinatura
MOCK_WEBSERVICE = True      # Simula web service
```

### 2. Executar Sistema
```python
# Método 1: Script principal
python orchestrator.py

# Método 2: Importar função
from orchestrator import process_pending_invoices
resultado = process_pending_invoices()
```

### 3. Verificar Resultado
```python
if resultado['sucesso']:
    print(f"✅ Sucesso! Protocolo: {resultado['protocolo']}")
else:
    print(f"❌ Erro: {resultado['erro']}")
```

## 🎯 Comandos Essenciais

### Processar NFSe
```bash
# Ativar ambiente
venv\Scripts\activate

# Executar processamento
python orchestrator.py
```

### Consultar Status
```python
from soap_client import check_lote_status
status = check_lote_status("PROTOCOLO_123")
print(status['status_descricao'])
```

### Ver Logs
```bash
# Últimas linhas
type nfse_orchestrator.log | Select-Object -Last 20

# Filtrar erros
Select-String "ERROR" nfse_orchestrator.log
```

## 🔧 Modos de Operação

| Modo | SKIP_SIGNATURE | MOCK_WEBSERVICE | Uso |
|------|----------------|-----------------|-----|
| **Teste** | `True` | `True` | Desenvolvimento |
| **Homologação** | `False` | `False` | Testes reais |
| **Produção** | `False` | `False` | NFSe reais |

## ⚠️ Checklist Antes de Usar

- [ ] CNPJ configurado em `config.py`
- [ ] Inscrição Municipal configurada
- [ ] Certificado na pasta `certs/` (se produção)
- [ ] Ambiente virtual ativado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)

## 🆘 Problemas Comuns

### "Certificado não encontrado"
```python
# Solução temporária (teste)
SKIP_SIGNATURE = True
```

### "Erro de conexão SOAP"
```python
# Solução temporária (teste)
MOCK_WEBSERVICE = True
```

### "Campo obrigatório não informado"
- Verifique CNPJ e Inscrição Municipal em `config.py`
- Confirme dados em `data_source.py`

## 📋 Status de Lote

| Código | Descrição | Ação |
|--------|-----------|------|
| 1 | Não Recebido | Aguardar |
| 2 | Processando | Aguardar |
| 3 | Erro | Verificar logs |
| 4 | Processado | Obter NFSe |

## 🔄 Fluxo Simples

1. **Configurar** → Editar `config.py`
2. **Testar** → `python orchestrator.py`
3. **Verificar** → Logs e resultado
4. **Produção** → Certificado + URLs reais

## 📞 Ajuda Rápida

- **Logs detalhados**: `nfse_orchestrator.log`
- **Documentação completa**: `README.md`
- **Teste primeiro**: Use modo simulado
- **Valide dados**: CNPJ e Inscrição Municipal

---
💡 **Dica**: Sempre teste em modo simulado antes de usar em produção!
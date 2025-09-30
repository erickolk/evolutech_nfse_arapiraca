#!/usr/bin/env python3
"""
Exemplo de Uso - Sistema NFSe Arapiraca
=======================================

Este script demonstra como usar o sistema NFSe de forma prática.
"""

import logging
import time
from datetime import datetime
from orchestrator import process_pending_invoices
from soap_client import check_lote_status, get_lote_results

# Configurar logging para ver o que está acontecendo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def exemplo_basico():
    """Exemplo básico: processar faturas pendentes"""
    
    print("=" * 60)
    print("🚀 EXEMPLO 1: Processamento Básico")
    print("=" * 60)
    
    print("Iniciando processamento de NFSe...")
    
    # Processar faturas pendentes
    resultado = process_pending_invoices()
    
    # Exibir resultado
    if resultado['sucesso']:
        print("\n✅ SUCESSO!")
        print(f"   📋 Protocolo: {resultado['protocolo']}")
        print(f"   ⏱️  Duração: {resultado['duracao_segundos']:.2f} segundos")
        print(f"   📊 Etapas concluídas: {len(resultado['etapas_concluidas'])}")
        print(f"   📄 NFSe geradas: {len(resultado.get('nfse_geradas', []))}")
        
        # Listar etapas concluídas
        print(f"   🔄 Etapas: {', '.join(resultado['etapas_concluidas'])}")
        
        return resultado['protocolo']
    else:
        print("\n❌ ERRO no processamento:")
        for erro in resultado['erros']:
            print(f"   - {erro}")
        return None

def exemplo_consulta_status(protocolo):
    """Exemplo: consultar status de um lote"""
    
    if not protocolo:
        print("⚠️  Protocolo não fornecido, pulando consulta de status")
        return
    
    print("\n" + "=" * 60)
    print("🔍 EXEMPLO 2: Consulta de Status")
    print("=" * 60)
    
    print(f"Consultando status do protocolo: {protocolo}")
    
    # Consultar status
    status = check_lote_status(protocolo)
    
    if status['sucesso']:
        print(f"✅ Status obtido com sucesso:")
        print(f"   📊 Código: {status['status']}")
        print(f"   📝 Descrição: {status['status_descricao']}")
        print(f"   🆔 Protocolo: {status['protocolo']}")
    else:
        print(f"❌ Erro ao consultar status: {status['erro']}")

def exemplo_obter_resultados(protocolo):
    """Exemplo: obter resultados finais de um lote"""
    
    if not protocolo:
        print("⚠️  Protocolo não fornecido, pulando obtenção de resultados")
        return
    
    print("\n" + "=" * 60)
    print("📄 EXEMPLO 3: Obter Resultados")
    print("=" * 60)
    
    print(f"Obtendo resultados do protocolo: {protocolo}")
    
    # Obter resultados
    resultados = get_lote_results(protocolo)
    
    if resultados['sucesso']:
        nfse_list = resultados.get('nfse_geradas', [])
        print(f"✅ Resultados obtidos:")
        print(f"   📊 Total de NFSe: {len(nfse_list)}")
        
        # Listar NFSe geradas
        for i, nfse in enumerate(nfse_list, 1):
            print(f"   📄 NFSe {i}:")
            print(f"      🔢 Número: {nfse.get('numero', 'N/A')}")
            print(f"      🔐 Código Verificação: {nfse.get('codigo_verificacao', 'N/A')}")
            print(f"      📅 Data Emissão: {nfse.get('data_emissao', 'N/A')}")
            print(f"      💰 Valor Serviços: R$ {nfse.get('valor_servicos', 0):.2f}")
            print(f"      🏛️  Valor ISS: R$ {nfse.get('valor_iss', 0):.2f}")
    else:
        print(f"❌ Erro ao obter resultados: {resultados['erro']}")

def exemplo_monitoramento(protocolo, max_tentativas=5):
    """Exemplo: monitorar um lote até conclusão"""
    
    if not protocolo:
        print("⚠️  Protocolo não fornecido, pulando monitoramento")
        return
    
    print("\n" + "=" * 60)
    print("⏳ EXEMPLO 4: Monitoramento de Lote")
    print("=" * 60)
    
    print(f"Monitorando protocolo: {protocolo}")
    print(f"Máximo de tentativas: {max_tentativas}")
    
    for tentativa in range(1, max_tentativas + 1):
        print(f"\n🔄 Tentativa {tentativa}/{max_tentativas}")
        
        # Consultar status
        status = check_lote_status(protocolo)
        
        if not status['sucesso']:
            print(f"❌ Erro na consulta: {status['erro']}")
            break
        
        status_code = status['status']
        status_desc = status['status_descricao']
        
        print(f"📊 Status atual: {status_code} - {status_desc}")
        
        if status_code == 4:  # Processado com sucesso
            print("✅ Lote processado com sucesso!")
            
            # Obter resultados finais
            print("📄 Obtendo NFSe geradas...")
            exemplo_obter_resultados(protocolo)
            break
            
        elif status_code == 3:  # Erro no processamento
            print("❌ Lote processado com erro!")
            break
            
        else:  # Ainda processando
            if tentativa < max_tentativas:
                print("⏳ Aguardando 10 segundos...")
                time.sleep(10)
    
    if tentativa == max_tentativas and status_code not in [3, 4]:
        print("⚠️  Limite de tentativas atingido. Lote ainda em processamento.")

def exemplo_completo():
    """Exemplo completo: fluxo end-to-end"""
    
    print("🎯 SISTEMA NFSe ARAPIRACA - EXEMPLOS DE USO")
    print("=" * 60)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # 1. Processamento básico
        protocolo = exemplo_basico()
        
        # Aguardar um pouco para simular processamento
        if protocolo:
            print("\n⏳ Aguardando 5 segundos...")
            time.sleep(5)
        
        # 2. Consulta de status
        exemplo_consulta_status(protocolo)
        
        # 3. Obter resultados
        exemplo_obter_resultados(protocolo)
        
        # 4. Monitoramento (comentado para não ser muito longo)
        # exemplo_monitoramento(protocolo)
        
        print("\n" + "=" * 60)
        print("🎉 EXEMPLOS CONCLUÍDOS!")
        print("=" * 60)
        
        # Resumo final
        print("\n📋 RESUMO:")
        print("✅ Processamento básico executado")
        print("✅ Consulta de status executada")
        print("✅ Obtenção de resultados executada")
        print("\n💡 Dicas:")
        print("- Verifique os logs em 'nfse_orchestrator.log'")
        print("- Configure seus dados em 'config.py'")
        print("- Use modo simulado para testes")
        
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {str(e)}")
        print("💡 Verifique:")
        print("- Se o ambiente virtual está ativado")
        print("- Se as dependências estão instaladas")
        print("- Se a configuração está correta")

def validar_configuracao():
    """Valida a configuração antes de executar exemplos"""
    
    print("🔍 Validando configuração...")
    
    try:
        import config
        import os
        
        erros = []
        avisos = []
        
        # Validar dados obrigatórios
        if not hasattr(config, 'PRESTADOR_CNPJ') or not config.PRESTADOR_CNPJ:
            erros.append("PRESTADOR_CNPJ não configurado")
        
        if not hasattr(config, 'PRESTADOR_IM') or not config.PRESTADOR_IM:
            erros.append("PRESTADOR_IM não configurado")
        
        # Verificar modo de operação
        skip_signature = getattr(config, 'SKIP_SIGNATURE', False)
        mock_webservice = getattr(config, 'MOCK_WEBSERVICE', False)
        
        if skip_signature and mock_webservice:
            avisos.append("Sistema em MODO TESTE (simulado)")
        elif not skip_signature and not os.path.exists(getattr(config, 'CERT_PATH', '')):
            erros.append("Certificado não encontrado e assinatura habilitada")
        
        # Exibir resultados
        if erros:
            print("❌ ERROS encontrados:")
            for erro in erros:
                print(f"   - {erro}")
            return False
        
        if avisos:
            print("⚠️  AVISOS:")
            for aviso in avisos:
                print(f"   - {aviso}")
        
        print("✅ Configuração válida!")
        return True
        
    except ImportError:
        print("❌ Erro ao importar configuração")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    # Validar configuração primeiro
    if validar_configuracao():
        print()
        exemplo_completo()
    else:
        print("\n💡 Corrija os erros de configuração antes de continuar.")
        print("📖 Consulte README.md para mais informações.")
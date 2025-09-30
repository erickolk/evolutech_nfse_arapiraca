"""
Orquestrador do fluxo de trabalho de NFSe - Arapiraca
Gerencia todo o processo assíncrono de envio e consulta de lotes RPS
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

# Importar módulos do sistema
import data_source
import xml_builder
import signer
import soap_client

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nfse_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OrchestrationError(Exception):
    """Exceção personalizada para erros de orquestração"""
    pass

def process_pending_invoices() -> Dict[str, Any]:
    """
    Função principal que orquestra todo o fluxo de trabalho de NFSe
    
    Executa a sequência completa:
    1. Obter faturas pendentes
    2. Construir XML do lote
    3. Assinar XML digitalmente
    4. Enviar para o web service
    5. Fazer polling do status
    6. Obter resultados finais
    
    Returns:
        Dict[str, Any]: Resultado completo do processamento
    """
    start_time = datetime.now()
    logger.info("=== INICIANDO PROCESSAMENTO DE FATURAS PENDENTES ===")
    
    resultado_final = {
        'sucesso': False,
        'inicio': start_time.isoformat(),
        'fim': None,
        'duracao_segundos': 0,
        'etapas_concluidas': [],
        'protocolo': None,
        'nfse_geradas': [],
        'erros': []
    }
    
    try:
        # ETAPA 1: Obter faturas pendentes
        logger.info("ETAPA 1: Obtendo faturas pendentes...")
        try:
            invoices_data = data_source.DataSource.get_invoices_to_process()
            if not invoices_data or len(invoices_data) == 0:
                logger.warning("Nenhuma fatura pendente encontrada")
                resultado_final['erros'].append("Nenhuma fatura pendente para processar")
                return resultado_final
            
            logger.info(f"Encontradas {len(invoices_data)} faturas para processar")
            resultado_final['etapas_concluidas'].append("obter_faturas")
            
        except Exception as e:
            error_msg = f"Erro ao obter faturas pendentes: {str(e)}"
            logger.error(error_msg)
            resultado_final['erros'].append(error_msg)
            return resultado_final
        
        # ETAPA 2: Construir XML do lote
        logger.info("ETAPA 2: Construindo XML do lote...")
        try:
            # Gerar número do lote
            numero_lote = data_source.DataSource.gerar_numero_lote()
            logger.info(f"Número do lote gerado: {numero_lote}")
            
            xml_lote = xml_builder.create_lote_xml(invoices_data, numero_lote)
            if xml_lote is None:
                error_msg = "Falha na construção do XML do lote"
                logger.error(error_msg)
                resultado_final['erros'].append(error_msg)
                return resultado_final
            
            logger.info("XML do lote construído com sucesso")
            logger.debug(f"XML construído (primeiros 500 chars): {str(xml_lote)[:500]}...")
            resultado_final['etapas_concluidas'].append("construir_xml")
            
        except Exception as e:
            error_msg = f"Erro ao construir XML do lote: {str(e)}"
            logger.error(error_msg)
            resultado_final['erros'].append(error_msg)
            return resultado_final
        
        # ETAPA 3: Assinar XML digitalmente
        logger.info("ETAPA 3: Assinando XML digitalmente...")
        try:
            xml_assinado = signer.sign_lote_rps_xml(xml_lote)
            if xml_assinado is None:
                error_msg = "Falha na assinatura digital do XML"
                logger.error(error_msg)
                resultado_final['erros'].append(error_msg)
                return resultado_final
            
            logger.info("XML assinado digitalmente com sucesso")
            resultado_final['etapas_concluidas'].append("assinar_xml")
            
        except Exception as e:
            error_msg = f"Erro ao assinar XML: {str(e)}"
            logger.error(error_msg)
            resultado_final['erros'].append(error_msg)
            return resultado_final
        
        # ETAPA 4: Enviar para o web service
        logger.info("ETAPA 4: Enviando lote para o web service...")
        try:
            resultado_envio = soap_client.send_lote_rps(xml_assinado)
            
            if not resultado_envio['sucesso']:
                error_msg = f"Falha no envio: {resultado_envio.get('erro', 'Erro desconhecido')}"
                logger.error(error_msg)
                resultado_final['erros'].append(error_msg)
                return resultado_final
            
            protocolo = resultado_envio.get('protocolo')
            if not protocolo:
                error_msg = "Protocolo não retornado pelo web service"
                logger.error(error_msg)
                resultado_final['erros'].append(error_msg)
                return resultado_final
            
            logger.info(f"Lote enviado com sucesso. Protocolo: {protocolo}")
            resultado_final['protocolo'] = protocolo
            resultado_final['etapas_concluidas'].append("enviar_lote")
            
        except Exception as e:
            error_msg = f"Erro ao enviar lote: {str(e)}"
            logger.error(error_msg)
            resultado_final['erros'].append(error_msg)
            return resultado_final
        
        # ETAPA 5: Fazer polling do status
        logger.info("ETAPA 5: Iniciando polling do status...")
        try:
            status_final = _fazer_polling_status(protocolo)
            
            if status_final['status'] == 3:  # Erro no processamento
                error_msg = f"Lote processado com erro: {status_final.get('erro', 'Erro desconhecido')}"
                logger.error(error_msg)
                resultado_final['erros'].append(error_msg)
                return resultado_final
            
            elif status_final['status'] != 4:  # Não foi processado com sucesso
                error_msg = f"Status final inesperado: {status_final.get('status_descricao', 'Desconhecido')}"
                logger.error(error_msg)
                resultado_final['erros'].append(error_msg)
                return resultado_final
            
            logger.info("Lote processado com sucesso pelo web service")
            resultado_final['etapas_concluidas'].append("polling_status")
            
        except Exception as e:
            error_msg = f"Erro durante polling de status: {str(e)}"
            logger.error(error_msg)
            resultado_final['erros'].append(error_msg)
            return resultado_final
        
        # ETAPA 6: Obter resultados finais
        logger.info("ETAPA 6: Obtendo resultados finais...")
        try:
            resultado_final_ws = soap_client.get_lote_results(protocolo)
            
            if not resultado_final_ws['sucesso']:
                error_msg = f"Erro ao obter resultados: {resultado_final_ws.get('erro', 'Erro desconhecido')}"
                logger.error(error_msg)
                resultado_final['erros'].append(error_msg)
                return resultado_final
            
            nfse_list = resultado_final_ws.get('nfse_list', [])
            total_nfse = len(nfse_list)
            
            logger.info(f"Resultados obtidos com sucesso. {total_nfse} NFSe geradas")
            resultado_final['nfse_geradas'] = nfse_list
            resultado_final['etapas_concluidas'].append("obter_resultados")
            
            # Log detalhado das NFSe geradas
            for i, nfse in enumerate(nfse_list, 1):
                logger.info(f"NFSe {i}: Número={nfse.get('numero', 'N/A')}, Data={nfse.get('data_emissao', 'N/A')}")
            
        except Exception as e:
            error_msg = f"Erro ao obter resultados finais: {str(e)}"
            logger.error(error_msg)
            resultado_final['erros'].append(error_msg)
            return resultado_final
        
        # SUCESSO COMPLETO
        resultado_final['sucesso'] = True
        end_time = datetime.now()
        resultado_final['fim'] = end_time.isoformat()
        resultado_final['duracao_segundos'] = (end_time - start_time).total_seconds()
        
        logger.info("=== PROCESSAMENTO CONCLUÍDO COM SUCESSO ===")
        logger.info(f"Duração total: {resultado_final['duracao_segundos']:.2f} segundos")
        logger.info(f"NFSe geradas: {len(resultado_final['nfse_geradas'])}")
        
        return resultado_final
        
    except Exception as e:
        error_msg = f"Erro inesperado durante orquestração: {str(e)}"
        logger.error(error_msg, exc_info=True)
        resultado_final['erros'].append(error_msg)
        
        end_time = datetime.now()
        resultado_final['fim'] = end_time.isoformat()
        resultado_final['duracao_segundos'] = (end_time - start_time).total_seconds()
        
        return resultado_final

def _fazer_polling_status(protocolo: str, max_tentativas: int = 20, intervalo_segundos: int = 15) -> Dict[str, Any]:
    """
    Faz polling do status do lote até conclusão ou timeout
    
    Args:
        protocolo (str): Número do protocolo do lote
        max_tentativas (int): Máximo de tentativas de consulta
        intervalo_segundos (int): Intervalo entre consultas
        
    Returns:
        Dict[str, Any]: Status final do lote
        
    Raises:
        OrchestrationError: Se timeout ou erro persistente
    """
    logger.info(f"Iniciando polling para protocolo {protocolo} (max {max_tentativas} tentativas, intervalo {intervalo_segundos}s)")
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            logger.info(f"Tentativa {tentativa}/{max_tentativas}: Consultando status...")
            
            resultado_status = soap_client.check_lote_status(protocolo)
            
            if not resultado_status['sucesso']:
                logger.warning(f"Erro na consulta de status: {resultado_status.get('erro', 'Desconhecido')}")
                if tentativa == max_tentativas:
                    raise OrchestrationError(f"Falha persistente na consulta de status: {resultado_status.get('erro')}")
                continue
            
            status = resultado_status.get('status')
            status_desc = resultado_status.get('status_descricao', 'Desconhecido')
            
            logger.info(f"Status atual: {status} - {status_desc}")
            
            if status == 1:  # Não Recebido
                logger.info("Lote ainda não foi recebido pelo servidor")
            elif status == 2:  # Processando
                logger.info("Lote está sendo processado")
            elif status == 3:  # Erro no Processamento
                logger.error("Lote processado com erro")
                return resultado_status
            elif status == 4:  # Processado com Sucesso
                logger.info("Lote processado com sucesso!")
                return resultado_status
            else:
                logger.warning(f"Status desconhecido: {status}")
            
            # Se não é status final, aguardar próxima tentativa
            if tentativa < max_tentativas:
                logger.info(f"Aguardando {intervalo_segundos} segundos para próxima consulta...")
                time.sleep(intervalo_segundos)
            
        except Exception as e:
            logger.error(f"Erro na tentativa {tentativa}: {str(e)}")
            if tentativa == max_tentativas:
                raise OrchestrationError(f"Erro persistente durante polling: {str(e)}")
            
            # Aguardar antes da próxima tentativa
            if tentativa < max_tentativas:
                time.sleep(intervalo_segundos)
    
    # Se chegou aqui, esgotou as tentativas
    raise OrchestrationError(f"Timeout no polling após {max_tentativas} tentativas")

def process_single_invoice(invoice_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa uma única fatura (útil para testes ou processamento individual)
    
    Args:
        invoice_data (Dict[str, Any]): Dados da fatura
        
    Returns:
        Dict[str, Any]: Resultado do processamento
    """
    logger.info("Processando fatura individual...")
    
    # Criar lista com uma única fatura
    invoices_list = [invoice_data]
    
    # Usar a função principal
    return process_pending_invoices()

def get_processing_status(protocolo: str) -> Dict[str, Any]:
    """
    Consulta o status de um protocolo específico (função utilitária)
    
    Args:
        protocolo (str): Número do protocolo
        
    Returns:
        Dict[str, Any]: Status atual do protocolo
    """
    logger.info(f"Consultando status do protocolo: {protocolo}")
    
    try:
        resultado = soap_client.check_lote_status(protocolo)
        
        if resultado['sucesso']:
            logger.info(f"Status: {resultado.get('status_descricao', 'N/A')}")
        else:
            logger.error(f"Erro na consulta: {resultado.get('erro', 'Desconhecido')}")
        
        return resultado
        
    except Exception as e:
        error_msg = f"Erro ao consultar status: {str(e)}"
        logger.error(error_msg)
        return {
            'sucesso': False,
            'erro': error_msg,
            'status': None
        }

def get_nfse_results(protocolo: str) -> Dict[str, Any]:
    """
    Obtém os resultados de NFSe de um protocolo específico (função utilitária)
    
    Args:
        protocolo (str): Número do protocolo
        
    Returns:
        Dict[str, Any]: Lista de NFSe geradas
    """
    logger.info(f"Obtendo resultados NFSe do protocolo: {protocolo}")
    
    try:
        resultado = soap_client.get_lote_results(protocolo)
        
        if resultado['sucesso']:
            total = len(resultado.get('nfse_list', []))
            logger.info(f"Obtidas {total} NFSe")
        else:
            logger.error(f"Erro ao obter resultados: {resultado.get('erro', 'Desconhecido')}")
        
        return resultado
        
    except Exception as e:
        error_msg = f"Erro ao obter resultados: {str(e)}"
        logger.error(error_msg)
        return {
            'sucesso': False,
            'erro': error_msg,
            'nfse_list': []
        }

# Exemplo de uso e teste
if __name__ == "__main__":
    print("=== TESTE DO ORQUESTRADOR NFSe ===")
    
    # Configurar logging para teste
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Teste do fluxo completo
        print("\n1. Testando processamento completo...")
        resultado = process_pending_invoices()
        
        print(f"\nResultado final:")
        print(f"- Sucesso: {resultado['sucesso']}")
        print(f"- Duração: {resultado['duracao_segundos']:.2f}s")
        print(f"- Etapas concluídas: {', '.join(resultado['etapas_concluidas'])}")
        print(f"- Protocolo: {resultado.get('protocolo', 'N/A')}")
        print(f"- NFSe geradas: {len(resultado.get('nfse_geradas', []))}")
        
        if resultado['erros']:
            print(f"- Erros: {'; '.join(resultado['erros'])}")
        
        # Se teve sucesso, testar funções utilitárias
        if resultado['sucesso'] and resultado.get('protocolo'):
            protocolo = resultado['protocolo']
            
            print(f"\n2. Testando consulta de status para protocolo {protocolo}...")
            status_result = get_processing_status(protocolo)
            print(f"Status: {status_result}")
            
            print(f"\n3. Testando obtenção de resultados para protocolo {protocolo}...")
            nfse_result = get_nfse_results(protocolo)
            print(f"NFSe: {len(nfse_result.get('nfse_list', []))} encontradas")
        
    except Exception as e:
        print(f"Erro durante teste: {str(e)}")
        logger.error("Erro durante teste", exc_info=True)
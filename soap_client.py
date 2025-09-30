"""
Cliente SOAP para comunicação com o Web Service da Ábaco - NFSe Arapiraca
Implementa as três funções principais para envio e consulta de lotes RPS
"""
import logging
from typing import Dict, Any, Optional
from zeep import Client, Settings, Transport
from zeep.exceptions import Fault, TransportError
import requests
from lxml import etree
import config

# Configurar logging
logger = logging.getLogger(__name__)

class SOAPClientError(Exception):
    """Exceção personalizada para erros do cliente SOAP"""
    pass

def _create_soap_client(wsdl_url: str) -> Client:
    """
    Cria e configura um cliente SOAP com as configurações apropriadas
    
    Args:
        wsdl_url (str): URL do WSDL do serviço
        
    Returns:
        Client: Cliente SOAP configurado
    """
    try:
        # Configurar sessão HTTP
        session = requests.Session()
        session.verify = True
        
        # Configurar transport
        transport = Transport(
            session=session,
            timeout=30,
            operation_timeout=30
        )
        
        # Configurar settings do Zeep para evitar problemas de parsing
        settings = Settings(
            strict=False,
            xml_huge_tree=True,
            force_https=False
        )
        
        # Criar cliente SOAP
        client = Client(
            wsdl=wsdl_url,
            transport=transport,
            settings=settings
        )
        
        logger.info(f"Cliente SOAP configurado com sucesso para: {wsdl_url}")
        return client
        
    except Exception as e:
        logger.error(f"Erro ao configurar cliente SOAP: {str(e)}")
        raise SOAPClientError(f"Falha na configuração do cliente SOAP: {str(e)}")

def send_lote_rps(signed_xml_bytes: bytes) -> Dict[str, Any]:
    """
    Envia um lote de RPS assinado para o web service
    
    Args:
        signed_xml_bytes (bytes): XML do lote de RPS assinado digitalmente
        
    Returns:
        Dict[str, Any]: Resposta do web service contendo protocolo ou erro
    """
    try:
        logger.info("Iniciando envio de lote RPS")
        
        # Verificar se está em modo de teste
        import config
        from datetime import datetime
        if getattr(config, 'MOCK_WEBSERVICE', False):
            logger.info("MODO TESTE: Simulando resposta do web service")
            return {
                'sucesso': True,
                'protocolo': f"TESTE_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'mensagem': 'Lote recebido com sucesso (simulado)',
                'resposta_xml': '<EnviarLoteRpsResposta><Protocolo>TESTE_20250930112656</Protocolo></EnviarLoteRpsResposta>'
            }
        
        # Converter bytes para string se necessário
        if isinstance(signed_xml_bytes, bytes):
            xml_string = signed_xml_bytes.decode('utf-8')
        else:
            xml_string = signed_xml_bytes
        
        # Criar cliente SOAP para recepcionar lote
        wsdl_url = f"{config.URL_HOMOLOGACAO['recepcionar_lote_rps']}"
        client = _create_soap_client(wsdl_url)
        
        # Preparar parâmetros da requisição SOAP
        # O payload XML vai dentro do parâmetro nfsedadosmsg
        parametros = {
            'nfsedadosmsg': xml_string
        }
        
        logger.debug(f"Enviando XML: {xml_string[:500]}...")  # Log apenas início do XML
        
        # Chamar o método do web service
        response = client.service.RecepcionarLoteRps(**parametros)
        
        # Processar resposta
        resultado = _processar_resposta_envio(response)
        
        if resultado['sucesso']:
            logger.info(f"Lote enviado com sucesso. Protocolo: {resultado.get('protocolo', 'N/A')}")
        else:
            logger.error(f"Erro no envio: {resultado.get('erro', 'Erro desconhecido')}")
        
        return resultado
        
    except Fault as e:
        logger.error(f"Erro SOAP ao enviar lote: {str(e)}")
        return {
            'sucesso': False,
            'erro': f"Erro SOAP: {str(e)}",
            'codigo_erro': 'SOAP_FAULT',
            'protocolo': None
        }
    except TransportError as e:
        logger.error(f"Erro de transporte ao enviar lote: {str(e)}")
        return {
            'sucesso': False,
            'erro': f"Erro de transporte: {str(e)}",
            'codigo_erro': 'TRANSPORT_ERROR',
            'protocolo': None
        }
    except Exception as e:
        logger.error(f"Erro inesperado ao enviar lote: {str(e)}")
        return {
            'sucesso': False,
            'erro': f"Erro inesperado: {str(e)}",
            'codigo_erro': 'UNEXPECTED_ERROR',
            'protocolo': None
        }

def check_lote_status(protocolo: str) -> Dict[str, Any]:
    """
    Consulta o status de processamento de um lote
    
    Args:
        protocolo (str): Protocolo do lote retornado pelo envio
        
    Returns:
        Dict[str, Any]: Status do lote e informações de processamento
    """
    try:
        logger.info(f"Consultando status do lote: {protocolo}")
        
        # Verificar se está em modo de teste
        import config
        if getattr(config, 'MOCK_WEBSERVICE', False):
            logger.info("MODO TESTE: Simulando consulta de status")
            return {
                'sucesso': True,
                'status': 4,  # Processado
                'status_descricao': 'Lote processado com sucesso',
                'protocolo': protocolo,
                'resposta_xml': f'<ConsultarSituacaoLoteRpsResposta><Situacao>4</Situacao><Protocolo>{protocolo}</Protocolo></ConsultarSituacaoLoteRpsResposta>'
            }
        
        # Construir XML de consulta
        xml_consulta = f"""<?xml version="1.0" encoding="UTF-8"?>
        <ConsultarSituacaoLoteRpsEnvio xmlns="http://www.abrasf.org.br/nfse.xsd">
            <Prestador>
                <Cnpj>{config.PRESTADOR_CNPJ}</Cnpj>
                <InscricaoMunicipal>{config.PRESTADOR_IM}</InscricaoMunicipal>
            </Prestador>
            <Protocolo>{protocolo}</Protocolo>
        </ConsultarSituacaoLoteRpsEnvio>"""
        
        # Criar cliente SOAP para consultar situação
        wsdl_url = f"{config.URL_HOMOLOGACAO['consultar_situacao_lote']}"
        client = _create_soap_client(wsdl_url)
        
        # Preparar parâmetros
        parametros = {
            'nfsedadosmsg': xml_consulta
        }
        
        logger.debug(f"Consultando protocolo: {protocolo}")
        
        # Chamar o método do web service
        response = client.service.ConsultarSituacaoLoteRps(**parametros)
        
        # Processar resposta
        resultado = _processar_resposta_status(response)
        
        if resultado['sucesso']:
            status_desc = _get_status_description(resultado.get('status', 0))
            logger.info(f"Status consultado: {status_desc}")
        else:
            logger.error(f"Erro na consulta: {resultado.get('erro', 'Erro desconhecido')}")
        
        return resultado
        
    except Exception as e:
        error_msg = f"Erro inesperado ao consultar status: {str(e)}"
        logger.error(error_msg)
        return {
            'sucesso': False,
            'erro': f"Erro inesperado: {str(e)}",
            'codigo_erro': 'UNEXPECTED_ERROR'
        }

def get_nfse_by_lote(protocolo: str) -> Dict[str, Any]:
    """
    Consulta as NFSe geradas por um lote
    
    Args:
        protocolo (str): Protocolo do lote processado
        
    Returns:
        Dict[str, Any]: Lista de NFSe geradas pelo lote
    """
    try:
        logger.info(f"Consultando NFSe do lote: {protocolo}")
        
        # Verificar se está em modo de teste
        import config
        if getattr(config, 'MOCK_WEBSERVICE', False):
            logger.info("MODO TESTE: Simulando consulta de NFSe")
            return {
                'sucesso': True,
                'nfse_list': [
                    {
                        'numero': '000000001',
                        'codigo_verificacao': 'ABC123',
                        'data_emissao': '2024-01-01T10:00:00',
                        'valor_servicos': 1000.00,
                        'valor_iss': 50.00
                    }
                ],
                'protocolo': protocolo,
                'resposta_xml': f'<ConsultarLoteRpsResposta><ListaNfse><CompNfse><Nfse><InfNfse><Numero>000000001</Numero></InfNfse></Nfse></CompNfse></ListaNfse></ConsultarLoteRpsResposta>'
            }
        
        # Construir XML de consulta
        xml_consulta = f"""<?xml version="1.0" encoding="UTF-8"?>
        <ConsultarLoteRpsEnvio xmlns="http://www.abrasf.org.br/nfse.xsd">
            <Prestador>
                <Cnpj>{config.PRESTADOR_CNPJ}</Cnpj>
                <InscricaoMunicipal>{config.PRESTADOR_IM}</InscricaoMunicipal>
            </Prestador>
            <Protocolo>{protocolo}</Protocolo>
        </ConsultarLoteRpsEnvio>"""
        
        # Criar cliente SOAP para consultar lote
        wsdl_url = f"{config.URL_HOMOLOGACAO['consultar_lote_rps']}"
        client = _create_soap_client(wsdl_url)
        
        # Preparar parâmetros
        parametros = {
            'nfsedadosmsg': xml_consulta
        }
        
        logger.debug(f"Consultando NFSe do protocolo: {protocolo}")
        
        # Chamar o método do web service
        response = client.service.ConsultarLoteRps(**parametros)
        
        # Processar resposta
        resultado = _processar_resposta_nfse(response)
        
        if resultado['sucesso']:
            nfse_count = len(resultado.get('nfse_list', []))
            logger.info(f"Encontradas {nfse_count} NFSe para o lote")
        else:
            logger.error(f"Erro na consulta: {resultado.get('erro', 'Erro desconhecido')}")
        
        return resultado
        
    except Exception as e:
        error_msg = f"Erro inesperado ao consultar NFSe: {str(e)}"
        logger.error(error_msg)
        return {
            'sucesso': False,
            'erro': f"Erro inesperado: {str(e)}",
            'codigo_erro': 'UNEXPECTED_ERROR'
        }

def get_lote_results(protocolo: str) -> Dict[str, Any]:
    """
    Obtém os resultados finais de um lote processado
    
    Args:
        protocolo (str): Protocolo do lote processado
        
    Returns:
        Dict[str, Any]: Resultados do processamento incluindo NFSe geradas
    """
    try:
        logger.info(f"Obtendo resultados do protocolo: {protocolo}")
        
        # Verificar se está em modo de teste
        import config
        if getattr(config, 'MOCK_WEBSERVICE', False):
            logger.info("MODO TESTE: Simulando obtenção de resultados")
            return {
                'sucesso': True,
                'nfse_geradas': [
                    {
                        'numero': '000000001',
                        'codigo_verificacao': 'ABC123',
                        'data_emissao': '2024-01-01T10:00:00',
                        'valor_servicos': 1000.00,
                        'valor_iss': 50.00,
                        'link_visualizacao': f'https://nfse.arapiraca.al.gov.br/visualizar/000000001/ABC123'
                    }
                ],
                'total_nfse': 1,
                'protocolo': protocolo,
                'resposta_xml': f'<ConsultarLoteRpsResposta><ListaNfse><CompNfse><Nfse><InfNfse><Numero>000000001</Numero></InfNfse></Nfse></CompNfse></ListaNfse></ConsultarLoteRpsResposta>'
            }
        
        # Primeiro consultar o status para garantir que está processado
        status_result = check_lote_status(protocolo)
        if not status_result['sucesso']:
            return {
                'sucesso': False,
                'erro': f"Erro ao consultar status: {status_result.get('erro', 'Erro desconhecido')}",
                'codigo_erro': 'STATUS_CHECK_ERROR'
            }
        
        # Se não está processado, retornar erro
        if status_result.get('status') != 4:
            return {
                'sucesso': False,
                'erro': f"Lote ainda não processado. Status: {status_result.get('status', 'N/A')}",
                'codigo_erro': 'LOTE_NOT_PROCESSED'
            }
        
        # Obter as NFSe geradas
        nfse_result = get_nfse_by_lote(protocolo)
        if not nfse_result['sucesso']:
            return {
                'sucesso': False,
                'erro': f"Erro ao obter NFSe: {nfse_result.get('erro', 'Erro desconhecido')}",
                'codigo_erro': 'NFSE_RETRIEVAL_ERROR'
            }
        
        # Compilar resultados finais
        nfse_list = nfse_result.get('nfse_list', [])
        
        return {
            'sucesso': True,
            'nfse_geradas': nfse_list,
            'total_nfse': len(nfse_list),
            'protocolo': protocolo,
            'status_final': status_result.get('status'),
            'resposta_xml': nfse_result.get('resposta_xml', '')
        }
        
    except Exception as e:
        error_msg = f"Erro inesperado ao obter resultados: {str(e)}"
        logger.error(error_msg)
        return {
            'sucesso': False,
            'erro': f"Erro inesperado: {str(e)}",
            'codigo_erro': 'UNEXPECTED_ERROR'
        }

def _processar_resposta_envio(response) -> Dict[str, Any]:
    """
    Processa a resposta do envio de lote para extrair o protocolo
    
    Args:
        response: Resposta do web service
        
    Returns:
        Dict[str, Any]: Resposta processada com protocolo
    """
    try:
        # Converter resposta para XML se necessário
        if hasattr(response, 'body'):
            xml_response = response.body
        else:
            xml_response = str(response)
        
        # Parse do XML de resposta
        root = etree.fromstring(xml_response.encode('utf-8') if isinstance(xml_response, str) else xml_response)
        
        # Buscar protocolo na resposta
        protocolo_elem = root.find('.//{http://www.abrasf.org.br/nfse.xsd}Protocolo')
        if protocolo_elem is not None:
            protocolo = protocolo_elem.text
            return {
                'sucesso': True,
                'protocolo': protocolo,
                'resposta_xml': xml_response
            }
        
        # Buscar erros na resposta
        erro_elem = root.find('.//{http://www.abrasf.org.br/nfse.xsd}MensagemRetorno')
        if erro_elem is not None:
            codigo_elem = erro_elem.find('.//{http://www.abrasf.org.br/nfse.xsd}Codigo')
            mensagem_elem = erro_elem.find('.//{http://www.abrasf.org.br/nfse.xsd}Mensagem')
            
            return {
                'sucesso': False,
                'erro': mensagem_elem.text if mensagem_elem is not None else 'Erro desconhecido',
                'codigo_erro': codigo_elem.text if codigo_elem is not None else 'UNKNOWN',
                'protocolo': None,
                'resposta_xml': xml_response
            }
        
        # Se não encontrou protocolo nem erro
        return {
            'sucesso': False,
            'erro': 'Resposta inválida - protocolo não encontrado',
            'codigo_erro': 'INVALID_RESPONSE',
            'protocolo': None,
            'resposta_xml': xml_response
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar resposta de envio: {str(e)}")
        return {
            'sucesso': False,
            'erro': f"Erro ao processar resposta: {str(e)}",
            'codigo_erro': 'PROCESSING_ERROR',
            'protocolo': None
        }

def _processar_resposta_status(response) -> Dict[str, Any]:
    """
    Processa a resposta da consulta de status
    
    Args:
        response: Resposta do web service
        
    Returns:
        Dict[str, Any]: Status processado (1, 2, 3 ou 4)
    """
    try:
        # Converter resposta para XML se necessário
        if hasattr(response, 'body'):
            xml_response = response.body
        else:
            xml_response = str(response)
        
        # Parse do XML de resposta
        root = etree.fromstring(xml_response.encode('utf-8') if isinstance(xml_response, str) else xml_response)
        
        # Buscar situação na resposta
        situacao_elem = root.find('.//{http://www.abrasf.org.br/nfse.xsd}Situacao')
        if situacao_elem is not None:
            status = int(situacao_elem.text)
            return {
                'sucesso': True,
                'status': status,
                'status_descricao': _get_status_description(status),
                'resposta_xml': xml_response
            }
        
        return {
            'sucesso': False,
            'erro': 'Status não encontrado na resposta',
            'codigo_erro': 'STATUS_NOT_FOUND',
            'status': None
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar resposta de status: {str(e)}")
        return {
            'sucesso': False,
            'erro': f"Erro ao processar resposta: {str(e)}",
            'codigo_erro': 'PROCESSING_ERROR',
            'status': None
        }

def _processar_resposta_nfse(response) -> Dict[str, Any]:
    """
    Processa a resposta da consulta de NFSe
    
    Args:
        response: Resposta do web service
        
    Returns:
        Dict[str, Any]: Lista de NFSe geradas
    """
    try:
        # Converter resposta para XML se necessário
        if hasattr(response, 'body'):
            xml_response = response.body
        else:
            xml_response = str(response)
        
        # Parse do XML de resposta
        root = etree.fromstring(xml_response.encode('utf-8') if isinstance(xml_response, str) else xml_response)
        
        # Buscar NFSe na resposta
        nfse_list = []
        nfse_elements = root.findall('.//{http://www.abrasf.org.br/nfse.xsd}CompNfse')
        
        for nfse_elem in nfse_elements:
            # Extrair dados básicos da NFSe
            numero_elem = nfse_elem.find('.//{http://www.abrasf.org.br/nfse.xsd}Numero')
            data_elem = nfse_elem.find('.//{http://www.abrasf.org.br/nfse.xsd}DataEmissao')
            codigo_verificacao_elem = nfse_elem.find('.//{http://www.abrasf.org.br/nfse.xsd}CodigoVerificacao')
            valor_servicos_elem = nfse_elem.find('.//{http://www.abrasf.org.br/nfse.xsd}ValorServicos')
            valor_iss_elem = nfse_elem.find('.//{http://www.abrasf.org.br/nfse.xsd}ValorIss')
            
            nfse_data = {
                'numero': numero_elem.text if numero_elem is not None else None,
                'data_emissao': data_elem.text if data_elem is not None else None,
                'codigo_verificacao': codigo_verificacao_elem.text if codigo_verificacao_elem is not None else None,
                'valor_servicos': float(valor_servicos_elem.text) if valor_servicos_elem is not None else 0.0,
                'valor_iss': float(valor_iss_elem.text) if valor_iss_elem is not None else 0.0,
                'xml_completo': etree.tostring(nfse_elem, encoding='unicode')
            }
            nfse_list.append(nfse_data)
        
        return {
            'sucesso': True,
            'nfse_list': nfse_list,
            'total_nfse': len(nfse_list),
            'resposta_xml': xml_response
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar resposta de NFSe: {str(e)}")
        return {
            'sucesso': False,
            'erro': f"Erro ao processar resposta: {str(e)}",
            'codigo_erro': 'PROCESSING_ERROR',
            'nfse_list': []
        }

def _processar_resposta_resultados(response) -> Dict[str, Any]:
    """
    Processa a resposta da consulta de resultados
    
    Args:
        response: Resposta do web service
        
    Returns:
        Dict[str, Any]: Lista de NFSe geradas
    """
    try:
        # Converter resposta para XML se necessário
        if hasattr(response, 'body'):
            xml_response = response.body
        else:
            xml_response = str(response)
        
        # Parse do XML de resposta
        root = etree.fromstring(xml_response.encode('utf-8') if isinstance(xml_response, str) else xml_response)
        
        # Buscar NFSe na resposta
        nfse_list = []
        nfse_elements = root.findall('.//{http://www.abrasf.org.br/nfse.xsd}CompNfse')
        
        for nfse_elem in nfse_elements:
            # Extrair dados básicos da NFSe
            numero_elem = nfse_elem.find('.//{http://www.abrasf.org.br/nfse.xsd}Numero')
            data_elem = nfse_elem.find('.//{http://www.abrasf.org.br/nfse.xsd}DataEmissao')
            
            nfse_data = {
                'numero': numero_elem.text if numero_elem is not None else None,
                'data_emissao': data_elem.text if data_elem is not None else None,
                'xml_completo': etree.tostring(nfse_elem, encoding='unicode')
            }
            nfse_list.append(nfse_data)
        
        return {
            'sucesso': True,
            'nfse_list': nfse_list,
            'total_nfse': len(nfse_list),
            'resposta_xml': xml_response
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar resposta de resultados: {str(e)}")
        return {
            'sucesso': False,
            'erro': f"Erro ao processar resposta: {str(e)}",
            'codigo_erro': 'PROCESSING_ERROR',
            'nfse_list': []
        }

def _get_status_description(status: int) -> str:
    """
    Retorna a descrição do status do lote
    
    Args:
        status (int): Código do status
        
    Returns:
        str: Descrição do status
    """
    status_map = {
        1: "Não Recebido",
        2: "Processando",
        3: "Erro no Processamento",
        4: "Processado com Sucesso"
    }
    return status_map.get(status, f"Status desconhecido: {status}")

# Exemplo de uso
if __name__ == "__main__":
    # Configurar logging para teste
    logging.basicConfig(level=logging.INFO)
    
    print("=== Teste do Cliente SOAP ===")
    
    # Teste com XML de exemplo (seria vindo do signer.py)
    xml_exemplo = b"""<?xml version="1.0" encoding="UTF-8"?>
    <EnviarLoteRpsEnvio xmlns="http://www.abrasf.org.br/nfse.xsd">
        <LoteRps Id="lote123">
            <NumeroLote>123</NumeroLote>
            <Cnpj>12345678000195</Cnpj>
            <InscricaoMunicipal>123456</InscricaoMunicipal>
            <QuantidadeRps>1</QuantidadeRps>
            <ListaRps>
                <Rps>
                    <InfRps Id="rps1">
                        <IdentificacaoRps>
                            <Numero>1</Numero>
                            <Serie>A1</Serie>
                            <Tipo>1</Tipo>
                        </IdentificacaoRps>
                    </InfRps>
                </Rps>
            </ListaRps>
        </LoteRps>
    </EnviarLoteRpsEnvio>"""
    
    print("1. Testando envio de lote...")
    try:
        resultado_envio = send_lote_rps(xml_exemplo)
        print(f"Resultado envio: {resultado_envio}")
        
        if resultado_envio['sucesso'] and resultado_envio['protocolo']:
            protocolo = resultado_envio['protocolo']
            
            print(f"\n2. Testando consulta de status para protocolo: {protocolo}")
            resultado_status = check_lote_status(protocolo)
            print(f"Resultado status: {resultado_status}")
            
            print(f"\n3. Testando obtenção de resultados para protocolo: {protocolo}")
            resultado_final = get_lote_results(protocolo)
            print(f"Resultado final: {resultado_final}")
        else:
            print("Envio falhou, não é possível testar consultas")
            
    except Exception as e:
        print(f"Erro durante teste: {str(e)}")
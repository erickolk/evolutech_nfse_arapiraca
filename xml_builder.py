"""
Módulo Construtor de XML para NFSe Arapiraca
Implementa o Design Pattern Builder para construção de XMLs seguindo o padrão ABRASF
"""

from typing import List, Dict, Any
from lxml import etree
from config import PRESTADOR_CNPJ, PRESTADOR_IM


def create_lote_xml(invoices: List[Dict[str, Any]], numero_lote: int) -> etree._Element:
    """
    Constrói o XML completo de um lote de RPS seguindo o padrão ABRASF.
    
    Args:
        invoices: Lista de dicionários contendo os dados das notas fiscais
        numero_lote: Número identificador do lote
        
    Returns:
        Elemento XML representando a estrutura completa do EnviarLoteRpsEnvio
    """
    # Namespace principal do padrão ABRASF
    namespace = "http://www.abrasf.org.br/nfse.xsd"
    
    # Elemento raiz do envelope de envio
    envio_element = etree.Element(
        "EnviarLoteRpsEnvio",
        xmlns=namespace
    )
    
    # Construção do elemento LoteRps
    lote_rps = _build_lote_rps(envio_element, invoices, numero_lote, namespace)
    
    return envio_element


def _build_lote_rps(parent: etree._Element, invoices: List[Dict[str, Any]], 
                   numero_lote: int, namespace: str) -> etree._Element:
    """
    Constrói o elemento LoteRps com todos os RPS do lote.
    
    Args:
        parent: Elemento pai onde será anexado o LoteRps
        invoices: Lista de notas fiscais
        numero_lote: Número do lote
        namespace: Namespace XML
        
    Returns:
        Elemento LoteRps construído
    """
    lote_rps = etree.SubElement(parent, "LoteRps")
    lote_rps.set("id", f"lote_{numero_lote}")
    
    # Número do lote
    numero_lote_elem = etree.SubElement(lote_rps, "NumeroLote")
    numero_lote_elem.text = str(numero_lote)
    
    # Dados do prestador (CNPJ)
    cpf_cnpj_prestador = etree.SubElement(lote_rps, "CpfCnpj")
    cnpj_elem = etree.SubElement(cpf_cnpj_prestador, "Cnpj")
    cnpj_elem.text = PRESTADOR_CNPJ
    
    # Inscrição Municipal do prestador
    inscricao_municipal = etree.SubElement(lote_rps, "InscricaoMunicipal")
    inscricao_municipal.text = PRESTADOR_IM
    
    # Quantidade de RPS no lote
    quantidade_rps = etree.SubElement(lote_rps, "QuantidadeRps")
    quantidade_rps.text = str(len(invoices))
    
    # Lista de RPS
    lista_rps = etree.SubElement(lote_rps, "ListaRps")
    
    # Construção de cada RPS individual
    for invoice in invoices:
        _build_rps(lista_rps, invoice)
    
    return lote_rps


def _build_rps(parent: etree._Element, invoice: Dict[str, Any]) -> etree._Element:
    """
    Constrói um elemento RPS individual.
    
    Args:
        parent: Elemento pai (ListaRps)
        invoice: Dicionário com dados da nota fiscal
        
    Returns:
        Elemento RPS construído
    """
    rps = etree.SubElement(parent, "Rps")
    
    # Informações do RPS com ID para assinatura
    inf_rps = etree.SubElement(rps, "InfRps")
    inf_rps.set("id", invoice["id_rps"])
    
    # Identificação do RPS
    identificacao_rps = _build_identificacao_rps(inf_rps, invoice)
    
    # Data de emissão
    data_emissao = etree.SubElement(inf_rps, "DataEmissao")
    data_emissao.text = invoice["data_emissao"]
    
    # Status do RPS
    status_rps = etree.SubElement(inf_rps, "StatusRps")
    status_rps.text = str(invoice["status_rps"])
    
    # Serviços prestados
    servico = _build_servico(inf_rps, invoice)
    
    # Dados do prestador
    prestador = _build_prestador(inf_rps)
    
    # Dados do tomador
    tomador = _build_tomador(inf_rps, invoice["tomador"])
    
    return rps


def _build_identificacao_rps(parent: etree._Element, invoice: Dict[str, Any]) -> etree._Element:
    """
    Constrói a identificação do RPS.
    
    Args:
        parent: Elemento pai (InfRps)
        invoice: Dados da nota fiscal
        
    Returns:
        Elemento IdentificacaoRps
    """
    identificacao = etree.SubElement(parent, "IdentificacaoRps")
    
    numero = etree.SubElement(identificacao, "Numero")
    numero.text = invoice["numero_rps"]
    
    serie = etree.SubElement(identificacao, "Serie")
    serie.text = invoice["serie_rps"]
    
    tipo = etree.SubElement(identificacao, "Tipo")
    tipo.text = str(invoice["tipo_rps"])
    
    return identificacao


def _build_servico(parent: etree._Element, invoice: Dict[str, Any]) -> etree._Element:
    """
    Constrói os dados do serviço prestado.
    
    Args:
        parent: Elemento pai (InfRps)
        invoice: Dados da nota fiscal
        
    Returns:
        Elemento Servico
    """
    servico = etree.SubElement(parent, "Servico")
    
    # Valores do serviço
    valores = etree.SubElement(servico, "Valores")
    
    valor_servicos = etree.SubElement(valores, "ValorServicos")
    valor_servicos.text = f"{invoice['valor_servicos']:.2f}"
    
    valor_iss = etree.SubElement(valores, "ValorIss")
    valor_iss.text = f"{invoice['valor_iss']:.2f}"
    
    aliquota = etree.SubElement(valores, "Aliquota")
    aliquota.text = f"{invoice['aliquota']:.4f}"
    
    # ISS Retido
    iss_retido = etree.SubElement(servico, "IssRetido")
    iss_retido.text = str(invoice["iss_retido"])
    
    # Item da lista de serviços
    item_lista_servico = etree.SubElement(servico, "ItemListaServico")
    item_lista_servico.text = invoice["item_lista_servico"]
    
    # Discriminação do serviço
    discriminacao = etree.SubElement(servico, "Discriminacao")
    discriminacao.text = invoice["discriminacao"]
    
    # Código do município onde o serviço foi prestado
    codigo_municipio = etree.SubElement(servico, "CodigoMunicipio")
    codigo_municipio.text = invoice["codigo_municipio"]
    
    return servico


def _build_prestador(parent: etree._Element) -> etree._Element:
    """
    Constrói os dados do prestador de serviços.
    
    Args:
        parent: Elemento pai (InfRps)
        
    Returns:
        Elemento Prestador
    """
    prestador = etree.SubElement(parent, "Prestador")
    
    # CNPJ do prestador
    cpf_cnpj = etree.SubElement(prestador, "CpfCnpj")
    cnpj = etree.SubElement(cpf_cnpj, "Cnpj")
    cnpj.text = PRESTADOR_CNPJ
    
    # Inscrição Municipal
    inscricao_municipal = etree.SubElement(prestador, "InscricaoMunicipal")
    inscricao_municipal.text = PRESTADOR_IM
    
    return prestador


def _build_tomador(parent: etree._Element, tomador_data: Dict[str, Any]) -> etree._Element:
    """
    Constrói os dados do tomador de serviços.
    
    Args:
        parent: Elemento pai (InfRps)
        tomador_data: Dicionário com dados do tomador
        
    Returns:
        Elemento Tomador
    """
    tomador = etree.SubElement(parent, "Tomador")
    
    # Identificação do tomador
    identificacao_tomador = etree.SubElement(tomador, "IdentificacaoTomador")
    
    cpf_cnpj_tomador = etree.SubElement(identificacao_tomador, "CpfCnpj")
    cnpj_tomador = etree.SubElement(cpf_cnpj_tomador, "Cnpj")
    cnpj_tomador.text = tomador_data["cnpj"]
    
    # Razão social
    razao_social = etree.SubElement(tomador, "RazaoSocial")
    razao_social.text = tomador_data["razao_social"]
    
    # Endereço do tomador
    endereco = _build_endereco_tomador(tomador, tomador_data)
    
    return tomador


def _build_endereco_tomador(parent: etree._Element, tomador_data: Dict[str, Any]) -> etree._Element:
    """
    Constrói o endereço do tomador.
    
    Args:
        parent: Elemento pai (Tomador)
        tomador_data: Dados do tomador
        
    Returns:
        Elemento Endereco
    """
    endereco = etree.SubElement(parent, "Endereco")
    
    endereco_elem = etree.SubElement(endereco, "Endereco")
    endereco_elem.text = tomador_data["endereco"]
    
    numero = etree.SubElement(endereco, "Numero")
    numero.text = tomador_data["numero"]
    
    bairro = etree.SubElement(endereco, "Bairro")
    bairro.text = tomador_data["bairro"]
    
    codigo_municipio = etree.SubElement(endereco, "CodigoMunicipio")
    codigo_municipio.text = tomador_data["codigo_municipio"]
    
    uf = etree.SubElement(endereco, "Uf")
    uf.text = tomador_data["uf"]
    
    cep = etree.SubElement(endereco, "Cep")
    cep.text = tomador_data["cep"]
    
    return endereco


def xml_to_string(element: etree._Element, pretty_print: bool = True) -> str:
    """
    Converte um elemento XML para string formatada.
    
    Args:
        element: Elemento XML a ser convertido
        pretty_print: Se deve formatar o XML com indentação
        
    Returns:
        String XML formatada
    """
    return etree.tostring(
        element,
        pretty_print=pretty_print,
        xml_declaration=True,
        encoding='UTF-8'
    ).decode('utf-8')


# Exemplo de uso e teste da função
if __name__ == "__main__":
    # Dados de exemplo para teste
    exemplo_invoices = [
        {
            "id_rps": "rps_1001",
            "numero_rps": "1001",
            "serie_rps": "A",
            "tipo_rps": 1,
            "data_emissao": "2025-09-30T10:00:00",
            "status_rps": 1,
            "valor_servicos": 1000.00,
            "valor_iss": 50.00,
            "aliquota": 0.05,
            "iss_retido": 2,
            "item_lista_servico": "0107",
            "discriminacao": "Serviços de consultoria em tecnologia da informação",
            "codigo_municipio": "2700102",
            "tomador": {
                "cnpj": "12345678000195",
                "razao_social": "Empresa Exemplo LTDA",
                "endereco": "Rua das Flores, 123",
                "numero": "123",
                "bairro": "Centro",
                "codigo_municipio": "2700102",
                "uf": "AL",
                "cep": "57000000"
            }
        }
    ]
    
    # Teste da função
    xml_lote = create_lote_xml(exemplo_invoices, 12345)
    print(xml_to_string(xml_lote))
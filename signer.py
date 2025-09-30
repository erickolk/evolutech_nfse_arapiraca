"""
Módulo de Assinatura Digital para NFSe Arapiraca
Implementa assinatura dupla seguindo o padrão ABRASF usando xmlsec
"""

import os
from typing import Optional
from lxml import etree
import xmlsec
from config import CERT_PATH, CERT_PASSWORD


def sign_lote_rps_xml(xml_tree_root: etree._Element) -> bytes:
    """
    Aplica assinatura digital dupla ao XML do lote de RPS seguindo o padrão ABRASF.
    
    Processo de assinatura:
    1. Assinaturas internas: Assina cada elemento <InfRps> dentro de cada <Rps>
    2. Assinatura externa: Assina o elemento <LoteRps> principal
    
    Args:
        xml_tree_root: Elemento raiz do XML gerado pelo xml_builder
        
    Returns:
        XML completo assinado como bytes string UTF-8 com declaração XML
        
    Raises:
        FileNotFoundError: Se o certificado não for encontrado
        ValueError: Se houver erro na configuração ou assinatura
        xmlsec.Error: Se houver erro específico do xmlsec
    """
    # Verificar se está em modo de teste
    import config
    if getattr(config, 'SKIP_SIGNATURE', False):
        print("MODO TESTE: Pulando assinatura digital")
        # Retornar XML sem assinatura como bytes
        xml_bytes = etree.tostring(
            xml_tree_root,
            pretty_print=True,
            xml_declaration=True,
            encoding='utf-8'
        )
        return xml_bytes
        
    if getattr(config, 'TEST_MODE', False):
        print("MODO TESTE: Simulando assinatura digital")
        # Adicionar comentário indicando assinatura simulada
        comment = etree.Comment(" ASSINATURA DIGITAL SIMULADA - MODO TESTE ")
        xml_tree_root.insert(0, comment)
        
        xml_bytes = etree.tostring(
            xml_tree_root,
            pretty_print=True,
            xml_declaration=True,
            encoding='utf-8'
        )
        return xml_bytes
    
    # Inicializa a biblioteca xmlsec
    xmlsec.enable_debug_trace(False)
    xmlsec.init()
    
    try:
        # Carrega a chave privada do certificado
        key = _load_private_key_from_pfx(CERT_PATH, CERT_PASSWORD)
        
        # Fase 1: Assinatura interna - Assina cada InfRps
        _sign_internal_rps_elements(xml_tree_root, key)
        
        # Fase 2: Assinatura externa - Assina o LoteRps
        _sign_external_lote_element(xml_tree_root, key)
        
        # Converte para bytes com declaração XML UTF-8
        xml_bytes = etree.tostring(
            xml_tree_root,
            pretty_print=True,
            xml_declaration=True,
            encoding='utf-8'
        )
        
        return xml_bytes
        
    finally:
        # Limpa recursos do xmlsec
        xmlsec.shutdown()


def _load_private_key_from_pfx(cert_path: str, cert_password: Optional[str]) -> xmlsec.Key:
    """
    Carrega a chave privada do arquivo PFX/P12.
    
    Args:
        cert_path: Caminho para o arquivo do certificado
        cert_password: Senha do certificado
        
    Returns:
        Chave privada carregada para uso com xmlsec
        
    Raises:
        FileNotFoundError: Se o certificado não existir
        xmlsec.Error: Se houver erro ao carregar a chave
    """
    if not os.path.exists(cert_path):
        raise FileNotFoundError(f"Certificado não encontrado: {cert_path}")
    
    # Carrega a chave privada do arquivo PKCS#12
    key = xmlsec.Key.from_file(cert_path, xmlsec.KeyFormat.PKCS12, cert_password)
    
    if key is None:
        raise ValueError("Falha ao carregar a chave privada do certificado")
    
    return key


def _sign_internal_rps_elements(xml_root: etree._Element, key: xmlsec.Key) -> None:
    """
    Assina todos os elementos InfRps individualmente (assinaturas internas).
    
    Para cada <Rps> no lote:
    1. Localiza o elemento <InfRps> e seu atributo id
    2. Cria um template de assinatura
    3. Aplica a assinatura digital
    4. Insere o bloco <Signature> como irmão do <InfRps>
    
    Args:
        xml_root: Elemento raiz do XML
        key: Chave privada para assinatura
    """
    # Localiza todos os elementos Rps no lote
    rps_elements = xml_root.xpath("//Rps")
    
    for rps_element in rps_elements:
        # Localiza o elemento InfRps dentro do Rps atual
        inf_rps_elements = rps_element.xpath("./InfRps")
        
        if not inf_rps_elements:
            continue
            
        inf_rps = inf_rps_elements[0]
        inf_rps_id = inf_rps.get("id")
        
        if not inf_rps_id:
            continue
        
        # Cria o template de assinatura para o InfRps
        signature_template = _create_signature_template(f"#{inf_rps_id}")
        
        # Insere o template como irmão do InfRps (dentro do Rps)
        rps_element.append(signature_template)
        
        # Aplica a assinatura
        _apply_signature(signature_template, key)


def _sign_external_lote_element(xml_root: etree._Element, key: xmlsec.Key) -> None:
    """
    Assina o elemento LoteRps principal (assinatura externa).
    
    1. Localiza o elemento <LoteRps> e seu atributo id
    2. Cria um template de assinatura
    3. Aplica a assinatura digital
    4. Insere o bloco <Signature> como irmão do <LoteRps>
    
    Args:
        xml_root: Elemento raiz do XML
        key: Chave privada para assinatura
    """
    # Localiza o elemento LoteRps
    lote_rps_elements = xml_root.xpath("//LoteRps")
    
    if not lote_rps_elements:
        raise ValueError("Elemento LoteRps não encontrado no XML")
    
    lote_rps = lote_rps_elements[0]
    lote_rps_id = lote_rps.get("id")
    
    if not lote_rps_id:
        raise ValueError("Atributo id não encontrado no elemento LoteRps")
    
    # Cria o template de assinatura para o LoteRps
    signature_template = _create_signature_template(f"#{lote_rps_id}")
    
    # Insere o template como irmão do LoteRps (dentro do EnviarLoteRpsEnvio)
    xml_root.append(signature_template)
    
    # Aplica a assinatura
    _apply_signature(signature_template, key)


def _create_signature_template(reference_uri: str) -> etree._Element:
    """
    Cria um template de assinatura XML seguindo o padrão ABRASF.
    
    Configurações utilizadas:
    - CanonicalizationMethod: c14n (Canonical XML 1.0)
    - SignatureMethod: rsa-sha1 (RSA com SHA-1)
    - DigestMethod: sha1 (SHA-1)
    - Transform: enveloped-signature
    
    Args:
        reference_uri: URI de referência para o elemento a ser assinado (ex: "#lote_123")
        
    Returns:
        Elemento XML template configurado para assinatura
    """
    # Namespace para assinatura digital XML
    ds_ns = "http://www.w3.org/2000/09/xmldsig#"
    
    # Elemento raiz da assinatura
    signature = etree.Element(f"{{{ds_ns}}}Signature")
    
    # Informações da assinatura
    signed_info = etree.SubElement(signature, f"{{{ds_ns}}}SignedInfo")
    
    # Método de canonicalização (c14n)
    canonicalization_method = etree.SubElement(signed_info, f"{{{ds_ns}}}CanonicalizationMethod")
    canonicalization_method.set("Algorithm", "http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
    
    # Método de assinatura (RSA-SHA1)
    signature_method = etree.SubElement(signed_info, f"{{{ds_ns}}}SignatureMethod")
    signature_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#rsa-sha1")
    
    # Referência ao elemento a ser assinado
    reference = etree.SubElement(signed_info, f"{{{ds_ns}}}Reference")
    reference.set("URI", reference_uri)
    
    # Transformações aplicadas
    transforms = etree.SubElement(reference, f"{{{ds_ns}}}Transforms")
    
    # Transformação enveloped-signature
    transform = etree.SubElement(transforms, f"{{{ds_ns}}}Transform")
    transform.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#enveloped-signature")
    
    # Método de digest (SHA-1)
    digest_method = etree.SubElement(reference, f"{{{ds_ns}}}DigestMethod")
    digest_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#sha1")
    
    # Valor do digest (será preenchido pelo xmlsec)
    digest_value = etree.SubElement(reference, f"{{{ds_ns}}}DigestValue")
    
    # Valor da assinatura (será preenchido pelo xmlsec)
    signature_value = etree.SubElement(signature, f"{{{ds_ns}}}SignatureValue")
    
    # Informações da chave (será preenchido pelo xmlsec)
    key_info = etree.SubElement(signature, f"{{{ds_ns}}}KeyInfo")
    x509_data = etree.SubElement(key_info, f"{{{ds_ns}}}X509Data")
    x509_certificate = etree.SubElement(x509_data, f"{{{ds_ns}}}X509Certificate")
    
    return signature


def _apply_signature(signature_template: etree._Element, key: xmlsec.Key) -> None:
    """
    Aplica a assinatura digital ao template configurado.
    
    Args:
        signature_template: Template de assinatura criado
        key: Chave privada para assinatura
        
    Raises:
        xmlsec.Error: Se houver erro durante a assinatura
    """
    # Cria o contexto de assinatura
    ctx = xmlsec.SignatureContext()
    ctx.key = key
    
    # Aplica a assinatura ao template
    ctx.sign(signature_template)


def validate_signed_xml(signed_xml: bytes) -> bool:
    """
    Valida as assinaturas digitais de um XML assinado.
    
    Args:
        signed_xml: XML assinado em bytes
        
    Returns:
        True se todas as assinaturas forem válidas, False caso contrário
    """
    try:
        xmlsec.init()
        
        # Parse do XML assinado
        doc = etree.fromstring(signed_xml)
        
        # Localiza todas as assinaturas no documento
        signatures = doc.xpath("//ds:Signature", namespaces={"ds": "http://www.w3.org/2000/09/xmldsig#"})
        
        if not signatures:
            return False
        
        # Valida cada assinatura encontrada
        for signature in signatures:
            ctx = xmlsec.SignatureContext()
            
            # Verifica a assinatura
            try:
                ctx.verify(signature)
            except xmlsec.Error:
                return False
        
        return True
        
    except Exception:
        return False
    finally:
        xmlsec.shutdown()


# Exemplo de uso e teste
if __name__ == "__main__":
    from xml_builder import create_lote_xml
    
    print("🔧 Testando o módulo signer.py...")
    
    # Teste 1: Verificar se as funções auxiliares funcionam
    print("\n1. Testando criação de template de assinatura...")
    try:
        template = _create_signature_template("#teste_123")
        print(f"✅ Template criado com sucesso! Elemento: {template.tag}")
    except Exception as e:
        print(f"❌ Erro ao criar template: {e}")
    
    # Teste 2: Verificar se o XML builder funciona
    print("\n2. Testando criação de XML não assinado...")
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
    
    try:
        xml_lote = create_lote_xml(exemplo_invoices, 12345)
        print(f"✅ XML não assinado criado! Elemento raiz: {xml_lote.tag}")
        
        # Verifica se os elementos necessários estão presentes
        rps_elements = xml_lote.xpath("//Rps")
        lote_rps_elements = xml_lote.xpath("//LoteRps")
        
        print(f"   - Elementos Rps encontrados: {len(rps_elements)}")
        print(f"   - Elementos LoteRps encontrados: {len(lote_rps_elements)}")
        
        if rps_elements:
            inf_rps = rps_elements[0].xpath("./InfRps")
            if inf_rps:
                print(f"   - InfRps ID: {inf_rps[0].get('id')}")
        
        if lote_rps_elements:
            print(f"   - LoteRps ID: {lote_rps_elements[0].get('id')}")
            
    except Exception as e:
        print(f"❌ Erro ao criar XML: {e}")
    
    # Teste 3: Verificar certificado (sem tentar carregar)
    print(f"\n3. Verificando configuração do certificado...")
    print(f"   - Caminho do certificado: {CERT_PATH}")
    print(f"   - Certificado existe: {os.path.exists(CERT_PATH)}")
    
    if not os.path.exists(CERT_PATH):
        print("⚠️  AVISO: Certificado não encontrado!")
        print("   Para testar a assinatura completa, coloque um certificado .pfx válido em:")
        print(f"   {os.path.abspath(CERT_PATH)}")
        print("   E configure a senha no arquivo .env (CERT_PASS=sua_senha)")
    else:
        print("\n4. Testando assinatura completa...")
        try:
            xml_assinado = sign_lote_rps_xml(xml_lote)
            print("✅ XML assinado com sucesso!")
            print(f"   Tamanho do XML assinado: {len(xml_assinado)} bytes")
            
            # Valida as assinaturas
            if validate_signed_xml(xml_assinado):
                print("✅ Assinaturas válidas!")
            else:
                print("❌ Assinaturas inválidas!")
                
        except Exception as e:
            print(f"❌ Erro durante a assinatura: {e}")
    
    print("\n🎉 Teste do módulo signer.py concluído!")
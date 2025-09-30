# config.py
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# --- DADOS DO CERTIFICADO DIGITAL ---
# Coloque seu arquivo .pfx na pasta 'certs'
CERT_PATH = "certs/seu_certificado.pfx" 
# A senha do certificado será lida do arquivo .env por segurança
CERT_PASSWORD = os.getenv("CERT_PASS")

# --- DADOS DA EMPRESA (PRESTADOR DE SERVIÇO) ---
PRESTADOR_CNPJ = "32649500000145"  # Substitua pelo CNPJ da sua patroa
PRESTADOR_IM = "123"            # Substitua pela Inscrição Municipal
CODIGO_MUNICIPIO = "2700102"    # Código IBGE de Arapiraca

# --- ENDPOINTS DOS WEB SERVICES (AMBIENTE DE TESTES) ---
URL_HOMOLOGACAO = {
    "recepcionar_lote_rps": "https://enfs-hom.abaco.com.br/arapiraca/servlet/arecepcionarloterps?wsdl",
    "consultar_situacao_lote": "https://enfs-hom.abaco.com.br/arapiraca/servlet/aconsultarsituacaoloterps?wsdl",
    "consultar_lote_rps": "https://enfs-hom.abaco.com.br/arapiraca/servlet/aconsultarloterps?wsdl",
    "consultar_nfse_por_rps": "https://enfs-hom.abaco.com.br/arapiraca/servlet/aconsultarnfseporrps?wsdl"
}

# Configurações de teste
TEST_MODE = False  # Quando True, simula assinatura digital sem certificado
SKIP_SIGNATURE = True  # Quando True, pula a etapa de assinatura completamente
MOCK_WEBSERVICE = True  # Quando True, simula respostas do web service
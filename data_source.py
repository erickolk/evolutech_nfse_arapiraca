"""
Módulo para gerenciamento de dados de exemplo e fontes de dados para NFSe
"""
from datetime import datetime
import config

class DataSource:
    """Classe para gerenciar dados de exemplo e fontes de dados"""
    
    @staticmethod
    def obter_dados_rps_exemplo():
        """Retorna dados de exemplo para um RPS"""
        return {
            'numero': 1,
            'serie': '1',
            'tipo': 1,
            'data_emissao': datetime.now(),
            'natureza_operacao': 1,
            'optante_simples_nacional': 2,
            'incentivador_cultural': 2,
            'status': 1,
            'servico': {
                'valor_servicos': 1000.00,
                'item_lista_servico': '01.01',
                'discriminacao': 'Serviços de consultoria em tecnologia da informação',
                'codigo_municipio': config.CODIGO_MUNICIPIO
            },
            'prestador': {
                'cnpj': config.PRESTADOR_CNPJ,
                'inscricao_municipal': config.PRESTADOR_IM
            },
            'tomador': {
                'cnpj': '12345678000195',
                'razao_social': 'Empresa Tomadora de Serviços Ltda',
                'endereco': {
                    'logradouro': 'Rua das Flores, 123',
                    'numero': '123',
                    'bairro': 'Centro',
                    'cep': '57300000',
                    'codigo_municipio': config.CODIGO_MUNICIPIO,
                    'uf': 'AL'
                },
                'contato': {
                    'telefone': '82999999999',
                    'email': 'contato@empresa.com.br'
                }
            }
        }
    
    @staticmethod
    def obter_dados_lote_exemplo(quantidade_rps=1):
        """
        Retorna dados de exemplo para um lote de RPS
        
        Args:
            quantidade_rps (int): Quantidade de RPS no lote
            
        Returns:
            list: Lista com dados dos RPS
        """
        lista_rps = []
        
        for i in range(quantidade_rps):
            rps_data = DataSource.obter_dados_rps_exemplo()
            rps_data['numero'] = i + 1
            lista_rps.append(rps_data)
        
        return lista_rps
    
    @staticmethod
    def validar_dados_rps(dados_rps):
        """
        Valida os dados de um RPS
        
        Args:
            dados_rps (dict): Dados do RPS
            
        Returns:
            tuple: (bool, list) - (é_válido, lista_de_erros)
        """
        erros = []
        
        # Validações obrigatórias
        if not dados_rps.get('numero'):
            erros.append("Número do RPS é obrigatório")
        
        if not dados_rps.get('data_emissao'):
            erros.append("Data de emissão é obrigatória")
        
        # Validações do serviço
        servico = dados_rps.get('servico', {})
        if not servico.get('valor_servicos'):
            erros.append("Valor dos serviços é obrigatório")
        
        if not servico.get('item_lista_servico'):
            erros.append("Item da lista de serviço é obrigatório")
        
        if not servico.get('discriminacao'):
            erros.append("Discriminação do serviço é obrigatória")
        
        # Validações do tomador
        tomador = dados_rps.get('tomador', {})
        if not tomador.get('razao_social'):
            erros.append("Razão social do tomador é obrigatória")
        
        if not tomador.get('cnpj') and not tomador.get('cpf'):
            erros.append("CNPJ ou CPF do tomador é obrigatório")
        
        return len(erros) == 0, erros
    
    @staticmethod
    def formatar_cnpj_cpf(documento):
        """
        Formata CNPJ ou CPF removendo caracteres especiais
        
        Args:
            documento (str): CNPJ ou CPF
            
        Returns:
            str: Documento formatado (apenas números)
        """
        if not documento:
            return ""
        
        # Remove todos os caracteres que não são dígitos
        return ''.join(filter(str.isdigit, documento))
    
    @staticmethod
    def validar_cnpj(cnpj):
        """
        Valida um CNPJ
        
        Args:
            cnpj (str): CNPJ a ser validado
            
        Returns:
            bool: True se o CNPJ é válido
        """
        cnpj = DataSource.formatar_cnpj_cpf(cnpj)
        
        if len(cnpj) != 14:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            return False
        
        # Calcula o primeiro dígito verificador
        soma = 0
        peso = 5
        for i in range(12):
            soma += int(cnpj[i]) * peso
            peso -= 1
            if peso < 2:
                peso = 9
        
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        # Calcula o segundo dígito verificador
        soma = 0
        peso = 6
        for i in range(13):
            soma += int(cnpj[i]) * peso
            peso -= 1
            if peso < 2:
                peso = 9
        
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return cnpj[12] == str(digito1) and cnpj[13] == str(digito2)
    
    @staticmethod
    def validar_cpf(cpf):
        """
        Valida um CPF
        
        Args:
            cpf (str): CPF a ser validado
            
        Returns:
            bool: True se o CPF é válido
        """
        cpf = DataSource.formatar_cnpj_cpf(cpf)
        
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Calcula o primeiro dígito verificador
        soma = 0
        for i in range(9):
            soma += int(cpf[i]) * (10 - i)
        
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        # Calcula o segundo dígito verificador
        soma = 0
        for i in range(10):
            soma += int(cpf[i]) * (11 - i)
        
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return cpf[9] == str(digito1) and cpf[10] == str(digito2)
    
    @staticmethod
    def gerar_numero_lote():
        """
        Gera um número de lote baseado na data/hora atual
        
        Returns:
            int: Número do lote
        """
        now = datetime.now()
        return int(now.strftime("%Y%m%d%H%M%S"))
    
    @staticmethod
    def obter_dados_consulta_exemplo():
        """Retorna dados de exemplo para consulta de NFSe"""
        return {
            'prestador': {
                'cnpj': config.PRESTADOR_CNPJ,
                'inscricao_municipal': config.PRESTADOR_IM
            },
            'numero_nfse': None,
            'periodo_emissao': {
                'data_inicial': datetime.now().replace(day=1),
                'data_final': datetime.now()
            },
            'tomador': {
                'cnpj': None,
                'inscricao_municipal': None
            },
            'intermediario_servico': {
                'cnpj': None,
                'inscricao_municipal': None
            }
        }

    @staticmethod
    def get_invoices_to_process():
        """
        Retorna lista de faturas pendentes para processamento
        
        Returns:
            List[Dict]: Lista de dados de RPS para processar
        """
        # Por enquanto, retorna dados de exemplo no formato esperado pelo xml_builder
        # Em produção, isso viria de um banco de dados ou API
        dados_exemplo = DataSource.obter_dados_rps_exemplo()
        
        # Converter para o formato esperado pelo xml_builder
        return [{
            "id_rps": f"rps_{dados_exemplo['numero']}",
            "numero_rps": str(dados_exemplo['numero']),
            "serie_rps": dados_exemplo['serie'],
            "tipo_rps": dados_exemplo['tipo'],
            "data_emissao": dados_exemplo['data_emissao'].strftime("%Y-%m-%dT%H:%M:%S"),
            "status_rps": dados_exemplo['status'],
            "valor_servicos": dados_exemplo['servico']['valor_servicos'],
            "valor_iss": dados_exemplo['servico']['valor_servicos'] * 0.05,  # 5% de ISS
            "aliquota": 0.05,
            "iss_retido": 2,  # Não retido
            "item_lista_servico": dados_exemplo['servico']['item_lista_servico'],
            "discriminacao": dados_exemplo['servico']['discriminacao'],
            "codigo_municipio": dados_exemplo['servico']['codigo_municipio'],
            "tomador": {
                "cnpj": dados_exemplo['tomador']['cnpj'],
                "razao_social": dados_exemplo['tomador']['razao_social'],
                "endereco": dados_exemplo['tomador']['endereco']['logradouro'],
                "numero": dados_exemplo['tomador']['endereco']['numero'],
                "bairro": dados_exemplo['tomador']['endereco']['bairro'],
                "codigo_municipio": dados_exemplo['tomador']['endereco']['codigo_municipio'],
                "uf": dados_exemplo['tomador']['endereco']['uf'],
                "cep": dados_exemplo['tomador']['endereco']['cep']
            }
        }]
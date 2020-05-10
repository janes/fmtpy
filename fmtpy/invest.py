from bs4 import BeautifulSoup
import requests
import numpy as np
from datetime import datetime
import pandas as pd

mes_trimestre = {
3:1, 6:2, 9:3, 12:4
}

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}


# retira acentos de uma string
def ascii(str):
    a={}
    [[a.update({j:'aeiouc'[n]}) for j in i] for n, i in enumerate(['áàâã','éê','í','óòôõ','ú','ç'])]
    nome = ''.join([a[i] if i in a else i for i in str])
    return nome

# converte string para date
def todate(data):
    return datetime.strptime(data, "%d/%m/%Y").date()
        

# Função para fazer obter o html do site da b3,
# muitas vezes a página fica carregando muito tempo, é necessário recarregar algumas vezes até funcionar
def bstimeout(url, time, data=''):
    for i in range(20):
        try:
            response = requests.post(url, data=data, headers=headers, timeout=time)
            soup = BeautifulSoup(response.content,'html.parser')
            return soup
        except:
 #           print(i)
            pass
        
    print('Número de tentavias excedidas no site da B3')


codigos = {
    'Resultado' : [4, 'dre_empresa'],
    'Balanço Ativo' : [2, 'balanco_empresa'],
    'Balanço Passivo': [3, 'balanco_empresa'],
    'Fluxo de Caixa' : [7, 'dfc_empresa'],
    'Valor Adicionado' : [9, 'dva_empresa']
}

trimestre = {
    1 : ['0331', 'ITR'],
    2 : ['0630', 'ITR'],
    3 : ['0930', 'ITR'],
    4 : ['1231', 'DFP']    
}

indice_ind = {
1:'Resultado', 2:'Balanço Ativo', 3:'Balanço Passivo', 4:'Valor Adicionado', 
5:'Fluxo de Caixa', 6:'Resultado Abrangente' #, 7:'Mutações do PL'
}

# Busca o codigo cvm, cnpj e isin usando o site da B3, 
# mas o site da B3 é muito instável, por padrão usamos a classe Dados
class Dados_B3:

    def __init__(self, papel):
        self.papel = papel

    # Obtem o cnpj e isin
    def cnpj(self):
    
        if 'cnpj_' in self.__dict__:
            return self.__dict__['cnpj_']

        cd = self.cd_cvm()

        url='http://bvmf.bmfbovespa.com.br/pt-br/mercados/acoes/empresas/ExecutaAcaoConsultaInfoEmp.asp?CodCVM='+str(cd)
        
        soup = bstimeout(url, 3)
        soup = soup.find('ul', class_='accordion').findAll('tr')
        
        tipo_papel = 'ACNOR' if int(self.papel[-1:]) == 3 else 'ACNPR'
        isin = [i.replace(',','') for i in list(set(soup[1].text.split())) if i[6:11] == tipo_papel][0]
        cnpj_ = soup[2].text.split()[1]

        setattr(self, '__isin', isin)
        setattr(self, 'cnpj_', cnpj_)

        return cnpj


    def isin(self):
        if '__isin' in self.__dict__:
            return self.__dict__['__isin']
        self.cnpj()
        isin = self.__isin
        return isin
        
    # Busca o nome da empresa listada na cvm e o código
    def cd_cvm(self):

        if 'cd_cvm' in self.__dict__:
            return self.__dict__['cd_cvm']

        url = f'http://bvmf.bmfbovespa.com.br/cias-listadas/empresas-listadas/BuscaEmpresaListada.aspx?Nome={self.papel}&idioma=pt-br'
        soup = bstimeout(url, 3)
        codigo = soup.find('tr', class_='GridRow_SiteBmfBovespa GridBovespaItemStyle')
        codigo = codigo.find('td').find('a')['href']
        codigo[codigo.find('codigoCvm=')+len('codigoCvm='):]
        cd_cvm_ = int(codigo[codigo.find('codigoCvm=')+len('codigoCvm='):])
        setattr(self, 'cd_cvm', cd_cvm_)
        return cd_cvm_


# Obtem dados de outros sites
class Dados:

    def __init__(self, papel):
        self.papel = papel
        self.dados = {}

    # Obtem o nome e cnpj da ação no site status invest
    def cnpj(self):
        if 'cnpj_' in self.__dict__:
            return self.__dict__['cnpj_']
        url = f"""https://statusinvest.com.br/acoes/"""+self.papel.lower()
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        try:
            cnpj_ = soup.find('small', class_ = 'd-block fs-4 fw-100 lh-4').text
            setattr(self, 'cnpj_', cnpj_)
            return cnpj_
        except:
            pass
            #print('CNPJ não encontrado')   

    # Obtem o isin no site adfvn
    def isin(self):
        if '__isin' in self.__dict__:
            return self.__dict__['__isin']
        url='https://br.advfn.com/p.php?pid=qkquote&symbol='+self.papel.lower()
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        isin = soup.find(id = 'quoteElementPiece6').text 
        setattr(self, '__isin', isin)
        return isin
        
    # Busca o código cvm no site da cvm
    def cd_cvm(self):
        if 'cd_cvm_' in self.__dict__:
            return self.__dict__['cd_cvm_']
        url=f'https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/CiaAb/ResultBuscaParticCiaAb.aspx?CNPJNome={self.cnpj()}&TipoConsult=C'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        cd_cvm_ = soup.find(id = 'dlCiasCdCVM__ctl1_Linkbutton5').text  
        setattr(self, 'cd_cvm_', int(cd_cvm_))   
        return int(cd_cvm_)


# Obtem dados do site investsite   
class Raw:

    def __init__(self, papel):
        self.papel = papel
        self.dados = Dados(self.papel)
        self.series = {}
        
        
    def raw(self, ind, ano, tri):
    
        tpind = codigos[indice_ind[ind]] if type(ind)==int else codigos[ind]

        if (ind, ano, tri) in self.series:
            return self.series[(ind, ano, tri)] 

        url = 'https://www.investsite.com.br/includes/demonstrativo_tabela_ajax.php'

        self.isin = self.dados.isin()
        
        data = {
            'tipo_dem': trimestre[tri][1],
            'tipo_fonte': 'XML',
            'ano_dem': str(ano),
            'mes_dia_dem': trimestre[tri][0],
            'consolid': '2',
            'tipocontabil': '2',
            'codigodem': str(tpind[0]),
            'ISIN': self.isin
          }
           
        response = requests.post(url, data=data, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        idd = tpind[1] if tri == 4 else tpind[1]+'_itr'
       # if not soup.find('table', id=idd):
       #     return
        soup = soup.find('table', id=idd).findAll('tr')
        if not len(soup[2:]):
            self.series.update({(ind, ano, tri):None})
            return
        
        th = [i.text.replace('(R$)', '').replace('(R$ mil)', '').replace(' ','') for i in soup[0].findAll('th')[:3]]
        td = [[i.text if i.text !='0' else None for i in j.findAll('td')[:3]] for j in soup[2:]]
        
        self.series.update({(ind, ano, tri):[th]+td})
        return [th]+td
        


class Balanco:

    def __init__(self, papel, site=True):
        self.papel=papel
        self.site = site
        self.balanco = Raw(self.papel) if site else None
        self.datarefs = {}


    # Transforma os valores em float
    def __trata_valores(self, dados):
        campos = np.array(dados[0])
        contents = dados[1:]
        contents = np.array(contents, dtype=object)
        contents[:,2] = [float(i.replace('.','').replace(',','.'))*1000 if i else None for i in contents[:,2]]
        return [campos, contents]
        
    # Verifica os trimestre que o valor está consolidado
    def __tri_cons(self, dados):
        datas = dados[0][2].split('a')
        meses = [int(i.split('/')[1]) for i in datas]
        tri = [mes_trimestre[i] for i in range(min(meses),max(meses)) if i in mes_trimestre]
        return tri

    # Subtrai aos trimestre anteriores para obter o valor específico do trimestre
    def __subtrai_mes_ant(self, x1, x2):
        isnull = lambda a:a if a else 0
        res = [isnull(i[2]) - isnull((lambda a:a[0][2] if len(a)>0 else 0)(x2[x2[:,0]==i[0]])) for i in x1]
        x1[:,2]=res
        return x1
        
    # puxa os dados e trata os campos
    def raw(self):
        raw = self.balanco.raw(self.ind,self.ano,self.tri)
        if not raw:
            return
        relatorio = self.__trata_valores(raw)
        
        if not self.ajustado:
            return relatorio
        
        listtri = self.__tri_cons(relatorio)
        
        while len(listtri)>0:
            b = self.balanco.raw(self.ind,self.ano,listtri[-1:][0])
            if not b:
                return
            triant = self.__trata_valores(b)
            relatorio[1] = self.__subtrai_mes_ant(relatorio[1], triant[1])
            listtri = [i for i in listtri[:-1] if i not in self.__tri_cons(triant)]
            
        relatorio[0][2] = relatorio[0][2].split('a')[-1:][0]

        return relatorio

    # Monta o layout da tabela
    def get(self, ind, ano, tri, ajustado=True):
        self.ind, self.ano, self.tri, self.ajustado = ind, ano, tri, ajustado
       # print(f'Obtendo {indice_ind[self.ind]} para {self.papel} referente ao {self.tri}º trimestre de {self.ano}')
        raw = self.raw()
        if not raw:
            return
        valores = raw[1]

      #  cdcvm = [self.balanco.dados.cd_cvm_ for i in valores]
      #  indice = [self.ind for i in valores]

        ativo = [self.papel for i in valores]
        indice = [indice_ind[self.ind] for i in valores]

        tabela = {}
       # tabela.update({'cdcvm':['CD_CVM', cdcvm]})
        tabela.update({'cdcvm':['CD_ATIVO', ativo]})
        tabela.update({'indice':['DS_IND', indice]})
        tabela.update({'conta':['CONTA', 'DS_CONTA', valores[:,[0,1]]], 'valor':['VALOR',valores[:,2]]})
        # adiciona outras colunas
        #encontra trimestre inicial e final
        datas = raw[0][2]
        if not self.ajustado:
            datas = raw[0][2].split('a')
            datas = [todate(i) for i in datas]
            datas = [min(datas), max(datas)]
            datas = [datas for i in valores]
            meses = [i.month for i in datas[0]]
            trimestre = [int(i/3)+1 if i%3 else int(i/3) for i in meses]
            trimestre = [trimestre for i in valores]
            tabela.update({'dataref': ['DATA_REF_INI', 'DATA_REF_FIN', datas]})
            tabela.update({'trimestre': ['TRIMESTRE_INI', 'TRIMESTRE_FIN', trimestre]})
            # salvando para a tabela de relatorios
            if not self.site:
                self.datarefs.update({(self.ind, self.ano, self.tri) : [self.balanco.dados.cd_cvm_, self.ind,
                self.balanco.relatorios[self.ano][self.tri][2], self.ano]+datas[0]+trimestre[0]})

            
        else:
            trimestre = self.tri
            trimestre = [trimestre for i in valores]
            datas = [todate(datas) for i in valores]
            tabela.update({'dataref':['DATA_REF', datas]})
            tabela.update({'trimestre':['TRIMESTRE', trimestre]})

        tabela.update({'ano':['ANO', [self.ano for i in valores]]})

        # Data de entrega só tem se for rodado pela cvm
        if not self.site:
            relat = self.balanco.relatorios[self.ano][self.tri]
            dataent = [relat[1] for i in valores]
            numrelat = [relat[2] for i in valores]
            tabela.update({'dataent':['DATA_ENT', dataent], 'relat':['CD_RELATORIO', numrelat]})

        tabela1 =  tabela['cdcvm'][-1]
        colunas = tabela['cdcvm'][:-1]

        # Gera a tabela final
        for i in ['indice', 'relat', 'conta', 'dataent', 'dataref', 'ano', 'trimestre', 'valor']:
            if i in tabela:
                colunas += tabela[i][:-1]
                tabela1 = np.column_stack([tabela1,tabela[i][-1]])

        return [colunas, tabela1]


    def df(self, ind, ano, tri, ajustado=True):
        tabela = self.get(ind, ano, tri, ajustado=True)
        return pd.DataFrame(tabela[1], columns=tabela[0])








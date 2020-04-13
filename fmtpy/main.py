# Esse pacote obtem os dados do site Investsite.com e da Uol

from bs4 import BeautifulSoup
import requests
import numpy as np
import json
from tabulate import tabulate
from scipy.stats import norm
from scipy.stats import pearsonr
from datetime import datetime


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
1:'Resultado', 2:'Balanço Ativo', 3:'Balanço Passivo', 4:'Resultado Abrangente', 5:'Fluxo de Caixa', 6:'Valor Adicionado', 7:'Mutações do PL'
}

# Busca o codigo cvm, cnpj e isin usando o site da B3, 
# mas o site da B3 é muito instável, por padrão usamos a classe Dados
class Dados_B3:

    def __init__(self, papel):
        self.papel = papel

    # Obtem o cnpj e isin
    def cnpj(self):
    
        if '__cnpj' in self.__dict__:
            return self.__dict__['__cnpj']

        cd = self.cd_cvm()

        url='http://bvmf.bmfbovespa.com.br/pt-br/mercados/acoes/empresas/ExecutaAcaoConsultaInfoEmp.asp?CodCVM='+str(cd)
        
        soup = bstimeout(url, 3)
        soup = soup.find('ul', class_='accordion').findAll('tr')
        
        tipo_papel = 'ACNOR' if int(self.papel[-1:]) == 3 else 'ACNPR'
        isin = [i.replace(',','') for i in list(set(soup[1].text.split())) if i[6:11] == tipo_papel][0]
        cnpj = soup[2].text.split()[1]

        setattr(self, '__isin', isin)
        setattr(self, '__cnpj', cnpj)

        return cnpj


    def isin(self):
        if '__isin' in self.__dict__:
            return self.__dict__['__isin']
        self.cnpj()
        isin = self.__isin
        return isin
        
    # Busca o nome da empresa listada na cvm e o código
    def cd_cvm(self):

        if '__cd_cvm' in self.__dict__:
            return self.__dict__['__cd_cvm']

        url = f'http://bvmf.bmfbovespa.com.br/cias-listadas/empresas-listadas/BuscaEmpresaListada.aspx?Nome={self.papel}&idioma=pt-br'
        soup = bstimeout(url, 3)
        codigo = soup.find('tr', class_='GridRow_SiteBmfBovespa GridBovespaItemStyle')
        codigo = codigo.find('td').find('a')['href']
        codigo[codigo.find('codigoCvm=')+len('codigoCvm='):]
        cd_cvm = int(codigo[codigo.find('codigoCvm=')+len('codigoCvm='):])
        setattr(self, '__cd_cvm', cd_cvm)
        return cd_cvm


# Obtem dados de outros sites
class Dados:

    def __init__(self, papel):
        self.papel = papel
        self.dados = {}

    # Obtem o nome e cnpj da ação no site status invest
    def cnpj(self):
        if '__cnpj' in self.__dict__:
            return self.__dict__['__cnpj']
        url = f"""https://statusinvest.com.br/acoes/"""+self.papel.lower()
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        try:
            cnpj = soup.find('small', class_ = 'd-block fs-4 fw-100 lh-4').text
            setattr(self, '__cnpj', cnpj)
            return cnpj
        except:
            print('CNPJ não encontrado')   

    # Obtem o isin no site adfvn
    def isin(self):
        url='https://br.advfn.com/p.php?pid=qkquote&symbol='+self.papel.lower()
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        isin = soup.find(id = 'quoteElementPiece5').text 
        setattr(self, '__isin', isin)
        return isin
        
    # Busca o código cvm no site da cvm
    def cd_cvm(self):
        url=f'https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/CiaAb/ResultBuscaParticCiaAb.aspx?CNPJNome={self.cnpj()}&TipoConsult=C'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        cd_cvm = soup.find(id = 'dlCiasCdCVM__ctl1_Linkbutton5').text  
        setattr(self, '__cd_cvm', cd_cvm)   
        return int(cd_cvm)


# Obtem dados do site investsite   
class Raw:

    def __init__(self, papel):
        self.papel = papel
        self.dados = Dados(self.papel)
        self.isin = self.dados.isin()
        self.series = {}
        
    def raw(self, ind, ano, tri):
    
        tpind = codigos[indice_ind[ind]] if type(ind)==int else codigos[ind]

        if (ind, ano, tri) in self.series:
            return self.series[(ind, ano, tri)] 

        url = 'https://www.investsite.com.br/includes/demonstrativo_tabela_ajax.php'
        
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
        soup = soup.find('table', id=idd).findAll('tr')
        
        th = [i.text.replace('(R$ mil)', '').replace(' ','') for i in soup[0].findAll('th')[:3]]
        td = [[i.text if i.text !='0' else None for i in j.findAll('td')[:3]] for j in soup[2:]]
        
        self.series.update({(ind, ano, tri):[th]+td})
        return [th]+td
        


class Balanco:

    def __init__(self, papel, site=True):
        self.papel=papel
        self.site = site
        self.balanco = Raw(self.papel) if site else None


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
        relatorio = self.__trata_valores(raw)
        
        if not self.ajustado:
            return relatorio
        
        listtri = self.__tri_cons(relatorio)
        
        while len(listtri)>0:
            triant = self.__trata_valores(self.balanco.raw(self.ind,self.ano,listtri[-1:][0]))
            relatorio[1] = self.__subtrai_mes_ant(relatorio[1], triant[1])
            listtri = [i for i in listtri[:-1] if i not in self.__tri_cons(triant)]
            
        relatorio[0][2] = relatorio[0][2].split('a')[-1:][0]

        return relatorio

    # Monta o layout da tabela
    def get(self, ind, ano, tri, ajustado=True):
        self.ind, self.ano, self.tri, self.ajustado = ind, ano, tri, ajustado
        print(f'Obtendo {indice_ind[self.ind]} para {self.papel} referente ao {self.tri}º trimestre de {self.ano}')
        raw = self.raw()
        valores = raw[1]

        ativo = [self.papel for i in valores]

        tabela = {}
        tabela.update({'ativo':['CD_ATIVO', ativo]})
        tabela.update({'conta':['CONTA', 'DS_CONTA', valores[:,[0,1]]], 'valor':['VALOR',valores[:,2]]})
        # adiciona outras colunas
        #encontra trimestre inicial e final
        datas = raw[0][2]
        if not self.ajustado:
            datas = raw[0][2].split('a')
            datas = [[todate(j) for j in datas] for i in valores]
            meses = [i.month for i in datas[0]]
            trimestre = [int(i/3)+1 if i%3 else int(i/3) for i in meses]
            trimestre = [trimestre for i in valores]
            tabela.update({'dataref': ['DATA_REF_INI', 'DATA_REF_FIM', datas]})
            tabela.update({'trimestre': ['TRIMESTRE_INI', 'TRIMESTRE_FIM', trimestre]})
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

        tabela1 =  tabela['ativo'][-1]
        colunas = tabela['ativo'][:-1]

        # Gera a tabela final
        for i in ['conta', 'relat', 'dataent', 'dataref', 'ano', 'trimestre', 'valor']:
            if i in tabela:
                colunas += tabela[i][:-1]
                tabela1 = np.column_stack([tabela1,tabela[i][-1]])

        return [colunas, tabela1]


# Gera um dataframe       
class Features:
    def __init__(self, head, dados, nome=''):    
        self.dados = np.array(dados)
        self.head = head
        self.ativo = nome
        for j, i in enumerate(self.head):
            setattr(self, i, [z[0] for z in self.dados[:,[j]]])
        
    def __repr__(self):
        ativos = list(self.__dict__)[3:3+len(self.head)]
        return str(self.ativo + '\n' + tabulate(np.concatenate(([ativos], np.column_stack([self.__dict__[i] for i in ativos])))))

    def __getitem__(self, *ativos):
        ativos = ativos[0] if type(ativos[0])==tuple else ativos
        return self.__class__(list(ativos), np.column_stack([self.__dict__[i] for i in ativos]), self.ativo)

    # Retorna os dados em numpy
    def np(self, *features):
        features = list(self.__dict__)[3:3+len(self.head)] if len(features)==0 else features
        features = features[0] if type(features[0])==tuple else features     
        return [[i for i in features], [np.column_stack([self.__dict__[i] for i in features])][0], self.ativo]
        

# As classes abaixo buscam cotações históricas e intraday
class Series:

    def __init__(self, papel):
        self.__papel = papel if type(papel)==list else [papel]
        self.__id = self.__acao_id()
        self.__head=''
        self.__dataini=20000101
        self.__datafin=20300101
    # Encontra o código das ações na uol
    def __acao_id(self):
        url = f"""http://cotacoes.economia.uol.com.br/ws/asset/stock/list?size=10000"""
        response = requests.get(url, headers=headers).json()
        return response

    # Busca as cotações
    def __busca_dados(self, papel, tipo):
        tipo = 'intraday/list' if tipo == 'intraday' else 'interday/list/years'
        # obtem os IDs da uol
        id = [i for i in self.__id['data'] if i['code']==papel+'.SA'] if papel != 'IBOVESPA' else [{'idt':'1'}]

        if len(id)>0:
            id = id[0]['idt']
            url = f"""https://api.cotacoes.uol.com/asset/{tipo}/?format=JSON&fields=date,price,high,low,open,volume,close,bid,ask&item={id}&"""
            response = requests.get(url, headers=headers).json()
            self.__head=[j for j in response['docs'][0]] if self.__head=='' else self.__head
            return [[float(i[j]) for j in i] for i in response['docs'] if int(i['date'][:len(str(self.__dataini))]) >= self.__dataini and int(i['date'][:len(str(self.__dataini))])<=self.__datafin]
            

    # busca todas as cotações
    def __dados(self, tipo='interday'):
        series1 = [[i, self.__busca_dados(i, tipo)] for i in self.__papel]
        acoes = [i[0] for i in series1 if i[1]]
        series = [i[1] for i in series1 if i[1]]
        
        # papeis não encontrados
        nones = [i[0] for i in series1 if not i[1]]
        if len(nones)>0:
            print('Os ativos: ' + ', '.join(nones) + ', não foram encontrados')
        
        return self.__head, series, acoes
    
    def historico(self, data1 = [2010, 2030], dataini=0):
        data1 = data1 if type(data1)==list else [data1]
        self.__dataini=min(data1) if dataini == 0 else dataini
        self.__datafin=max(data1) if dataini == 0 else 20300101
        dados = self.__dados('interday')
        hist = Serie(dados) if len(self.__papel)>1 else Features_series(dados[0], dados[1][0], dados[2][0])
        self.__dataini=20000101 
        self.__datafin=20300101
        return hist

    def intraday(self):
        dados = self.__dados('intraday')
        return Serie(dados) if len(self.__papel)>1 else Features_series(dados[0], dados[1][0], dados[2][0])
        
        



class Features_series(Features):

    def __init__(self, head, dados, nome):
        super().__init__(head, dados, nome)
    # Gera a coluna de retornos dia a dia
    def gera_retornos(self):
        precos = self.__dict__['price']
        dados, retornos = self.dados, np.array([np.log(precos[i]/precos[i+1]) for i in range(len(precos[:-1]))])
        return self.__class__(list(self.__dict__)[3:]+['retornos'], np.column_stack([dados, np.append(retornos,0)]), self.ativo) 
      
    # Gera coluna com as curvas moveis
    def curvas_moveis(self, n):
        precos = self.__dict__['price']
        curvas = [sum(precos[i:(i+n)])/len(precos[i:(i+n)]) for i in range(len(precos)-(n-1))]
        curvas = np.append(curvas, [0 for i in range(n-1)])
        return self.__class__(list(self.__dict__)[3:]+['curva_movel'], np.column_stack([self.dados, curvas]), self.ativo)      
        
      

    


class Serie:

    def __init__(self, dados):
        self.dados = dados[1]
        self.head = dados[0]
        self.ativos = dados[2]
        
        for j, i in enumerate(self.ativos):
            setattr(self, i, Features_series(self.head, self.dados[j], i))
            

    def __repr__(self):
        if len(self.dados)==1:
            return str(tabulate(np.concatenate(([self.head], np.array(self.dados[0])))))
        else:
            return ','.join(self.ativos)
            

    def __getitem__(self, ativo):
        return self.__dict__[ativo]
        
    # Gera a matriz de correlação
    def matriz_correl(self):
        ativos = list(self.__dict__)[3:]
        retornos = [self.__dict__[i].gera_retornos().retornos for i in ativos]
        return [[[pearsonr(i[:min(len(i), len(j))-1], j[:min(len(i), len(j))-1])[0] for j in retornos] for i in retornos], self.ativos]


    














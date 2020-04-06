from bs4 import BeautifulSoup
import requests
import numpy as np
import json
from tabulate import tabulate
from scipy.stats import norm
from scipy.stats import pearsonr


mes_trimestre = {
3:1, 6:2, 9:3, 12:4
}

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def teste():
    print('b')

# retira acentos de uma string
def ascii(str):
    a={}
    [[a.update({j:'aeiouc'[n]}) for j in i] for n, i in enumerate(['áàâã','éê','í','óòôõ','ú','ç'])]
    nome = ''.join([a[i] if i in a else i for i in str])
    return nome

# Obtem o cnpj e isin
def cnpj(papel):
 
    cd = cd_cvm(papel)

    url='http://bvmf.bmfbovespa.com.br/pt-br/mercados/acoes/empresas/ExecutaAcaoConsultaInfoEmp.asp?CodCVM='+str(cd)
    
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, 'html.parser').find('ul', class_='accordion').findAll('tr')
    
    tipo_papel = 'ACNOR' if int(papel[-1:]) == 3 else 'ACNPR'
    
    return {'isin' : [i.replace(',','') for i in list(set(soup[1].text.split())) if i[6:11] == tipo_papel][0],
            'CNPJ' : soup[2].text.split()[1]}
    
    
  
        
# Busca o código cvm
def cd_cvm(papel):
    url = f'http://bvmf.bmfbovespa.com.br/cias-listadas/empresas-listadas/BuscaEmpresaListada.aspx?Nome={papel}&idioma=pt-br'
    for i in range(20):
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.content, 'html.parser')
        codigo = soup.find('tr', class_='GridRow_SiteBmfBovespa GridBovespaItemStyle')
        if codigo != None:
            break
        elif i==19:
            print('Número de tentativas excedidads para o site da B3!!')   
    codigo = codigo.find('td').find('a')['href']
    codigo[codigo.find('codigoCvm=')+len('codigoCvm='):]
    return int(codigo[codigo.find('codigoCvm=')+len('codigoCvm='):])
    
    
    
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

class Dados:

    def __init__(self, papel):
        self.papel = papel

    # Obtem o nome e cnpj da ação no site status invest
    def cnpj(self):
        return cnpj(self.papel)
        
    # Busca o nome da empresa listada na cvm e o código
    def cd_cvm(self):
        return cd_cvm(self.papel)


# Obtem dados do site investsite   
class RawIndicador:

    def __init__(self, papel):
        self.papel = papel
        self.dados = Dados(self.papel)
        self.isin = self.dados.cnpj()['isin']
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
        


class Indicador:

    def __init__(self, papel, site=True):
        self.papel=papel
        self.indicador = RawIndicador(self.papel) if site else None


    # Transforma os valores em float
    def __trata_valores(self, dados):
        campos = np.array(dados[0])
        contents = dados[1:]
        contents = np.array(contents, dtype=object)
        contents[:,2] = [float(i.replace('.','').replace(',','.')) if i else None for i in contents[:,2]]
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
        
        
    def serie(self, ind, ano, tri, ajustado=True):
        raw = self.indicador.raw(ind,ano,tri)
        relatorio = self.__trata_valores(raw)
        
        if not ajustado:
            return relatorio
        
        listtri = self.__tri_cons(relatorio)
        
        while len(listtri)>0:
            triant = self.__trata_valores(self.indicador.raw(ind,ano,listtri[-1:][0]))
            relatorio[1] = self.__subtrai_mes_ant(relatorio[1], triant[1])
            listtri = [i for i in listtri[:-1] if i not in self.__tri_cons(triant)]
            
        relatorio[0][2] = relatorio[0][2].split('a')[-1:][0]

        return relatorio
        


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
        hist = Serie(dados) if len(self.__papel)>1 else Features([dados[0], dados[1][0], dados[2][0]])
        self.__dataini=20000101 
        self.__datafin=20300101
        return hist

    def intraday(self):
        dados = self.__dados('intraday')
        return Serie(dados) if len(self.__papel)>1 else Features([dados[0], dados[1][0], dados[2][0]])
        
        
class Features:
    def __init__(self, dados):    
        self.__dados = np.array(dados[1])
        self.__head = dados[0]
        self.__ativo = dados[2]
        for j, i in enumerate(self.__head):
            setattr(self, i, [z[0] for z in self.__dados[:,[j]]])

        
    def __repr__(self):
        ativos = list(self.__dict__)[3:]
        return str(self.__ativo + '\n' + tabulate(np.concatenate(([ativos], np.column_stack([self.__dict__[i] for i in ativos])))))

    def __getitem__(self, *ativos):
        ativos = ativos[0] if type(ativos[0])==tuple else ativos
        return Features([list(ativos), np.column_stack([self.__dict__[i] for i in ativos]), self.__ativo])

    # Gera a coluna de retornos dia a dia
    def gera_retornos(self):
        precos = self.__dict__['price']
        dados, retornos = self.__dados, np.array([np.log(precos[i]/precos[i+1]) for i in range(len(precos[:-1]))])
        return Features([list(self.__dict__)[3:]+['retornos'], np.column_stack([dados, np.append(retornos,0)]), self.__ativo]) 
      
    def curvas_moveis(self, n):
        precos = self.__dict__['price']
        curvas = [sum(precos[i:(i+n)])/len(precos[i:(i+n)]) for i in range(len(precos)-(n-1))]
        curvas = np.append(curvas, [0 for i in range(n-1)])
        return Features([list(self.__dict__)[3:]+['curva_movel'], np.column_stack([self.__dados, curvas]), self.__ativo])      
        
      
    # Retorna os dados em numpy
    def np(self, *features):
        features = list(self.__dict__)[3:] if len(features)==0 else features
        features = features[0] if type(features[0])==tuple else features     
        return [[i for i in features], [np.column_stack([self.__dict__[i] for i in features])][0], self.__ativo]
        
    


class Serie:

    def __init__(self, dados):
        self.dados = dados[1]
        self.head = dados[0]
        self.ativos = dados[2]
        
        for j, i in enumerate(self.ativos):
            setattr(self, i, Features([self.head, self.dados[j], i]))
            

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


    














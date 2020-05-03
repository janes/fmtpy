# Esse pacote obtem os dados do site Investsite.com e da Uol


import requests
import numpy as np
import json
from tabulate import tabulate
from scipy.stats import norm
from scipy.stats import pearsonr

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

#  Encontra os dias úteis a partir da petrobras
dus=None
def dias_uteis():
    global dus
    if not dus:
        dus = Series(['PETR4']).historico().date.tolist()

# Gera um dataframe       
class Features:
    def __init__(self, head, dados, nome=''):    
        self.dados = np.array(dados)
        self.head = head
        self.ativo = nome

        for j, i in enumerate(self.head):
            setattr(self, i, self.dados[:,j])
        
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
        val = [np.column_stack([self.__dict__[i] for i in features])][0] if len(features)>1 else self.__dict__[features[0]]
        features1 = [[i for i in features], val, self.ativo]
        return features1
        

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
        id = [i for i in self.__id['data'] if i['code']==papel+'.SA'] if papel != 'IBOV' else [{'idt':'1'}]

        if len(id)>0:
            id = id[0]['idt']
            url = f"""https://api.cotacoes.uol.com/asset/{tipo}/?format=JSON&fields=date,price,high,low,open,volume,close,bid,ask&item={id}&"""
            response = requests.get(url, headers=headers).json()
            self.__head=[j for j in response['docs'][0]] if self.__head=='' else self.__head
            s = [[float(i[j]) for j in i] for i in response['docs'] if int(i['date'][:len(str(self.__dataini))]) >= self.__dataini and int(i['date'][:len(str(self.__dataini))])<=self.__datafin]
            s = np.array(s)
            s = np.array([i for n, i in enumerate(s) if i[0]!=s[n-1][0]]).tolist()
            return s


    # busca todas as cotações
    def __dados(self, tipo='interday'):
        series1 = [[i, self.__busca_dados(i, tipo)] for i in self.__papel]
        acoes = [i[0] for i in series1 if i[1]]
        series = [i[1] for i in series1 if i[1]]
        
        # papeis não encontrados
        nones = [i[0] for i in series1 if not i[1]]
        if len(nones)>0:
            print('Os ativos: ' + ', '.join(nones) + ', não foram encontrados')
        
        return [self.__head, series, acoes]
    
    # Gera cotaões historicas
    def historico(self, data1 = [2010, 2030], dataini=0):
        # Gera os dias úteis
        if self.__papel != ['PETR4']: 
            dias_uteis()
    
        data1 = data1 if type(data1)==list else [data1]
        self.__dataini=min(data1) if dataini == 0 else dataini
        self.__datafin=max(data1) if dataini == 0 else 20300101
        dados = self.__dados('interday')
        dados[1] = [np.array(i) for i in dados[1]]
        for n, i in enumerate(dados[1]):
            dados[1][n][:,0] = [i/1000000 for i in i[:,0]]
        dados[1] = [i[np.isin(i[:,0], dus)].tolist() for i in dados[1]] if self.__papel != ['PETR4'] else dados[1]
        hist = Serie(dados) if len(self.__papel)>1 else Features_series(dados[0], dados[1][0], dados[2][0])
        self.__dataini=20000101 
        self.__datafin=20300101
        return hist

    # Gera cotações do último dia ou atual
    def intraday(self):
        dados = self.__dados('intraday')
        return Serie(dados) if len(self.__papel)>1 else Features_series(dados[0], dados[1][0], dados[2][0])
        


class Features_series(Features):

    def __init__(self, head, dados, nome):
        super().__init__(head, dados, nome)
        # 0 para retornos log, 1 para retorno comum

    def retorno(self, p1, p2, tipo):
        retorno = (p1/p2)-1 if tipo else np.log(p1/p2)
        return retorno

    # Gera a coluna de retornos dia a dia
    def gera_retornos(self, tipo=0):
        precos = self.__dict__['price']
        dados, retornos = self.dados, np.array([self.retorno(precos[i],precos[i+1], tipo) for i in range(len(precos[:-1]))])
        return self.__class__(list(self.__dict__)[3:]+['retornos'], np.column_stack([dados, np.append(retornos,0)]), self.ativo) 
      
    # Gera coluna com as curvas moveis
    def curvas_moveis(self, n):
        precos = self.__dict__['price']
        curvas = [sum(precos[i:(i+n)])/len(precos[i:(i+n)]) for i in range(len(precos)-(n-1))]
        curvas = np.append(curvas, [0 for i in range(n-1)])
        return self.__class__(list(self.__dict__)[3:]+['curva_movel'], np.column_stack([self.dados, curvas]), self.ativo)      
        
    # Simula o resultado de operações seguindo uma curva móvel
    def simulacao(self, n, valor):
        curvas = self.curvas_moveis(n)['date','price','curva_movel'].np()
        curvas[1] = np.column_stack([curvas[1], [i[1]>i[2] for i in curvas[1]]])
        cv = curvas[1]
        cv[0][3]=0
        cv = np.array([cv[i] for i in range(len(cv)) if cv[i][3] not in [np.concatenate([cv,cv[-1:]])[i+1][3]]])
        if cv[-1][3] == 1:
            cv = cv[:-1]
        if cv[-1][3] == 0:
            cv = cv[:-1]
        qtd = int(valor/cv[-1][1])
        return sum([-(i[1]*qtd) if i[3] else i[1]*qtd for i in cv])

    # Gera o coeficiente beta
    def coefbeta(self, tipo=0):
        r = self.gera_retornos(tipo).retornos[:-1]
        if len(str(int(self.date.min()))) > 8:
            ibov = Series('IBOV').intraday()   
        else:
            t = [int(self.date.min()), int(self.date.max())]
            ibov = Series('IBOV').historico(t)

        ribov = ibov.gera_retornos(tipo).retornos[:-1]
        cov = np.cov(r, ribov)[0][1]
        beta = cov/np.var(ribov, ddof=1)
        return beta
        


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
        self.gera_retornos()
        retornos = [self.__dict__[i].retornos for i in ativos]
        return [[[pearsonr(i[:min(len(i), len(j))-1], j[:min(len(i), len(j))-1])[0] for j in retornos] for i in retornos], self.ativos]

    # Gera a coluna de retornos dia a dia
    def gera_retornos(self):
        for i in self.ativos:
            if 'retornos' not in self.__dict__[i].__dict__:
                self.__dict__[i] = self.__dict__[i].gera_retornos()

    # Gera coluna de curvas moveis
    def curvas_moveis(self, n):
        for i in self.ativos:
            if 'curva_movel' not in self.__dict__[i].__dict__:
                self.__dict__[i] = self.__dict__[i].curvas_moveis(n)












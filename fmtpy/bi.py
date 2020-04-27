import main
import sqlite3
import numpy as np
import pandas as pd
#from fmtpy import main
import main
#from fmtpy import cvmpy as cvm
import cvmpy as cvm
from datetime import datetime, date

class sqlite:
    def __init__(self, banco):
        self.banco = banco
        self.connect()
        self.formato_sql = {
            int:'int',
            str:'varchar',
            float:'decimal(18,2)',
            date:'date',
            datetime:'datetime'
        }

    def connect(self):
        self.cnn = sqlite3.connect(self.banco)
        self.cursor = self.cnn.cursor()

    def close(self):
        self.cnn.close()

    # Cria a tabela no sql
    def create_table(self, campos, valores, nome):
        cols = [campos[n] + ' ' + self.formato_sql[type(i)] for n, i in enumerate(valores[0])]
        cols = ', '.join(cols)
        query = f'CREATE TABLE {nome} ({cols})'
        self.cursor.execute(query)

    # Insere na tabela no sql
    def insert_into(self, nome, valores):
        self.cursor.execute(f"select * from {nome}")
        cols = list(map(lambda x: x[0], self.cursor.description))
        query = f"insert into {nome} ({', '.join(cols)})values ({', '.join(['?' for i in cols])})"
        for i in valores:
            self.cursor.execute(query, tuple(i))
        self.cnn.commit()

    # Verifica se a tabela existe
    def table_exist(self, nome):
        self.cursor.execute(f"select count(*) from sqlite_master where type='table' and name='{nome}'")
        return self.cursor.fetchone()[0]

    # Deleta de uma tabela de acordo com condições
    def delete_from(self, nome, **campos):
        cond = [f"{i} = '{campos[i]}'" for i in campos]
        cond = ' and '.join(cond)
        query = f' delete from {nome} where {cond}'
        self.cursor.execute(query)
        self.cnn.commit()

    # Verifica se registros existem em uma tabela
    def reg_existe(self, nome, **campos):
        if not self.table_exist(nome):
            return 0
        cond = [f"{i} = '{campos[i]}'" for i in campos]
        cond = ' and '.join(cond)
        query = f' select count(*) from {nome} where {cond}'
        self.cursor.execute(query)
        return self.cursor.fetchone()[0]

    # Exporta para o sql
    def to_sql(self, nome, campos, valores, seexiste='fail'):
        if self.table_exist(nome):
            if seexiste == 'replace':
                self.cursor.execute('drop table ' + nome)    
                self.create_table(campos, valores, nome)
                self.insert_into(nome, valores)
            elif seexiste == 'append':
                self.insert_into(nome, valores)
            elif seexiste == 'fail':
                print('ERRO: A tabela já existe')
        else:
            self.create_table(campos, valores, nome)
            self.insert_into(nome, valores)



class Features(main.Features):

    def __init__(self, head, dados, nome=''):
        super().__init__(head, dados, nome)

    # no caso de replace, retorna os dados que serão deletados
    def dictin(self, condicoes=False):
        condicoes = condicoes if type(condicoes)==list else [condicoes]
        return dict(zip(list(condicoes), [self.__dict__[i][0] for i in condicoes]))

    # sobe os dados no sql, caso for sobrescrever os dados, inserir os campos chave no campos
    def to_sql(self, tabela, cnn, campos=False, sobrescrever=True):
        if campos and cnn.table_exist(tabela):
            campos = self.dictin(condicoes=campos)
            if sobrescrever:
                cnn.delete_from(tabela, **campos)
            elif cnn.reg_existe(tabela, **campos):
                return
        cnn.to_sql(tabela, self.head, self.dados, 'append')

    def df(self):
        tabela = self.np()
        return pd.DataFrame(tabela[1], columns=tabela[0])




# Gera as tabelas no layout para o banco de dados pelo site Invest
class BalancosInv(main.Balanco):

    def __init__(self, papel):
        super().__init__(papel)

    def fat_balancos_desagregado(self, ind, ano, tri, sk):
        tabela = self.get(ind,ano,tri,True)
        tabela[0]+=['SK_RELATORIO']
        tabela[1] = np.column_stack([tabela[1], [sk for i in tabela[1]]])
        return Features(tabela[0], tabela[1])['SK_RELATORIO', 'CONTA', 'DS_CONTA', 'VALOR']

    def fat_balancos_agregado(self, ind, ano, tri, sk):
        tabela = self.get(ind,ano,tri,False)
        tabela[0]+=['SK_RELATORIO']
        tabela[1] = np.column_stack([tabela[1], [sk for i in tabela[1]]])
        return Features(tabela[0], tabela[1])['SK_RELATORIO', 'CONTA', 'DS_CONTA', 'VALOR']

    def dim_conta(self, ind, ano, tri):
        tabela = self.get(ind,ano,tri,False)
        return Features(tabela[0], tabela[1])['CONTA', 'DS_CONTA']

    def dim_ativo(self):
        self.balanco.dados.cd_cvm()
        tb_ativo=[['CD_CVM','CD_ATIVO','CNPJ','ISIN'],
        np.array([[self.balanco.dados.cd_cvm_, self.papel,
        self.balanco.dados.cnpj_,
        self.balanco.dados.isin()]], dtype=object)]
        return Features(tb_ativo[0], tb_ativo[1])

    def dim_relatorio(self, ind, ano, tri, sk):
        self.balanco.dados.cd_cvm()
        t1 = self.get(ind,ano,tri,True)[1][0]
        t2 = self.get(ind,ano,tri,False)[1][0]
        tb_relatorio = [['SK_RELATORIO','CD_CVM', 'IND', 'ANO', 'DATA_REF', 'DATA_REF_INI', 
                'DATA_REF_FIN', 'TRIMESTRE', 'TRIMESTRE_INI', 'TRIMESTRE_FIN'],
                        np.array([[sk, self.balanco.dados.cd_cvm_, ind, ano,
                                    t1[4], t2[4], t2[5], t1[6],t2[7], t2[8]]])]

        return Features(tb_relatorio[0], tb_relatorio[1])



# Sobe dados para um banco de dados
class Upload:
    def __init__(self, cnn, acao, anos):
        self.cnn = cnn
        self.acao = acao if type(acao)==list else [acao]
        anos = anos if type(anos)==list else [anos]
        self.anos = range(min(anos), max(anos)+1)

    def go(self):
        print("%.2f" % (0) + ' %', end='\r')
        for n, papel in enumerate(self.acao):
            print(papel +' ' "%.2f" % ((n+1)/len(self.acao)*100) + ' %'+' '*10, end='\r')
            self.balanco = BalancosInv(papel)
            cd_cvm=False
            isin = False
            # verifica se o ativo já existe no banco de dados
            try:   
                cd_cvm = self.cnn.cursor.execute(f"select cd_cvm, cnpj, isin from dim_ativo where CD_ATIVO=='{papel}'").fetchone() if \
                        self.cnn.table_exist('dim_ativo') else False
                self.balanco.balanco.dados.cd_cvm_ = cd_cvm[0] if cd_cvm else self.balanco.balanco.dados.cd_cvm()
                self.balanco.balanco.dados.cnpj_ = cd_cvm[1] if cd_cvm else self.balanco.balanco.dados.cnpj()
                self.balanco.balanco.dados.__isin = cd_cvm[2] if cd_cvm else self.balanco.balanco.dados.isin()
                cd_cvm = self.balanco.balanco.dados.cd_cvm_ 
                isin = self.balanco.balanco.dados.__isin
            except:
                pass
            if cd_cvm and isin:
                if not self.cnn.reg_existe('dim_ativo', CD_ATIVO=papel):
                    self.balanco.dim_ativo().to_sql('dim_ativo', self.cnn, campos=['CD_CVM'])
                anos_disp = self.anos_disponiveis(papel)[:-1]
                for ano in self.anos:
                    if ano in anos_disp:
                        for tri in [1,2,3,4]:
                            for ind in [1,2,3,4,5]:
                                try:
                                    self.input(ind, ano, tri)
                                except:
                                    self.cnn.to_sql('upload_erros', ['CD_ATIVO', 'IND', 'ANO', 'TRI'],
                                                    [[papel, ind, ano, tri]], 'append', campos=['CD_ATIVO'])

            
                

    def input(self, ind, ano, tri):
        # Defininfo o SK_RELATORIO
        if self.cnn.table_exist('dim_relatorio'):
            sk_relatorio = self.cnn.cursor.execute(f"""select SK_RELATORIO from dim_relatorio where 
                                CD_CVM = {self.balanco.balanco.dados.cd_cvm_} and IND = {ind} and ANO = {ano} and TRIMESTRE = {tri}""").fetchall()
            if sk_relatorio:
                sk_relatorio = sk_relatorio[0][0]
            else:
                ultimo = self.cnn.cursor.execute('select max(SK_RELATORIO) from dim_relatorio').fetchall()[0][0]
                sk_relatorio = ultimo+1
        else:
            sk_relatorio = 1
    
        for i in ['dim_relatorio','fat_balancos_agregado', 'fat_balancos_desagregado']:
            if not self.cnn.reg_existe(i, 
                    SK_RELATORIO = sk_relatorio):
                if self.balanco.balanco.raw(ind,ano,tri):
                    exec(f"""self.balanco.{i}(ind, ano, tri, sk_relatorio).to_sql(i,self.cnn, campos=['SK_RELATORIO'])""")

    def dim_indicador(self):
            self.cnn.to_sql('dim_indicador', ['IND', 'DS_IND'], [[i, main.indice_ind[i]] for i in main.indice_ind], 'replace')

    # Encontra os anos que o papel possui balanço
    def anos_disponiveis(self, papel):
        url = f"""https://www.investsite.com.br/demonstracao_resultado.php?cod_negociacao={papel}"""
        response = main.requests.get(url)
        soup = main.BeautifulSoup(response.content, 'html.parser')
        anos_disp = soup.find(id='ano_dem').find_all('option')
        return [int(i.text) for i in anos_disp]

# Nome dos ativos no site da uol
def ativos_uol():
    url = f"""http://cotacoes.economia.uol.com.br/ws/asset/stock/list?size=10000"""
    response = main.requests.get(url).json()
    return [i['code'][:i['code'].find('.')] for i in response['data']]
        
# Retorna os dados de balanços do banco de dados
class Balanco:
    def __init__(self, papel, cnn):
        self.papel=papel
        self.cnn = cnn
        
    def get(self, ind, ano, tri, ajustado=True):
        if ajustado:
            tab = self.cnn.cursor.execute(f"""select CD_ATIVO, DS_IND, a.CONTA, 
                DS_CONTA, DATA_REF, ANO, TRIMESTRE, VALOR from fat_balancos_desagregado a
                inner join dim_relatorio b
                on a.SK_RELATORIO = b.SK_RELATORIO
                inner join dim_ativo c
                on b.CD_CVM = c.CD_CVM
                inner join dim_indicador d
                on b.IND = d.IND
                where c.CD_ATIVO = '{self.papel}' and b.IND = {ind} and b.ANO = {ano} and b.TRIMESTRE = {tri}""")
        else:
            tab = self.cnn.cursor.execute(f"""select CD_ATIVO, DS_IND, a.CONTA, 
                DS_CONTA, DATA_REF_INI, DATA_REF_FIN, ANO, TRIMESTRE_INI, TRIMESTRE_FIN, VALOR from fat_balancos_agregado a
                inner join dim_relatorio b
                on a.SK_RELATORIO = b.SK_RELATORIO
                inner join dim_ativo c
                on b.CD_CVM = c.CD_CVM
                inner join dim_indicador d
                on b.IND = d.IND
                where c.CD_ATIVO = '{self.papel}' and b.IND = {ind} and b.ANO = {ano} and b.TRIMESTRE = {tri}""")
                   
        valores = tab.fetchall()
        if len(valores):
            tabela = [[i[0] for i in tab.description], np.array([list(i) for i in valores])]
            return Features(tabela[0], tabela[1])
        else:
            print('Não encontrado')
        






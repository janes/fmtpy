import main
import sqlite3
import numpy as np
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
    def to_sql(self, tabela, cnn, campos=False):
        # se não for sobrescrever, os dados não são adicionados se já existirem
        if campos:
            campos = self.dictin(condicoes=campos)
            cnn.delete_from(tabela, **campos)

        cnn.to_sql(tabela, self.head, self.dados, 'append')



class Balancos(cvm.Balanco):
    def __init__(self, papel, wdriver = 'chromedriver.exe'):
        super().__init__(papel, wdriver)

    def fat_balancos_cvm_desagregado(self, ind, ano, tri):
        return self.get(ind,ano,tri,True)

    def fat_balancos_cvm_agregado(self, ind, ano, tri):
        return self.get(ind,ano,tri,False)

    def dim_ativo(self):
        tb_ativo=[['CD_ATIVO','CD_CVM','CNPJ','ISIN'],
        np.array([[self.papel, self.balanco.dados.cd_cvm,
        self.balanco.dados.cnpj,
        self.balanco.dados.isin()]])]
        return tb_ativo

    def dim_relatorios(self):
        relat = self.balanco.relatorios[self.ano]
        relatorios = np.array([list(relat[i]) for i in relat])
        relatorios = np.column_stack([relatorios, list(relat)])
        relatorios = np.column_stack([relatorios, [self.ano for i in list(relat)]])
        relatorios = np.column_stack([relatorios, [self.papel for i in list(relat)]])

        tb_relatorio = [['DATA_REF','DATA_ENT','CD_RELATORIO','TRIMESTRE', 'ANO', 'CD_ATIVO'], relatorios]
        tb_relatorio = Features(tb_relatorio[0], tb_relatorio[1])\
            ['CD_ATIVO', 'CD_RELATORIO', 'ANO', 'TRIMESTRE', 'DATA_REF', 'DATA_ENT']

        return tb_relatorio.np()[:2]


    def dim_relatorios_datas_aggs(self, ind, ano, tri):
        relat = self.balanco.relatorios[self.ano]
        relat = [['CD_ATIVO', 'CD_RELATORIO', 'ANO', 'TRIMESTRE_INI', 'TRIMESTRE_FIM', 'DATA_REF_INI', 'DATA_REF_FIM'],
                    np.array([[self.papel,self.balanco.relatorios[self.ano][self.tri][2], self.ano] + self.trimestres + self.datas])]
        return relat


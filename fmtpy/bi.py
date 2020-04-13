import main
import sqlite3
import numpy as np
#from fmtpy import main
import main
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

    def to_sql(self, banco, replace=False):
        banco







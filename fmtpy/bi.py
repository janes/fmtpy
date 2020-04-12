import main
import sqlite3
from fmtpy import main
#import main


# Cria a tabela no sql
def create_table(campos, valores, nome):
    cols = [campos[n] + ' ' + formato_sql[type(i)] for n, i in enumerate(valores[0])]
    cols = ', '.join(cols)
    query = f'CREATE TABLE {nome} ({cols})'
    cursor.execute(query)

# Insere na tabela no sql
def insert_into(nome, valores):
    cursor.execute(f"select * from {nome}")
    cols = list(map(lambda x: x[0], cursor.description))
    query = f"insert into {nome} ({', '.join(cols)})values ({', '.join(['?' for i in cols])})"
    for i in valores:
        cursor.execute(query, tuple(i))
    conn.commit()

# Verifica se a tabela existe
def table_exist(nome):
    cursor.execute(f"select count(*) from sqlite_master where type='table' and name='{nome}'")
    return cursor.fetchone()[0]

# Exporta para o sql
def to_sql(nome, campos, valores, con, seexiste='fail'):
    cnn = con
    cursor = cnn.cursor()
    if table_exist(nome):
        print(1)
        if seexiste == 'replace':
            cursor.execute('drop table ' + nome)    
            create_table(campos, valores, nome)
            insert_into(nome, valores)
        elif seexiste == 'append':
            insert_into(nome, valores)
        elif seexiste == 'fail':
            print('ERRO: A tabela já existe')
    else:
        print(0)
        create_table(campos, valores, nome)
        insert_into(nome, valores)



class Features(main.Features):

    def __init__(self, dados):
        super().__init__(dados[0], dados[1], dados[2])






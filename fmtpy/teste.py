


# Gera as tabelas no layout para o banco de dados
class Balancos(cvm.Balanco):
    def __init__(self, papel, wdriver = 'chromedriver.exe'):
        super().__init__(papel, wdriver)

    def fat_balancos_cvm_desagregado(self, ind, ano, tri):
        tabela = self.get(ind,ano,tri,True)
        tabela[0]+=['CD_CVM']
        tabela[1][:,1]=[ind for i in tabela[1]]
        tabela[1] = np.column_stack([tabela[1], [self.balanco.dados.cd_cvm_ for i in tabela[1]]])
        return Features(tabela[0], tabela[1])['CD_CVM', 'IND', 'CD_RELATORIO', 'CONTA', 'VALOR']

    def fat_balancos_cvm_agregado(self, ind, ano, tri):
        tabela = self.get(ind,ano,tri,False)
        tabela[0]+=['CD_CVM']
        tabela[1][:,1]=[ind for i in tabela[1]]
        tabela[1] = np.column_stack([tabela[1], [self.balanco.dados.cd_cvm_ for i in tabela[1]]])
        return Features(tabela[0], tabela[1])['CD_CVM', 'IND', 'CD_RELATORIO', 'CONTA', 'VALOR']

    def dim_conta(self, ind, ano, tri):
        tabela = self.get(ind,ano,tri,False)
        return Features(tabela[0], tabela[1])['CONTA', 'DS_CONTA']

    def dim_ativo(self):
        tb_ativo=[['CD_CVM','CD_ATIVO','CNPJ','ISIN'],
        np.array([[self.balanco.dados.cd_cvm_, self.papel,
        self.balanco.dados.cnpj_,
        self.balanco.dados.isin()]], dtype=object)]
        return Features(tb_ativo[0], tb_ativo[1])

    def dim_relatorios(self, ano):
        relat = self.balanco.relatorios[ano]
        relatorios = np.array([list(relat[i]) for i in relat])
        relatorios = np.column_stack([relatorios, list(relat)])
        relatorios = np.column_stack([relatorios, [ano for i in list(relat)]])
        relatorios = np.column_stack([relatorios, [self.balanco.dados.cd_cvm_ for i in list(relat)]])

        tb_relatorio = [['DATA_REF','DATA_ENT','CD_RELATORIO','TRIMESTRE', 'ANO', 'CD_CVM'], relatorios]
        tb_relatorio = Features(tb_relatorio[0], tb_relatorio[1])\
            ['CD_CVM', 'CD_RELATORIO', 'ANO', 'TRIMESTRE', 'DATA_REF', 'DATA_ENT']

        return tb_relatorio


    def dim_relatorios_datas_aggs(self, ind, ano, tri):
        tb_relatorio = [['CD_CVM', 'IND', 'CD_RELATORIO', 'ANO','DATA_REF_INI', 
                'DATA_REF_FIN', 'TRIMESTRE_INI', 'TRIMESTRE_FIN'],
                        np.array([self.datarefs[(ind, ano, tri)]])]

        return Features(tb_relatorio[0], tb_relatorio[1])



class Upload:
    def __init__(self, cnn, acao, anos, wdriver = 'chromedriver.exe'):
        self.cnn = cnn
        self.wdriver = wdriver
        self.acao = acao if type(acao)==list else [acao]
        anos = anos if type(anos)==list else [anos]
        self.anos = range(min(anos), max(anos)+1)

    def go(self):
        for papel in self.acao:
            self.balanco = Balancos(papel,self.wdriver)
            # Verifica se a empresa existe no banco
            cd_cvm=False
            try:   
                cd_cvm = self.cnn.cursor.execute(f"select cd_cvm, cnpj from dim_ativo where CD_ATIVO=='{papel}'").fetchone() if \
                        self.cnn.table_exist('dim_ativo') else False
                self.balanco.balanco.dados.cd_cvm_ = cd_cvm[0] if cd_cvm else self.balanco.balanco.dados.cd_cvm()
                self.balanco.balanco.dados.cnpj_ = cd_cvm[1] if cd_cvm else self.balanco.balanco.dados.cnpj()
                cd_cvm = self.balanco.balanco.dados.cd_cvm_ 
                print(1)
            except:
                pass
            if cd_cvm:
                if not self.cnn.reg_existe('dim_ativo', CD_ATIVO=papel):
                    self.balanco.dim_ativo().to_sql('dim_ativo', self.cnn, campos=['CD_CVM'])
                print(3)
                for ano in self.anos:
                    print(ano)
                    self.balanco.balanco.relatorios.update(self.relatorios_bd(ano))
                    if self.balanco.balanco.relatorios_cvm(ano):
                        self.balanco.dim_relatorios(ano).to_sql('dim_relatorios', self.cnn, campos=['CD_CVM', 'ANO'])
                        for tri in [i for i in self.balanco.balanco.relatorios[ano]]:
                            print(tri)
                            for ind in main.indice_ind:
                                self.input(ind, ano, tri)

    # busca o número dos relatórios na base se já existir
    def relatorios_bd(self, ano):
        query = f'select * from dim_relatorios where CD_CVM={str(self.balanco.balanco.dados.cd_cvm_)} and ANO={str(ano)}'
        relatorios = self.cnn.cursor.execute(query).fetchall() if self.cnn.table_exist('dim_relatorios') else []
        if len(relatorios)==0:
            return {}
        relatorios = np.array([list(i) for i in relatorios], dtype=object)
        for n in [4,5]:
            relatorios[:,n] = [datetime.strptime(i, "%Y-%m-%d").date() for i in relatorios[:,n]]
        return {ano:dict(zip(relatorios[:,3], [i for i in relatorios[:,[4,5,1]]]))}
                    
    def input(self, ind, ano, tri):
    
        for i in ['fat_balancos_cvm_agregado', 'fat_balancos_cvm_desagregado', 'dim_relatorios_datas_aggs']:
            
            if not self.cnn.reg_existe(i, 
                    CD_CVM=self.balanco.balanco.dados.cd_cvm_, IND=ind, 
                    CD_RELATORIO=self.balanco.balanco.relatorios[ano][tri][2]):

                print([i, self.balanco.balanco.dados.cd_cvm_, ind. self.balanco.balanco.relatorios[ano][tri][2]])

                exec(f"""self.balanco.{i}(ind, ano, tri).to_sql(i,self.cnn, campos=['CD_CVM', 'IND', 'CD_RELATORIO'])""")

                if i in ['fat_balancos_cvm_agregado']:
                    self.balanco.dim_conta(ind, ano, tri).to_sql('dim_conta', self.cnn)
                    #remove duplicados na dim_conta
                    self.cnn.cursor.execute('create table temp_dim_conta as select distinct * from dim_conta')
                    self.cnn.cursor.execute('drop table dim_conta')
                    self.cnn.cursor.execute('create table dim_conta as select distinct * from temp_dim_conta')
                    self.cnn.cursor.execute('drop table temp_dim_conta')

















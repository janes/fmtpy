## Esse pacote busca os dados na CVM usando o Selenium, é necessário fazer o download do Chromewebdriver

from bs4 import BeautifulSoup
import requests
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
import numpy as np
import time
from . import Indicador as fmt
from . import Dados as fmtdados

options = webdriver.ChromeOptions()
options.add_argument("--headless")
#--start-maximized
# --headless
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}


mes_semestre = {
3:1, 6:2, 9:3, 12:4
}

# links cvm

link_ind = {
'Resultado' : 'https://www.rad.cvm.gov.br/ENETCONSULTA/frmDemonstracaoFinanceiraITR.aspx?Informacao=2&Demonstracao=4&Periodo=0&Grupo=DFs+Consolidadas&Quadro=Demonstra%c3%a7%c3%a3o+do+Resultado&NomeTipoDocumento=ITR&Empresa=MAGAZ%20LUIZA&DataReferencia=2014-09-30&Versao=1&CodTipoDocumento=3&NumeroSequencialDocumento=',
'Balanço Ativo' : 'https://www.rad.cvm.gov.br/ENETCONSULTA/frmDemonstracaoFinanceiraITR.aspx?Informacao=2&Demonstracao=2&Periodo=0&Grupo=DFs+Consolidadas&Quadro=Balan%C3%A7o+Patrimonial+Ativo&NomeTipoDocumento=&DataReferencia=&Versao=1&CodTipoDocumento=3&NumeroSequencialDocumento=',
'Balanço Passivo': 'https://www.rad.cvm.gov.br/ENETCONSULTA/frmDemonstracaoFinanceiraITR.aspx?Informacao=2&Demonstracao=3&Periodo=0&Grupo=DFs+Consolidadas&Quadro=Balan%c3%a7o+Patrimonial+Passivo&NomeTipoDocumento=ITR&Empresa=MOVIDA&DataReferencia=&Versao=3&CodTipoDocumento=3&NumeroSequencialDocumento=',
'Resultado Abrangente' : 'https://www.rad.cvm.gov.br/ENETCONSULTA/frmDemonstracaoFinanceiraITR.aspx?Informacao=2&Demonstracao=5&Periodo=0&Grupo=DFs+Consolidadas&Quadro=Demonstra%c3%a7%c3%a3o+do+Resultado+Abrangente&NomeTipoDocumento=ITR&Empresa=&DataReferencia=&Versao=1&CodTipoDocumento=3&NumeroSequencialDocumento=',
'Fluxo de Caixa' : 'https://www.rad.cvm.gov.br/ENETCONSULTA/frmDemonstracaoFinanceiraITR.aspx?Informacao=2&Demonstracao=99&Periodo=0&Grupo=DFs+Consolidadas&Quadro=Demonstra%C3%A7%C3%A3o+do+Fluxo+de+Caixa&NomeTipoDocumento=&Empresa=&DataReferencia=&Versao=1&CodTipoDocumento=3&NumeroSequencialDocumento=',
'Valor Adicionado' : 'https://www.rad.cvm.gov.br/ENETCONSULTA/frmDemonstracaoFinanceiraITR.aspx?Informacao=2&Demonstracao=9&Periodo=0&Grupo=DFs+Consolidadas&Quadro=Demonstra%c3%a7%c3%a3o+de+Valor+Adicionado&NomeTipoDocumento=&Empresa=&DataReferencia=&Versao=1&CodTipoDocumento=3&NumeroSequencialDocumento=',
'Mutações do PL' : 'https://www.rad.cvm.gov.br/ENETCONSULTA/frmDemonstracaoFinanceiraITR.aspx?Informacao=200&Demonstracao=8&Periodo=4|6&Grupo=DFs+Consolidadas&Quadro=Demonstra%c3%a7%c3%a3o+das+Muta%c3%a7%c3%b5es+do+Patrim%c3%b4nio+L%c3%adquido&NomeTipoDocumento=&Empresa=&DataReferencia=&Versao=1&CodTipoDocumento=3&NumeroSequencialDocumento='

}

indice_ind = {
1:'Resultado', 2:'Balanço Ativo', 3:'Balanço Passivo', 4:'Resultado Abrangente', 5:'Fluxo de Caixa', 6:'Valor Adicionado', 7:'Mutações do PL'
}


class RawIndicador:

    def __init__(self, papel, wdriver = 'chromedriver.exe'):
        self.papel = papel
        self.dados = fmtdados(self.papel)
        self.cd_cvm = self.dados.cd_cvm()
        self.wdriver = wdriver
        self.relatorios = {}
        self.series = {}
        
    # Extrai o número do relatório do script da B3
    def __num_doc(self, href):  
        strn = 'NumeroSequencialDocumento='
        href = href['href']
        href = href[href.find(strn)+len(strn):]
        return int(href[:href.find('&')])

    # Extrai a data de referência e data de publicação do relatório do script da B3
    def __datas(self, relat):
        dats = relat['onmouseover']
        strm = 'MontaHint'
        tp = eval(dats[dats.find(strm)+len(strm):][:-2])
        return [tp[0], tp[3][:10]]
        
    # busca no site da B3 as datas e números dos relatórios de um ano para um papel
    def relatorios_cvm(self, ano):
        # Verifica se o ano já foi pesquisado antes para esse objeto
        if ano in self.relatorios:
            return self.relatorios[ano]
        
        url = f'http://bvmf.bmfbovespa.com.br/cias-listadas/empresas-listadas/ResumoDemonstrativosFinanceiros.aspx?codigoCvm={self.cd_cvm}&idioma=pt-br'
        

        for i in range(20):
            response = requests.post(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
  
            viewstate = soup.find('input', id='__VIEWSTATE')
            
            if viewstate != None:
                break
            elif i==19:
                print(url)
                print('Número de tentativas excedidads para o site da B3!!')
                

        viewstate = viewstate['value']
        eventval = soup.find('input', id='__EVENTVALIDATION')['value']
        data = {
            '__EVENTTARGET': 'ctl00$contentPlaceHolderConteudo$cmbAno',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': viewstate,
            '__VIEWSTATEGENERATOR': '72E426D7',
            '__EVENTVALIDATION': eventval,
            'ctl00$contentPlaceHolderConteudo$MenuEmpresasListadas1$tabMenuEmpresa':' {"State":{},"TabState":{"ctl00_contentPlaceHolderConteudo_MenuEmpresasListadas1_tabMenuEmpresa_tabRelatoriosFinanceiros":{"Selected":true}}}',
            'ctl00$contentPlaceHolderConteudo$cmbAno': str(ano)
            }
            

        # as vezes a página da bolsa precisa de mais de uma tentativa para retornar os dados
        for i in range(20):
            response = requests.post(url, data=data, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            relatorios = [i for i in soup.find_all('a') if "Informações Trimestrais" in i.text or 'Demonstrações Financeiras Padronizadas' in i.text]
            
            if len(relatorios) > 0:
                break
            elif i==19:
                print('Número de tentativas excedidads para o site da B3!!')
                
        
        d = np.array([[mes_semestre[int(self.__datas(i)[0][3:5])]]+self.__datas(i)+[self.__num_doc(i)] for i in relatorios], dtype='object')
        # retorna os números dos relatórios do ano
        dic = dict(zip(d[:,0], d[:,[1,2,3]]))
        self.relatorios.update({ano:dic})
        return dic
        
    def raw(self, ind, ano, tri):
    
        link = link_ind[indice_ind[ind]] if type(ind)==int else link_ind[ind]
        if (ind, ano, tri) in self.series:
            return self.series[(ind, ano, tri)] 
            
        dados = self.relatorios_cvm(ano)
        num = dados[tri][2]

        driver = webdriver.Chrome(self.wdriver, chrome_options=options)
        # instanciar
        url = f'http://www.rad.cvm.gov.br/ENETCONSULTA/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={num}&CodigoTipoInstituicao=2'
        driver.get(url)
        
        url=link+str(num)
        driver.get(url)

        response = driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
        soup = BeautifulSoup(response)
        tabela = soup.find('tbody').findAll('tr')
        
        driver.close()
        tabela = [[i.text.replace('\xa0','') if i.text.replace('\xa0','') not in ('','0') else None for i in j.find_all('td')[:3]] for j in tabela]
        self.series.update({(ind, ano, tri):tabela})   
        
        return tabela


class Indicador(fmt):

    def __init__(self, papel, wdriver = 'chromedriver.exe'):
        super().__init__(papel, False)
        self.driver = wdriver
        self.indicador = RawIndicador(self.papel, self.wdriver)
    






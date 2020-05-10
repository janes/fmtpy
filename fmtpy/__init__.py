# Esse pacote obtem os dados do site Investsite.com e da Uol

from fmtpy import main 
from fmtpy import cvmpy
from fmtpy import invest
from fmtpy import bi
from fmtpy import opcoes
import warnings
warnings.filterwarnings('ignore')


def help():
    print("""
    # Gerar balanços financeiros:
    Método: balancos
        - Paramentros:
            - papel: Indicar o código da ação da empresa a qual deseja obter os balanços
            - wdriver (não obrigatório): Indicar o caminho de um webdriver caso deseja obter os balanços direto do site da cvm
            - cnn (não obrigatório): Indicar a conexão com um banco de dados caso já estiver carregado informações em um banco de dados

            Se nem o wdriver nem o cnn forem indicados, os dados serão buscados no site investsite.com.br, no mesmo padrão da cvm

        O método balancos retorna um objeto da classe Balancos:
            Método: 
                - get:
                    - Parametros:
                        ind: Indica qual o relatório desejado, conforme seguinte índice:
                            1:'Resultado', 
                            2:'Balanço Ativo', 
                            3:'Balanço Passivo', 
                            4:'Valor Adicionado', 
                            5:'Fluxo de Caixa', 
                            6:'Resultado Abrangente' (Este vale apenas para o site da cvm)
                        ano: Ano do relatório desejado
                        tri: Trimestre desejado
                        ajustado (Boolean): Alguns relatórios vem com o valor agregado do ano inteiro (somando os trimestres anteriores) 
                                            Indique True caso queira desagregar o valor. (o padrão é True).

                    retorna os resultados em numpy Array.

                - df:
                    - Parametros:
                        mesmos parametros do get, retorna os resultados em um pandas DataFrame.

            Exemplo:
                empresa = fmtpy.balanco('PETR4')
                resultado = empresa.df(1,2019,4,True)
                
                retorna o relatório de resultados da Petrobras para o 4° trimestre de 2019 desagregado.


    # Séries de ações:
    Classe Series:
        - Paramentros:
            - papel: Indicar um ou mais* códigos da ação da empresa a qual deseja obter os balanços

        Método:
            - histórico:
                - Parâmetros:
                    data1: lista com o período inicial e final no formado AAAAMMDD (pode ser só o ano ou só o mês) 
                        exemplo: se desejar o ano de 2019 inteiro, inserir [201901, 201912] ou apenas [2019]
                    dataini: valor da data no mesmo formato acima indicando a data inicial

                    obs: Se nenhum parametro for inserido, retornará todo o período disponível
                
        
            - intraday:
                retorna a série do dia atual por minuto (ou do último dia)


            * Se apenas um papel for selecionado, retornará a classe Features. Os métodos estão descritos abaixo:
                - gera_retornos:
                    Adiciona a coluna coma série de retornos em percentual:
                    - Parâmetros:
                        tipo (padrão = 0): 0 gera o log retorno, 1 gera o retorno comum.
                    
                - medias_moveis:
                    Adiciona a coluna com o calculo da média móvel
                    Parâmetros:
                        n: Indica o número de períodos

                - simulacao:
                    Gera o resultado financeiro que seria obtido seguindo uma média móvel.
                    Parâmetros:
                        n: Indica o número de períodos
                        valor: Valor financeiro aplicado

                - coefbeta:
                    Gera o coeficiente beta do ativo no período.
                    Parâmetros:
                        tipo (padrão = 0): 0 gera o log retorno, 1 gera o retorno comum.

                selecionando apenas algumas features:
                    Exemplo:
                        serie = fmtpy.Series(['PETR4']).historico()
                        serie['date', 'price']
                        # isso retorna apenas as featrues date e price 

            * Se mais de um for selecionado, retornará a classe Serie. Essa série contem um conjunto de objetos Features.
                                        Os métodos estão descritos abaixo:
                - gera_retornos:
                    Adiciona a coluna de retornos para todos os ativos
                    - Parâmetros:
                        tipo (padrão = 0): 0 gera o log retorno, 1 gera o retorno comum.

                - medias_moveis:
                    Adiciona a coluna com o calculo da média móvel para todos os ativos
                    Parâmetros:
                        n: Indica o número de períodos

                - matriz_correl:
                    Gera a matriz de correlação dos ativos.
                    - Parâmetros:
                        tipo (padrão = 0): 0 gera o log retorno, 1 gera o retorno comum.     

                Selecionando apenas um ativo:
                    Exemplo:
                        ativos = fmtpy.Series(['PETR4', 'ABEV3']).historico()
                        # ativos['PETR4'] retorna o equivalente a fmtpy.Series('PETR4').historico()


    # Opções
    Classe Opcoes:
        Utiliza as mesmas classes das ações, mas contém apenas um método:
            Método listar:
                retorna a lista de opões do ativo

            exemplo:
                opcoes = fmtpy.Opcoes(['VALE3','PETR4']).listar()
                opcoes['VALE3']
                # retorna as opões de VALE3


    # Sobre:
    Em desenvolvimento por: Fábio Minutti Teixeira.
    https://www.linkedin.com/in/fabiomt/
    https://github.com/Fabiocke
        
    """)

def balancos(papel, wdriver=False, cnn=False):
    if cnn:
        return bi.Balanco(papel, cnn)
    elif wdriver:
        return cvmpy.Balanco(papel, wdriver)
    else:
        return invest.Balanco(papel)



class Series(main.Series):
    def __init__(self, papel):
        super().__init__(papel)


class Opcoes(opcoes.Opcoes):
    def __init__(self, papel):
        super().__init__(papel)







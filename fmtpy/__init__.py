# Esse pacote obtem os dados do site Investsite.com e da Uol

import main 
import cvmpy

class Balancos_invest(main.Indicador):
    def __init__(self, papel):
        super().__init__(papel, True)

class Balancos_cvm(cvmpy.Indicador):
    def __init__(self, papel, wdriver = 'chromedriver.exe'):
        super().__init__(papel, wdriver)


class Series(main.Series):
    def __init__(self, papel):
        super().__init__(papel)







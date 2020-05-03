# Esse pacote obtem os dados do site Investsite.com e da Uol

from fmtpy import main 
from fmtpy import cvmpy
from fmtpy import invest

class Balancos_invest(invest.Balanco):
    def __init__(self, papel):
        super().__init__(papel, True)

class Balancos_cvm(cvmpy.Balanco):
    def __init__(self, papel, wdriver = 'chromedriver.exe'):
        super().__init__(papel, wdriver)


class Series(main.Series):
    def __init__(self, papel):
        super().__init__(papel)







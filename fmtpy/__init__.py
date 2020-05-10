# Esse pacote obtem os dados do site Investsite.com e da Uol

from fmtpy import main 
from fmtpy import cvmpy
from fmtpy import invest
from fmtpy import bi
from fmtpy import opcoes

class BalancosInvest(invest.Balanco):
    def __init__(self, papel):
        super().__init__(papel, True)

class BalancosCVM(cvmpy.Balanco):
    def __init__(self, papel, wdriver = 'chromedriver.exe'):
        super().__init__(papel, wdriver)




def balanco(papel, wdriver=False, cnn=False):
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







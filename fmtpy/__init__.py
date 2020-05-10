# Esse pacote obtem os dados do site Investsite.com e da Uol

from fmtpy import main 
from fmtpy import cvmpy
from fmtpy import invest
from fmtpy import bi
from fmtpy import opcoes
import warnings
warnings.filterwarnings('ignore')


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







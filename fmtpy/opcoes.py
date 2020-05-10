
#from fmtpy import main
import main
import numpy as np
import requests
import json
from tabulate import tabulate

# Lista opções de um papel pelo site opcoes.net
class Opcoes:
    def __init__(self, papel):
        self.papel = papel if type(papel)==list else [papel]

    # Gera os vencimentos
    def vencimentos(self, papel):
        url = f'https://opcoes.net.br/listaopcoes/completa?au=False&uinhc=0&idLista=ML&idAcao={papel}&listarVencimentos=true&cotacoes=true'
        response = requests.get(url).json()
        vctos = [[i['value'], i['text']] for i in response['data']['vencimentos']]
        return vctos

    # Gera as lista de opções
    def lista_opcoes(self, papel):
        vctos = self.vencimentos(papel)
        opc=[]
        for vcto in vctos:
            url=f'https://opcoes.net.br/listaopcoes/completa?au=False&uinhc=0&idLista=ML&idAcao={papel}&listarVencimentos=false&cotacoes=true&vencimentos={vcto[0]}'
            response = requests.get(url).json()
            opc += ([[i[0][:i[0].find('_')]] + i[2:4] + [main.todate(vcto[1])] + [i[5]] + [i[8]] for i in response['data']['cotacoesOpcoes']])
            
        return opc

    # Gera a lista de todos os papeis
    def listar(self):
        opc=[]
        for i in self.papel:
            opc.append(self.lista_opcoes(i))
        if len(self.papel)>1:
            return Serie([['ativo', 'tipo', 'mod', 'vcto', 'strike', 'price'], opc, self.papel])
        else:
            return Features(['ativo', 'tipo', 'mod', 'vcto', 'strike', 'price'], opc[0], self.papel[0])

        

class Features(main.Features):
    def __init__(self, head, dados, nome):
        super().__init__(head,dados,nome)


class Serie(main.Serie):
    def __init__(self, dados):
        super().__init__(dados, Features)



import pandas as pd


def exposition(**kwargs):
    """
        Cette fonction est modulaire selon les arguments qu'on lui transmet:
        - Son but: calculer l'exposition selon l'indice ou les indices et l'echelle soit individuelle ou national
                   souhaitée

        - Parametres: il faut renseigne un dictionnaire contenant la base de données traitée, une liste avec l'indice ou
                      les indices et un booleen si on veut à l'echelle individuelle des entreprises

        -Resultat : une dataframe avec les expositions brute, net et ratio brute net selon nos parametres
    """
    parametres = list(kwargs.keys())
    scale = False
    if len(kwargs[parametres[0]]) < 1:
        raise ValueError('Aucune donnée a été soumise')
    elif kwargs[parametres[1]] is None:
        raise ValueError('Au moins un niveau de filtrage doit etre renseigné')
    elif len(parametres) > 2:
        if len(kwargs[parametres[2]]) > 1:
            raise ValueError("L'échelle n'est pas reconnue")
        else:
            scale = kwargs[parametres[2]]
    index = list(kwargs[parametres[1]])

    def filtering(idx: list, scl: bool):

        buyer = kwargs[parametres[0]]["Buyer"]
        seller = kwargs[parametres[0]]["Seller"]

        buyer = buyer[buyer['Index'].isin(idx)]
        seller = seller[seller['Index'].isin(idx)]

        if scl is False:
            buyer = buyer.groupby(['Country', 'Index'])
            seller = seller.groupby(['Country', 'Index'])
        else:
            buyer = buyer.groupby(['Name', 'Country', 'Index'])
            seller = seller.groupby(['Name', 'Country', 'Index'])

        repository = pd.DataFrame({
            'Gross_Exposure': buyer['Notional'].sum().add(seller['Notional'].sum(), fill_value=0),
            'Net_Exposure': seller['Notional'].sum().subtract(buyer['Notional'].sum(), fill_value=0),
            'Cash_Flow': seller['Cash_Flow'].sum().add(buyer['Cash_Flow'].sum(), fill_value=0)
        }).reset_index()

        repository['Ratio'] = repository.apply(
            lambda row: (row['Net_Exposure'] / row['Gross_Exposure']) if row['Gross_Exposure'] != 0 else 0,
            axis=1
        )
        result = repository
        return result

    return filtering(index, scale)


if __name__ == '__main__':
    from repository import (get_config, set_data, get_directories)

    config_file = get_config()
    data = set_data(get_directories(config_file['files']['names']))
    eonia_exposition = exposition(d=data, i=['EONIA'])
    libor_exposition = exposition(d=data, i=['LIBOR'])
    eonia_libor_expo = exposition(d=data, i=['EONIA', 'LIBOR'])
    firm_eonia_libor_expo = exposition(d=data, i=['EONIA', 'LIBOR'], scl=[True])

    print(f'{eonia_exposition.head()}\n')
    print(f'{libor_exposition.head()}\n')
    print(f'{eonia_libor_expo.head()}\n')
    print(f'{firm_eonia_libor_expo.head()}\n')
    print('Test succesfully done !!!')

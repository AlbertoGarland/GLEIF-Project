import os
import pandas as pd
import toml


def get_config():
    toml_file = None
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file == 'config.toml':
                toml_file = toml.load(os.path.join(root, file))
    return toml_file


def get_directories(file_names: list):
    """
    Cette fonction permet d'avoir les chemins d'acces de nos fichiers:
        - Son but: Grâce au fichier toml, on a le nom des nos excels servent à initialiser notre data

        - Parametres: il faut renseigne le dictionnaire file avec la clé de names

        - Resultat : un dictionnaire contenant les clé d'acces de nos fichiers
    """
    directories = {key: [] for key in ['TR', 'GLEIF']}
    for root, dirs, files in os.walk('.'):
        for file_name in file_names:
            if file_name in files:
                if file_name != 'GLEIF.xlsx':
                    directories['TR'].append(os.path.join(root, file_name))
                else:
                    directories["GLEIF"].append(os.path.join(root, file_name))

    if len(directories["GLEIF"]) == 0:
        raise ValueError('Aucune nomenclature GLEIF a été retrouvée')
    elif len(directories["GLEIF"]) > 1:
        raise ValueError('Plusieurs nomenclatures GLEIF ont été retrouvées')
    else:
        return directories


def set_data(directories: dict):
    """
    Cette fonction est celle qui initialise notre data:
    - Son but: Nettoyage nos differents Trade repositories en fonction de leur nombre et rajoute
               des informations de la nomenclature GLEIF

    - Parametres: il faut renseigne un dictionnaire contenant les chemins d'acces de nos fichiers

    -Resultat : un dictionnaire contenant des dataframes pour le buyer et seller side et une df recapitulative
    """
    trade_repositories = []
    gleif = None
    # On verifie avoir biend des directories
    if len(directories['TR']) == 0:
        raise ValueError('Aucun Trade Repository a été transmis')
    # Settings nos DataFrames"
    for key, directory in directories.items():
        if key != "GLEIF":
            trade_repositories = [pd.read_excel(file) for file in directory]
        else:
            gleif = pd.read_excel(directory[0])

    # Voici nos différents Trade repositories et la nomenclature GLEIF convertit en Data Frames

    # Nettoyage des doublons nettoyage des doublons
    trade_repository = pd.concat(trade_repositories, ignore_index=True)

    duplicates = trade_repository[trade_repository.duplicated(subset="uti", keep=False)]
    duplicates = duplicates['uti'].value_counts()

    # On regarde si on a des doublons
    if duplicates.shape[0] != 0:
        trade_repository = trade_repository.drop_duplicates(subset=['uti'], keep='first')
        print(f" We have {duplicates.shape[0]} transactions that have been registered twice on our data base\n\n")

    # Rajout de la nomeclature GLEIF sur le trade repository

    # On isole les LEI respectif pour chaque déclarant"
    lei_rptg = trade_repository.drop('lei_othr', axis=1)
    lei_othr = trade_repository.drop('lei_rptg', axis=1)

    # On merge chaque LEI avec la Nomeclature GLEIF
    df_rptg = pd.merge(lei_rptg, gleif, left_on="lei_rptg", right_on="lei")
    df_othr = pd.merge(lei_othr, gleif, left_on="lei_othr", right_on="lei")

    # On drop les colonnes poour chaque doublon de lei et on rename certaines colonnes pour plus de clarté
    df_rptg = df_rptg.drop(["lei"], axis=1)
    df_othr = df_othr.drop(["lei"], axis=1)

    df_rptg = df_rptg[["lei_rptg", "name", "country", "notional", "side", "fxd", "flt", "uti"]]
    df_othr = df_othr[["lei_othr", "name", "country", "notional", "side", "fxd", "flt", "uti"]]

    df_rptg = df_rptg.rename(columns={"name": "name_rptg", "country": "country_rptg"})
    df_othr = df_othr.rename(columns={"name": "name_othr", "country": "country_othr"})

    # Finalement, on reagroupe tout sur une nouvelle Data Frame

    gleif_trade = pd.DataFrame({
        "Lei_rptg": df_rptg["lei_rptg"],
        "Name_rptg": df_rptg["name_rptg"],
        "Country_rptg": df_rptg["country_rptg"],
        "Lei_othr": df_othr["lei_othr"],
        "Name_othr": df_othr["name_othr"],
        "Country_othr": df_othr["country_othr"],
        "Notional": df_rptg["notional"],
        "Side": df_rptg["side"],
        "Fxd": df_rptg["fxd"],
        "Flt": df_rptg["flt"],
        "Uti": df_rptg["uti"]
    })

    gleif_trade.set_index("Uti", inplace=True)  # On set l'index sur UTI car ID unique par transaction

    # Creation des dataframes, buyer et seller qui nous permetront de faire des calculs
    b_rows = []
    s_rows = []

    for i in gleif_trade.index:

        row = gleif_trade.loc[i]
        fxd = abs(row['Fxd']) if row['Side'] == 'B' and row['Fxd'] < 0 else row['Fxd']

        if row['Side'] == 'B':
            b_row = {
                "Uti": i,
                "Lei": row["Lei_rptg"],
                "Country": row["Country_rptg"],
                "Name": row["Name_rptg"],
                "Position": "Buyer",
                "Notional": row["Notional"],
                "Cash_Flow": row["Notional"] * fxd,
                "Index": row["Flt"]
            }
            s_row = {
                "Uti": i,
                "Lei": row["Lei_othr"],
                "Country": row["Country_othr"],
                "Name": row["Name_othr"],
                "Position": "Seller",
                "Notional": row["Notional"],
                "Cash_Flow": row["Notional"] * -fxd,
                "Index": row["Flt"]
            }
        else:
            b_row = {
                "Uti": i,
                "Lei": row["Lei_othr"],
                "Country": row["Country_othr"],
                "Name": row["Name_othr"],
                "Position": "Buyer",
                "Notional": row["Notional"],
                "Cash_Flow": row["Notional"] * -fxd,
                "Index": row["Flt"]
            }
            s_row = {
                "Uti": i,
                "Lei": row["Lei_rptg"],
                "Country": row["Country_rptg"],
                "Name": row["Name_rptg"],
                "Position": "Seller",
                "Notional": row["Notional"],
                "Cash_Flow": row["Notional"] * fxd,
                "Index": row["Flt"]
            }
        b_rows.append(b_row)
        s_rows.append(s_row)

    result = {"Buyer": pd.DataFrame(b_rows), "Seller": pd.DataFrame(s_rows), "Repository": gleif_trade}

    return result


if __name__ == '__main__':

    config_file = get_config()
    directoires = get_directories(config_file['files']['names'])
    data = set_data(directoires)

    print(data['Buyer'])
    print('Test succesfully done !!!')
import pandas as pd

'''
Esporta i comuni siciliani
e li ordina per codice ISTAT
'''

# Leggo CSV (ISTAT, 2021) e creo dataframe
df = pd.DataFrame(pd.read_csv("Elenco-comuni-italiani.csv", encoding='latin-1', sep=';', keep_default_na=False, converters={'Codice Regione': '{:0>2}'.format}))
df = df[['Codice Regione', 'Codice Provincia (Storico)(1)', 'Denominazione dell\'Unità territoriale sovracomunale \n(valida a fini statistici)', 'Codice Comune formato alfanumerico', 'Denominazione in italiano']]

# Rinomino e riordino le colonne
df.columns = ['cod_reg', 'cod_prov', 'provincia', 'pro_com_t', 'comune']
df = df[['cod_reg', 'cod_prov', 'pro_com_t', 'provincia', 'comune']]

# Correggo format codice ISTAT
df['pro_com_t'] = df['pro_com_t'].apply('{:0>6}'.format)

# Seleziona solo i comuni siciliani
df = df[df['cod_reg']=='19']
df = df.drop(columns='cod_reg')

# Esporta a CSV
df.to_csv('Elenco-comuni-siciliani.csv', index=False)

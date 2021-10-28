import pandas as pd

'''
Esporta i comuni siciliani
e li ordina per codice ISTAT
'''

#pd.set_option('display.width', 1000)
#pd.set_option('display.max_columns', 20)

df = pd.DataFrame(pd.read_csv("Elenco-comuni-italiani.csv", encoding='latin-1', sep=';', keep_default_na=False, converters={'Codice Regione': '{:0>2}'.format}))
df = df[['Codice Regione', 'Codice Provincia (Storico)(1)', 'Denominazione dell\'Unità territoriale sovracomunale \n(valida a fini statistici)', 'Codice Comune formato alfanumerico', 'Denominazione in italiano']]

df.columns = ['cod_reg', 'cod_prov', 'provincia', 'pro_com_t', 'comune']
df = df[['cod_reg', 'cod_prov', 'pro_com_t', 'provincia', 'comune']]

df['pro_com_t'] = df['pro_com_t'].apply('{:0>6}'.format)

df = df[df['cod_reg']=='19']
df = df.drop(columns='cod_reg')

df.to_csv('Elenco-comuni-siciliani.csv', index=False)

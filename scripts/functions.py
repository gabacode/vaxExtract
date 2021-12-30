from bs4 import BeautifulSoup
from datetime import datetime
import feedparser
import json
import locale
import os
import pandas as pd
from PyPDF2 import PdfFileReader
import re
import requests
import time
import tabula
import telegram

date = None
now = datetime.now().date()
path = '../downloads/'


def getRanges(file):
    '''
    Estrae i range delle pagine
    Allegato 1 e Allegato 2
    '''

    result_list = []
    r_pages = []

    reader = PdfFileReader(file)
    pages = reader.numPages

    for page_number in range(0, pages):
        page = reader.getPage(page_number)
        page_content = page.extractText()

        if "ALLEGATO" in page_content:
            result = {"page": page_number}
            result_list.append(result)

    r_pages.append(pages)

    for i in range(len(result_list)):
        r_pages.append(result_list[i]['page'])

    r_pages.sort()

    allegati = {
        "incidenza": [r_pages[0], r_pages[1]],
        "vaccini": [r_pages[1]+1, r_pages[2]]
    }

    return allegati

def getDate(file):
    '''
    Estrae la data dalla prima pagina del PDF
    '''
    reader = PdfFileReader(file)
    page = reader.getPage(0)
    content = page.extractText().replace('\n','')
    match = re.search(r'\d+/\d+/\d+', content)
    date = datetime.strptime(match.group(), '%d/%m/%Y').date()

    return date

def parsePDF(link, url):
    '''
    Estrae tutti i links che contengono files .pdf
    '''

    html = requests.get(link)
    soup = BeautifulSoup(html.text, 'html.parser')
    links = soup.find_all('a')
    for link in links:
        if ('.pdf' in link.get('href')):
            pdf = url+link.get('href')
    return pdf


def download(pdf):
    '''
    Scarica il PDF e prepara le pagine da leggere
    '''

    # Scarica il PDF
    filename = pdf.rsplit('/',1)[-1]
    r = requests.get(pdf, stream=True)
    with open('../downloads/'+filename, 'wb') as f:
        f.write(r.content)

    # Estrai la data dal nome del PDF e aggiungi timestamp
    global date

    try: 
        date = getDate(path+filename)
    except:
        try: 
            date = filename.rsplit('/', 1)[-1].replace('%20', '-').rstrip('.pdf').rsplit('-', 3)[1:]
            date = datetime.strptime(' '.join(date), '%d %B %Y').date()
        except:
            date = now
    finally:
        os.rename(path+filename, path+'report-'+date.strftime('%Y%m%d')+'.pdf')

    # Seleziona il piu recente PDF scaricato
    files = []

    for file in os.listdir(path):
        if (file.endswith('.pdf')):
            files.append(file)

    files.sort()
    file = files[-1]

    # Quali pagine leggiamo?
    ranges = getRanges(path+file)
    incidenza = ranges['incidenza']
    vaccini = ranges['vaccini']
    allegato1 = list(range(incidenza[0], incidenza[1]+1))
    allegato2 = list(range(vaccini[0], vaccini[1]+1))
    pagine = {"file": path+file, "incidenza": allegato1, "vaccini": allegato2}
    return pagine


def getVax(vax):
    '''
    Estrae tabella Vaccini da file PDF
    '''
    
    #Leggi il PDF  VAX con tabula-py
    print('Leggo tabella Vaccini...attendi...')
    pdf = tabula.read_pdf(vax['file'], pages=vax['vaccini'], pandas_options={'header': None}, multiple_tables=True, stream=True, silent=True)
    print('Ho letto.')

    #Unisci in un unico dataframe e bonifica i dati
    vax = pd.concat(pdf).reset_index(drop=True)
    vax = vax.dropna(thresh=3)
    vax = vax[~vax[0].str.contains("Provincia", na=False)]
    vax.drop(vax.columns[[0]], axis=1, inplace=True)

    for index, row in vax.iterrows():
        if(pd.isnull(row[2])):
            row[2] = row[3]
            row[3] = row[4]

    vax.reset_index(drop=True, inplace=True)
    vax.drop(vax.columns[3], axis=1, inplace=True)
    vax.columns = ['comune', '%vaccinati', '%immunizzati']

    #Carica l'helper comuni siciliani
    comuni = pd.DataFrame(pd.read_csv('https://raw.githubusercontent.com/gabacode/vaxExtract/main/utilities/Elenco-comuni-siciliani.csv', converters={'pro_com_t': '{:0>6}'.format}))
    out = pd.merge(vax, comuni, on='comune', how='inner')
    out = out[['cod_prov','pro_com_t','provincia','comune','%vaccinati','%immunizzati']]
    out['%vaccinati'] = out['%vaccinati'].str.replace(',','.').str.rstrip('%')
    out['%immunizzati'] = out['%immunizzati'].str.replace(',','.').str.rstrip('%')
    out.insert(0, 'data', date.strftime('%Y-%m-%d'))

    #Esporta CSV
    print('Esporto CSV...')
    out.to_csv('../dati-csv/vaccini-'+date.strftime('%Y%m%d')+'.csv', index=None, header=True)
    csv = '../dati-csv/vaccini-'+date.strftime('%Y%m%d')+'.csv'

    return csv


def getIncidenza(pdf):
    '''
    Estrae l'incidenza da file PDF
    '''
    
    #Legge le pagine relative all'incidenza
    reader = PdfFileReader(pdf['file'])
    pages=pdf['incidenza']

    #Looppa le pagine, rimuovi numero della pagina e sostituisce breaklines
    #Appende ad un'unica, grande stringa
    textes = []
    try:
        for i in range(pages[0], pages[-1]+1):
            page = reader.getPage(i)
            text = page.extractText()
            text = text.replace('\n', ' ')
            textes.append(text[2::])
    except Exception as e:
        pass

    #Seleziona parti di interesse, formatta elementi ambigui e ritorna una lista
    out = ' '.join(textes)\
         .rpartition('settimane')[2]\
         .rpartition('Totale')[0]\
         .replace('- ', '-')\
         .replace('---', '0%')\
         .replace('  ', ' ')\
         .replace('  ', ' ')\
         .replace('  ', ' ')\
         .replace('%', '')\
         .replace("O'","Ò").replace("I'","Ì").replace("U'","Ù")\
         .split()

    #Riconosce il nome del comune rispetto ad un numero,
    #Applica e rimuovi separatori, e ritorna una nuova lista
    new = ""
    for split in out:
        if not isDigit(split):
            new = new + split + ' '
        if isDigit(split):
            new = new + ','+ split + ','
    new = new.replace(',,', ',').replace(' ,', ',').replace(' -','-').split(',')

    #Looppa la lista e crea tuple a gruppi di 4
    it = iter(new)
    data = list(zip(it, it, it, it))

    #Crea dataframe
    df = pd.DataFrame(data, columns = ['comune', 'casi', 'incidenza', 'variazione'])
    df = df[['comune', 'incidenza', 'casi']]

    #Rimuovi distretti (duplicati)
    incidenza = df[~df["comune"].duplicated(keep="last")]
    incidenza.reset_index(inplace=True, drop=True)

    #Inner join e recupera info comuni
    comuni = pd.DataFrame(pd.read_csv('https://raw.githubusercontent.com/gabacode/vaxExtract/main/utilities/Elenco-comuni-siciliani.csv', converters={'pro_com_t': '{:0>6}'.format}))
    out = pd.merge(incidenza, comuni, left_on=incidenza["comune"].str.lower(), right_on=comuni["comune"].str.lower(), how="inner")
    out.rename(columns = {'comune_y':'comune'}, inplace = True)
    out = out[['cod_prov','pro_com_t','provincia','comune','incidenza','casi']].sort_values(by=['provincia', 'comune'])
    out.reset_index(drop=True, inplace=True)
    out.insert(0, 'data', date.strftime('%Y-%m-%d'))

    #Esporta CSV
    print('Esporto CSV...')
    out.to_csv('../dati-csv/incidenza-'+date.strftime('%Y%m%d')+'.csv', index=None, header=True)
    csv = '../dati-csv/incidenza-'+date.strftime('%Y%m%d')+'.csv'

    return csv

def check(url):
    '''
    Controlla se è uscito un nuovo bollettino
    Se si, aggiungi l'url del PDF al log.txt
    e manda una notifica tramite bot telegram
    '''

    try:
        feed = feedparser.parse(url+'/feed')
        f = [field for field in feed['entries'] if ("bollettino settimanale" in field['title'] or "a cura del Dasoe" in field['summary'] or "Bollettino settimanale" in field['title'])]
        link = f[0]['links'][0]['href']
        if(link):
            newfile = parsePDF(link, url)
            with open("../log.txt", "r+") as log:
                if newfile not in log.read():
                    print(datetime.now(), "Nuovo PDF!")
                    notify("Nuovo PDF: "+newfile)
                    #try:
                    #    send(open(getVax(download(newfile)), 'r'))
                    #except Exception as e:
                    #    print(e)
                    #try:
                    #    send(open(getIncidenza(download(newfile)), 'r'))
                    #except Exception as e:
                    #    print(e)
                    log.write(newfile+"\n")
                    log.close()
                else:
                    print(datetime.now(), "PDF già presente in archivio")
    except Exception as e:
        print(datetime.now(), e)
    finally:
        time.sleep(900)


def isDigit(x):
    '''
    True se x contiene un numero
    '''
    try:
        float(x)
        return True
    except ValueError:
        return False


def notify(message):
    with open('../config.json', 'r') as keys_file:
        k = json.load(keys_file)
        token = k['telegram_token']
        chat_id = k['telegram_chat_id']
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=message)


def send(file):
    with open('../config.json', 'r') as keys_file:
        k = json.load(keys_file)
        token = k['telegram_token']
        chat_id = k['telegram_chat_id']
    bot = telegram.Bot(token=token)
    bot.sendDocument(chat_id=chat_id, document=file)

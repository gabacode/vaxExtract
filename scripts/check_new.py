from bs4 import BeautifulSoup
import feedparser
import time

'''
Controlla se è uscito un nuovo bollettino
Se si, aggiungi l'url del PDF al log.txt
'''

def parse(link):
    html = requests.get(link)
    soup = BeautifulSoup(html.text, 'html.parser')
    links = soup.find_all('a')
    for link in links:
        if ('.pdf' in link.get('href')):
            pdf = url+link.get('href')
    return pdf

def check(url):
    try:
        feed = feedparser.parse(url)
        f = [field for field in feed['entries'] if "bollettino settimanale" in field['title']]
        link = f[0]['links'][0]['href']
        if(link):
            newfile = parse(link)
            with open("log.txt","w") as log:
                if newfile not in log.read():
                    log.write(newfile+"\n")
    except:
        pass
    finally:
        time.sleep(30)

while True:
    check('https://www.regione.sicilia.it/feed')

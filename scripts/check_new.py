from bs4 import BeautifulSoup
import feedparser
import json
import os
import requests
import telegram
import time

'''
Controlla se è uscito un nuovo bollettino
Se si, aggiungi l'url del PDF al log.txt
'''

if not os.path.exists('log.txt'):
    open('log.txt', 'w').close()

def notify(message):
    with open('./config.json', 'r') as keys_file:
        k = json.load(keys_file)
        token = k['telegram_token']
        chat_id = k['telegram_chat_id']
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=message)

def parse(link, url):
    html = requests.get(link)
    soup = BeautifulSoup(html.text, 'html.parser')
    links = soup.find_all('a')
    for link in links:
        if ('.pdf' in link.get('href')):
            pdf = url+link.get('href')
    return pdf

def check(url):
    try:
        feed = feedparser.parse(url+'/feed')
        f = [field for field in feed['entries'] if "bollettino settimanale" in field['title']]
        link = f[0]['links'][0]['href']
        if(link):
            newfile = parse(link, url)
            with open("log.txt","r+") as log:
                if newfile not in log.read():
                    log.write(newfile+"\n")
                    log.close()
                    notify("Nuovo PDF: "+newfile)
    except Exception as e:
        print(e)
    finally:
        time.sleep(30)

while True:
    check('https://www.regione.sicilia.it')

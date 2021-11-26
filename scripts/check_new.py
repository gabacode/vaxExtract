from functions import *
import os

if not os.path.exists('../log.txt'):
    open('../log.txt', 'w').close()

while True:
    check('https://www.regione.sicilia.it')

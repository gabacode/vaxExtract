## check_new.py

Controlla se è uscito un nuovo bollettino. Se si, aggiungi l'url del PDF al log.txt

Start:

1. `pip install -r requirements.txt`
2. `sudo chmod +x check_new.py`
3. `nohup python3 -u check_new.py &`

Stop:

1. `pkill check_new.py`

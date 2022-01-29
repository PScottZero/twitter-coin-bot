import requests
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
tokens = config['Tokens']

result = requests.get('https://api.numista.com/api/v2/issuers', headers={'Numista-API-Key': tokens['NumistaAPIKey']})
with open('issuers.json', 'w') as f:
  f.write(result.text)

import random
import tweepy
import requests
import json
import html
from PIL import Image
from io import BytesIO
from os import environ


def lambda_handler(event, context):
  url = tweet_random_coin()
  return {
    'statusCode': 200,
    'coin_url': url,
  }


def tweet_random_coin():
  with open('issuers.json', 'r') as f:
    issuers = json.load(f)['issuers']
  url, name, years, issuer = get_random_coin(issuers)
  auth = tweepy.OAuthHandler(
    environ['CONSUMER_KEY'],
    environ['CONSUMER_SECRET'],
    environ['ACCESS_TOKEN'],
    environ['ACCESS_TOKEN_SECRET']
  )
  api = tweepy.API(auth)
  tweet_text = f'{issuer}\n{name}\n{years}\n{url}' if years else f'{name}\n{url}'
  result1 = api.media_upload('/tmp/obv_img.jpg')
  result2 = api.media_upload('/tmp/rev_img.jpg')
  media_ids = [result1.media_id, result2.media_id]
  api.update_status(tweet_text, media_ids=media_ids)
  return url


def get_random_coin(issuers):
  while len(issuers) > 0:
    random_issuer = issuers.pop(random.randrange(len(issuers)))
    data = get_json(
      'https://api.numista.com/api/v2/coins',
      params={
        'q': random_issuer['name'],
        'issuer': random_issuer['code'],
        'count': '10000'
      },
    )
    if data['count'] > 0:
      coins = data['coins']
      while len(coins) > 0:
        random_coin = coins.pop(random.randrange(len(coins)))
        coin_data = get_json(f'https://api.numista.com/api/v2/coins/{random_coin["id"]}')
        if coin_has_relevant_data(coin_data):
          coin_url, coin_name = coin_data['url'], coin_data['title']
          coin_years = get_years(coin_data)
          download_image(coin_data['obverse']['picture'], '/tmp/obv_img.jpg')
          download_image(coin_data['reverse']['picture'], '/tmp/rev_img.jpg')
          coin_name = html.unescape(coin_name.split('(')[0])
          coin_issuer = format_issuer(coin_data['issuer']['name'])
          return coin_url, coin_name, coin_years, coin_issuer


def get_years(coin_data):
  if 'min_year' in coin_data and 'max_year' in coin_data:
    min_year = format_year(coin_data['min_year'])
    max_year = format_year(coin_data['max_year'])
    if min_year != max_year:
      return f'{min_year}-{max_year}'
    else:
      return min_year
  else:
    return None


def format_year(year):
  return f'{abs(year)}BCE' if year < 0 else str(year)


def get_json(url, params=None):
  result = requests.get(
    url, params=params,
    headers={'Numista-API-Key': environ['NUMISTA_API_KEY']},
  )
  if result.status_code == 200:
    return json.loads(result.text)
  else:
    print(f'Code {result.status_code} for request: {url}')
    return None


def download_image(img_url, img_file):
  result = requests.get(img_url)
  Image.open(BytesIO(result.content)).save(img_file)
  
  
def format_issuer(issuer):
  issuer_split = issuer.split(', ')
  if len(issuer_split) > 1:
    return html.unescape(f'{issuer_split[1]} {issuer_split[0]}')
  else:
    return html.unescape(issuer)


def coin_has_relevant_data(coin_data):
  return 'url' in coin_data and \
    'title' in coin_data and \
    'obverse' in coin_data and \
    'reverse' in coin_data and \
    'picture' in coin_data['obverse'] and \
    'picture' in coin_data['reverse'] and \
    'issuer' in coin_data and \
    'name' in coin_data['issuer']

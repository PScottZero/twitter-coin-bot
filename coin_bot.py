import random
import tweepy
import requests
import json
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
  url, name, years = get_random_coin(issuers)
  auth = tweepy.OAuthHandler(
    environ['CONSUMER_KEY'],
    environ['CONSUMER_SECRET'],
    environ['ACCESS_TOKEN'],
    environ['ACCESS_TOKEN_SECRET']
  )
  api = tweepy.API(auth)
  tweet_text = f'{name}\n{years}\n{url}' if years else f'{name}\n{url}'
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
          coin_name = coin_name.split('(')[0]
          return coin_url, coin_name, coin_years


def get_years(coin_data):
  coin_years = []
  for year_key in ['min_year', 'max_year']:
    if year_key in coin_data:
      year = coin_data[year_key]
      if year < 0:
        year = f'{abs(year)}BCE'
      coin_years.append(str(year))
  if len(coin_years) == 2:
    return f'{coin_years[0]} - {coin_years[1]}'
  elif len(coin_years) == 1:
    return str(coin_years[0])
  else:
    return None


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


def coin_has_relevant_data(coin_data):
  return 'url' in coin_data and \
    'title' in coin_data and \
    'obverse' in coin_data and \
    'reverse' in coin_data and \
    'picture' in coin_data['obverse'] and \
    'picture' in coin_data['reverse']

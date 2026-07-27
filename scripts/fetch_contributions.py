#!/usr/bin/env python3
"""Fetch total GitHub contributions (all-time) for RyutoYoda."""
import os
import json
import urllib.request
from datetime import datetime

USERNAME = 'RyutoYoda'
TOKEN = os.environ['GITHUB_TOKEN']
OUT_FILE = os.environ.get('COMMITS_FILE', '/tmp/commits.txt')
GQL_URL = 'https://api.github.com/graphql'


def gql(query, variables=None):
    payload = json.dumps({'query': query, 'variables': variables or {}}).encode()
    req = urllib.request.Request(GQL_URL, data=payload, headers={
        'Authorization': f'bearer {TOKEN}',
        'Content-Type': 'application/json',
    })
    with urllib.request.urlopen(req) as r:
        return json.load(r)


# Get account creation year
resp = gql('query($l:String!){user(login:$l){createdAt}}', {'l': USERNAME})
created_year = int(resp['data']['user']['createdAt'][:4])
current_year = datetime.now().year

total = 0
for year in range(created_year, current_year + 1):
    resp = gql(
        '''query($l:String!,$f:DateTime!,$t:DateTime!){
          user(login:$l){
            contributionsCollection(from:$f,to:$t){
              contributionCalendar{totalContributions}
            }
          }
        }''',
        {'l': USERNAME, 'f': f'{year}-01-01T00:00:00Z', 't': f'{year}-12-31T23:59:59Z'},
    )
    n = resp['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions']
    print(f'{year}: {n}')
    total += n

print(f'Total: {total}')
with open(OUT_FILE, 'w') as f:
    f.write(str(total))

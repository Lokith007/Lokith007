"""Build script-free animated SVGs from GitHub's public contribution data."""
import datetime as dt
import html
import json
import os
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USER = 'Lokith007'
VIOLET = '#b69cff'
MUTED = '#8b9aae'
CSS = 'text{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;fill:#e6edf3}\n.muted{fill:#8b9aae}.accent{fill:#b69cff}\n@keyframes pulse{0%,100%{opacity:.4}50%{opacity:1}}\n.pulse{animation:pulse 3s ease-in-out infinite}\n@media(prefers-reduced-motion:reduce){*{animation:none!important}}\n'

def svg(title, body, height):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="{height}" viewBox="0 0 860 {height}" role="img" aria-labelledby="title"><title id="title">{html.escape(title)}</title><style>{CSS}</style><rect width="860" height="{height}" rx="14" fill="#0d1117"/>{body}</svg>'''

def txt(x, y, value, size=12, cls='', extra=''):
    return f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}" {extra}>{html.escape(str(value))}</text>'

def query(document, variables):
    token = os.environ.get('GH_TOKEN')
    if not token:
        raise RuntimeError('GH_TOKEN is required; never replace missing data with invented numbers.')
    req = urllib.request.Request('https://api.github.com/graphql',
        data=json.dumps({'query':document,'variables':variables}).encode(),
        headers={'Authorization':f'Bearer {token}', 'Content-Type':'application/json', 'User-Agent':'Lokith007-profile'})
    with urllib.request.urlopen(req, timeout=60) as response:
        result=json.load(response)
    if result.get('errors'):
        raise RuntimeError(json.dumps(result['errors']))
    return result['data']

def collect():
    now=dt.datetime.now(dt.timezone.utc)
    data=query('''query($login:String!){user(login:$login){createdAt contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}''',{'login':USER})['user']
    if not data:
        raise RuntimeError('GitHub user not found')
    return {'calendar':data['contributionsCollection']['contributionCalendar'],
            'updated':now.strftime('%Y-%m-%d %H:%M UTC')}

def streaks(days):
    best=run=0
    for day in days:
        run=run+1 if day['contributionCount'] else 0
        best=max(best,run)
    # Today can remain empty until the day ends without breaking yesterday's streak.
    today=dt.datetime.now(dt.timezone.utc).date().isoformat()
    end=len(days)-1
    if end>=0 and days[end]['date']==today and days[end]['contributionCount']==0:
        end-=1
    current=0
    while end>=0 and days[end]['contributionCount']>0:
        current+=1
        end-=1
    return current,best

def render(data=None):
    current=longest=contributions=None
    if data:
        days=[d for w in data['calendar']['weeks'] for d in w['contributionDays']]
        current,longest=streaks(days)
        contributions=data['calendar']['totalContributions']
    body='<rect x="1" y="1" width="858" height="200" rx="16" fill="none" stroke="#35415d" stroke-width="2"/>'
    body+=txt(24,29,'GITHUB / ACTIVITY',11,'muted')
    body+=txt(836,29,'BUILDING, ONE DAY AT A TIME',9,'muted','text-anchor="end"')
    metrics=[(18,contributions,'contributions','last 12 months · public','#b69cff','12M'),
             (298,current,'current streak','days · UTC','#66dbf5','NOW'),
             (578,longest,'longest streak','days · last 12 months','#ffc07c','BEST')]
    for x,value,label,detail,color,tag in metrics:
        number=f'{value:,}' if value is not None else '—'
        body+=f'<rect x="{x}" y="48" width="264" height="136" rx="12" fill="#131a29" stroke="#39435e" stroke-width="1.5"/>'
        body+=f'<path d="M{x+15} 49H{x+82}" stroke="{color}" stroke-width="3" stroke-linecap="round"/>'
        body+=txt(x+244,72,tag,9,'muted','text-anchor="end"')
        body+=txt(x+20,111,number,34,'',f'style="fill:{color}"')
        body+=txt(x+20,139,label,12)
        body+=txt(x+20,163,detail,10,'muted')
    (ROOT/'assets/stats.svg').write_text(svg('Lokith007 public contributions and streaks',body,202))

if __name__=='__main__':
    data=collect()
    render(data)
    (ROOT/'assets/activity.json').write_text(json.dumps(data,indent=2)+'\n')
    print('Updated profile assets from GitHub public data.')

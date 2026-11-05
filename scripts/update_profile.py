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
CSS = 'text{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;fill:#e6edf3}\n.muted{fill:#8b9aae}\n@keyframes flow{to{stroke-dashoffset:-280}}\n@keyframes reveal{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}\n@keyframes breathe{0%,100%{opacity:.35}50%{opacity:1}}\n.flow{stroke-dasharray:24 256;animation:flow 6s linear infinite}.metric{animation:reveal .9s ease-out both}.pulse{animation:breathe 3s ease-in-out infinite}\n@media(prefers-reduced-motion:reduce){*{animation:none!important}}\n'

def svg(title, body, height):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="{height}" viewBox="0 0 860 {height}" role="img" aria-labelledby="title"><title id="title">{html.escape(title)}</title><style>{CSS}</style><defs></defs><rect width="860" height="{height}" rx="16" fill="#0b0f14"/>{body}</svg>'''

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
    body=txt(28,30,'GITHUB / ACTIVITY',11,'muted')
    body+='<path d="M192 26H797" stroke="#26373f"/><circle cx="820" cy="26" r="4" fill="#7ee787" class="pulse"/>'
    metrics=[(28,contributions,'contributions','last 12 months · public','#7ee787'),
             (328,current,'current streak','days · UTC','#9dd9e8'),
             (616,longest,'longest streak','days · last 12 months','#d8bd91')]
    body+='<path d="M296 62V145M584 62V145" stroke="#293840"/>'
    for i,(x,value,label,detail,color) in enumerate(metrics):
        number=f'{value:,}' if value is not None else '—'
        body+=f'<g class="metric" style="animation-delay:{i*.18}s">'
        body+=txt(x,103,number,38,'',f'style="fill:{color}"')
        body+=txt(x,128,label,12)+txt(x,148,detail,10,'muted')+'</g>'
        body+=f'<path d="M{x} 164h216" stroke="#24333b"/><path d="M{x} 164h216" stroke="{color}" stroke-width="1.5" class="flow" style="animation-delay:{-i*2}s"/>'
    (ROOT/'assets/stats.svg').write_text(svg('Lokith007 public contributions and streaks',body,184))

if __name__=='__main__':
    data=collect()
    render(data)
    (ROOT/'assets/activity.json').write_text(json.dumps(data,indent=2)+'\n')
    print('Updated profile assets from GitHub public data.')

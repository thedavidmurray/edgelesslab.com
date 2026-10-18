import json, os, subprocess
from pathlib import Path
from urllib.parse import quote
BASE = Path(__file__).resolve().parent
TOKEN = os.environ['GUMROAD_ACCESS_TOKEN']
KIT = '-IKTPvWDTSi4X8T37-bvpw=='
def api(path, method='GET'):
    r = subprocess.run(['curl','-fsS','-X',method,'-H',f'Authorization: Bearer {TOKEN}',f'https://api.gumroad.com/v2/{path}'],capture_output=True,text=True,check=True)
    d=json.loads(r.stdout)
    if not d.get('success'): raise RuntimeError(d.get('message','API failed'))
    return d
products=[]; key=None
while True:
    d=api('products'+('?'+'page_key='+quote(key,safe='') if key else ''))
    products.extend(d['products']); key=d.get('next_page_key')
    if not key: break
for p in products:
    if p['id'] != KIT and p['published']:
        api('products/'+quote(p['id'],safe='')+'/disable','PUT')
summary=[]
for p in products:
    r=api('products/'+quote(p['id'],safe=''))['product']
    summary.append({k:r[k] for k in ['id','name','price','published','short_url','sales_count']})
(BASE/'catalog-verified.json').write_text(json.dumps(summary,indent=2))
assert len(summary)==22
assert all(p['price']==0 for p in summary)
assert [p['id'] for p in summary if p['published']]==[KIT]
print(json.dumps(summary,indent=2))

import pathlib,zipfile,json,re,hashlib,ast,html
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from PIL import Image,ImageDraw,ImageFont
root=pathlib.Path(__file__).parent
out=root/'kit';out.mkdir(exist_ok=True)
original=json.loads((root/'original-products.json').read_text())
retired={'ffRrNYBAC1X1x4tq3IiWQA==':'No delivered files; empty paid tiers.', 'cnAmbRRWqoU85SeBxJEgLw==':'No delivered files; unfinished draft.', 'gwwky7Aa8b8CB0ZDSk2hHw==':'No delivered files; unfinished draft with paid tiers.', 'fbtiMzjMKWiq_x7vxgmkQQ==':'Corrupt ZIP: zlib invalid distances; cannot extract.'}
items=[]; checks=[];secret_hits=[]
for p in original:
 if p['id'] in retired:continue
 # One complete edition replaces three duplicative Prompt OS price tiers.
 files=p.get('files',[])
 if p['name']=='The Prompt Engineering OS':files=[f for f in files if f['name'].endswith('-team')]
 folder=re.sub(r'[^a-z0-9]+','-',p['name'].lower()).strip('-')
 for f in files:
  source=root/'downloads'/(f['name']+'.'+f['filetype']);z=zipfile.ZipFile(source);assert z.testzip() is None
  for info in z.infolist():
   path=pathlib.PurePosixPath(info.filename)
   if info.is_dir() or any(a in {'node_modules','__pycache__','dist','listings','.git','.DS_Store'} for a in path.parts) or info.filename.endswith(('.pyc','.map')):continue
   assert '..' not in path.parts and not path.is_absolute()
   data=z.read(info)
   if path.suffix in {'.md','.html','.py','.ts','.sh','.json','.env','.yml','.yaml'}:
    text=data.decode(errors='replace')
    if re.search(r'(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{25,}|gh[pous]_[A-Za-z0-9]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY)',text):secret_hits.append(folder+'/'+str(path))
    if path.suffix=='.py':ast.parse(text)
   target=out/folder/path;target.parent.mkdir(exist_ok=True,parents=True);target.write_bytes(data)
  items.append({'name':p['name'],'folder':folder,'source':source.name})
assert set(secret_hits) <= {'production-mcp-server-kit/content/templates/api-proxy/test/sanitizer.test.ts', 'claude-code-hooks-deep-dive/content/guide.md'},secret_hits
# Reviewed matches: intentionally fake credential fixtures in sanitizer tests and scanner documentation; no live credentials.
# Preserve original license files and content; replace only the package entry-point guidance.
contents='\n'.join(f"{i+1:02}. {p['name']} ({p['folder']}/)" for i,p in enumerate(items))
intro='Edgeless Free Kit\nReferences, templates, and examples for AI-assisted development.\n\nStart here: open the CLAUDE.md Template Pack and choose one template.\nThen open the Claude Code Cheat Sheet HTML in a browser.\n\n'+contents+'\n\nUsage notes\nThese are reference materials originally assembled in March-April 2026, not a promise of current compatibility. Tool APIs and commands change: check current vendor documentation before installing hooks or running examples. Review scripts, configure your own paths and credentials, and test in a disposable project. No scripts are run automatically. Dependencies and paid API usage are not included.\n\nValidation: original archives downloaded and CRC-tested; bundled Python source syntax checked. Examples have not all been integration-tested against current services. Removed node_modules, generated builds, bytecode, and sales-listing drafts. Original licenses retained per item.\n\nSupport and current work: https://edgelesslab.com\n'
(out/'START-HERE.txt').write_text(intro)
links=''.join(f'<li><a href="{p["folder"]}/">{html.escape(p["name"])}</a></li>' for p in items)
(out/'CONTENTS.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Edgeless Free Kit</title><style>body{font:18px/1.6 system-ui;max-width:850px;margin:64px auto;padding:24px;background:#101517;color:#e8eee9}a{color:#8ce5bb}h1{font-size:52px}</style><h1>Edgeless Free Kit</h1><p>Start with START-HERE.pdf. Choose one resource; you do not need to install everything.</p><ol>'+links+'</ol><p>Reference edition: March–April 2026. Check current vendor documentation before running examples.</p></html>')
pdf=canvas.Canvas(str(out/'START-HERE.pdf'),pagesize=(612,792));pdf.setTitle('Edgeless Free Kit — Start Here');pdf.setAuthor('Edgeless Lab')
import textwrap
for page_no,lines in enumerate([intro.split('\n')[:4]+['','Contents']+contents.split('\n'), intro.split('\n')[4:7]+intro.split('Usage notes')[1].split('\n')]):
 pdf.setFillColor(HexColor('#101517'));pdf.rect(0,0,612,792,fill=1,stroke=0);pdf.setFillColor(HexColor('#8ce5bb'));pdf.setFont('Helvetica-Bold',24);pdf.drawString(42,738,'Edgeless Free Kit' if page_no==0 else 'Start small. Read first.')
 y=696;pdf.setFillColor(HexColor('#e8eee9'));pdf.setFont('Helvetica',10)
 for line in lines:
  for s in textwrap.wrap(line,95) or ['']:
   pdf.drawString(42,y,s);y-=15
 pdf.showPage()
pdf.save()
cover=Image.new('RGB',(1600,900),'#101517');d=ImageDraw.Draw(cover)
font='/System/Library/Fonts/Helvetica.ttc'
f=lambda n:ImageFont.truetype(font,n)
d.rectangle((80,80,110,110),fill='#8ce5bb');d.text((135,78),'EDGELESS LAB / OPEN RESOURCES',font=f(28),fill='#8ce5bb');d.text((80,250),'Edgeless',font=f(125),fill='#e8eee9');d.text((80,385),'Free Kit',font=f(125),fill='#e8eee9');d.line((80,595,1520,595),fill='#385549',width=2);d.text((80,650),'Templates. Field guides. Working examples.',font=f(38),fill='#c4d1c9');d.text((80,755),'ONE DOWNLOAD  /  START WITH ONE RESOURCE',font=f(25),fill='#8ce5bb')
cover.save(root/'site/public/edgeless-free-kit-cover.png')
manifest=[]
for p in out.rglob('*'):
 if p.is_file():manifest.append({'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(root/'Edgeless-Free-Kit.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in out.rglob('*'):
  if p.is_file():z.write(p,'Edgeless-Free-Kit/'+str(p.relative_to(out)))
assert zipfile.ZipFile(root/'Edgeless-Free-Kit.zip').testzip() is None
(root/'kit-items.json').write_text(json.dumps(items,indent=2));print(json.dumps({'items':len(items),'files':len(manifest),'bytes':(root/'Edgeless-Free-Kit.zip').stat().st_size,'secret_pattern_hits':secret_hits,'retired':retired},indent=2))

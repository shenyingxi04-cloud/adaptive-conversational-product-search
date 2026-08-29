import json,sys,time
from pathlib import Path
import numpy as np
from model2vec import StaticModel
catalog=Path('data/catalog.jsonl')
texts=[]
with catalog.open(encoding='utf-8',errors='replace') as f:
 for line in f:
  p=json.loads(line); fs=p.get('features',[]); fs=fs if isinstance(fs,list) else [str(fs)]
  texts.append(' | '.join([str(p.get('title','')),str(p.get('categories','')),*map(str,fs[:4])])[:600])
t=time.perf_counter(); m=StaticModel.from_pretrained(Path('submission/models/potion-base-8M'),normalize=True,force_download=False); print('load_s',round(time.perf_counter()-t,3),flush=True)
t=time.perf_counter(); v=m.encode(texts); print('encode_s',round(time.perf_counter()-t,3),'shape',v.shape,'mb',round(v.nbytes/1024/1024,2),flush=True)
t=time.perf_counter(); scores=v @ v[0]; top=np.argpartition(scores,-50)[-50:]; print('search_s',round(time.perf_counter()-t,4),'top',len(top),flush=True)
time.sleep(1)


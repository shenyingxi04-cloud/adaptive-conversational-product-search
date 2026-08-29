import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from starter.agent import Agent
rows=[json.loads(x) for x in Path('debug_v512b_failures.jsonl').read_text(encoding='utf-8').splitlines()]
rows=[r for r in rows if r['scenario_type']=='browsing']
a=Agent('data/catalog.jsonl')
for row in rows:
 sid='probe_'+row['sample_id']; a.reset(sid,row.get('user_profile',{})); bc=br=None
 for turn in row['turns']:
  a.respond(sid,turn['user_message'],turn['turn'],10)
  state=a._session_state[sid]; q=a._build_query(state); ids=a._retrieve_candidates(q,state); target=row['target_parent_asin']
  cr=ids.index(target)+1 if target in ids else None
  ranked=a._rerank(ids,q,state,len(ids)); rids=[x['parent_asin'] for x in ranked]; rr=rids.index(target)+1 if target in rids else None
  if cr is not None: bc=cr if bc is None else min(bc,cr)
  if rr is not None: br=rr if br is None else min(br,rr)
 kind='RETRIEVAL' if bc is None else 'RERANK'
 print(json.dumps({'id':row['sample_id'],'target':target,'title':row['target_title'],'kind':kind,'best_candidate_rank':bc,'best_rerank_rank':br},ensure_ascii=False))


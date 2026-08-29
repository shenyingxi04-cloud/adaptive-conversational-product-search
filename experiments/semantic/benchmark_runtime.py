import statistics, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from starter.agent import Agent

catalog='data/catalog.jsonl'
t=time.perf_counter(); a=Agent(catalog); init=time.perf_counter()-t
print('semantic_enabled',a.semantic_model is not None)
print('startup_seconds',round(init,4))
a.reset('bench',{})
messages=['I am looking for comfortable shoes','For that, what matters is: lightweight; breathable','I do not have an additional preference for color','Show me something casual for summer','For that, what matters is: machine washable','I do not have an additional preference for size','I prefer a modern style','I do not have an additional preference for brand','Something suitable for daily use','Those options are not quite right yet. Ask me about one specific attribute.']
times=[]
for i,msg in enumerate(messages,1):
    t=time.perf_counter(); out=a.respond('bench',msg,i,10); times.append(time.perf_counter()-t); assert len(out['recommendations'])==10
print('response_seconds', [round(x,4) for x in times])
print('response_median_seconds',round(statistics.median(times),4))
print('response_p95_seconds',round(sorted(times)[int(0.95*(len(times)-1))],4))
print('response_max_seconds',round(max(times),4))





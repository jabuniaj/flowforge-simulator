// Offline discrete-event engine; same model assumptions as Python, independent PRNG.
export const stations=['Picking','Packing','Shipping'];
function random(seed){let a=seed>>>0;return()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
function gamma(shape,scale,r){
  if(shape<1)return gamma(shape+1,scale,r)*Math.pow(Math.max(r(),1e-12),1/shape);
  const d=shape-1/3,c=1/Math.sqrt(9*d);
  for(;;){const x=Math.sqrt(-2*Math.log(Math.max(r(),1e-12)))*Math.cos(2*Math.PI*r());let v=1+c*x;if(v<=0)continue;v=v*v*v;const u=r();if(u<1-.0331*x*x*x*x||Math.log(u)<.5*x*x+d*(1-v+Math.log(v)))return d*v*scale;}
}
class Heap{
  data=[];seq=0;
  less(a,b){return a.t<b.t||(a.t===b.t&&a.seq<b.seq);}
  push(e){e.seq=this.seq++;let d=this.data,i=d.length;d.push(e);while(i){let p=(i-1)>>1;if(!this.less(d[i],d[p]))break;[d[i],d[p]]=[d[p],d[i]];i=p;}}
  pop(){const d=this.data,first=d[0],last=d.pop();if(d.length){d[0]=last;let i=0;for(;;){let l=2*i+1,r=l+1,n=i;if(l<d.length&&this.less(d[l],d[n]))n=l;if(r<d.length&&this.less(d[r],d[n]))n=r;if(n===i)break;[d[i],d[n]]=[d[n],d[i]];i=n;}}return first;}
}
export function simulate(c,seed=410){
  if(!Number.isInteger(c.orders)||c.orders<0||!Number.isFinite(c.minutes)||c.minutes<=0)throw Error('Invalid shift');
  if(c.staff.length!==3||c.times.length!==3||c.equipment.length!==3||c.times.some(x=>!Number.isFinite(x)||x<=0)||[...c.staff,...c.equipment].some(x=>!Number.isInteger(x)||x<0))throw Error('Invalid resources');
  const heap=new Heap(),r=random(seed),arrivals=Array.from({length:c.orders},()=>r()*c.minutes).sort((a,b)=>a-b);
  const active=[0,0,0],queues=[[],[],[]],slots=c.staff.map((n,i)=>Math.min(n,c.equipment[i]));
  const trace=[];let completed=0;
  function start(i,t){while(queues[i].length&&active[i]<slots[i]){const id=queues[i].shift();active[i]++;const rr=random(seed*1000003+id*7+i+1);let duration=c.cv?gamma(1/c.cv**2,c.times[i]*c.cv**2,rr):c.times[i];let finish=t+duration;
    if(i===c.outage_station&&c.outage_duration){const a=c.outage_start,b=a+c.outage_duration;if(t>=a&&t<b)finish=b+duration;else if(t<a&&finish>a)finish+=c.outage_duration;}
    heap.push({t:finish,type:'done',i,id});}}
  arrivals.forEach((t,id)=>heap.push({t,type:'arrive',i:0,id}));
  for(let t=0;t<c.minutes;t+=5)heap.push({t,type:'sample'});
  while(heap.data.length){const e=heap.pop();if(e.t>c.minutes)break;if(e.type==='sample'){trace.push({minute:e.t,queues:queues.map(q=>q.length),completed});continue;}
    if(e.type==='done'){active[e.i]--;if(e.i===2)completed++;else{queues[e.i+1].push(e.id);start(e.i+1,e.t);}start(e.i,e.t);}else{queues[e.i].push(e.id);start(e.i,e.t);}}
  return{completed,unfinished:c.orders-completed,trace};
}
export function plan(m,staff,bench=false,repair=false){
  if(staff.length!==3||staff.some(n=>!Number.isInteger(n)||n<0||n>12)||staff.reduce((a,b)=>a+b,0)!==m.config.staff.reduce((a,b)=>a+b,0))throw Error('Assign exactly the available team.');
  if((bench&&!m.bench_cost)||(repair&&!m.repair_cost))throw Error('That intervention is unavailable.');
  const cost=Number(bench)*m.bench_cost+Number(repair)*m.repair_cost;if(cost>m.budget)throw Error('This plan exceeds your budget.');
  const c={...m.config,staff:[...staff],equipment:[...m.config.equipment]};c.equipment[1]+=Number(bench);if(repair)c.outage_duration=m.repaired_duration;return{config:c,cost};
}
export function evaluate(m,staff,bench=false,repair=false){const p=plan(m,staff,bench,repair),seeds=Array.from({length:10},(_,i)=>410+i);const before=seeds.map(s=>simulate(m.config,s)),after=seeds.map(s=>simulate(p.config,s));const avg=rr=>rr.reduce((s,r)=>s+r.completed,0)/rr.length;return{...p,seeds,before,after,baseline:avg(before),mean:avg(after),gain:avg(after)-avg(before),successes:after.filter(r=>r.completed>=m.target).length};}

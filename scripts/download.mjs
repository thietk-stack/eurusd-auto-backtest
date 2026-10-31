// Read-only EURUSD H1 bid/ask downloader; no synthetic substitutes or credentials.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { coversRequestedInterval } from './coverage_guard.mjs';
import { createRequire } from 'node:module';
const require=createRequire(import.meta.url);
const {getHistoricalRates}=require('dukascopy-node');
const FROM=process.env.FROM||'2010-01-01', TO=process.env.TO||'2026-10-30';
const limit=Math.max(1,Number(process.env.MONTHS_PER_RUN||24));
if(!/^\d{4}-\d{2}-\d{2}$/.test(FROM)||!/^\d{4}-\d{2}-\d{2}$/.test(TO)||FROM>=TO)throw Error('Invalid FROM/TO date');
const start=new Date(FROM+'T00:00:00Z'),end=new Date(TO+'T00:00:00Z');
if(isNaN(+start)||isNaN(+end))throw Error('Invalid dates');
fs.mkdirSync('data',{recursive:true});fs.mkdirSync('results',{recursive:true});
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const months=[];
for(let d=new Date(Date.UTC(start.getUTCFullYear(),start.getUTCMonth(),1));d<end;d=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,1))){
 const next=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,1));
 months.push({key:d.toISOString().slice(0,7),from:new Date(Math.max(+d,+start)),to:new Date(Math.min(+next,+end))});
}
function validated(data,label){
 if(!Array.isArray(data))throw Error(label+' is not an array');
 const rows=new Map();
 for(const x of data){
  const t=Number(x.timestamp),p=['open','high','low','close'].map(k=>Number(x[k]));
  if(!Number.isFinite(t)||t<9e11||t>2.2e12)throw Error('Invalid millisecond timestamp');
  if(p.some(z=>!Number.isFinite(z)||z<0.5||z>2)||p[1]<Math.max(p[0],p[3])||p[2]>Math.min(p[0],p[3]))throw Error('Invalid FX OHLC');
  rows.set(t,{t,o:p[0],h:p[1],l:p[2],c:p[3],v:Number(x.volume)||0});
 }
 return rows;
}
async function get(side,from,to){
 const result=await getHistoricalRates({instrument:'eurusd',dates:{from,to},timeframe:'h1',priceType:side,format:'json',batchSize:5,pauseBetweenBatchesMs:1200,useCache:true,cacheFolderPath:'.dukascopy-cache',retryCount:2,pauseBetweenRetriesMs:2500});
 return validated(result,side);
}
let downloaded=0,finished=0;
for(const m of months){
 const f=path.join('data',m.key+'.csv'),meta=f+'.source.json';
 if(fs.existsSync(f)){
  if(!fs.existsSync(meta))throw Error('Missing provenance manifest '+f);
  const j=JSON.parse(fs.readFileSync(meta,'utf8')),b=fs.readFileSync(f);
  if(j.source!=='dukascopy-node'||j.sha256!==hash(b)||j.candle_count<5)throw Error('Provenance check failed '+f);
  if(coversRequestedInterval(j,m.from,m.to)){finished++;continue;}
  console.log('REFRESH_PARTIAL_CACHED_MONTH',m.key,'cached_end',j.to_exclusive,'required_end',m.to.toISOString());
 }
 if(downloaded>=limit)break;
 console.log('Download real EURUSD '+m.key+' '+m.from.toISOString()+' to '+m.to.toISOString());
 const bid=await get('bid',m.from,m.to);
 await sleep(200);
 const ask=await get('ask',m.from,m.to);
 const ids=[...bid.keys()].filter(t=>ask.has(t)&&t>=+m.from&&t<+m.to).sort((a,b)=>a-b);
 if(ids.length<5||ids.length<Math.min(bid.size,ask.size)*.90)throw Error('Incomplete BID/ASK '+m.key+' '+ids.length);
 const lines=['timestamp,open,high,low,close,volume,bid_open,ask_open,spread_open_pips'];
 for(const t of ids){
  const b=bid.get(t),a=ask.get(t),s=(a.o-b.o)/0.0001;
  if(s<0||s>100)throw Error('Invalid spread '+m.key);
  const o=(a.o+b.o)/2,c=(a.c+b.c)/2;
  const hi=Math.max((a.h+b.h)/2,o,c),lo=Math.min((a.l+b.l)/2,o,c);
  lines.push([new Date(t).toISOString(),o.toFixed(8),hi.toFixed(8),lo.toFixed(8),c.toFixed(8),Math.max(b.v,a.v),b.o.toFixed(8),a.o.toFixed(8),s.toFixed(3)].join(','));
 }
 const buf=lines.join('\n')+'\n';
 fs.writeFileSync(f+'.tmp',buf);fs.renameSync(f+'.tmp',f);
 fs.writeFileSync(meta,JSON.stringify({source:'dukascopy-node',instrument:'eurusd',timeframe:'h1',from:m.from.toISOString(),to_exclusive:m.to.toISOString(),candle_count:ids.length,sha256:hash(Buffer.from(buf))},null,2));
 downloaded++;finished++;
 console.log('Saved '+f+': '+ids.length+' candles');
 await sleep(250);
}
console.log('PROGRESS '+finished+'/'+months.length+' completed months');
fs.writeFileSync('results/DOWNLOAD_STATUS.json',JSON.stringify({source:'dukascopy-node',from:FROM,to:TO,months_expected:months.length,months_verified:finished,downloaded_this_run:downloaded,status:finished===months.length?'COMPLETE':'INCOMPLETE'},null,2));
if(finished!==months.length)process.exitCode=3;
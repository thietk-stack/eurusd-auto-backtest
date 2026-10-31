// Download REAL Bid/Ask hourly FX history; store checksummed monthly CSV, abort on missing bars.
// This script never contacts Exness or submits any orders.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
const require=createRequire(import.meta.url);
const {getHistoricalRates}=require('dukascopy-node');
const instruments=['gbpusd','audusd','usdjpy'];
const FROM=process.env.PORTFOLIO_FROM||'2020-01-01';
const TO=process.env.PORTFOLIO_TO||'2026-10-30';
const LIMIT=Number(process.env.MONTHS_PER_RUN||300);
const begin=new Date(FROM+'T00:00:00Z'), end=new Date(TO+'T00:00:00Z');
if(!(begin<end) || !Number.isFinite(LIMIT)||LIMIT<1)throw Error('Invalid dates or MONTHS_PER_RUN');
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
function checked(values,side,symbol){
 if(!Array.isArray(values))throw Error('No '+side+' candle array '+symbol);
 let out=new Map();
 for(const row of values){
  let t=Number(row.timestamp),ohlc=['open','high','low','close'].map(k=>Number(row[k]));
  if(!Number.isFinite(t)||t<1e12||!ohlc.every(x=>Number.isFinite(x)&&x>0))throw Error('Corrupt OHLC '+symbol);
  if(ohlc[1]+1e-8<Math.max(ohlc[0],ohlc[3]) || ohlc[2]-1e-8>Math.min(ohlc[0],ohlc[3]))throw Error('High/low inconsistent');
  out.set(t,{o:ohlc[0],h:ohlc[1],l:ohlc[2],c:ohlc[3]});
 }
 return out;
}
async function oneSide(symbol,side,from,to){
 const raw=await getHistoricalRates({instrument:symbol,dates:{from,to},timeframe:'h1',priceType:side,format:'json',batchSize:6,pauseBetweenBatchesMs:150,useCache:true,cacheFolderPath:'.dukascopy-cache',retryCount:2,pauseBetweenRetriesMs:1800});
 return checked(raw,side,symbol);
}
let items=[];
for(let year=begin.getUTCFullYear(),month=begin.getUTCMonth(); Date.UTC(year,month,1)<+end;){
 let st=new Date(Date.UTC(year,month,1)),next=new Date(Date.UTC(year,month+1,1));
 for(const symbol of instruments)items.push({symbol,from:new Date(Math.max(+begin,+st)),to:new Date(Math.min(+end,+next)),key:st.toISOString().slice(0,7)});
 month++;if(month>=12){year++;month=0}
}
let downloaded=0,verified=0;
for(let {symbol,from,to,key} of items){
 const folder=path.join('portfolio_data',symbol);
 fs.mkdirSync(folder,{recursive:true});
 const f=path.join(folder,key+'.csv'),m=f+'.source.json';
 if(fs.existsSync(f)&&fs.existsSync(m)){
  const meta=JSON.parse(fs.readFileSync(m,'utf8'));
  if(meta.instrument!==symbol||meta.source!=='dukascopy-node'||meta.sha256!==digest(fs.readFileSync(f))||meta.candles<5)throw Error('Provenance failure '+f);
  verified++;continue;
 }
 if(downloaded>=LIMIT)break;
 console.log('REQUEST',symbol,key);
 const bid=await oneSide(symbol,'bid',from,to);
 const ask=await oneSide(symbol,'ask',from,to);
 const timestamps=[...bid.keys()].filter(x=>ask.has(x)&&x>=+from&&x<+to).sort((a,b)=>a-b);
 if(timestamps.length<5 || timestamps.length<.9*Math.min(bid.size,ask.size))throw Error('Incomplete '+symbol+' '+key);
 let lines=['timestamp,open,high,low,close,bid_open,ask_open,spread_open_pips'];
 let rejected_inverted_spread=0;
 const pip=symbol==='usdjpy'?0.01:0.0001;
 for(const t of timestamps){
   const b=bid.get(t),a=ask.get(t),spread=(a.o-b.o)/pip;
   if(!(spread>=0&&spread<150)){
     // Source BID and ASK historical OHLC are independently timestamped.
     // Never correct a crossed/open quote or manufacture a replacement candle.
     rejected_inverted_spread++;
     continue;
   }
   const open=(a.o+b.o)/2,close=(a.c+b.c)/2,high=Math.max((a.h+b.h)/2,open,close),low=Math.min((a.l+b.l)/2,open,close);
   lines.push([new Date(t).toISOString(),open,high,low,close,b.o,a.o,spread].join(','));
 }
 // Fail closed if a substantial fraction of observations have invalid quotes.
 // <=2% cap per source month, no forward fill or interpolation; audited count.
 if(rejected_inverted_spread>Math.max(2,Math.floor(timestamps.length*.02)))
   throw Error('Too many crossed BID ASK quotes '+symbol+'/'+key+': '+rejected_inverted_spread);
 if(lines.length<Math.floor(timestamps.length*.98))
   throw Error('Quote filtering removed >2% '+symbol+'/'+key);
 if(rejected_inverted_spread)
   console.warn('QUOTE_CROSSED_DISCARDED',symbol,key,rejected_inverted_spread,'/',timestamps.length);
 const data=Buffer.from(lines.join('\n')+'\n');
 fs.writeFileSync(f+'.temp',data);fs.renameSync(f+'.temp',f);
 fs.writeFileSync(m,JSON.stringify({source:'dukascopy-node',instrument:symbol,candles:lines.length-1,rejected_inverted_spread,raw_matching_bars:timestamps.length,
   screening:'Drop only inverted or implausible original BID ASK open quotes, <=2percent per month; never fill',timeframe:'h1',from:from.toISOString(),to:to.toISOString(),sha256:digest(data)},null,2));
 downloaded++;verified++;
 console.log('SAVED',symbol,key,'bars',lines.length-1,'bad_quote_bars',rejected_inverted_spread);
 await pause(100);
}
fs.mkdirSync('portfolio_results',{recursive:true});
fs.writeFileSync('portfolio_results/DOWNLOAD_STATUS.json',JSON.stringify({source:'dukascopy-node',from:FROM,to:TO,needed:items.length,verified,downloaded,complete:verified===items.length},null,2));
console.log('VERIFIED',verified,'of',items.length);
if(verified!==items.length)process.exitCode=3;
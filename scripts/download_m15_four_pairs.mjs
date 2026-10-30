// Authentic 15-minute Dukascopy BID and ASK OHLC (not hourly interpolation).
// Month-wise resumable verified gzip CSV. No trading APIs or broker credentials.
import fs from "node:fs"; import path from "node:path";
import crypto from "node:crypto"; import zlib from "node:zlib";
import {createRequire} from "node:module";
const require=createRequire(import.meta.url);
const {getHistoricalRates}=require("dukascopy-node");
const START=process.env.M15_FROM||"2019-01-01";
const END=process.env.M15_TO||"2026-01-01";
const MAX=Number(process.env.M15_MONTHS_PER_RUN||400);
const syms=["eurusd","gbpusd","audusd","usdjpy"];
const a=new Date(START+"T00:00:00Z"),b=new Date(END+"T00:00:00Z");
if(!(a<b)||MAX<1||!Number.isFinite(MAX))throw Error("Invalid dates or monthly limit");
const hash=buf=>crypto.createHash("sha256").update(buf).digest("hex");
const wait=ms=>new Promise(ok=>setTimeout(ok,ms));
function checked(rows,side,sym,from,to){
 if(!Array.isArray(rows))throw Error("Invalid "+side+" data "+sym);
 const map=new Map();
 for(const v of rows){
  const t=Number(v.timestamp), [o,h,l,c]=["open","high","low","close"].map(x=>Number(v[x]));
  if(!Number.isFinite(t)||t<+from||t>=+to)continue;
  if(t%900000!==0)throw Error("Non-M15 timestamp "+sym);
  if(![o,h,l,c].every(x=>Number.isFinite(x)&&x>0)||h<Math.max(o,c)-1e-9||l>Math.min(o,c)+1e-9)throw Error("Invalid M15 OHLC "+sym+" "+side);
  map.set(t,{o,h,l,c});
 }
 return map;
}
async function download(sym,side,from,to){
 const r=await getHistoricalRates({instrument:sym,dates:{from,to},timeframe:"m15",priceType:side,format:"json",batchSize:12,pauseBetweenBatchesMs:50,useCache:true,cacheFolderPath:".dukascopy-cache-m15",retryCount:2,pauseBetweenRetriesMs:600});
 return checked(r,side,sym,from,to);
}
let jobs=[];
for(let y=a.getUTCFullYear(),m=a.getUTCMonth();Date.UTC(y,m,1)<+b;){
 const st=new Date(Date.UTC(y,m,1)),ed=new Date(Date.UTC(y,m+1,1));
 for(const sym of syms)jobs.push({sym,from:new Date(Math.max(+a,+st)),to:new Date(Math.min(+b,+ed)),month:st.toISOString().slice(0,7)});
 m++;if(m===12){y++;m=0}
}
let completed=0,requested=0;
for(const {sym,from,to,month} of jobs){
 const folder=path.join("m15_market",sym);fs.mkdirSync(folder,{recursive:true});
 const file=path.join(folder,month+".csv.gz"),meta=file+".source.json";
 if(fs.existsSync(file)&&fs.existsSync(meta)){
  const obj=JSON.parse(fs.readFileSync(meta,"utf8"));
  if(obj.source!=="dukascopy-node"||obj.timeframe!=="m15"||obj.symbol!==sym||obj.sha256!==hash(fs.readFileSync(file))||obj.candles<30)throw Error("Bad checksum/provenance: "+file);
  completed++;continue;
 }
 if(requested>=MAX)break;
 console.log("M15_REAL_DOWNLOAD",sym,month);
 const bid=await download(sym,"bid",from,to),ask=await download(sym,"ask",from,to);
 const common=[...bid.keys()].filter(t=>ask.has(t)).sort((a,b)=>a-b);
 if(common.length<30||common.length<.9*Math.min(bid.size,ask.size))throw Error("Missing actual BID/ASK m15 "+sym+" "+month);
 const pip=sym==="usdjpy"?.01:.0001;
 const lines=["timestamp,open,high,low,close,bid_open,bid_high,bid_low,bid_close,ask_open,ask_high,ask_low,ask_close,spread_open_pips"];
 for(const time of common){
  const d=bid.get(time),u=ask.get(time);
  if(u.o<d.o-1e-9||u.h<d.h-1e-6||u.l<d.l-1e-6||u.c<d.c-1e-6)throw Error("Inverted quotes "+sym);
  const mid=v=>(d[v]+u[v])/2;
  const o=mid("o"),c=mid("c"),h=Math.max(o,c,mid("h")),l=Math.min(o,c,mid("l"));
  const spread=(u.o-d.o)/pip;
  if(spread<0||spread>100)throw Error("Impossible spread "+sym);
  lines.push([new Date(time).toISOString(),o,h,l,c,d.o,d.h,d.l,d.c,u.o,u.h,u.l,u.c,spread].join(","));
 }
 const zip=zlib.gzipSync(Buffer.from(lines.join("\n")+"\n"),{level:6});
 fs.writeFileSync(file+".temp",zip);fs.renameSync(file+".temp",file);
 fs.writeFileSync(meta,JSON.stringify({source:"dukascopy-node",timeframe:"m15",symbol:sym,month,from:from.toISOString(),to:to.toISOString(),candles:common.length,sha256:hash(zip)},null,2));
 completed++;requested++;console.log("M15_SAVED",sym,month,"candles",common.length,"compressed_bytes",zip.length);
 await wait(50);
}
fs.mkdirSync("m15_results",{recursive:true});
fs.writeFileSync("m15_results/DOWNLOAD_PROGRESS.json",JSON.stringify({from:START,to:END,complete:completed===jobs.length,verified_months:completed,expected_months:jobs.length,downloaded:requested,source:"REAL_DUKASCOPY_M15_BID_ASK"},null,2));
if(completed!==jobs.length){console.log("DOWNLOAD_INCOMPLETE",completed,jobs.length);process.exitCode=3}
else console.log("M15_DATASET_COMPLETE",completed,"months");

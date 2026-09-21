import {useState} from 'react';
import {Search} from 'lucide-react';
export default function AssetLibrary({catalogue,disabled,add}:{catalogue:any[],disabled:boolean,add:(id:string)=>void}){
 const [query,setQuery]=useState(''),[category,setCategory]=useState('All');
 const categories=['All','Compute','Networking','Security','Devices & robotics','AWS','Boundaries & other'];
 const filtered=catalogue.filter(a=>(category==='All'||a.category===category)&&[a.label,a.id,...a.tags||[]].join(' ').toLowerCase().includes(query.toLowerCase()));
 return <section className="asset-library"><h2>Component library <span className="count">{catalogue.length}</span></h2><label className="library-search"><Search size={14}/><input aria-label="Search component library" placeholder="Find a component…" value={query} onChange={e=>setQuery(e.target.value)}/></label><select aria-label="Component category" value={category} onChange={e=>setCategory(e.target.value)}>{categories.map(c=><option key={c}>{c}</option>)}</select>
 {categories.slice(1).filter(c=>filtered.some(a=>a.category===c)).map(c=><details className="asset-group" key={c} open><summary>{c}<span>{filtered.filter(a=>a.category===c).length}</span></summary><div className="palette">{filtered.filter(a=>a.category===c).map(a=><button key={a.id} draggable onDragStart={e=>e.dataTransfer.setData('asset',a.id)} onClick={()=>add(a.id)} disabled={disabled} title={'Add '+a.id}><img src={'/api/assets/'+a.icon} alt=""/>{a.label||a.id.replaceAll('-',' ')}</button>)}</div></details>)}
 {!filtered.length&&<p className="muted">No matching components.</p>}{category==='AWS'&&<p className="muted">AWS service labels use generic symbols. Availability and network configuration are separate design decisions.</p>}
 </section>
}

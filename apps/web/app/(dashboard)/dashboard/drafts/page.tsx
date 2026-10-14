import {api, type Draft} from "../../../../lib/api";
import NewDraft from "../../../components/NewDraft";
export default async function Drafts(){
 const me=await api<{workspaces:{id:string,name:string}[]}>("/api/v1/auth/me");
 const w=me?.workspaces[0];const drafts=w?await api<Draft[]>("/api/v1/workspaces/"+w.id+"/drafts"):[];
 return <><p className="eyebrow">Content management</p><h1 className="heading">Draft Library</h1><p className="muted">Drafts are isolated per workspace. AI content generation will be connected in the next milestone.</p>{w&&<NewDraft workspaceId={w.id}/>}<div className="grid">{drafts?.map(d=><div className="card" key={d.id}><span className="tag">{d.status}</span><h3>{d.title}</h3><p className="muted">{d.caption}</p><p className="muted" style={{fontSize:12}}>{new URL(d.source_url).hostname}</p></div>)}</div>{!drafts?.length&&<p className="muted">No drafts yet. Create your first workspace draft above.</p>}</>
}

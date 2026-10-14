"use client";
import {useState} from "react";
export default function NewDraft({workspaceId}:{workspaceId:string}){
 const [error,setError]=useState("");const [busy,setBusy]=useState(false);
 async function create(e:React.FormEvent<HTMLFormElement>){
  e.preventDefault();setBusy(true);setError("");const data=Object.fromEntries(new FormData(e.currentTarget).entries());
  try{const r=await fetch("/api/workspaces/"+workspaceId+"/drafts",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
   if(!r.ok){const j=await r.json();throw new Error(j.detail||"Unable to save draft")}window.location.reload()
  }catch(e){setError(e instanceof Error?e.message:"Unexpected error")}finally{setBusy(false)}
 }
 return <section className="card" style={{maxWidth:680}}><h2>New draft</h2><form onSubmit={create}><label>Title<input className="field" name="title" required minLength={3}/></label><label>Caption<input className="field" name="caption" required/></label><label>Official source URL<input className="field" name="source_url" type="url" required placeholder="https://shopify.dev/changelog/..."/></label>{error&&<p className="error" role="alert">{error}</p>}<button className="button" disabled={busy}>{busy?"Saving...":"Save draft"}</button></form></section>
}

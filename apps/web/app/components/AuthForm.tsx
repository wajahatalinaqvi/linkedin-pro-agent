"use client";
import { useState } from "react";
import Link from "next/link";
export default function AuthForm({mode}:{mode:"login"|"register"}){
 const [error,setError]=useState("");const [busy,setBusy]=useState(false);
 async function submit(event:React.FormEvent<HTMLFormElement>){
  event.preventDefault();setBusy(true);setError("");
  const data=new FormData(event.currentTarget);
  const payload=Object.fromEntries(data.entries());
  try {
   const reply=await fetch("/api/session/"+mode,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
   const result=await reply.json();
   if(!reply.ok)throw new Error(result.detail||"Unable to sign in");
   window.location.assign("/dashboard");
  }catch(e){setError(e instanceof Error?e.message:"Unexpected error")}finally{setBusy(false)}
 }
 return <main className="auth"><p className="eyebrow">LinkedIn Pro Studio</p><h1>{mode==="register"?"Create your workspace":"Welcome back"}</h1><p className="muted">Manage research, drafts and carousels in one place.</p><form onSubmit={submit}>{mode==="register"&&<label>Workspace name<input className="field" required minLength={2} name="workspace_name" placeholder="My Content Studio"/></label>}<label>Email<input className="field" required type="email" name="email" placeholder="you@example.com"/></label><label>Password<input className="field" required type="password" minLength={mode==="register"?12:1} name="password" placeholder="••••••••••••"/></label>{error&&<p className="error" role="alert">{error}</p>}<button className="button" disabled={busy}>{busy?"Please wait...":mode==="register"?"Create account":"Sign in"}</button></form><p className="muted">{mode==="register"?"Already have an account?":"New here?"} <Link href={mode==="register"?"/login":"/register"} style={{color:"#3a5ec7"}}>{mode==="register"?"Sign in":"Create an account"}</Link></p></main>;
}

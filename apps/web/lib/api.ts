import { cookies } from "next/headers";
const API=process.env.API_INTERNAL_URL||"http://localhost:8000";
export type Workspace={id:string,name:string,timezone:string};
export type Draft={id:string,workspace_id:string,title:string,caption:string,source_url:string,status:string,created_at:string};
export async function api<T>(path:string):Promise<T|null>{
 const token=(await cookies()).get("lp_session")?.value;
 if(!token)return null;
 try{const res=await fetch(API+path,{headers:{Authorization:"Bearer "+token},cache:"no-store"});return res.ok?await res.json():null}catch{return null}
}

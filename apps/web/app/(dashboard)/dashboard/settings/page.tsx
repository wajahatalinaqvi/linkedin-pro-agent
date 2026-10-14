import {api} from "../../../../lib/api";
export default async function Settings(){const me=await api<{email:string,workspaces:{name:string,timezone:string}[]}>("/api/v1/auth/me");
 return <><p className="eyebrow">Workspace configuration</p><h1 className="heading">Settings</h1><div className="card"><h3>Account</h3><p className="muted">{me?.email}</p><h3>Workspace</h3><p className="muted">{me?.workspaces[0]?.name} · {me?.workspaces[0]?.timezone}</p><p className="muted">LinkedIn OAuth, team membership and profile preferences will follow in later milestones.</p></div></>
}

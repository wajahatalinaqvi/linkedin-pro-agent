import {NextRequest,NextResponse} from "next/server";
const API=process.env.API_INTERNAL_URL||"http://localhost:8000";
export async function POST(req:NextRequest,{params}:{params:Promise<{workspaceId:string}>}){
 const {workspaceId}=await params;
 if(!/^[a-f0-9-]{36}$/.test(workspaceId))return NextResponse.json({detail:"Invalid workspace"},{status:400});
 const token=req.cookies.get("lp_session")?.value;if(!token)return NextResponse.json({detail:"Not authenticated"},{status:401});
 try{const response=await fetch(API+"/api/v1/workspaces/"+workspaceId+"/drafts",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:await req.text(),cache:"no-store"});
 return NextResponse.json(await response.json(),{status:response.status})
 }catch{return NextResponse.json({detail:"API unavailable"},{status:502})}
}

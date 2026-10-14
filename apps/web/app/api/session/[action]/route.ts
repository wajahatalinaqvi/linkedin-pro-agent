import { NextRequest, NextResponse } from "next/server";
const API=process.env.API_INTERNAL_URL||"http://localhost:8000";
export async function POST(req:NextRequest,{params}:{params:Promise<{action:string}>}){
 const {action}=await params;
 if(action!=="login"&&action!=="register")return NextResponse.json({detail:"Invalid action"},{status:404});
 try{
  const upstream=await fetch(API+"/api/v1/auth/"+action,{method:"POST",headers:{"Content-Type":"application/json"},body:await req.text(),cache:"no-store"});
  const json=await upstream.json();
  if(!upstream.ok)return NextResponse.json(json,{status:upstream.status});
  const result=NextResponse.json({ok:true});
  result.cookies.set("lp_session",json.access_token,{httpOnly:true,secure:process.env.NODE_ENV==="production",sameSite:"lax",path:"/",maxAge:8*60*60});
  return result;
 }catch{return NextResponse.json({detail:"API unavailable. Start FastAPI on port 8000."},{status:502})}
}

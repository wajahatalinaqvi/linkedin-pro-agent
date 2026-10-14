import {NextResponse} from "next/server";
export async function POST(){const r=NextResponse.redirect(new URL("/login",process.env.APP_ORIGIN||"http://localhost:3000"),303);r.cookies.delete("lp_session");return r}

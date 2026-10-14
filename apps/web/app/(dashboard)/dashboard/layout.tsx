import Link from "next/link";
import {redirect} from "next/navigation";
import {api} from "../../../lib/api";
import {LayoutDashboard,Compass,Layers,CalendarDays,Settings} from "lucide-react";
import type {ReactNode} from "react";
export default async function DashboardLayout({children}:{children:ReactNode}){
 const me=await api<{email:string}>("/api/v1/auth/me");if(!me)redirect("/login");
 const links=[{href:"/dashboard",label:"Overview",icon:LayoutDashboard},{href:"/dashboard/discover",label:"Discover",icon:Compass},{href:"/dashboard/drafts",label:"Drafts",icon:Layers},{href:"/dashboard/calendar",label:"Calendar",icon:CalendarDays},{href:"/dashboard/settings",label:"Settings",icon:Settings}];
 return <div className="shell"><aside className="sidebar"><div className="brand">LinkedIn <span>Pro Studio</span></div><nav className="navlist">{links.map(l=><Link className="nav" key={l.href} href={l.href}><l.icon size={17}/>{l.label}</Link>)}</nav></aside><main className="main">{children}</main></div>
}

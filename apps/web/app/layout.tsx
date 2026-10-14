import type { ReactNode } from "react";
import "./globals.css";
export const metadata = { title: "LinkedIn Pro Studio", description: "AI powered LinkedIn content studio" };
export default function RootLayout({children}:{children:ReactNode}) { return <html lang="en"><body>{children}</body></html> }

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import Link from "next/link";
import { Trophy, BarChart3, LineChart, Home, Activity } from "lucide-react";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "World Cup Prediction Engine",
  description: "Probabilistic prediction engine for national football teams.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-slate-950 text-slate-50 antialiased`}>
        <Providers>
          <div className="flex h-screen overflow-hidden">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
              <div className="p-6 flex items-center gap-3">
                <Trophy className="w-8 h-8 text-amber-500" />
                <span className="font-bold text-lg tracking-tight">PredictWC</span>
              </div>
              <nav className="flex-1 px-4 py-4 space-y-2">
                <Link href="/" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-800 text-slate-300 hover:text-white transition-colors">
                  <Home className="w-5 h-5" />
                  <span>Dashboard</span>
                </Link>
                <Link href="/predict" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-800 text-slate-300 hover:text-white transition-colors">
                  <Activity className="w-5 h-5" />
                  <span>Match Predictor</span>
                </Link>
                <Link href="/simulate" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-800 text-slate-300 hover:text-white transition-colors">
                  <LineChart className="w-5 h-5" />
                  <span>Tournament Simulator</span>
                </Link>
                <Link href="/rankings" className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-slate-800 text-slate-300 hover:text-white transition-colors">
                  <BarChart3 className="w-5 h-5" />
                  <span>Global Rankings</span>
                </Link>
              </nav>
            </aside>
            
            {/* Main Content */}
            <main className="flex-1 overflow-y-auto bg-slate-950">
              <div className="max-w-7xl mx-auto p-8">
                {children}
              </div>
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Trophy, BarChart3, LineChart, Home, Activity, Settings2, Globe2 } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Match Predictor", href: "/predict", icon: Activity },
  { name: "Tournament Simulator", href: "/simulate", icon: Settings2 },
  { name: "World Cup Tournament", href: "/tournament", icon: Globe2 },
  { name: "Monte Carlo Forecast", href: "/monte-carlo", icon: LineChart },
  { name: "Global Rankings", href: "/rankings", icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
      <div className="p-6 flex items-center gap-3">
        <Trophy className="w-8 h-8 text-amber-500" />
        <span className="font-bold text-lg tracking-tight">PredictWC</span>
      </div>
      <nav className="flex-1 px-4 py-4 space-y-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                isActive 
                  ? "bg-slate-800 text-amber-500 font-medium" 
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              )}
            >
              <Icon className="w-5 h-5" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

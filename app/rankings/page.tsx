"use client";

import { useState } from "react";
import { useRankings } from "@/hooks/useApi";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { BarChart3, Search } from "lucide-react";
import { useRouter } from "next/navigation";

export default function RankingsPage() {
  const { data: rankings, isLoading } = useRankings(300);
  const [search, setSearch] = useState("");
  const router = useRouter();

  const filtered = rankings?.filter(r => r.team.toLowerCase().includes(search.toLowerCase())) || [];

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <BarChart3 className="text-primary" />
            Global Rankings
          </h1>
          <p className="text-muted-foreground mt-2">
            Current Elo ratings for all national teams, updated after every match.
          </p>
        </div>
        
        <div className="relative w-full md:w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search team..." 
            className="pl-9 bg-slate-900 border-slate-800"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden">
        <Table>
          <TableHeader className="bg-slate-800/50">
            <TableRow className="border-slate-800">
              <TableHead className="w-24 text-center">Rank</TableHead>
              <TableHead>National Team</TableHead>
              <TableHead className="text-right">Elo Rating</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={3} className="text-center py-8 text-muted-foreground">Loading rankings...</TableCell>
              </TableRow>
            )}
            {!isLoading && filtered.length === 0 && (
              <TableRow>
                <TableCell colSpan={3} className="text-center py-8 text-muted-foreground">No teams found.</TableCell>
              </TableRow>
            )}
            {filtered.map((r) => (
              <TableRow 
                key={r.team} 
                className="border-slate-800 cursor-pointer hover:bg-slate-800/50 transition-colors"
                onClick={() => router.push(`/team/${encodeURIComponent(r.team)}`)}
              >
                <TableCell className="text-center font-bold text-slate-400">#{r.rank}</TableCell>
                <TableCell className="font-semibold">{r.team}</TableCell>
                <TableCell className="text-right font-mono text-primary">{r.elo.toFixed(1)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

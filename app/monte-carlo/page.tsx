"use client";

import { useState } from "react";
import { useMonteCarlo } from "@/hooks/useApi";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { LineChart, Loader2, Trophy, Medal } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from "recharts";

export default function MonteCarloPage() {
  const [simulations, setSimulations] = useState<string>("1000");
  const monteCarloMutation = useMonteCarlo();

  const handleSimulate = () => {
    monteCarloMutation.mutate(parseInt(simulations));
  };

  const results = monteCarloMutation.data?.results || [];
  const sortedResults = [...results].sort((a, b) => b.champion - a.champion);
  const top10 = sortedResults.slice(0, 10);

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-10">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <LineChart className="text-primary" />
          Tournament Probabilities
        </h1>
        <p className="text-muted-foreground mt-2">
          Run the Monte Carlo engine to forecast the World Cup 2026.
        </p>
      </div>

      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <CardTitle>Monte Carlo Forecast</CardTitle>
            <CardDescription>
              Select the number of full tournament realizations to run.
            </CardDescription>
          </div>
          <div className="flex items-center gap-4">
            <Select value={simulations} onValueChange={(val) => val && setSimulations(val)}>
              <SelectTrigger className="w-[180px] bg-slate-800 border-slate-700">
                <SelectValue placeholder="Select runs" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1000">1,000 runs (Fast)</SelectItem>
                <SelectItem value="5000">5,000 runs (Balanced)</SelectItem>
                <SelectItem value="10000">10,000 runs (Accurate)</SelectItem>
              </SelectContent>
            </Select>
            <Button 
              onClick={handleSimulate} 
              disabled={monteCarloMutation.isPending}
            >
              {monteCarloMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Run Forecast
            </Button>
          </div>
        </CardHeader>

        {monteCarloMutation.isSuccess && (
          <CardContent className="pt-6 space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Top Favorite */}
              <div className="bg-slate-800/50 rounded-lg p-6 flex items-center gap-6 border border-slate-700">
                <Trophy className="w-12 h-12 text-amber-500" />
                <div>
                  <div className="text-sm text-muted-foreground uppercase tracking-wider font-semibold mb-1">Most Likely Champion</div>
                  <div className="text-3xl font-black">{top10[0]?.team}</div>
                  <div className="text-lg text-amber-500 font-medium">
                    {top10[0]?.champion.toFixed(1)}% chance to win
                  </div>
                </div>
              </div>

              {/* Second Favorite */}
              <div className="bg-slate-800/50 rounded-lg p-6 flex items-center gap-6 border border-slate-700">
                <Medal className="w-12 h-12 text-slate-400" />
                <div>
                  <div className="text-sm text-muted-foreground uppercase tracking-wider font-semibold mb-1">Second Favorite</div>
                  <div className="text-3xl font-black">{top10[1]?.team}</div>
                  <div className="text-lg text-slate-400 font-medium">
                    {top10[1]?.champion.toFixed(1)}% chance to win
                  </div>
                </div>
              </div>
            </div>

            {/* Chart */}
            <div className="h-[350px] w-full mt-6">
              <h3 className="text-lg font-semibold mb-4">Top 10 Favorites</h3>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={top10} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#334155" />
                  <XAxis type="number" hide />
                  <YAxis dataKey="team" type="category" width={120} tick={{ fill: '#94a3b8' }} />
                  <Tooltip 
                    formatter={(value: any) => [`${Number(value).toFixed(1)}%`, 'Champion Prob']}
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc' }}
                  />
                  <Bar dataKey="champion" radius={[0, 4, 4, 0]}>
                    {top10.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={index === 0 ? '#f59e0b' : '#3b82f6'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Data Grid */}
            <div className="mt-8 rounded-md border border-slate-800 overflow-hidden">
              <Table>
                <TableHeader className="bg-slate-900">
                  <TableRow className="border-slate-800 hover:bg-slate-900/50">
                    <TableHead className="font-semibold text-slate-300">Team</TableHead>
                    <TableHead className="text-right font-semibold text-slate-300">R32</TableHead>
                    <TableHead className="text-right font-semibold text-slate-300">R16</TableHead>
                    <TableHead className="text-right font-semibold text-slate-300">QF</TableHead>
                    <TableHead className="text-right font-semibold text-slate-300">SF</TableHead>
                    <TableHead className="text-right font-semibold text-slate-300">Final</TableHead>
                    <TableHead className="text-right font-semibold text-amber-500">Champion</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedResults.map((r, i) => (
                    <TableRow key={r.team} className="border-slate-800 hover:bg-slate-800/50">
                      <TableCell className="font-medium">
                        {i + 1}. {r.team}
                      </TableCell>
                      <TableCell className="text-right">{r["round-of-32"].toFixed(1)}%</TableCell>
                      <TableCell className="text-right">{r["round-of-16"].toFixed(1)}%</TableCell>
                      <TableCell className="text-right">{r.quarterfinalist.toFixed(1)}%</TableCell>
                      <TableCell className="text-right">{r.semifinalist.toFixed(1)}%</TableCell>
                      <TableCell className="text-right">{r.finalist.toFixed(1)}%</TableCell>
                      <TableCell className="text-right font-bold text-amber-500">{r.champion.toFixed(1)}%</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        )}

        {!monteCarloMutation.isSuccess && !monteCarloMutation.isPending && (
          <CardContent className="pt-6">
            <div className="flex-1 flex items-center justify-center text-muted-foreground border-2 border-dashed border-slate-800 rounded-lg p-12">
              Select simulation count and click Run Forecast
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
}

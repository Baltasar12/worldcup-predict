"use client";

import { useState } from "react";
import { useRankings, useSimulation } from "@/hooks/useApi";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LineChart, Trophy, Loader2 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from "recharts";

const WC_2026_PRESET = [
  "Argentina", "France", "Brazil", "England", "Spain", "Portugal", "Netherlands", "Italy", 
  "Germany", "Croatia", "Uruguay", "Colombia", "Morocco", "Senegal", "Japan", "USA"
];

export default function SimulatePage() {
  const { data: rankings } = useRankings(50);
  const [selectedTeams, setSelectedTeams] = useState<string[]>([]);
  
  const simMutation = useSimulation();

  const toggleTeam = (team: string) => {
    setSelectedTeams(prev => 
      prev.includes(team) ? prev.filter(t => t !== team) : [...prev, team]
    );
  };

  const loadPreset = (preset: string[]) => {
    setSelectedTeams(preset);
  };

  const handleSimulate = () => {
    if (selectedTeams.length < 2) return;
    simMutation.mutate(selectedTeams);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <LineChart className="text-primary" />
          Tournament Simulator
        </h1>
        <p className="text-muted-foreground mt-2">
          Run 10,000 Monte Carlo knockout tournament simulations for the selected teams.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Team Selection */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
              <CardTitle>Presets</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="secondary" className="w-full justify-start" onClick={() => loadPreset(WC_2026_PRESET)}>
                World Cup 2026 Favorites (Top 16)
              </Button>
              <Button variant="secondary" className="w-full justify-start" onClick={() => {
                if (rankings) loadPreset(rankings.slice(0, 32).map(r => r.team));
              }}>
                Current Top 32 Ranked
              </Button>
              <Button variant="outline" className="w-full justify-start text-destructive" onClick={() => loadPreset([])}>
                Clear All
              </Button>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
              <CardTitle>Select Teams ({selectedTeams.length})</CardTitle>
              <CardDescription>Click to add or remove</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {rankings?.map((r) => {
                  const isSelected = selectedTeams.includes(r.team);
                  return (
                    <Badge 
                      key={r.team}
                      variant={isSelected ? "default" : "outline"}
                      className={`cursor-pointer transition-colors ${isSelected ? 'bg-primary' : 'hover:bg-slate-800'}`}
                      onClick={() => toggleTeam(r.team)}
                    >
                      {r.team}
                    </Badge>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Results */}
        <div className="lg:col-span-2">
          <Card className="bg-slate-900 border-slate-800 h-full min-h-[500px] flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Simulation Results</CardTitle>
                <CardDescription>
                  {simMutation.isSuccess 
                    ? `Based on ${simMutation.data.simulations_run.toLocaleString()} runs`
                    : "Select teams and run simulation"}
                </CardDescription>
              </div>
              <Button 
                onClick={handleSimulate} 
                disabled={selectedTeams.length < 2 || simMutation.isPending}
              >
                {simMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Run Simulator
              </Button>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              {simMutation.isSuccess && (
                <div className="space-y-8 flex-1">
                  
                  {/* Winner highlight */}
                  <div className="bg-slate-800/50 rounded-lg p-6 flex items-center gap-6 border border-slate-700">
                    <Trophy className="w-12 h-12 text-amber-500" />
                    <div>
                      <div className="text-sm text-muted-foreground uppercase tracking-wider font-semibold mb-1">Most Likely Champion</div>
                      <div className="text-3xl font-black">{simMutation.data.champions[0].team}</div>
                      <div className="text-lg text-amber-500 font-medium">
                        {(simMutation.data.champions[0].probability * 100).toFixed(1)}% chance to win
                      </div>
                    </div>
                  </div>

                  {/* Chart */}
                  <div className="h-[350px] w-full mt-6">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={simMutation.data.champions.slice(0, 15)} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#334155" />
                        <XAxis type="number" hide />
                        <YAxis dataKey="team" type="category" width={120} tick={{ fill: '#94a3b8' }} />
                        <Tooltip 
                          formatter={(value: string | number | undefined | readonly (string | number)[]) => [`${(Number(value || 0) * 100).toFixed(1)}%`, 'Probability']}
                          contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc' }}
                        />
                        <Bar dataKey="probability" radius={[0, 4, 4, 0]}>
                          {simMutation.data.champions.slice(0, 15).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={index === 0 ? '#f59e0b' : '#3b82f6'} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {!simMutation.isSuccess && !simMutation.isPending && (
                <div className="flex-1 flex items-center justify-center text-muted-foreground border-2 border-dashed border-slate-800 rounded-lg m-4">
                  Select at least 2 teams and click Run Simulator
                </div>
              )}
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}

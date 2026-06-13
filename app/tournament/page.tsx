"use client";

import { useWorldCupSimulation } from "@/hooks/useApi";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Trophy, Loader2, PlayCircle } from "lucide-react";

export default function TournamentPage() {
  const simMutation = useWorldCupSimulation();

  return (
    <div className="max-w-[1400px] mx-auto space-y-8 pb-20">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Trophy className="text-primary" />
            World Cup 2026 Simulator
          </h1>
          <p className="text-muted-foreground mt-2">
            Run a full deterministic realization of the 48-team tournament, from group stages to the final.
          </p>
        </div>
        <Button 
          size="lg" 
          onClick={() => simMutation.mutate()} 
          disabled={simMutation.isPending}
          className="w-full md:w-auto"
        >
          {simMutation.isPending ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : <PlayCircle className="mr-2 h-5 w-5" />}
          Simulate Tournament
        </Button>
      </div>

      {!simMutation.data && !simMutation.isPending && (
        <Card className="bg-slate-900 border-slate-800 border-dashed">
          <CardContent className="flex items-center justify-center py-24 text-muted-foreground">
            Click "Simulate Tournament" to generate a full World Cup realization.
          </CardContent>
        </Card>
      )}

      {simMutation.data && (
        <div className="space-y-12 animate-in fade-in duration-500">
          
          {/* Final Result Banner */}
          <Card className="bg-gradient-to-r from-amber-500/20 to-amber-900/20 border-amber-500/50">
            <CardContent className="flex flex-col md:flex-row items-center justify-center py-10 gap-6">
              <Trophy className="w-20 h-20 text-amber-500" />
              <div className="text-center md:text-left">
                <div className="text-amber-500 font-bold tracking-widest uppercase mb-2">World Champion</div>
                <div className="text-5xl font-black">{simMutation.data.bracket.champion}</div>
              </div>
            </CardContent>
          </Card>

          {/* Group Stage */}
          <div>
            <h2 className="text-2xl font-bold mb-6">Group Stage</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {simMutation.data.groups.map(group => (
                <Card key={group.group} className="bg-slate-900 border-slate-800 overflow-hidden">
                  <div className="bg-slate-800 px-4 py-2 font-bold text-slate-200">
                    Group {group.group}
                  </div>
                  <Table className="text-sm">
                    <TableHeader>
                      <TableRow className="border-slate-800 hover:bg-transparent">
                        <TableHead className="h-8">Team</TableHead>
                        <TableHead className="h-8 text-right">Pts</TableHead>
                        <TableHead className="h-8 text-right">GD</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {group.standings.map((team, idx) => (
                        <TableRow key={team.team} className={`border-slate-800 hover:bg-slate-800/50 ${idx < 2 ? 'bg-green-900/10' : ''}`}>
                          <TableCell className="font-medium py-2">
                            <span className="text-muted-foreground mr-2">{idx + 1}</span>
                            {team.team}
                          </TableCell>
                          <TableCell className="text-right font-bold py-2">{team.points}</TableCell>
                          <TableCell className="text-right py-2">{team.goal_difference > 0 ? `+${team.goal_difference}` : team.goal_difference}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Card>
              ))}
            </div>
          </div>

          {/* Knockout Matches (Simple List representation because full tree is huge) */}
          <div>
            <h2 className="text-2xl font-bold mb-6">Knockout Stage</h2>
            <div className="space-y-8">
              {[
                { title: 'Round of 32', matches: simMutation.data.bracket.round_of_32 },
                { title: 'Round of 16', matches: simMutation.data.bracket.round_of_16 },
                { title: 'Quarterfinals', matches: simMutation.data.bracket.quarterfinals },
                { title: 'Semifinals', matches: simMutation.data.bracket.semifinals },
                { title: 'Final', matches: simMutation.data.bracket.final }
              ].map(round => {
                if (!round.matches || round.matches.length === 0) return null;
                
                return (
                  <div key={round.title}>
                    <h3 className="text-xl font-semibold mb-4 text-slate-300 border-b border-slate-800 pb-2">{round.title}</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      {round.matches.map(match => (
                        <Card key={match.match_id} className="bg-slate-900 border-slate-800">
                          <CardContent className="p-4 space-y-3">
                            <div className="flex justify-between items-center">
                              <span className="font-medium">{match.team_a}</span>
                            </div>
                            <div className="h-[1px] bg-slate-800 w-full" />
                            <div className="flex justify-between items-center">
                              <span className="font-medium">{match.team_b}</span>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}

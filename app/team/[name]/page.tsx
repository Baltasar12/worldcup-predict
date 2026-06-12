"use client";

import { useTeam, useRankings } from "@/hooks/useApi";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Trophy, Activity, Globe } from "lucide-react";

export default function TeamDetailPage() {
  const params = useParams();
  const router = useRouter();
  const teamName = decodeURIComponent(params.name as string);

  const { data: teamData, isLoading: teamLoading } = useTeam(teamName);
  const { data: rankings } = useRankings(300);

  const rank = rankings?.find(r => r.team === teamName)?.rank;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <Button variant="ghost" className="mb-4 text-muted-foreground hover:text-white" onClick={() => router.back()}>
        <ArrowLeft className="w-4 h-4 mr-2" /> Back
      </Button>

      {teamLoading ? (
        <div className="h-40 flex items-center justify-center text-muted-foreground">Loading team data...</div>
      ) : teamData ? (
        <div className="space-y-8">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-6 border-b border-slate-800">
            <div>
              <h1 className="text-4xl font-black">{teamData.name}</h1>
              <p className="text-xl text-muted-foreground mt-2">National Football Team</p>
            </div>
            {rank && (
              <div className="bg-primary/10 text-primary px-4 py-2 rounded-lg font-bold text-xl flex items-center gap-2">
                <Globe className="w-5 h-5" /> World Rank #{rank}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Current Elo Rating</CardTitle>
                <Activity className="w-4 h-4 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold">{teamData.elo.toFixed(1)}</div>
              </CardContent>
            </Card>

            <Card className="bg-slate-900 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Matches Tracked</CardTitle>
                <Trophy className="w-4 h-4 text-amber-500" />
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold">{teamData.matches_played}</div>
              </CardContent>
            </Card>
          </div>

          <div className="flex justify-center mt-12">
            <Button size="lg" onClick={() => router.push(`/predict?team_a=${encodeURIComponent(teamData.name)}`)}>
              Use in Match Predictor
            </Button>
          </div>
        </div>
      ) : (
        <div className="text-center py-12 text-destructive">Team not found.</div>
      )}
    </div>
  );
}

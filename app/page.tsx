"use client";

import { useRankings } from "@/hooks/useApi";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Trophy, Activity, LineChart, ArrowRight } from "lucide-react";

import { useRouter } from "next/navigation";

export default function HomePage() {
  const { data: rankings, isLoading } = useRankings(10);
  const router = useRouter();
  
  const topTeam = rankings?.[0];

  return (
    <div className="max-w-5xl mx-auto space-y-12">
      {/* Hero */}
      <section className="text-center space-y-4 py-12">
        <h1 className="text-5xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-primary to-blue-500">
          World Cup Prediction Engine
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          A probabilistic engine powered by historical match data, empirical draw calibration, and Elo ratings to predict the beautiful game.
        </p>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Top Team Highlight */}
        <Card className="bg-gradient-to-br from-amber-500/20 to-slate-900 border-amber-500/30 md:col-span-1 shadow-lg shadow-amber-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-500">
              <Trophy className="w-5 h-5" /> Current #1 Team
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading ? (
              <div className="h-20 animate-pulse bg-slate-800/50 rounded-lg"></div>
            ) : topTeam ? (
              <>
                <div className="text-4xl font-black">{topTeam.team}</div>
                <div className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                  Elo Rating: <span className="text-foreground text-lg ml-1">{topTeam.elo.toFixed(1)}</span>
                </div>
                <Button 
                  variant="outline" 
                  className="w-full mt-4 border-amber-500/50 hover:bg-amber-500/10 text-amber-500"
                  onClick={() => router.push(`/team/${encodeURIComponent(topTeam.team)}`)}
                >
                  View Team Profile
                </Button>
              </>
            ) : (
              <div className="text-muted-foreground">Unavailable</div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-6">
          <Card className="bg-slate-900 border-slate-800 hover:border-primary/50 transition-colors group cursor-pointer" onClick={() => router.push('/predict')}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-primary" /> Match Predictor
              </CardTitle>
              <CardDescription>Generate win/draw/loss probabilities between any two nations.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex justify-end">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                  <ArrowRight className="w-5 h-5 text-primary" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800 hover:border-blue-500/50 transition-colors group cursor-pointer" onClick={() => router.push('/simulate')}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LineChart className="w-5 h-5 text-blue-500" /> Tournament Simulator
              </CardTitle>
              <CardDescription>Run Monte Carlo simulations of knockout tournaments.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex justify-end">
                <div className="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center group-hover:bg-blue-500/20 transition-colors">
                  <ArrowRight className="w-5 h-5 text-blue-500" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

      </div>

      {/* Top 10 Preview */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Top 10 Global Rankings</CardTitle>
            <CardDescription>The current best teams in the world.</CardDescription>
          </div>
          <Button variant="ghost" onClick={() => router.push('/rankings')}>
            View All Rankings
          </Button>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {isLoading ? (
              Array(10).fill(0).map((_, i) => (
                <div key={i} className="h-16 animate-pulse bg-slate-800/50 rounded-lg"></div>
              ))
            ) : (
              rankings?.map((r) => (
                <div key={r.team} className="bg-slate-800/30 p-4 rounded-lg border border-slate-800/50 flex flex-col items-center text-center hover:bg-slate-800/50 transition-colors cursor-pointer" onClick={() => router.push(`/team/${encodeURIComponent(r.team)}`)}>
                  <div className="text-xs font-bold text-slate-500 mb-1">#{r.rank}</div>
                  <div className="font-semibold">{r.team}</div>
                  <div className="text-sm font-mono text-primary mt-1">{Math.round(r.elo)}</div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

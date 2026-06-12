"use client";

import { useState } from "react";
import { useRankings, usePredict } from "@/hooks/useApi";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Trophy, Activity } from "lucide-react";

export default function PredictPage() {
  const { data: rankings } = useRankings(300); // Fetch top 300 to populate dropdowns
  
  const [teamA, setTeamA] = useState<string>("");
  const [teamB, setTeamB] = useState<string>("");
  const [queryA, setQueryA] = useState<string>("");
  const [queryB, setQueryB] = useState<string>("");

  const handlePredict = () => {
    setQueryA(teamA);
    setQueryB(teamB);
  };

  const { data: prediction, isLoading } = usePredict(queryA, queryB);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Activity className="text-primary" />
          Match Predictor
        </h1>
        <p className="text-muted-foreground mt-2">
          Select two national teams to generate a probabilistic prediction based on our Elo model and empirical draw calibration.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle>Team A (Home)</CardTitle>
          </CardHeader>
          <CardContent>
            <Select value={teamA} onValueChange={(val) => setTeamA(val || "")}>
              <SelectTrigger>
                <SelectValue placeholder="Select Team A" />
              </SelectTrigger>
              <SelectContent>
                {rankings?.map((r) => (
                  <SelectItem key={r.team} value={r.team}>{r.team} (Elo: {Math.round(r.elo)})</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle>Team B (Away)</CardTitle>
          </CardHeader>
          <CardContent>
            <Select value={teamB} onValueChange={(val) => setTeamB(val || "")}>
              <SelectTrigger>
                <SelectValue placeholder="Select Team B" />
              </SelectTrigger>
              <SelectContent>
                {rankings?.map((r) => (
                  <SelectItem key={r.team} value={r.team}>{r.team} (Elo: {Math.round(r.elo)})</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-center">
        <Button 
          size="lg" 
          onClick={handlePredict} 
          disabled={!teamA || !teamB || teamA === teamB || isLoading}
          className="w-full md:w-auto"
        >
          {isLoading ? "Calculating..." : "Predict Match"}
        </Button>
      </div>

      {prediction && (
        <Card className="bg-slate-900 border-slate-800 overflow-hidden">
          <CardHeader className="bg-slate-800/50 border-b border-slate-800">
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="text-2xl">{prediction.team_a}</CardTitle>
                <CardDescription>Elo: {prediction.elo_a.toFixed(1)}</CardDescription>
              </div>
              <div className="text-4xl font-black text-slate-700">VS</div>
              <div className="text-right">
                <CardTitle className="text-2xl">{prediction.team_b}</CardTitle>
                <CardDescription>Elo: {prediction.elo_b.toFixed(1)}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-8 space-y-8">
            
            <div className="flex items-center justify-center gap-2 text-xl font-bold text-amber-500 mb-6">
              <Trophy className="w-6 h-6" />
              Favorite: {prediction.favorite}
            </div>

            <div className="space-y-6">
              <div className="space-y-2">
                <div className="flex justify-between text-sm font-medium">
                  <span>{prediction.team_a} Win</span>
                  <span>{(prediction.win_probability_a * 100).toFixed(1)}%</span>
                </div>
                <Progress value={prediction.win_probability_a * 100} className="h-3 bg-slate-800 [&>div]:bg-green-500" />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm font-medium">
                  <span>Draw</span>
                  <span>{(prediction.draw_probability * 100).toFixed(1)}%</span>
                </div>
                <Progress value={prediction.draw_probability * 100} className="h-3 bg-slate-800 [&>div]:bg-slate-400" />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm font-medium">
                  <span>{prediction.team_b} Win</span>
                  <span>{(prediction.win_probability_b * 100).toFixed(1)}%</span>
                </div>
                <Progress value={prediction.win_probability_b * 100} className="h-3 bg-slate-800 [&>div]:bg-blue-500" />
              </div>
            </div>

          </CardContent>
        </Card>
      )}
    </div>
  );
}

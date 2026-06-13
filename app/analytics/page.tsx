"use client";

import { useAnalyticsPerformance } from "@/hooks/useApi";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Target, Trophy, FileDigit } from "lucide-react";

export default function AnalyticsPage() {
  const { data: metrics, isLoading, error } = useAnalyticsPerformance();

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-amber-500 mb-4"></div>
        <div className="text-slate-400">Loading evaluation metrics...</div>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6 text-center text-red-400 max-w-2xl mx-auto mt-12">
        <h3 className="text-xl font-bold mb-2">Evaluation Data Unavailable</h3>
        <p>Could not load performance summary. Make sure to run the backend evaluator module first.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500 pb-12">
      <div className="flex justify-between items-end border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-4xl font-black tracking-tight mb-2 text-slate-100">Prediction Quality</h1>
          <p className="text-slate-400 max-w-2xl">
            Mathematical backtesting and calibration results. Evaluated over the entire historical match database using 3-way (Win/Draw/Loss) metric formulations.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-slate-900 border-slate-800">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-blue-500/20 text-blue-400 rounded-lg">
                <Target className="w-6 h-6" />
              </div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">3-Way</span>
            </div>
            <div className="text-3xl font-bold mb-1">{(metrics.accuracy * 100).toFixed(2)}%</div>
            <div className="text-sm text-slate-400">Global Accuracy</div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-purple-500/20 text-purple-400 rounded-lg">
                <Activity className="w-6 h-6" />
              </div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Penalty</span>
            </div>
            <div className="text-3xl font-bold mb-1">{metrics.log_loss.toFixed(4)}</div>
            <div className="text-sm text-slate-400">Log Loss (Cross-Entropy)</div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-lg">
                <Activity className="w-6 h-6" />
              </div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Squared Error</span>
            </div>
            <div className="text-3xl font-bold mb-1">{metrics.brier_score.toFixed(4)}</div>
            <div className="text-sm text-slate-400">Brier Score</div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-slate-800 text-slate-300 rounded-lg">
                <FileDigit className="w-6 h-6" />
              </div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Dataset</span>
            </div>
            <div className="text-3xl font-bold mb-1">{metrics.evaluated_matches.toLocaleString()}</div>
            <div className="text-sm text-slate-400">Evaluated Matches</div>
          </CardContent>
        </Card>
      </div>

      <div>
        <h2 className="text-2xl font-bold mb-6 mt-12 flex items-center gap-3">
          <Trophy className="w-6 h-6 text-amber-500" />
          Historical World Cup Validation
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {metrics.world_cups.map((wc) => (
            <Card key={wc.year} className="bg-slate-900 border-slate-800 hover:border-slate-700 transition-colors">
              <CardHeader className="pb-2">
                <CardTitle className="text-xl flex items-center justify-between">
                  <span>FIFA World Cup {wc.year}</span>
                </CardTitle>
                <CardDescription className="text-amber-500 font-medium">
                  Champion: {wc.champion}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mt-4 pt-4 border-t border-slate-800">
                  <div className="text-sm text-slate-400 mb-3">Model Prediction Details</div>
                  <div className="space-y-4">
                    <div className="bg-slate-950 p-3 rounded-md">
                      <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">Predicted Rank of Champion</div>
                      <div className="font-mono text-lg text-slate-200">
                        #{wc.champion_predicted_rank} <span className="text-slate-500 text-sm ml-1">in the world</span>
                      </div>
                    </div>
                    
                    <div>
                      <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">Top 5 Predicted Teams</div>
                      <div className="flex flex-wrap gap-2">
                        {wc.top_predicted_teams.map((team, idx) => (
                          <span 
                            key={team} 
                            className={`px-2 py-1 text-xs rounded-full font-medium ${team === wc.champion ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-slate-800 text-slate-300'}`}
                          >
                            {idx + 1}. {team}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

const API_BASE_URL = "http://127.0.0.1:9000";

export interface TeamRanking {
  rank: number;
  team: string;
  elo: number;
}

export interface PredictionResult {
  team_a: string;
  team_b: string;
  elo_a: number;
  elo_b: number;
  win_probability_a: number;
  draw_probability: number;
  win_probability_b: number;
  favorite: string;
}

export interface ChampionProb {
  team: string;
  probability: number;
}

export interface SimulationResult {
  simulations_run: number;
  champions: ChampionProb[];
}

export interface TeamDetails {
  name: string;
  elo: number;
  matches_played: number;
}

export const fetchRankings = async (limit: number = 50): Promise<TeamRanking[]> => {
  const res = await fetch(`${API_BASE_URL}/rankings?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch rankings");
  return res.json();
};

export const fetchTeam = async (team: string): Promise<TeamDetails> => {
  const res = await fetch(`${API_BASE_URL}/team/${encodeURIComponent(team)}`);
  if (!res.ok) throw new Error("Failed to fetch team details");
  return res.json();
};

export const predictMatch = async (teamA: string, teamB: string): Promise<PredictionResult> => {
  const res = await fetch(`${API_BASE_URL}/predict?team_a=${encodeURIComponent(teamA)}&team_b=${encodeURIComponent(teamB)}`);
  if (!res.ok) throw new Error("Failed to predict match");
  return res.json();
};

export const simulateTournament = async (teams: string[]): Promise<SimulationResult> => {
  const res = await fetch(`${API_BASE_URL}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ teams }),
  });
  if (!res.ok) throw new Error("Failed to simulate tournament");
  return res.json();
};

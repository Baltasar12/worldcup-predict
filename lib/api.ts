const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:9000";

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

export interface MonteCarloTeamResult {
  team: string;
  "round-of-32": number;
  "round-of-16": number;
  quarterfinalist: number;
  semifinalist: number;
  finalist: number;
  champion: number;
}

export interface MonteCarloResponse {
  simulations: number;
  results: MonteCarloTeamResult[];
}

export interface WorldCupValidationResponse {
  year: number;
  champion: string;
  champion_predicted_rank: number;
  top_predicted_teams: string[];
}

export interface MonteCarloRequest {
  simulations: number;
  seed?: number;
}

export interface AnalyticsPerformanceResponse {
  accuracy: number;
  log_loss: number;
  brier_score: number;
  evaluated_matches: number;
  world_cups: WorldCupValidationResponse[];
}

export const runMonteCarlo = async (data: MonteCarloRequest): Promise<MonteCarloResponse> => {
  const response = await fetch(`${API_BASE_URL}/world-cup/monte-carlo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error('Failed to run Monte Carlo simulation');
  return response.json();
};

export const getAnalyticsPerformance = async (): Promise<AnalyticsPerformanceResponse> => {
  const response = await fetch(`${API_BASE_URL}/analytics/model-performance`);
  if (!response.ok) throw new Error('Failed to fetch analytics performance');
  return response.json();
};

export interface GroupStageMatchResult {
  team_a: string;
  team_b: string;
  score_a: number;
  score_b: number;
}

export interface TeamStandingResponse {
  team: string;
  points: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  elo: number;
}

export interface GroupStandingsResponse {
  group: string;
  standings: TeamStandingResponse[];
  matches: GroupStageMatchResult[];
}

export interface BracketMatchResponse {
  match_id: number;
  round: string;
  team_a: string;
  team_b: string;
  team_a_origin: string;
  team_b_origin: string;
}

export interface BracketResponse {
  round_of_32: BracketMatchResponse[];
  round_of_16: BracketMatchResponse[];
  quarterfinals: BracketMatchResponse[];
  semifinals: BracketMatchResponse[];
  final: BracketMatchResponse[];
  champion: string;
  qualified_teams: number;
}

export interface WorldCupSimulationResponse {
  groups: GroupStandingsResponse[];
  bracket: BracketResponse;
}

export const runWorldCupSimulation = async (): Promise<WorldCupSimulationResponse> => {
  const res = await fetch(`${API_BASE_URL}/world-cup/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to run World Cup simulation");
  return res.json();
};

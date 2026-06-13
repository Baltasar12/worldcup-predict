import { useQuery, useMutation } from "@tanstack/react-query";
import { fetchRankings, fetchTeam, predictMatch, simulateTournament, runMonteCarlo, runWorldCupSimulation } from "@/lib/api";

export const useRankings = (limit: number = 50) => {
  return useQuery({
    queryKey: ["rankings", limit],
    queryFn: () => fetchRankings(limit),
  });
};

export const useTeam = (team: string) => {
  return useQuery({
    queryKey: ["team", team],
    queryFn: () => fetchTeam(team),
    enabled: !!team,
  });
};

export const usePredict = (teamA: string, teamB: string) => {
  return useQuery({
    queryKey: ["predict", teamA, teamB],
    queryFn: () => predictMatch(teamA, teamB),
    enabled: !!teamA && !!teamB && teamA !== teamB,
  });
};

export const useSimulation = () => {
  return useMutation({
    mutationFn: (teams: string[]) => simulateTournament(teams),
  });
};

export const useMonteCarlo = () => {
  return useMutation({
    mutationFn: (simulations: number) => runMonteCarlo(simulations),
  });
};

export const useWorldCupSimulation = () => {
  return useMutation({
    mutationFn: () => runWorldCupSimulation(),
  });
};

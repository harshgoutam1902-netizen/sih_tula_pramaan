/**
 * Mock drift risk calculation for offline mode.
 * Mirrors backend formula: sigmoid(-3.2 + 0.35*abs(deltaT) + 0.04*abs(deltaRH) + 0.02*load + 0.9*timeSpanning)
 */

export function mockDriftRisk(
  deltaTemp: number,
  deltaRh: number,
  loadPct: number = 50,
  timeSpanning: number = 1
): number {
  // Hardcoded weights (same as backend)
  let z = -3.2 + 0.35 * Math.abs(deltaTemp) + 0.04 * Math.abs(deltaRh) + 0.02 * loadPct + 0.9 * timeSpanning;
  
  // Clamp z to prevent overflow
  z = Math.max(-50, Math.min(50, z));
  
  // Sigmoid: 1 / (1 + exp(-z))
  const risk = 1 / (1 + Math.exp(-z));
  
  // Clamp to [0, 1]
  return Math.max(0, Math.min(1, risk));
}

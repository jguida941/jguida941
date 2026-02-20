// === Progression System (XP / Level / Skill Points) ===

import type { GameState } from "../core/types.js";
import { pushLog } from "../state/createState.js";

function xpForNextLevel(level: number): number {
  return Math.floor(90 + level * level * 28);
}

export function awardKillProgress(state: GameState, baseReward: number): void {
  const xpGain = Math.floor(8 + baseReward * 1.2);
  state.progression.xp += xpGain;
  state.progression.kills += 1;

  while (state.progression.xp >= xpForNextLevel(state.progression.level)) {
    const threshold = xpForNextLevel(state.progression.level);
    state.progression.xp -= threshold;
    state.progression.level += 1;
    state.progression.skillPoints += 1;
    pushLog(state, `Level up! Reached level ${state.progression.level}.`);
  }
}

export function awardWaveProgress(state: GameState): void {
  const xpGain = 24 + state.stage * 8 + state.wave * 4;
  state.progression.xp += xpGain;

  while (state.progression.xp >= xpForNextLevel(state.progression.level)) {
    const threshold = xpForNextLevel(state.progression.level);
    state.progression.xp -= threshold;
    state.progression.level += 1;
    state.progression.skillPoints += 1;
    pushLog(state, `Level up! Reached level ${state.progression.level}.`);
  }
}

export function xpToNextLevel(state: GameState): number {
  return xpForNextLevel(state.progression.level);
}

// === Economy System ===

import { getClassEconomyMultiplier } from "./classes.js";
import { getEconomyMultiplier } from "./upgrades.js";
import type { GameState } from "../core/types.js";

export function updateEconomy(state: GameState): void {
  const currentTick = Math.floor(state.clockSeconds / 18);
  if (currentTick <= state.passiveIncomeTick) {
    return;
  }

  const ticksElapsed = currentTick - state.passiveIncomeTick;
  const globalMultiplier = getEconomyMultiplier(state) * getClassEconomyMultiplier(state);
  const baseTickValue = 2 + Math.floor(state.stage / 2);
  const goldPerTick = Math.max(1, Math.floor(baseTickValue * globalMultiplier));

  state.gold += ticksElapsed * goldPerTick;
  state.passiveIncomeTick = currentTick;
}

// === HUD Renderer ===

import { HERO_CLASS_DEFINITIONS, SPELL_DEFINITIONS, SPELL_ORDER } from "../core/config.js";
import type { GameState } from "../core/types.js";
import { xpToNextLevel } from "../systems/progression.js";

export interface HudRefs {
  phaseValue: HTMLElement;
  stageValue: HTMLElement;
  waveValue: HTMLElement;
  waveGoalValue: HTMLElement;
  healthValue: HTMLElement;
  goldValue: HTMLElement;
  levelValue: HTMLElement;
  xpValue: HTMLElement;
  skillPointsValue: HTMLElement;
  classValue: HTMLElement;
  placementModeValue: HTMLElement;
  selectedTowerValue: HTMLElement;
  selectedBuildingValue: HTMLElement;
  spellChargesValue: HTMLElement;
  combatStatsValue: HTMLElement;
  logList: HTMLElement;
}

export function renderHud(state: GameState, refs: HudRefs): void {
  refs.phaseValue.textContent = state.phase.toUpperCase();
  refs.stageValue.textContent = String(state.stage);
  refs.waveValue.textContent = String(state.wave);
  refs.waveGoalValue.textContent = state.waveGoalText;
  refs.healthValue.textContent = `${state.baseHealth} / ${state.maxBaseHealth}`;
  refs.goldValue.textContent = String(state.gold);
  refs.levelValue.textContent = String(state.progression.level);
  refs.skillPointsValue.textContent = String(state.progression.skillPoints);

  const nextXp = xpToNextLevel(state);
  refs.xpValue.textContent = `${Math.floor(state.progression.xp)} / ${nextXp}`;

  refs.classValue.textContent = HERO_CLASS_DEFINITIONS[state.heroClass].label;
  refs.placementModeValue.textContent = state.placementMode;
  refs.selectedTowerValue.textContent = state.selectedTower;
  refs.selectedBuildingValue.textContent = state.selectedBuilding;

  refs.spellChargesValue.textContent = SPELL_ORDER.map((spellKind) => {
    const spell = state.spells[spellKind];
    const label = SPELL_DEFINITIONS[spellKind].label;
    return `${label}: ${spell.charges}/${spell.maxCharges}`;
  }).join(" | ");

  refs.combatStatsValue.textContent =
    `kills ${state.progression.kills} | leaks ${state.roundStats.leaked} | hit ${state.roundStats.shotsHit}/${state.roundStats.shotsFired} | spells ${state.roundStats.spellsCast}`;

  refs.logList.innerHTML = state.logs.map((line) => `<li>${line}</li>`).join("");
}

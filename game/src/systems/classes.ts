// === Hero Class System ===

import { HERO_CLASS_DEFINITIONS } from "../core/config.js";
import { pushLog } from "../state/createState.js";
import type { GameState, HeroClass, HeroClassDefinition } from "../core/types.js";

export function getHeroClassDefinition(heroClass: HeroClass): HeroClassDefinition {
  return HERO_CLASS_DEFINITIONS[heroClass];
}

export function getActiveClassDefinition(state: GameState): HeroClassDefinition {
  return HERO_CLASS_DEFINITIONS[state.heroClass];
}

export function trySelectHeroClass(state: GameState, heroClass: HeroClass): boolean {
  if (state.classLocked) {
    pushLog(state, "Class is locked after the first wave starts.");
    return false;
  }

  if (state.heroClass === heroClass) {
    return false;
  }

  state.heroClass = heroClass;
  const classDef = getActiveClassDefinition(state);
  pushLog(state, `Class selected: ${classDef.label}.`);
  return true;
}

export function lockClassSelection(state: GameState): void {
  if (state.classLocked) {
    return;
  }

  state.classLocked = true;
  pushLog(state, "Class locked for this run.");
}

export function getClassDamageMultiplier(state: GameState): number {
  return getActiveClassDefinition(state).damageMultiplier;
}

export function getClassRangeMultiplier(state: GameState): number {
  return getActiveClassDefinition(state).rangeMultiplier;
}

export function getClassFireRateMultiplier(state: GameState): number {
  return getActiveClassDefinition(state).fireRateMultiplier;
}

export function getClassEconomyMultiplier(state: GameState): number {
  return getActiveClassDefinition(state).economyMultiplier;
}

export function getClassSpellPowerMultiplier(state: GameState): number {
  return getActiveClassDefinition(state).spellPowerMultiplier;
}

export function getClassBuildCostMultiplier(state: GameState): number {
  return getActiveClassDefinition(state).buildCostMultiplier;
}

export function getClassBonusSpellCharges(state: GameState): number {
  return getActiveClassDefinition(state).bonusSpellCharges;
}

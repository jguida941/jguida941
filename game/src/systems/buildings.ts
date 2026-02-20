// === Building System ===

import { BUILDING_DEFINITIONS } from "../core/config.js";
import { getClassBuildCostMultiplier, getClassEconomyMultiplier } from "./classes.js";
import { getEconomyMultiplier } from "./upgrades.js";
import { nextBuildingId, pushLog } from "../state/createState.js";
import type { BuildingKind, BuildingState, GameState } from "../core/types.js";

function buildingCost(state: GameState, kind: BuildingKind): number {
  const baseCost = BUILDING_DEFINITIONS[kind].cost;
  const classCostMultiplier = getClassBuildCostMultiplier(state);
  return Math.max(1, Math.floor(baseCost * classCostMultiplier));
}

export function getBuildingCount(state: GameState, kind: BuildingKind): number {
  let count = 0;
  for (const building of state.buildings) {
    if (building.kind === kind) {
      count += 1;
    }
  }
  return count;
}

export function getSpellLabBonusCharges(state: GameState): number {
  return getBuildingCount(state, "spell_lab");
}

export function getSpellLabRechargeMultiplier(state: GameState): number {
  const labs = getBuildingCount(state, "spell_lab");
  return 1 + labs * 0.22;
}

export function getBaseDamageTakenMultiplier(state: GameState): number {
  const barracks = getBuildingCount(state, "barracks");
  return Math.max(0.5, 1 - barracks * 0.12);
}

export function tryPlaceBuilding(state: GameState, slotId: number, kind: BuildingKind): boolean {
  if (state.phase !== "prep") {
    pushLog(state, "Build during prep phase.");
    return false;
  }

  const slot = state.towerSlots.find((candidate) => candidate.id === slotId);
  if (!slot) {
    return false;
  }

  if (slot.towerId !== null || slot.buildingId !== null) {
    pushLog(state, "Slot already occupied.");
    return false;
  }

  const cost = buildingCost(state, kind);
  const buildingDef = BUILDING_DEFINITIONS[kind];

  if (state.gold < cost) {
    pushLog(state, `Not enough gold for ${buildingDef.label}.`);
    return false;
  }

  const building: BuildingState = {
    id: nextBuildingId(state),
    kind,
    slotId,
    level: 1,
    timer: 0,
  };

  state.gold -= cost;
  state.buildings.push(building);
  slot.buildingId = building.id;

  if (kind === "barracks") {
    state.maxBaseHealth += 2;
    state.baseHealth = Math.min(state.maxBaseHealth, state.baseHealth + 2);
  }

  pushLog(state, `Built ${buildingDef.label}.`);
  return true;
}

function tickGoldMine(state: GameState, building: BuildingState, dt: number): void {
  building.timer += dt;

  const payoutInterval = 6.6;
  while (building.timer >= payoutInterval) {
    const economyMultiplier = getEconomyMultiplier(state) * getClassEconomyMultiplier(state);
    const payout = Math.max(1, Math.floor((8 + state.stage * 2) * economyMultiplier));
    state.gold += payout;
    building.timer -= payoutInterval;
  }
}

function tickBarracks(state: GameState, building: BuildingState, dt: number): void {
  building.timer += dt;

  const healInterval = 9.5;
  while (building.timer >= healInterval) {
    const healAmount = 1 + Math.floor(building.level / 2);
    state.baseHealth = Math.min(state.maxBaseHealth, state.baseHealth + healAmount);
    building.timer -= healInterval;
  }
}

export function updateBuildings(state: GameState, dt: number): void {
  for (const building of state.buildings) {
    if (building.kind === "gold_mine") {
      tickGoldMine(state, building, dt);
      continue;
    }

    if (building.kind === "barracks") {
      tickBarracks(state, building, dt);
      continue;
    }

    building.timer += dt;
  }
}

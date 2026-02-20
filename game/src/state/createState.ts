// === Game State Factory & State Helpers ===

import {
  HERO_CLASS_DEFINITIONS,
  MAX_STAGE,
  SPELL_DEFINITIONS,
  STARTING_BASE_HEALTH,
  STARTING_GOLD,
  TOWER_SLOT_POSITIONS,
  WAVES_PER_STAGE,
} from "../core/config.js";
import type {
  GameState,
  PlayerCommand,
  ProgressionState,
  RoundStats,
  SpellBookState,
  SpellState,
  TowerSlot,
  UpgradeState,
} from "../core/types.js";

function createTowerSlots(): TowerSlot[] {
  return TOWER_SLOT_POSITIONS.map((position, id) => ({
    id,
    position,
    towerId: null,
    buildingId: null,
  }));
}

function createProgressionState(): ProgressionState {
  return {
    xp: 0,
    level: 1,
    skillPoints: 0,
    kills: 0,
  };
}

function createUpgradeState(): UpgradeState {
  return {
    damageLevel: 0,
    rangeLevel: 0,
    fireRateLevel: 0,
    economyLevel: 0,
  };
}

function createRoundStats(): RoundStats {
  return {
    leaked: 0,
    shotsFired: 0,
    shotsHit: 0,
    spellsCast: 0,
  };
}

function createSpellBook(): SpellBookState {
  const book = {} as SpellBookState;
  const classBonusCharges = HERO_CLASS_DEFINITIONS.warlord.bonusSpellCharges;

  for (const [kind, spell] of Object.entries(SPELL_DEFINITIONS)) {
    const maxCharges = spell.baseMaxCharges + classBonusCharges;
    const value: SpellState = {
      kind: kind as keyof SpellBookState,
      charges: maxCharges,
      maxCharges,
      cooldownRemaining: 0,
    };

    book[kind as keyof SpellBookState] = value;
  }

  return book;
}

export function createInitialState(): GameState {
  return {
    phase: "prep",
    stage: 1,
    wave: 1,
    maxStage: MAX_STAGE,
    wavesPerStage: WAVES_PER_STAGE,
    baseHealth: STARTING_BASE_HEALTH,
    maxBaseHealth: STARTING_BASE_HEALTH,
    gold: STARTING_GOLD,
    selectedTower: "cannon",
    selectedBuilding: "gold_mine",
    placementMode: "tower",
    heroClass: "warlord",
    classLocked: false,
    enemies: [],
    towers: [],
    buildings: [],
    towerSlots: createTowerSlots(),
    projectiles: [],
    spells: createSpellBook(),
    pendingSpawns: [],
    wavePackets: [],
    waveGoalText: "Prep: select a class, build, then press Start Wave.",
    progression: createProgressionState(),
    upgrades: createUpgradeState(),
    roundStats: createRoundStats(),
    commands: [],
    clockSeconds: 0,
    passiveIncomeTick: 0,
    logs: [
      "Welcome to Tower Forge Defense.",
      "Pick a class before your first wave.",
      "Press 1-4 for towers, 5-7 for buildings.",
      "Use Z/X/C to cast spells during combat.",
    ],
    nextEnemyId: 1,
    nextTowerId: 1,
    nextBuildingId: 1,
    nextProjectileId: 1,
  };
}

export function enqueueCommand(state: GameState, command: PlayerCommand): void {
  state.commands.push(command);
}

export function pushLog(state: GameState, message: string): void {
  state.logs.unshift(message);
  state.logs = state.logs.slice(0, 10);
}

export function nextEnemyId(state: GameState): number {
  const id = state.nextEnemyId;
  state.nextEnemyId += 1;
  return id;
}

export function nextTowerId(state: GameState): number {
  const id = state.nextTowerId;
  state.nextTowerId += 1;
  return id;
}

export function nextBuildingId(state: GameState): number {
  const id = state.nextBuildingId;
  state.nextBuildingId += 1;
  return id;
}

export function nextProjectileId(state: GameState): number {
  const id = state.nextProjectileId;
  state.nextProjectileId += 1;
  return id;
}

export function clearTransientWaveState(state: GameState): void {
  state.pendingSpawns = [];
  state.wavePackets = [];
}

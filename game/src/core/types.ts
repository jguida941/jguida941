// === Core Shared Types ===

export type GamePhase = "prep" | "combat" | "game_over" | "victory";

export type EnemyKind = "grunt" | "runner" | "tank" | "splitter" | "bomber" | "shaman";

export type TowerKind = "cannon" | "rapid" | "sniper" | "frost";

export type BuildingKind = "gold_mine" | "barracks" | "spell_lab";

export type UpgradeKind = "damage" | "range" | "fire_rate" | "economy";

export type SpellKind = "meteor" | "frost_nova" | "healing_aura";

export type HeroClass = "warlord" | "arcanist" | "architect";

export type PlacementMode = "tower" | "building";

export interface Vec2 {
  x: number;
  y: number;
}

export interface EnemyDefinition {
  kind: EnemyKind;
  label: string;
  maxHp: number;
  speed: number;
  reward: number;
  baseDamage: number;
  radius: number;
  color: string;
  abilityCooldown: number;
}

export interface WeaponProfile {
  projectileSpeed: number;
  baseDamage: number;
  cooldownSeconds: number;
  projectileRadius: number;
  pierce: number;
  splashRadius: number;
  slowFactor: number;
  slowDuration: number;
}

export interface TowerDefinition {
  kind: TowerKind;
  label: string;
  cost: number;
  range: number;
  color: string;
  weapon: WeaponProfile;
}

export interface BuildingDefinition {
  kind: BuildingKind;
  label: string;
  cost: number;
  color: string;
  description: string;
}

export interface SpellDefinition {
  kind: SpellKind;
  label: string;
  rechargeSeconds: number;
  baseMaxCharges: number;
  description: string;
}

export interface HeroClassDefinition {
  kind: HeroClass;
  label: string;
  description: string;
  damageMultiplier: number;
  rangeMultiplier: number;
  fireRateMultiplier: number;
  economyMultiplier: number;
  spellPowerMultiplier: number;
  buildCostMultiplier: number;
  bonusSpellCharges: number;
}

export interface TowerSlot {
  id: number;
  position: Vec2;
  towerId: number | null;
  buildingId: number | null;
}

export interface EnemyState {
  id: number;
  kind: EnemyKind;
  hp: number;
  maxHp: number;
  speed: number;
  reward: number;
  baseDamage: number;
  radius: number;
  color: string;
  pathProgress: number;
  slowFactor: number;
  slowTimer: number;
  splitGeneration: number;
  abilityTimer: number;
}

export interface TowerState {
  id: number;
  kind: TowerKind;
  slotId: number;
  cooldown: number;
  level: number;
}

export interface BuildingState {
  id: number;
  kind: BuildingKind;
  slotId: number;
  level: number;
  timer: number;
}

export interface ProjectileState {
  id: number;
  sourceTowerId: number;
  position: Vec2;
  velocity: Vec2;
  damage: number;
  radius: number;
  pierce: number;
  splashRadius: number;
  slowFactor: number;
  slowDuration: number;
  ttl: number;
}

export interface SpellState {
  kind: SpellKind;
  charges: number;
  maxCharges: number;
  cooldownRemaining: number;
}

export type SpellBookState = Record<SpellKind, SpellState>;

export interface WavePacket {
  kind: EnemyKind;
  count: number;
  cadence: number;
}

export interface PendingSpawn {
  kind: EnemyKind;
  remaining: number;
  cadence: number;
  timer: number;
}

export interface ProgressionState {
  xp: number;
  level: number;
  skillPoints: number;
  kills: number;
}

export interface UpgradeState {
  damageLevel: number;
  rangeLevel: number;
  fireRateLevel: number;
  economyLevel: number;
}

export interface RoundStats {
  leaked: number;
  shotsFired: number;
  shotsHit: number;
  spellsCast: number;
}

export type PlayerCommand =
  | { type: "start_wave" }
  | { type: "select_class"; heroClass: HeroClass }
  | { type: "select_tower"; tower: TowerKind }
  | { type: "select_building"; building: BuildingKind }
  | { type: "place_selected"; slotId: number }
  | { type: "cast_spell"; spell: SpellKind }
  | { type: "buy_upgrade"; upgrade: UpgradeKind };

export interface PathSegment {
  start: Vec2;
  end: Vec2;
  length: number;
  cumulativeLength: number;
}

export interface PathModel {
  waypoints: Vec2[];
  segments: PathSegment[];
  length: number;
}

export interface GameState {
  phase: GamePhase;
  stage: number;
  wave: number;
  maxStage: number;
  wavesPerStage: number;
  baseHealth: number;
  maxBaseHealth: number;
  gold: number;
  selectedTower: TowerKind;
  selectedBuilding: BuildingKind;
  placementMode: PlacementMode;
  heroClass: HeroClass;
  classLocked: boolean;
  enemies: EnemyState[];
  towers: TowerState[];
  buildings: BuildingState[];
  towerSlots: TowerSlot[];
  projectiles: ProjectileState[];
  spells: SpellBookState;
  pendingSpawns: PendingSpawn[];
  wavePackets: WavePacket[];
  waveGoalText: string;
  progression: ProgressionState;
  upgrades: UpgradeState;
  roundStats: RoundStats;
  commands: PlayerCommand[];
  clockSeconds: number;
  passiveIncomeTick: number;
  logs: string[];
  nextEnemyId: number;
  nextTowerId: number;
  nextBuildingId: number;
  nextProjectileId: number;
}

// === Spell System ===

import { SPELL_DEFINITIONS, SPELL_ORDER } from "../core/config.js";
import { getClassBonusSpellCharges, getClassSpellPowerMultiplier } from "./classes.js";
import { getSpellLabBonusCharges, getSpellLabRechargeMultiplier } from "./buildings.js";
import { samplePathPosition } from "./pathing.js";
import { applyHitToEnemy } from "./enemies.js";
import { distanceSquared } from "../core/math.js";
import { pushLog } from "../state/createState.js";
import type { EnemyState, GameState, PathModel, SpellKind, SpellState, Vec2 } from "../core/types.js";

function ensureSpellState(state: GameState, kind: SpellKind): SpellState {
  return state.spells[kind];
}

export function recomputeSpellCapacities(state: GameState): void {
  const classCharges = getClassBonusSpellCharges(state);
  const buildingCharges = getSpellLabBonusCharges(state);

  for (const spellKind of SPELL_ORDER) {
    const spell = ensureSpellState(state, spellKind);
    const previousMax = spell.maxCharges;
    const baseMax = SPELL_DEFINITIONS[spellKind].baseMaxCharges;
    const maxCharges = Math.max(1, baseMax + classCharges + buildingCharges);

    spell.maxCharges = maxCharges;

    if (maxCharges > previousMax) {
      spell.charges = Math.min(maxCharges, spell.charges + (maxCharges - previousMax));
    } else {
      spell.charges = Math.min(maxCharges, spell.charges);
    }

    if (spell.charges >= spell.maxCharges) {
      spell.cooldownRemaining = 0;
    }
  }
}

function pickLeadEnemy(state: GameState): EnemyState | null {
  let target: EnemyState | null = null;

  for (const enemy of state.enemies) {
    if (!target || enemy.pathProgress > target.pathProgress) {
      target = enemy;
    }
  }

  return target;
}

function castMeteor(state: GameState, path: PathModel): boolean {
  const lead = pickLeadEnemy(state);
  if (!lead) {
    pushLog(state, "No target for Meteor.");
    return false;
  }

  const center = samplePathPosition(path, lead.pathProgress);
  const radius = 124;
  const radiusSq = radius * radius;
  const spellPower = getClassSpellPowerMultiplier(state);
  const directDamage = 102 * spellPower;

  let hits = 0;
  for (const enemy of [...state.enemies]) {
    const position = samplePathPosition(path, enemy.pathProgress);
    if (distanceSquared(position, center) > radiusSq) {
      continue;
    }

    const killed = applyHitToEnemy(state, enemy.id, {
      damage: directDamage,
      slowFactor: 1,
      slowDuration: 0,
    });

    hits += killed ? 1 : 0;
  }

  pushLog(state, `Meteor cast. Impact zone hit ${Math.max(1, hits)} targets.`);
  return true;
}

function castFrostNova(state: GameState): boolean {
  if (state.enemies.length === 0) {
    pushLog(state, "No enemies for Frost Nova.");
    return false;
  }

  const spellPower = getClassSpellPowerMultiplier(state);
  const novaDamage = 24 * spellPower;

  for (const enemy of [...state.enemies]) {
    applyHitToEnemy(state, enemy.id, {
      damage: novaDamage,
      slowFactor: 0.44,
      slowDuration: 2.7,
    });
  }

  pushLog(state, `Frost Nova cast on ${state.enemies.length} enemies.`);
  return true;
}

function castHealingAura(state: GameState): boolean {
  const spellPower = getClassSpellPowerMultiplier(state);
  const heal = Math.max(1, Math.floor((6 + state.stage) * spellPower));

  if (state.baseHealth >= state.maxBaseHealth) {
    pushLog(state, "Base already at full health.");
    return false;
  }

  state.baseHealth = Math.min(state.maxBaseHealth, state.baseHealth + heal);
  pushLog(state, `Healing Aura restored ${heal} base HP.`);
  return true;
}

function spendSpellCharge(state: GameState, spell: SpellState): void {
  spell.charges = Math.max(0, spell.charges - 1);

  if (spell.charges < spell.maxCharges && spell.cooldownRemaining <= 0) {
    spell.cooldownRemaining = SPELL_DEFINITIONS[spell.kind].rechargeSeconds;
  }
}

export function tryCastSpell(state: GameState, path: PathModel, spellKind: SpellKind): boolean {
  if (state.phase !== "combat") {
    pushLog(state, "Spells can only be cast during combat.");
    return false;
  }

  const spell = ensureSpellState(state, spellKind);
  if (spell.charges <= 0) {
    pushLog(state, `${SPELL_DEFINITIONS[spellKind].label} has no charges.`);
    return false;
  }

  let castSucceeded = false;
  if (spellKind === "meteor") {
    castSucceeded = castMeteor(state, path);
  } else if (spellKind === "frost_nova") {
    castSucceeded = castFrostNova(state);
  } else {
    castSucceeded = castHealingAura(state);
  }

  if (!castSucceeded) {
    return false;
  }

  spendSpellCharge(state, spell);
  state.roundStats.spellsCast += 1;
  return true;
}

function advanceSingleSpellCooldown(spell: SpellState, dt: number, rechargeMultiplier: number): void {
  if (spell.charges >= spell.maxCharges) {
    spell.cooldownRemaining = 0;
    return;
  }

  spell.cooldownRemaining -= dt * rechargeMultiplier;

  const recharge = SPELL_DEFINITIONS[spell.kind].rechargeSeconds;
  while (spell.cooldownRemaining <= 0 && spell.charges < spell.maxCharges) {
    spell.charges += 1;

    if (spell.charges >= spell.maxCharges) {
      spell.cooldownRemaining = 0;
      break;
    }

    spell.cooldownRemaining += recharge;
  }
}

export function updateSpells(state: GameState, dt: number): void {
  const rechargeMultiplier = getSpellLabRechargeMultiplier(state);

  for (const spellKind of SPELL_ORDER) {
    advanceSingleSpellCooldown(state.spells[spellKind], dt, rechargeMultiplier);
  }
}

export function getSpellChargeLabel(state: GameState, spellKind: SpellKind): string {
  const spell = state.spells[spellKind];
  const cooldown = spell.cooldownRemaining > 0 ? ` (${spell.cooldownRemaining.toFixed(1)}s)` : "";
  return `${spell.charges}/${spell.maxCharges}${cooldown}`;
}

export function getLeadEnemyPosition(state: GameState, path: PathModel): Vec2 | null {
  const lead = pickLeadEnemy(state);
  if (!lead) {
    return null;
  }

  return samplePathPosition(path, lead.pathProgress);
}

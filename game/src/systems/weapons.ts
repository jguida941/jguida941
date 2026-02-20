// === Weapon Logic (Projectile Creation) ===

import { normalize, subtract } from "../core/math.js";
import { TOWER_DEFINITIONS } from "../core/config.js";
import { nextProjectileId } from "../state/createState.js";
import type { GameState, ProjectileState, TowerState, Vec2 } from "../core/types.js";

export interface WeaponModifiers {
  damageMultiplier: number;
  fireRateMultiplier: number;
}

export function cooldownForTower(tower: TowerState, fireRateMultiplier: number): number {
  const baseCooldown = TOWER_DEFINITIONS[tower.kind].weapon.cooldownSeconds;
  return baseCooldown / fireRateMultiplier;
}

export function buildProjectileFromTower(
  state: GameState,
  tower: TowerState,
  origin: Vec2,
  target: Vec2,
  modifiers: WeaponModifiers,
): ProjectileState {
  const towerDef = TOWER_DEFINITIONS[tower.kind];
  const weapon = towerDef.weapon;
  const direction = normalize(subtract(target, origin));

  return {
    id: nextProjectileId(state),
    sourceTowerId: tower.id,
    position: { x: origin.x, y: origin.y },
    velocity: {
      x: direction.x * weapon.projectileSpeed,
      y: direction.y * weapon.projectileSpeed,
    },
    damage: weapon.baseDamage * modifiers.damageMultiplier,
    radius: weapon.projectileRadius,
    pierce: weapon.pierce,
    splashRadius: weapon.splashRadius,
    slowFactor: weapon.slowFactor,
    slowDuration: weapon.slowDuration,
    ttl: 4.5,
  };
}

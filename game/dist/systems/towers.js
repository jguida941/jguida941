// === Tower System (Placement / Targeting / Firing) ===
import { TOWER_DEFINITIONS } from "../core/config.js";
import { distanceSquared } from "../core/math.js";
import { samplePathPosition } from "./pathing.js";
import { buildProjectileFromTower, cooldownForTower } from "./weapons.js";
import { getClassBuildCostMultiplier, getClassDamageMultiplier, getClassFireRateMultiplier, getClassRangeMultiplier, } from "./classes.js";
import { getDamageMultiplier, getFireRateMultiplier, getRangeMultiplier } from "./upgrades.js";
import { nextTowerId, pushLog } from "../state/createState.js";
function towerPositionFromSlot(state, tower) {
    const slot = state.towerSlots.find((candidate) => candidate.id === tower.slotId);
    return slot?.position ?? { x: 0, y: 0 };
}
function pickTarget(state, path, origin, range) {
    const rangeSq = range * range;
    let bestEnemy = null;
    for (const enemy of state.enemies) {
        const enemyPos = samplePathPosition(path, enemy.pathProgress);
        const distSq = distanceSquared(origin, enemyPos);
        if (distSq > rangeSq) {
            continue;
        }
        if (!bestEnemy || enemy.pathProgress > bestEnemy.pathProgress) {
            bestEnemy = enemy;
        }
    }
    return bestEnemy;
}
function buildCost(state, kind) {
    const baseCost = TOWER_DEFINITIONS[kind].cost;
    const classCostMultiplier = getClassBuildCostMultiplier(state);
    return Math.max(1, Math.floor(baseCost * classCostMultiplier));
}
export function tryPlaceTower(state, slotId, kind) {
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
    const towerDef = TOWER_DEFINITIONS[kind];
    const cost = buildCost(state, kind);
    if (state.gold < cost) {
        pushLog(state, `Not enough gold for ${towerDef.label}.`);
        return false;
    }
    const tower = {
        id: nextTowerId(state),
        kind,
        slotId,
        cooldown: 0,
        level: 1,
    };
    state.gold -= cost;
    state.towers.push(tower);
    slot.towerId = tower.id;
    pushLog(state, `Built ${towerDef.label} tower.`);
    return true;
}
export function updateTowers(state, path, dt) {
    const damageMultiplier = getDamageMultiplier(state) * getClassDamageMultiplier(state);
    const fireRateMultiplier = getFireRateMultiplier(state) * getClassFireRateMultiplier(state);
    const rangeMultiplier = getRangeMultiplier(state) * getClassRangeMultiplier(state);
    for (const tower of state.towers) {
        const towerDef = TOWER_DEFINITIONS[tower.kind];
        const origin = towerPositionFromSlot(state, tower);
        tower.cooldown -= dt;
        if (tower.cooldown > 0) {
            continue;
        }
        const range = towerDef.range * rangeMultiplier;
        const target = pickTarget(state, path, origin, range);
        if (!target) {
            continue;
        }
        const targetPosition = samplePathPosition(path, target.pathProgress);
        const projectile = buildProjectileFromTower(state, tower, origin, targetPosition, {
            damageMultiplier,
            fireRateMultiplier,
        });
        state.projectiles.push(projectile);
        state.roundStats.shotsFired += 1;
        tower.cooldown = cooldownForTower(tower, fireRateMultiplier);
    }
}

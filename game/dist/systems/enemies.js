// === Enemy System (Spawn / Move / Damage / Death) ===
import { ENEMY_DEFINITIONS } from "../core/config.js";
import { getBaseDamageTakenMultiplier } from "./buildings.js";
import { getClassEconomyMultiplier } from "./classes.js";
import { getEconomyMultiplier } from "./upgrades.js";
import { awardKillProgress } from "./progression.js";
import { pushLog, nextEnemyId } from "../state/createState.js";
function createEnemy(state, kind, pathProgress, splitGeneration) {
    const base = ENEMY_DEFINITIONS[kind];
    const hpScale = 1 + (state.stage - 1) * 0.22 + (state.wave - 1) * 0.08;
    const speedScale = 1 + (state.stage - 1) * 0.05 + (state.wave - 1) * 0.02;
    const hp = Math.floor(base.maxHp * hpScale * (splitGeneration > 0 ? 0.65 : 1));
    const speed = base.speed * speedScale * (splitGeneration > 0 ? 1.08 : 1);
    return {
        id: nextEnemyId(state),
        kind,
        hp,
        maxHp: hp,
        speed,
        reward: Math.max(1, Math.floor(base.reward * (splitGeneration > 0 ? 0.5 : 1))),
        baseDamage: base.baseDamage,
        radius: base.radius * (splitGeneration > 0 ? 0.78 : 1),
        color: base.color,
        pathProgress,
        slowFactor: 1,
        slowTimer: 0,
        splitGeneration,
        abilityTimer: base.abilityCooldown,
    };
}
export function spawnEnemy(state, kind, pathProgress = 0, splitGeneration = 0) {
    state.enemies.push(createEnemy(state, kind, pathProgress, splitGeneration));
}
function onEnemyLeaked(state, enemy, rawDamage = enemy.baseDamage) {
    const incoming = Math.max(1, rawDamage);
    const multiplier = getBaseDamageTakenMultiplier(state);
    const appliedDamage = Math.max(1, Math.floor(incoming * multiplier));
    state.baseHealth -= appliedDamage;
    state.roundStats.leaked += appliedDamage;
    if (state.baseHealth <= 0) {
        state.baseHealth = 0;
        state.phase = "game_over";
        pushLog(state, "Base destroyed. Run failed.");
    }
}
function onEnemyKilled(state, enemy) {
    const economyMultiplier = getEconomyMultiplier(state) * getClassEconomyMultiplier(state);
    const goldGain = Math.floor(enemy.reward * economyMultiplier);
    state.gold += goldGain;
    awardKillProgress(state, enemy.reward);
    if (enemy.kind === "splitter" && enemy.splitGeneration < 1) {
        spawnEnemy(state, "runner", enemy.pathProgress, enemy.splitGeneration + 1);
        spawnEnemy(state, "runner", enemy.pathProgress, enemy.splitGeneration + 1);
    }
}
function pulseShamanAura(state, caster) {
    const healAmount = 7 + state.stage * 2;
    for (const enemy of state.enemies) {
        if (enemy.id === caster.id) {
            continue;
        }
        const distanceByPath = Math.abs(enemy.pathProgress - caster.pathProgress);
        if (distanceByPath > 0.09) {
            continue;
        }
        enemy.hp = Math.min(enemy.maxHp, enemy.hp + healAmount);
        enemy.slowFactor = Math.min(1, enemy.slowFactor + 0.2);
        enemy.slowTimer = Math.max(0, enemy.slowTimer - 0.85);
    }
}
function tickEnemyAbility(state, enemy, dt) {
    if (enemy.abilityTimer <= 0) {
        return;
    }
    enemy.abilityTimer -= dt;
    if (enemy.abilityTimer > 0) {
        return;
    }
    if (enemy.kind === "shaman") {
        pulseShamanAura(state, enemy);
    }
    const cooldown = ENEMY_DEFINITIONS[enemy.kind].abilityCooldown;
    if (cooldown > 0) {
        enemy.abilityTimer += cooldown;
    }
}
export function applyHitToEnemy(state, enemyId, hit) {
    const enemy = state.enemies.find((e) => e.id === enemyId);
    if (!enemy) {
        return false;
    }
    enemy.hp -= hit.damage;
    if (hit.slowFactor < 1) {
        enemy.slowFactor = Math.min(enemy.slowFactor, hit.slowFactor);
        enemy.slowTimer = Math.max(enemy.slowTimer, hit.slowDuration);
    }
    if (enemy.hp > 0) {
        return false;
    }
    state.enemies = state.enemies.filter((e) => e.id !== enemy.id);
    onEnemyKilled(state, enemy);
    return true;
}
export function updateEnemies(state, path, dt) {
    const survivors = [];
    for (const enemy of state.enemies) {
        if (enemy.slowTimer > 0) {
            enemy.slowTimer -= dt;
            if (enemy.slowTimer <= 0) {
                enemy.slowFactor = 1;
            }
        }
        tickEnemyAbility(state, enemy, dt);
        const speed = enemy.speed * enemy.slowFactor;
        enemy.pathProgress += (speed * dt) / path.length;
        if (enemy.kind === "bomber" && enemy.pathProgress >= 0.92) {
            onEnemyLeaked(state, enemy, enemy.baseDamage + 2);
            continue;
        }
        if (enemy.pathProgress >= 1) {
            onEnemyLeaked(state, enemy);
            continue;
        }
        survivors.push(enemy);
    }
    state.enemies = survivors;
}

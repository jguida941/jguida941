// === Projectile System (Travel / Collision / Damage Application) ===
import { distanceSquared } from "../core/math.js";
import { samplePathPosition } from "./pathing.js";
import { applyHitToEnemy } from "./enemies.js";
function moveProjectile(projectile, dt) {
    projectile.position.x += projectile.velocity.x * dt;
    projectile.position.y += projectile.velocity.y * dt;
    projectile.ttl -= dt;
}
function firstCollision(state, path, projectile) {
    for (const enemy of state.enemies) {
        const enemyPosition = samplePathPosition(path, enemy.pathProgress);
        const hitDistance = enemy.radius + projectile.radius;
        const hitDistanceSq = hitDistance * hitDistance;
        if (distanceSquared(projectile.position, enemyPosition) <= hitDistanceSq) {
            return { enemy, enemyPosition };
        }
    }
    return null;
}
function applySplash(state, path, center, projectile, ignoreEnemyId) {
    if (projectile.splashRadius <= 0) {
        return;
    }
    const splashDamage = projectile.damage * 0.55;
    const splashRadiusSq = projectile.splashRadius * projectile.splashRadius;
    for (const enemy of [...state.enemies]) {
        if (enemy.id === ignoreEnemyId) {
            continue;
        }
        const enemyPos = samplePathPosition(path, enemy.pathProgress);
        if (distanceSquared(enemyPos, center) > splashRadiusSq) {
            continue;
        }
        applyHitToEnemy(state, enemy.id, {
            damage: splashDamage,
            slowFactor: projectile.slowFactor,
            slowDuration: projectile.slowDuration,
        });
    }
}
export function updateProjectiles(state, path, dt) {
    const survivors = [];
    for (const projectile of state.projectiles) {
        moveProjectile(projectile, dt);
        if (projectile.ttl <= 0) {
            continue;
        }
        const collision = firstCollision(state, path, projectile);
        if (!collision) {
            survivors.push(projectile);
            continue;
        }
        const { enemy, enemyPosition } = collision;
        applyHitToEnemy(state, enemy.id, {
            damage: projectile.damage,
            slowFactor: projectile.slowFactor,
            slowDuration: projectile.slowDuration,
        });
        applySplash(state, path, enemyPosition, projectile, enemy.id);
        state.roundStats.shotsHit += 1;
        projectile.pierce -= 1;
        if (projectile.pierce > 0) {
            survivors.push(projectile);
        }
    }
    state.projectiles = survivors;
}

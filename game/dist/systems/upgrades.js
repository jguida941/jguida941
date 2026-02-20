// === Upgrade Math & Upgrade Purchases ===
import { pushLog } from "../state/createState.js";
const MAX_UPGRADE_LEVEL = 12;
export function getDamageMultiplier(state) {
    return 1 + state.upgrades.damageLevel * 0.1;
}
export function getRangeMultiplier(state) {
    return 1 + state.upgrades.rangeLevel * 0.06;
}
export function getFireRateMultiplier(state) {
    return 1 + state.upgrades.fireRateLevel * 0.08;
}
export function getEconomyMultiplier(state) {
    return 1 + state.upgrades.economyLevel * 0.08;
}
function currentLevel(state, upgrade) {
    if (upgrade === "damage") {
        return state.upgrades.damageLevel;
    }
    if (upgrade === "range") {
        return state.upgrades.rangeLevel;
    }
    if (upgrade === "fire_rate") {
        return state.upgrades.fireRateLevel;
    }
    return state.upgrades.economyLevel;
}
function incrementLevel(state, upgrade) {
    if (upgrade === "damage") {
        state.upgrades.damageLevel += 1;
        return;
    }
    if (upgrade === "range") {
        state.upgrades.rangeLevel += 1;
        return;
    }
    if (upgrade === "fire_rate") {
        state.upgrades.fireRateLevel += 1;
        return;
    }
    state.upgrades.economyLevel += 1;
}
export function tryBuyUpgrade(state, upgrade) {
    if (state.progression.skillPoints <= 0) {
        pushLog(state, "No skill points available.");
        return false;
    }
    const level = currentLevel(state, upgrade);
    if (level >= MAX_UPGRADE_LEVEL) {
        pushLog(state, `${upgrade} already maxed.`);
        return false;
    }
    state.progression.skillPoints -= 1;
    incrementLevel(state, upgrade);
    pushLog(state, `Upgrade applied: ${upgrade}.`);
    return true;
}

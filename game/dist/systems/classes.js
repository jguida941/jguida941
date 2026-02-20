// === Hero Class System ===
import { HERO_CLASS_DEFINITIONS } from "../core/config.js";
import { pushLog } from "../state/createState.js";
export function getHeroClassDefinition(heroClass) {
    return HERO_CLASS_DEFINITIONS[heroClass];
}
export function getActiveClassDefinition(state) {
    return HERO_CLASS_DEFINITIONS[state.heroClass];
}
export function trySelectHeroClass(state, heroClass) {
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
export function lockClassSelection(state) {
    if (state.classLocked) {
        return;
    }
    state.classLocked = true;
    pushLog(state, "Class locked for this run.");
}
export function getClassDamageMultiplier(state) {
    return getActiveClassDefinition(state).damageMultiplier;
}
export function getClassRangeMultiplier(state) {
    return getActiveClassDefinition(state).rangeMultiplier;
}
export function getClassFireRateMultiplier(state) {
    return getActiveClassDefinition(state).fireRateMultiplier;
}
export function getClassEconomyMultiplier(state) {
    return getActiveClassDefinition(state).economyMultiplier;
}
export function getClassSpellPowerMultiplier(state) {
    return getActiveClassDefinition(state).spellPowerMultiplier;
}
export function getClassBuildCostMultiplier(state) {
    return getActiveClassDefinition(state).buildCostMultiplier;
}
export function getClassBonusSpellCharges(state) {
    return getActiveClassDefinition(state).bonusSpellCharges;
}

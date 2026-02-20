// === Main Runtime Orchestration ===
import { BUILDING_DEFINITIONS, BUILDING_ORDER, CANVAS, HERO_CLASS_DEFINITIONS, HERO_CLASS_ORDER, SPELL_DEFINITIONS, SPELL_ORDER, TOWER_DEFINITIONS, TOWER_ORDER, UPGRADE_ORDER, } from "./core/config.js";
import { createInitialState, enqueueCommand, pushLog } from "./state/createState.js";
import { createPathModel } from "./systems/pathing.js";
import { startWave, updateWaveSpawning, resolveWaveState } from "./systems/waves.js";
import { updateEnemies } from "./systems/enemies.js";
import { updateTowers, tryPlaceTower } from "./systems/towers.js";
import { updateProjectiles } from "./systems/projectiles.js";
import { updateEconomy } from "./systems/economy.js";
import { tryBuyUpgrade } from "./systems/upgrades.js";
import { trySelectHeroClass } from "./systems/classes.js";
import { tryPlaceBuilding, updateBuildings } from "./systems/buildings.js";
import { recomputeSpellCapacities, tryCastSpell, updateSpells } from "./systems/spells.js";
import { renderCanvas } from "./render/canvasRenderer.js";
import { renderHud } from "./render/hudRenderer.js";
import { bindInput } from "./input/controller.js";
function mustGet(id) {
    const node = document.getElementById(id);
    if (!node) {
        throw new Error(`Missing required element: #${id}`);
    }
    return node;
}
function createClassButtons(container) {
    const map = {};
    const hotkeys = {
        warlord: "A",
        arcanist: "S",
        architect: "D",
    };
    for (const heroClass of HERO_CLASS_ORDER) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "action-btn";
        button.textContent = `${HERO_CLASS_DEFINITIONS[heroClass].label} [${hotkeys[heroClass]}]`;
        button.dataset.heroClass = heroClass;
        container.appendChild(button);
        map[heroClass] = button;
    }
    return map;
}
function createTowerButtons(container) {
    const map = {};
    for (const towerKind of TOWER_ORDER) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "action-btn";
        button.textContent = `${TOWER_DEFINITIONS[towerKind].label} [${TOWER_ORDER.indexOf(towerKind) + 1}]`;
        button.dataset.tower = towerKind;
        container.appendChild(button);
        map[towerKind] = button;
    }
    return map;
}
function createBuildingButtons(container) {
    const map = {};
    for (const buildingKind of BUILDING_ORDER) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "action-btn";
        button.textContent = `${BUILDING_DEFINITIONS[buildingKind].label} [${BUILDING_ORDER.indexOf(buildingKind) + 5}]`;
        button.dataset.building = buildingKind;
        container.appendChild(button);
        map[buildingKind] = button;
    }
    return map;
}
function createSpellButtons(container) {
    const map = {};
    const hotkeys = {
        meteor: "Z",
        frost_nova: "X",
        healing_aura: "C",
    };
    for (const spellKind of SPELL_ORDER) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "action-btn";
        button.textContent = `${SPELL_DEFINITIONS[spellKind].label} [${hotkeys[spellKind]}]`;
        button.dataset.spell = spellKind;
        container.appendChild(button);
        map[spellKind] = button;
    }
    return map;
}
function createUpgradeButtons(container) {
    const map = {};
    const labels = {
        damage: "Damage",
        range: "Range",
        fire_rate: "Fire Rate",
        economy: "Economy",
    };
    const hotkeys = {
        damage: "Q",
        range: "W",
        fire_rate: "E",
        economy: "R",
    };
    for (const upgradeKind of UPGRADE_ORDER) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "action-btn";
        button.textContent = `${labels[upgradeKind]} [${hotkeys[upgradeKind]}]`;
        button.dataset.upgrade = upgradeKind;
        container.appendChild(button);
        map[upgradeKind] = button;
    }
    return map;
}
function collectUi() {
    const canvas = mustGet("gameCanvas");
    canvas.width = CANVAS.width;
    canvas.height = CANVAS.height;
    const classButtons = createClassButtons(mustGet("classButtons"));
    const towerButtons = createTowerButtons(mustGet("towerButtons"));
    const buildingButtons = createBuildingButtons(mustGet("buildingButtons"));
    const spellButtons = createSpellButtons(mustGet("spellButtons"));
    const upgradeButtons = createUpgradeButtons(mustGet("upgradeButtons"));
    return {
        canvas,
        startWaveButton: mustGet("startWaveBtn"),
        classButtons,
        towerButtons,
        buildingButtons,
        spellButtons,
        upgradeButtons,
        phaseValue: mustGet("phaseValue"),
        stageValue: mustGet("stageValue"),
        waveValue: mustGet("waveValue"),
        waveGoalValue: mustGet("waveGoalValue"),
        healthValue: mustGet("healthValue"),
        goldValue: mustGet("goldValue"),
        levelValue: mustGet("levelValue"),
        xpValue: mustGet("xpValue"),
        skillPointsValue: mustGet("skillPointsValue"),
        classValue: mustGet("classValue"),
        placementModeValue: mustGet("placementModeValue"),
        selectedTowerValue: mustGet("selectedTowerValue"),
        selectedBuildingValue: mustGet("selectedBuildingValue"),
        spellChargesValue: mustGet("spellChargesValue"),
        combatStatsValue: mustGet("combatStatsValue"),
        logList: mustGet("logList"),
    };
}
function processCommands(state, path) {
    while (state.commands.length > 0) {
        const command = state.commands.shift();
        if (!command) {
            continue;
        }
        if (command.type === "start_wave") {
            startWave(state);
            continue;
        }
        if (command.type === "select_class") {
            const changed = trySelectHeroClass(state, command.heroClass);
            if (changed) {
                recomputeSpellCapacities(state);
            }
            continue;
        }
        if (command.type === "select_tower") {
            state.selectedTower = command.tower;
            state.placementMode = "tower";
            pushLog(state, `Selected ${TOWER_DEFINITIONS[command.tower].label}.`);
            continue;
        }
        if (command.type === "select_building") {
            state.selectedBuilding = command.building;
            state.placementMode = "building";
            pushLog(state, `Selected ${BUILDING_DEFINITIONS[command.building].label}.`);
            continue;
        }
        if (command.type === "place_selected") {
            if (state.placementMode === "tower") {
                tryPlaceTower(state, command.slotId, state.selectedTower);
            }
            else {
                const built = tryPlaceBuilding(state, command.slotId, state.selectedBuilding);
                if (built) {
                    recomputeSpellCapacities(state);
                }
            }
            continue;
        }
        if (command.type === "cast_spell") {
            tryCastSpell(state, path, command.spell);
            continue;
        }
        if (command.type === "buy_upgrade") {
            tryBuyUpgrade(state, command.upgrade);
        }
    }
}
function updateActionButtonStates(state, ui) {
    for (const [heroClass, button] of Object.entries(ui.classButtons)) {
        button.classList.toggle("active", heroClass === state.heroClass);
        button.disabled = state.classLocked;
    }
    for (const [towerKind, button] of Object.entries(ui.towerButtons)) {
        button.classList.toggle("active", state.placementMode === "tower" && towerKind === state.selectedTower);
        button.disabled = state.phase !== "prep";
    }
    for (const [buildingKind, button] of Object.entries(ui.buildingButtons)) {
        button.classList.toggle("active", state.placementMode === "building" && buildingKind === state.selectedBuilding);
        button.disabled = state.phase !== "prep";
    }
    const spellHotkeys = {
        meteor: "Z",
        frost_nova: "X",
        healing_aura: "C",
    };
    for (const [spellKind, button] of Object.entries(ui.spellButtons)) {
        const spellState = state.spells[spellKind];
        button.textContent = `${SPELL_DEFINITIONS[spellKind].label} [${spellHotkeys[spellKind]}] ${spellState.charges}/${spellState.maxCharges}`;
        button.disabled = state.phase !== "combat" || spellState.charges <= 0;
    }
    const upgradeDisabled = state.progression.skillPoints <= 0;
    for (const button of Object.values(ui.upgradeButtons)) {
        button.disabled = upgradeDisabled;
    }
    ui.startWaveButton.disabled = state.phase !== "prep";
}
export function bootTowerDefense() {
    const ui = collectUi();
    const path = createPathModel();
    const state = createInitialState();
    const ctx = ui.canvas.getContext("2d");
    if (!ctx) {
        throw new Error("Unable to initialize 2D context.");
    }
    const inputBindings = {
        canvas: ui.canvas,
        startWaveButton: ui.startWaveButton,
        classButtons: ui.classButtons,
        towerButtons: ui.towerButtons,
        buildingButtons: ui.buildingButtons,
        spellButtons: ui.spellButtons,
        upgradeButtons: ui.upgradeButtons,
    };
    bindInput(inputBindings, (command) => enqueueCommand(state, command), () => state.towerSlots);
    recomputeSpellCapacities(state);
    let lastTs = performance.now();
    const frame = (now) => {
        const dt = Math.min(0.05, (now - lastTs) / 1000);
        lastTs = now;
        state.clockSeconds += dt;
        processCommands(state, path);
        if (state.phase === "combat") {
            updateWaveSpawning(state, dt);
            updateEnemies(state, path, dt);
            updateTowers(state, path, dt);
            updateProjectiles(state, path, dt);
            resolveWaveState(state);
        }
        if (state.phase !== "game_over" && state.phase !== "victory") {
            updateBuildings(state, dt);
            updateEconomy(state);
            updateSpells(state, dt);
        }
        updateActionButtonStates(state, ui);
        renderCanvas(ctx, state, path);
        renderHud(state, ui);
        requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
}

// === Main Runtime Orchestration ===

import {
  BUILDING_DEFINITIONS,
  BUILDING_ORDER,
  CANVAS,
  HERO_CLASS_DEFINITIONS,
  HERO_CLASS_ORDER,
  SPELL_DEFINITIONS,
  SPELL_ORDER,
  TOWER_DEFINITIONS,
  TOWER_ORDER,
  UPGRADE_ORDER,
} from "./core/config.js";
import type {
  BuildingKind,
  HeroClass,
  SpellKind,
  TowerKind,
  UpgradeKind,
} from "./core/types.js";
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
import { renderHud, type HudRefs } from "./render/hudRenderer.js";
import { bindInput, type InputBindings } from "./input/controller.js";

interface RuntimeUi extends HudRefs {
  canvas: HTMLCanvasElement;
  startWaveButton: HTMLButtonElement;
  classButtons: Record<HeroClass, HTMLButtonElement>;
  towerButtons: Record<TowerKind, HTMLButtonElement>;
  buildingButtons: Record<BuildingKind, HTMLButtonElement>;
  spellButtons: Record<SpellKind, HTMLButtonElement>;
  upgradeButtons: Record<UpgradeKind, HTMLButtonElement>;
}

function mustGet<T extends HTMLElement>(id: string): T {
  const node = document.getElementById(id);
  if (!node) {
    throw new Error(`Missing required element: #${id}`);
  }
  return node as T;
}

function createClassButtons(container: HTMLElement): Record<HeroClass, HTMLButtonElement> {
  const map = {} as Record<HeroClass, HTMLButtonElement>;
  const hotkeys: Record<HeroClass, string> = {
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

function createTowerButtons(container: HTMLElement): Record<TowerKind, HTMLButtonElement> {
  const map = {} as Record<TowerKind, HTMLButtonElement>;

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

function createBuildingButtons(container: HTMLElement): Record<BuildingKind, HTMLButtonElement> {
  const map = {} as Record<BuildingKind, HTMLButtonElement>;

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

function createSpellButtons(container: HTMLElement): Record<SpellKind, HTMLButtonElement> {
  const map = {} as Record<SpellKind, HTMLButtonElement>;
  const hotkeys: Record<SpellKind, string> = {
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

function createUpgradeButtons(container: HTMLElement): Record<UpgradeKind, HTMLButtonElement> {
  const map = {} as Record<UpgradeKind, HTMLButtonElement>;
  const labels: Record<UpgradeKind, string> = {
    damage: "Damage",
    range: "Range",
    fire_rate: "Fire Rate",
    economy: "Economy",
  };
  const hotkeys: Record<UpgradeKind, string> = {
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

function collectUi(): RuntimeUi {
  const canvas = mustGet<HTMLCanvasElement>("gameCanvas");
  canvas.width = CANVAS.width;
  canvas.height = CANVAS.height;

  const classButtons = createClassButtons(mustGet<HTMLElement>("classButtons"));
  const towerButtons = createTowerButtons(mustGet<HTMLElement>("towerButtons"));
  const buildingButtons = createBuildingButtons(mustGet<HTMLElement>("buildingButtons"));
  const spellButtons = createSpellButtons(mustGet<HTMLElement>("spellButtons"));
  const upgradeButtons = createUpgradeButtons(mustGet<HTMLElement>("upgradeButtons"));

  return {
    canvas,
    startWaveButton: mustGet<HTMLButtonElement>("startWaveBtn"),
    classButtons,
    towerButtons,
    buildingButtons,
    spellButtons,
    upgradeButtons,
    phaseValue: mustGet<HTMLElement>("phaseValue"),
    stageValue: mustGet<HTMLElement>("stageValue"),
    waveValue: mustGet<HTMLElement>("waveValue"),
    waveGoalValue: mustGet<HTMLElement>("waveGoalValue"),
    healthValue: mustGet<HTMLElement>("healthValue"),
    goldValue: mustGet<HTMLElement>("goldValue"),
    levelValue: mustGet<HTMLElement>("levelValue"),
    xpValue: mustGet<HTMLElement>("xpValue"),
    skillPointsValue: mustGet<HTMLElement>("skillPointsValue"),
    classValue: mustGet<HTMLElement>("classValue"),
    placementModeValue: mustGet<HTMLElement>("placementModeValue"),
    selectedTowerValue: mustGet<HTMLElement>("selectedTowerValue"),
    selectedBuildingValue: mustGet<HTMLElement>("selectedBuildingValue"),
    spellChargesValue: mustGet<HTMLElement>("spellChargesValue"),
    combatStatsValue: mustGet<HTMLElement>("combatStatsValue"),
    logList: mustGet<HTMLElement>("logList"),
  };
}

function processCommands(
  state: ReturnType<typeof createInitialState>,
  path: ReturnType<typeof createPathModel>,
): void {
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
      } else {
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

function updateActionButtonStates(state: ReturnType<typeof createInitialState>, ui: RuntimeUi): void {
  for (const [heroClass, button] of Object.entries(ui.classButtons) as Array<
    [HeroClass, HTMLButtonElement]
  >) {
    button.classList.toggle("active", heroClass === state.heroClass);
    button.disabled = state.classLocked;
  }

  for (const [towerKind, button] of Object.entries(ui.towerButtons) as Array<[TowerKind, HTMLButtonElement]>) {
    button.classList.toggle(
      "active",
      state.placementMode === "tower" && towerKind === state.selectedTower,
    );
    button.disabled = state.phase !== "prep";
  }

  for (const [buildingKind, button] of Object.entries(ui.buildingButtons) as Array<
    [BuildingKind, HTMLButtonElement]
  >) {
    button.classList.toggle(
      "active",
      state.placementMode === "building" && buildingKind === state.selectedBuilding,
    );
    button.disabled = state.phase !== "prep";
  }

  const spellHotkeys: Record<SpellKind, string> = {
    meteor: "Z",
    frost_nova: "X",
    healing_aura: "C",
  };

  for (const [spellKind, button] of Object.entries(ui.spellButtons) as Array<[SpellKind, HTMLButtonElement]>) {
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

export function bootTowerDefense(): void {
  const ui = collectUi();
  const path = createPathModel();
  const state = createInitialState();

  const ctx = ui.canvas.getContext("2d");
  if (!ctx) {
    throw new Error("Unable to initialize 2D context.");
  }

  const inputBindings: InputBindings = {
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

  const frame = (now: number) => {
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

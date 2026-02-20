const DEFAULT_DATA = {
  username: "jguida941",
  generated_at: "2026-02-20T00:57:00Z",
  profile_url: "https://github.com/jguida941",
  stats: {
    total_commits: 3500,
    total_repos: 203,
    total_stars: 8,
    languages_count: 9,
    prs_merged: 25,
    releases: 15,
    ci_pipelines: 45,
    streak_days: 12,
    total_contributions: 935,
  },
  derived: {
    level: 10,
    class_name: "Full-Stack Mage",
    title: "Apprentice Builder",
    total_xp: 4670,
    xp_current: 929,
    xp_next: 1922,
  },
  top_languages: [
    { name: "Python", percent: 63.9 },
    { name: "Java", percent: 15.3 },
    { name: "C++", percent: 10.2 },
    { name: "Rust", percent: 3.8 },
  ],
};

const WIDTH = 960;
const HEIGHT = 540;

const PRESETS = {
  rookie: {
    label: "Rookie",
    spawnMul: 1.2,
    asteroidSpeedMul: 0.9,
    damageTakenMul: 0.8,
    scoreMul: 0.92,
    livesBonus: 1,
  },
  standard: {
    label: "Standard",
    spawnMul: 1,
    asteroidSpeedMul: 1,
    damageTakenMul: 1,
    scoreMul: 1,
    livesBonus: 0,
  },
  elite: {
    label: "Elite",
    spawnMul: 0.86,
    asteroidSpeedMul: 1.18,
    damageTakenMul: 1.25,
    scoreMul: 1.24,
    livesBonus: -1,
  },
};

const UPGRADE_DEFS = [
  {
    key: "weapon",
    name: "Pulse Cannon",
    description: "+1 laser damage",
    baseCost: 32,
    stepCost: 22,
    maxLevel: 8,
  },
  {
    key: "fire",
    name: "Burst Mod",
    description: "faster fire cooldown",
    baseCost: 30,
    stepCost: 20,
    maxLevel: 8,
  },
  {
    key: "armor",
    name: "Hull Plating",
    description: "more shield and survivability",
    baseCost: 36,
    stepCost: 24,
    maxLevel: 8,
  },
  {
    key: "reactor",
    name: "Reactor Core",
    description: "ship speed and score bonus",
    baseCost: 34,
    stepCost: 23,
    maxLevel: 8,
  },
];

const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

const ui = {
  score: document.getElementById("scoreValue"),
  wave: document.getElementById("waveValue"),
  lives: document.getElementById("livesValue"),
  shield: document.getElementById("shieldValue"),
  scrap: document.getElementById("scrapValue"),
  best: document.getElementById("bestValue"),
  status: document.getElementById("statusText"),
  overlay: document.getElementById("overlay"),
  menuPanel: document.getElementById("menuPanel"),
  shopPanel: document.getElementById("shopPanel"),
  gameOverPanel: document.getElementById("gameOverPanel"),
  presetWrap: document.getElementById("presetWrap"),
  startBtn: document.getElementById("startBtn"),
  continueBtn: document.getElementById("continueBtn"),
  restartBtn: document.getElementById("restartBtn"),
  shopText: document.getElementById("shopText"),
  shopOptions: document.getElementById("shopOptions"),
  shopScrap: document.getElementById("shopScrapValue"),
  gameOverText: document.getElementById("gameOverText"),
  finalScore: document.getElementById("finalScore"),
  finalWave: document.getElementById("finalWave"),
  finalPreset: document.getElementById("finalPreset"),
  leaderboardList: document.getElementById("leaderboardList"),
  clearLeaderboardBtn: document.getElementById("clearLeaderboardBtn"),
  leftBtn: document.getElementById("leftBtn"),
  fireBtn: document.getElementById("fireBtn"),
  rightBtn: document.getElementById("rightBtn"),
};

const input = {
  left: false,
  right: false,
  fire: false,
};

const state = {
  mode: "menu",
  preset: "rookie",
  data: DEFAULT_DATA,
  buffs: null,
  score: 0,
  wave: 1,
  lives: 3,
  scrap: 0,
  shield: 100,
  best: 0,
  upgrades: {
    weapon: 0,
    fire: 0,
    armor: 0,
    reactor: 0,
  },
  wavePlan: null,
  running: false,
  lastTs: 0,
  spawnTimer: 0,
  fireTimer: 0,
  ship: {
    x: WIDTH / 2,
    y: HEIGHT - 56,
    w: 46,
    h: 26,
    invuln: 0,
  },
  bullets: [],
  asteroids: [],
  particles: [],
  stars: [],
  leaderboard: [],
};

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function rand(min, max) {
  return Math.random() * (max - min) + min;
}

function randInt(min, max) {
  return Math.floor(rand(min, max + 1));
}

function number(value) {
  return new Intl.NumberFormat("en-US").format(Math.round(value));
}

function formatDate(isoDate) {
  const dt = new Date(isoDate);
  if (Number.isNaN(dt.getTime())) {
    return "unknown";
  }
  return dt.toISOString().slice(0, 10);
}

function leaderboardKey(username) {
  return `devquest_asteroid_leaderboard_${username || "unknown"}`;
}

function computeBuffs(data) {
  const stats = data.stats || {};

  return {
    shipSpeedBase: clamp(312 + (stats.streak_days || 0) * 4, 300, 560),
    fireCooldownBase: clamp(218 - (stats.prs_merged || 0) * 3, 82, 230),
    bulletSpeedBase: clamp(560 + Math.floor((stats.total_commits || 0) / 14), 560, 980),
    bulletDamageBase: clamp(1 + Math.floor((stats.total_commits || 0) / 1900), 1, 4),
    spawnIntervalBase: clamp(980 - (stats.total_contributions || 0) / 7, 320, 980),
    asteroidSpeedBase: clamp(92 + (stats.total_repos || 0) / 4, 92, 250),
    startingLives: clamp(2 + Math.floor((stats.ci_pipelines || 0) / 16), 2, 6),
    scoreMultiplierBase: 1 + (stats.total_stars || 0) / 60,
    invulnSeconds: clamp(0.9 + (stats.ci_pipelines || 0) / 130, 0.9, 2.4),
    shieldBase: clamp(96 + (stats.languages_count || 0) * 4, 90, 160),
  };
}

function getPreset() {
  return PRESETS[state.preset] || PRESETS.standard;
}

function getShipSpeed() {
  const preset = getPreset();
  return (state.buffs.shipSpeedBase + state.upgrades.reactor * 24) * (2 - preset.asteroidSpeedMul * 0.7);
}

function getFireCooldown() {
  return clamp(state.buffs.fireCooldownBase - state.upgrades.fire * 15, 58, 240);
}

function getBulletDamage() {
  return state.buffs.bulletDamageBase + state.upgrades.weapon;
}

function getBulletRadius() {
  return 3 + Math.min(3, Math.floor((getBulletDamage() - 1) / 2));
}

function getScoreMultiplier() {
  const preset = getPreset();
  return (state.buffs.scoreMultiplierBase + state.upgrades.reactor * 0.06) * preset.scoreMul;
}

function getMaxLives() {
  return clamp(state.buffs.startingLives + Math.floor(state.upgrades.armor / 2) + getPreset().livesBonus, 1, 10);
}

function getShieldMax() {
  return state.buffs.shieldBase + state.upgrades.armor * 36;
}

function getSpawnIntervalSeconds() {
  const preset = getPreset();
  const waveFactor = Math.max(0.4, 1 - state.wave * 0.045);
  const reactorFactor = 1 - state.upgrades.reactor * 0.03;
  const ms = state.buffs.spawnIntervalBase * preset.spawnMul * waveFactor * reactorFactor;
  return clamp(ms / 1000, 0.16, 1.2);
}

function getAsteroidSpeed() {
  const preset = getPreset();
  const waveBoost = 1 + state.wave * 0.06;
  return state.buffs.asteroidSpeedBase * preset.asteroidSpeedMul * waveBoost;
}

function upgradeCost(def) {
  return def.baseCost + state.upgrades[def.key] * def.stepCost;
}

function setOverlayPanel(panel) {
  ui.menuPanel.classList.toggle("hidden", panel !== "menu");
  ui.shopPanel.classList.toggle("hidden", panel !== "shop");
  ui.gameOverPanel.classList.toggle("hidden", panel !== "gameover");
}

function setMode(mode) {
  state.mode = mode;

  if (mode === "running") {
    ui.overlay.classList.add("hidden");
    return;
  }

  ui.overlay.classList.remove("hidden");

  if (mode === "menu") {
    setOverlayPanel("menu");
  }
  if (mode === "shop") {
    setOverlayPanel("shop");
  }
  if (mode === "gameover") {
    setOverlayPanel("gameover");
  }
}

function setPreset(presetKey) {
  if (!PRESETS[presetKey]) {
    return;
  }
  state.preset = presetKey;

  const buttons = ui.presetWrap.querySelectorAll(".preset-btn");
  buttons.forEach((button) => {
    button.classList.toggle("active", button.dataset.preset === presetKey);
  });
}

function renderLeaderboard() {
  ui.leaderboardList.innerHTML = "";

  if (!state.leaderboard.length) {
    const empty = document.createElement("li");
    empty.textContent = "No runs yet";
    ui.leaderboardList.appendChild(empty);
    state.best = 0;
    return;
  }

  state.best = state.leaderboard[0].score;

  state.leaderboard.forEach((entry, idx) => {
    const li = document.createElement("li");
    li.innerHTML = `#${idx + 1} ${number(entry.score)} <span class="meta">Wave ${entry.wave} · ${entry.preset.toUpperCase()} · ${formatDate(entry.at)}</span>`;
    ui.leaderboardList.appendChild(li);
  });
}

function saveLeaderboard() {
  const key = leaderboardKey(state.data.username);
  localStorage.setItem(key, JSON.stringify(state.leaderboard));
}

function loadLeaderboard() {
  const key = leaderboardKey(state.data.username);
  try {
    const raw = localStorage.getItem(key);
    if (!raw) {
      state.leaderboard = [];
      renderLeaderboard();
      return;
    }

    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      throw new Error("leaderboard payload is not an array");
    }

    state.leaderboard = parsed
      .filter((item) => Number.isFinite(item.score) && Number.isFinite(item.wave) && typeof item.preset === "string")
      .slice(0, 10);
  } catch (error) {
    state.leaderboard = [];
  }

  renderLeaderboard();
}

function addLeaderboardEntry() {
  state.leaderboard.push({
    score: Math.round(state.score),
    wave: state.wave,
    preset: state.preset,
    at: new Date().toISOString(),
  });

  state.leaderboard.sort((a, b) => {
    if (b.score !== a.score) {
      return b.score - a.score;
    }
    return b.wave - a.wave;
  });

  state.leaderboard = state.leaderboard.slice(0, 10);
  saveLeaderboard();
  renderLeaderboard();
}

function updateProfileUI() {
  const data = state.data;

  document.getElementById("playerHandle").textContent = data.username || "unknown";
  document.getElementById("playerClass").textContent = data.derived?.class_name || "Code Wanderer";
  document.getElementById("playerLevel").textContent = `Lv ${data.derived?.level || 1}`;

  const profileLink = document.getElementById("profileLink");
  profileLink.href = data.profile_url || `https://github.com/${data.username || ""}`;

  const stats = data.stats || {};
  document.getElementById("signalCommits").textContent = number(stats.total_commits || 0);
  document.getElementById("signalCi").textContent = number(stats.ci_pipelines || 0);
  document.getElementById("signalPrs").textContent = number(stats.prs_merged || 0);
  document.getElementById("signalStreak").textContent = number(stats.streak_days || 0);

  document.getElementById("buffDamage").textContent = `x${state.buffs.bulletDamageBase}`;
  document.getElementById("buffRate").textContent = `${Math.round(1000 / state.buffs.fireCooldownBase)} shots/s`;
  document.getElementById("buffSpeed").textContent = `${Math.round(state.buffs.shipSpeedBase)} u/s`;
  document.getElementById("buffLives").textContent = `${state.buffs.startingLives}`;

  const chips = document.getElementById("languageChips");
  chips.innerHTML = "";
  (data.top_languages || []).slice(0, 8).forEach((item) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    const pct = typeof item.percent === "number" ? `${item.percent.toFixed(1)}%` : "";
    chip.textContent = `${item.name}${pct ? ` ${pct}` : ""}`;
    chips.appendChild(chip);
  });
}

function buildStars() {
  state.stars = [];
  for (let i = 0; i < 130; i += 1) {
    state.stars.push({
      x: rand(0, WIDTH),
      y: rand(0, HEIGHT),
      r: rand(0.7, 2.1),
      v: rand(12, 42),
      a: rand(0.3, 0.9),
    });
  }
}

function resetRunState() {
  state.score = 0;
  state.wave = 1;
  state.scrap = 0;
  state.upgrades = {
    weapon: 0,
    fire: 0,
    armor: 0,
    reactor: 0,
  };

  state.ship.x = WIDTH / 2;
  state.ship.y = HEIGHT - 56;
  state.ship.invuln = 0;

  state.bullets = [];
  state.asteroids = [];
  state.particles = [];

  state.lives = getMaxLives();
  state.shield = getShieldMax();

  state.fireTimer = 0;
  state.spawnTimer = 0.5;

  setupWavePlan(state.wave);
}

function setupWavePlan(wave) {
  const normalCount = 8 + wave * 2;
  const bossWave = wave % 5 === 0;

  state.wavePlan = {
    normalTotal: normalCount,
    normalSpawned: 0,
    normalDestroyed: 0,
    bossWave,
    bossSpawned: false,
    bossDefeated: !bossWave,
  };

  state.spawnTimer = 0.35;
  state.shield = Math.min(getShieldMax(), state.shield + getShieldMax() * 0.35);

  if (bossWave) {
    ui.status.textContent = `Wave ${wave}: boss wave incoming.`;
  } else {
    ui.status.textContent = `Wave ${wave}: clear ${normalCount} asteroids.`;
  }
}

function addParticleBurst(x, y, color) {
  for (let i = 0; i < 16; i += 1) {
    state.particles.push({
      x,
      y,
      vx: rand(-150, 150),
      vy: rand(-150, 150),
      life: rand(0.28, 0.72),
      ttl: rand(0.28, 0.72),
      color,
    });
  }
}

function updateHud() {
  ui.score.textContent = number(state.score);
  ui.wave.textContent = String(state.wave);
  ui.lives.textContent = String(state.lives);

  const shieldPct = Math.round((state.shield / Math.max(getShieldMax(), 1)) * 100);
  ui.shield.textContent = `${clamp(shieldPct, 0, 100)}%`;

  ui.scrap.textContent = number(state.scrap);
  ui.best.textContent = number(state.best);
}

function spawnBullet() {
  state.bullets.push({
    x: state.ship.x,
    y: state.ship.y - state.ship.h / 2,
    vy: -state.buffs.bulletSpeedBase,
    r: getBulletRadius(),
    damage: getBulletDamage(),
  });
}

function spawnNormalAsteroid() {
  const size = randInt(14, 42);
  const hp = Math.ceil(1 + state.wave * 0.32 + size / 18);

  state.asteroids.push({
    kind: "normal",
    x: rand(size, WIDTH - size),
    y: -size - 12,
    r: size,
    vy: getAsteroidSpeed() + rand(0, 80),
    vx: rand(-44, 44),
    rot: rand(0, Math.PI * 2),
    spin: rand(-1.7, 1.7),
    hp,
    maxHp: hp,
    scoreValue: 12 + Math.floor(size / 3),
    scrapValue: 3 + Math.floor(size / 14),
  });

  state.wavePlan.normalSpawned += 1;
}

function spawnBossAsteroid() {
  const hp = Math.ceil(28 + state.wave * 5.5);

  state.asteroids.push({
    kind: "boss",
    x: WIDTH / 2,
    y: -110,
    r: 84,
    vy: getAsteroidSpeed() * 0.56,
    vx: rand(-26, 26),
    rot: rand(0, Math.PI * 2),
    spin: rand(-0.7, 0.7),
    hp,
    maxHp: hp,
    scoreValue: 240 + state.wave * 26,
    scrapValue: 55 + state.wave * 8,
  });

  state.wavePlan.bossSpawned = true;
  ui.status.textContent = `Wave ${state.wave}: boss asteroid deployed.`;
}

function intersectsCircleRect(circle, rect) {
  const closestX = clamp(circle.x, rect.x - rect.w / 2, rect.x + rect.w / 2);
  const closestY = clamp(circle.y, rect.y - rect.h / 2, rect.y + rect.h / 2);
  const dx = circle.x - closestX;
  const dy = circle.y - closestY;
  return dx * dx + dy * dy <= circle.r * circle.r;
}

function onAsteroidDestroyed(asteroid) {
  const scoreGain = Math.round((asteroid.scoreValue + state.wave * 3) * getScoreMultiplier());
  state.score += scoreGain;
  state.scrap += asteroid.scrapValue;

  if (asteroid.kind === "boss") {
    state.wavePlan.bossDefeated = true;
    ui.status.textContent = `Boss destroyed. Entering hangar after cleanup.`;
  } else {
    state.wavePlan.normalDestroyed += 1;
  }

  addParticleBurst(asteroid.x, asteroid.y, asteroid.kind === "boss" ? "#ff7488" : "#ffbf69");
}

function applyShipImpact(asteroid) {
  const preset = getPreset();
  const baseDamage = asteroid.kind === "boss" ? 54 : 16 + asteroid.r * 0.52;
  const mitigation = 1 + state.upgrades.armor * 0.17;
  const damage = (baseDamage * preset.damageTakenMul) / mitigation;

  state.shield -= damage;
  addParticleBurst(state.ship.x, state.ship.y, "#69dcff");

  if (state.shield > 0) {
    ui.status.textContent = `Shield impact: ${Math.round(damage)}.`;
    return;
  }

  state.lives -= 1;

  if (state.lives <= 0) {
    endRun();
    return;
  }

  state.shield = getShieldMax();
  state.ship.invuln = state.buffs.invulnSeconds + state.upgrades.armor * 0.07;
  ui.status.textContent = `Hull breach. Lives remaining: ${state.lives}.`;
}

function completeWave() {
  const waveBonus = Math.round((26 + state.wave * 11 + state.lives * 5) * getScoreMultiplier());
  const scrapBonus = 18 + state.wave * 9 + Math.max(0, state.lives - 1) * 4;

  state.score += waveBonus;
  state.scrap += scrapBonus;

  openShop();
}

function openShop() {
  setMode("shop");
  renderShop();
  ui.status.textContent = `Wave ${state.wave} cleared. Upgrade and continue.`;
}

function renderShop() {
  ui.shopText.textContent = `Wave ${state.wave} complete. Upgrade before wave ${state.wave + 1}.`;
  ui.shopScrap.textContent = number(state.scrap);

  const html = UPGRADE_DEFS.map((def) => {
    const level = state.upgrades[def.key];
    const cost = upgradeCost(def);
    const maxed = level >= def.maxLevel;
    const disabled = maxed || state.scrap < cost;

    return `
      <div class="shop-item">
        <h4>${def.name} Lv.${level}</h4>
        <p>${def.description}</p>
        <div class="shop-line">
          <span>Cost ${maxed ? "MAX" : number(cost)}</span>
          <button class="shop-buy" data-upgrade="${def.key}" ${disabled ? "disabled" : ""} type="button">
            ${maxed ? "MAXED" : "Buy"}
          </button>
        </div>
      </div>
    `;
  }).join("");

  ui.shopOptions.innerHTML = html;
}

function buyUpgrade(upgradeKey) {
  const def = UPGRADE_DEFS.find((item) => item.key === upgradeKey);
  if (!def) {
    return;
  }

  const current = state.upgrades[upgradeKey];
  if (current >= def.maxLevel) {
    return;
  }

  const cost = upgradeCost(def);
  if (state.scrap < cost) {
    return;
  }

  state.scrap -= cost;
  state.upgrades[upgradeKey] += 1;

  if (upgradeKey === "armor") {
    state.shield = Math.min(getShieldMax(), state.shield + getShieldMax() * 0.3);
    const maxLives = getMaxLives();
    if (state.lives < maxLives) {
      state.lives += 1;
    }
  }

  if (upgradeKey === "reactor") {
    state.score += Math.round(8 * getScoreMultiplier());
  }

  renderShop();
  updateHud();
  ui.status.textContent = `${def.name} upgraded.`;
}

function continueFromShop() {
  state.wave += 1;
  setupWavePlan(state.wave);
  state.running = true;
  setMode("running");
}

function endRun() {
  state.running = false;
  setMode("gameover");

  addLeaderboardEntry();
  updateHud();

  ui.finalScore.textContent = number(state.score);
  ui.finalWave.textContent = String(state.wave);
  ui.finalPreset.textContent = getPreset().label;
  ui.gameOverText.textContent = `Ship destroyed on wave ${state.wave}. Tune your build and try again.`;
  ui.status.textContent = `Run complete. Final score ${number(state.score)}.`;
}

function startRun() {
  resetRunState();
  state.running = true;
  setMode("running");
}

function updateStars(dt) {
  const speedFactor = state.mode === "running" ? 1 : 0.42;
  state.stars.forEach((star) => {
    star.y += star.v * dt * speedFactor;
    if (star.y > HEIGHT + 4) {
      star.y = -4;
      star.x = rand(0, WIDTH);
    }
  });
}

function updateGameplay(dt) {
  const plan = state.wavePlan;

  state.ship.invuln = Math.max(0, state.ship.invuln - dt);

  if (input.left) {
    state.ship.x -= getShipSpeed() * dt;
  }
  if (input.right) {
    state.ship.x += getShipSpeed() * dt;
  }
  state.ship.x = clamp(state.ship.x, state.ship.w / 2 + 6, WIDTH - state.ship.w / 2 - 6);

  state.fireTimer -= dt * 1000;
  if (input.fire && state.fireTimer <= 0) {
    spawnBullet();
    state.fireTimer = getFireCooldown();
  }

  state.spawnTimer -= dt;
  if (plan.normalSpawned < plan.normalTotal && state.spawnTimer <= 0) {
    spawnNormalAsteroid();
    state.spawnTimer = getSpawnIntervalSeconds();
  }

  if (
    plan.bossWave &&
    !plan.bossSpawned &&
    plan.normalSpawned >= plan.normalTotal &&
    plan.normalDestroyed >= plan.normalTotal &&
    state.asteroids.length <= 2
  ) {
    spawnBossAsteroid();
  }

  state.bullets.forEach((bullet) => {
    bullet.y += bullet.vy * dt;
  });
  state.bullets = state.bullets.filter((bullet) => bullet.y > -32);

  state.asteroids.forEach((asteroid) => {
    asteroid.x += asteroid.vx * dt;
    asteroid.y += asteroid.vy * dt;
    asteroid.rot += asteroid.spin * dt;

    if (asteroid.x < asteroid.r) {
      asteroid.x = asteroid.r;
      asteroid.vx *= -1;
    }
    if (asteroid.x > WIDTH - asteroid.r) {
      asteroid.x = WIDTH - asteroid.r;
      asteroid.vx *= -1;
    }
  });

  for (let i = state.bullets.length - 1; i >= 0; i -= 1) {
    const bullet = state.bullets[i];
    let consumed = false;

    for (let j = state.asteroids.length - 1; j >= 0; j -= 1) {
      const asteroid = state.asteroids[j];
      const dx = bullet.x - asteroid.x;
      const dy = bullet.y - asteroid.y;
      const hitDistance = asteroid.r + bullet.r;

      if (dx * dx + dy * dy <= hitDistance * hitDistance) {
        asteroid.hp -= bullet.damage;
        consumed = true;

        if (asteroid.hp <= 0) {
          onAsteroidDestroyed(asteroid);
          state.asteroids.splice(j, 1);
        }
        break;
      }
    }

    if (consumed) {
      state.bullets.splice(i, 1);
    }
  }

  for (let i = state.asteroids.length - 1; i >= 0; i -= 1) {
    const asteroid = state.asteroids[i];

    if (asteroid.y - asteroid.r > HEIGHT + 16) {
      state.asteroids.splice(i, 1);
      state.score = Math.max(0, state.score - 12);
      continue;
    }

    if (state.ship.invuln <= 0 && intersectsCircleRect(asteroid, state.ship)) {
      state.asteroids.splice(i, 1);
      applyShipImpact(asteroid);

      if (!state.running) {
        return;
      }
    }
  }

  state.particles.forEach((particle) => {
    particle.x += particle.vx * dt;
    particle.y += particle.vy * dt;
    particle.life -= dt;
  });
  state.particles = state.particles.filter((particle) => particle.life > 0);

  if (plan.normalDestroyed >= plan.normalTotal && plan.bossDefeated && state.asteroids.length === 0) {
    state.running = false;
    completeWave();
  }

  updateHud();
}

function drawShip(ship) {
  const blink = ship.invuln > 0 && Math.floor(ship.invuln * 12) % 2 === 0;
  if (blink) {
    return;
  }

  ctx.save();
  ctx.translate(ship.x, ship.y);

  ctx.fillStyle = "#7be2ff";
  ctx.beginPath();
  ctx.moveTo(0, -ship.h / 2 - 4);
  ctx.lineTo(ship.w / 2, ship.h / 2);
  ctx.lineTo(0, ship.h / 3);
  ctx.lineTo(-ship.w / 2, ship.h / 2);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = "#def9ff";
  ctx.fillRect(-3, -ship.h / 2 + 2, 6, 8);

  ctx.restore();
}

function drawAsteroid(asteroid) {
  const ratio = asteroid.hp / asteroid.maxHp;
  const tone = Math.floor(150 + ratio * 70);

  ctx.save();
  ctx.translate(asteroid.x, asteroid.y);
  ctx.rotate(asteroid.rot);

  if (asteroid.kind === "boss") {
    ctx.fillStyle = `rgb(${tone + 20}, ${tone - 40}, ${tone - 50})`;
  } else {
    ctx.fillStyle = `rgb(${tone}, ${tone - 25}, ${tone - 36})`;
  }

  ctx.beginPath();
  ctx.arc(0, 0, asteroid.r, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "rgba(41, 48, 74, 0.46)";
  ctx.beginPath();
  ctx.arc(-asteroid.r * 0.24, -asteroid.r * 0.16, asteroid.r * 0.21, 0, Math.PI * 2);
  ctx.arc(asteroid.r * 0.22, asteroid.r * 0.14, asteroid.r * 0.16, 0, Math.PI * 2);
  ctx.fill();

  if (asteroid.kind === "boss") {
    ctx.strokeStyle = "rgba(255, 127, 146, 0.65)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(0, 0, asteroid.r + 5, 0, Math.PI * 2);
    ctx.stroke();
  }

  ctx.restore();
}

function draw() {
  ctx.clearRect(0, 0, WIDTH, HEIGHT);

  const gradient = ctx.createLinearGradient(0, 0, 0, HEIGHT);
  gradient.addColorStop(0, "#091022");
  gradient.addColorStop(1, "#121a33");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  state.stars.forEach((star) => {
    ctx.globalAlpha = star.a;
    ctx.fillStyle = "#d7e6ff";
    ctx.beginPath();
    ctx.arc(star.x, star.y, star.r, 0, Math.PI * 2);
    ctx.fill();
  });
  ctx.globalAlpha = 1;

  state.bullets.forEach((bullet) => {
    ctx.fillStyle = "#9cf8ff";
    ctx.beginPath();
    ctx.arc(bullet.x, bullet.y, bullet.r, 0, Math.PI * 2);
    ctx.fill();
  });

  state.asteroids.forEach((asteroid) => drawAsteroid(asteroid));
  drawShip(state.ship);

  state.particles.forEach((particle) => {
    const alpha = particle.life / particle.ttl;
    ctx.globalAlpha = alpha;
    ctx.fillStyle = particle.color;
    ctx.fillRect(particle.x, particle.y, 3, 3);
  });
  ctx.globalAlpha = 1;

  ctx.fillStyle = "#8fa7dd";
  ctx.font = "14px Space Grotesk";
  ctx.fillText(`Wave ${state.wave}`, 14, 22);
  ctx.fillText(`Targets ${state.wavePlan ? state.wavePlan.normalDestroyed : 0}/${state.wavePlan ? state.wavePlan.normalTotal : 0}`, 14, 42);
}

function loop(ts) {
  if (!state.lastTs) {
    state.lastTs = ts;
  }

  const dt = Math.min(0.033, (ts - state.lastTs) / 1000);
  state.lastTs = ts;

  updateStars(dt);

  if (state.mode === "running" && state.running) {
    updateGameplay(dt);
  }

  draw();
  requestAnimationFrame(loop);
}

function setControlButton(button, keyName) {
  const activate = () => {
    input[keyName] = true;
    button.classList.add("active");

    if (keyName === "fire" && state.mode === "running" && state.fireTimer <= 0) {
      spawnBullet();
      state.fireTimer = getFireCooldown();
    }
  };

  const release = () => {
    input[keyName] = false;
    button.classList.remove("active");
  };

  button.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    activate();
  });
  button.addEventListener("pointerup", release);
  button.addEventListener("pointerleave", release);
  button.addEventListener("pointercancel", release);
}

function bindInput() {
  setControlButton(ui.leftBtn, "left");
  setControlButton(ui.rightBtn, "right");
  setControlButton(ui.fireBtn, "fire");

  window.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft" || event.key === "a" || event.key === "A") {
      input.left = true;
    }
    if (event.key === "ArrowRight" || event.key === "d" || event.key === "D") {
      input.right = true;
    }
    if (event.key === " " || event.code === "Space") {
      input.fire = true;
      event.preventDefault();
    }
  });

  window.addEventListener("keyup", (event) => {
    if (event.key === "ArrowLeft" || event.key === "a" || event.key === "A") {
      input.left = false;
    }
    if (event.key === "ArrowRight" || event.key === "d" || event.key === "D") {
      input.right = false;
    }
    if (event.key === " " || event.code === "Space") {
      input.fire = false;
    }
  });
}

function bindUiEvents() {
  ui.presetWrap.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-preset]");
    if (!button) {
      return;
    }
    setPreset(button.dataset.preset);
  });

  ui.startBtn.addEventListener("click", startRun);
  ui.restartBtn.addEventListener("click", startRun);
  ui.continueBtn.addEventListener("click", continueFromShop);

  ui.shopOptions.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-upgrade]");
    if (!button) {
      return;
    }
    buyUpgrade(button.dataset.upgrade);
  });

  ui.clearLeaderboardBtn.addEventListener("click", () => {
    const key = leaderboardKey(state.data.username);
    localStorage.removeItem(key);
    state.leaderboard = [];
    renderLeaderboard();
    updateHud();
  });
}

async function loadData() {
  try {
    const response = await fetch("./data.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Failed to load data.json (${response.status})`);
    }
    return await response.json();
  } catch (error) {
    console.warn("Using fallback game data", error);
    return DEFAULT_DATA;
  }
}

async function boot() {
  state.data = await loadData();
  state.buffs = computeBuffs(state.data);

  loadLeaderboard();
  updateProfileUI();
  buildStars();
  bindInput();
  bindUiEvents();

  setPreset("rookie");
  resetRunState();
  setMode("menu");
  state.running = false;
  ui.status.textContent = "Choose a preset and launch.";

  updateHud();
  requestAnimationFrame(loop);
}

boot();

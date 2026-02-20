// Bootstrap loader: keep this file plain JS so CI syntax checks remain simple.
(function boot() {
  import("./dist/main.js")
    .then((mod) => {
      if (typeof mod.bootTowerDefense === "function") {
        mod.bootTowerDefense();
      } else {
        throw new Error("dist/main.js loaded but no bootTowerDefense export was found");
      }
    })
    .catch((error) => {
      // eslint-disable-next-line no-console
      console.error("Tower Forge bootstrap failed", error);

      const fallback = document.createElement("div");
      fallback.style.padding = "1rem";
      fallback.style.margin = "1rem";
      fallback.style.border = "1px solid #cf6b75";
      fallback.style.borderRadius = "8px";
      fallback.style.background = "#2b1c24";
      fallback.style.color = "#ffe2e6";
      fallback.textContent = "Game failed to load. Run `npm --prefix game run build` to refresh dist files.";
      document.body.prepend(fallback);
    });
})();

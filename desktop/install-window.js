const { execFileSync } = require("child_process");
const fs = require("fs");

// Electron's package no longer runs its download on install. On WSL, fetch
// the Windows build so the window is a normal Windows app.
const env = { ...process.env };
let wsl = false;
try {
  wsl = fs.readFileSync("/proc/version", "utf8").toLowerCase().includes("microsoft");
} catch (_error) {
  wsl = false;
}
const inContainer = fs.existsSync("/.dockerenv") || env.CARD_CONTAINER === "1";
if (wsl && !inContainer && !env.ELECTRON_INSTALL_PLATFORM && !env.npm_config_platform) {
  env.ELECTRON_INSTALL_PLATFORM = "win32";
  env.ELECTRON_INSTALL_ARCH = env.ELECTRON_INSTALL_ARCH || env.npm_config_arch || "x64";
}

execFileSync(process.execPath, ["node_modules/electron/install.js"], {
  stdio: "inherit",
  env,
});

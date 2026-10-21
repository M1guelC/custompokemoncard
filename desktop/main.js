const { app, BrowserWindow, Menu } = require("electron");

function cardUrl() {
  if (process.env.CARD_URL) return process.env.CARD_URL;
  const flag = process.argv.find((arg) => arg.startsWith("--card-url="));
  return flag ? flag.slice("--card-url=".length) : "";
}

app.whenReady().then(() => {
  Menu.setApplicationMenu(null);
  const window = new BrowserWindow({
    width: 1280,
    height: 880,
    minWidth: 980,
    minHeight: 680,
    title: "Card creator",
    backgroundColor: "#1c1916",
    autoHideMenuBar: true,
    show: false,
  });
  window.once("ready-to-show", () => {
    window.show();
    window.restore();
    window.focus();
  });
  const url = cardUrl();
  if (!url) {
    console.error("Missing card URL. Start the app with: python main.py");
    app.quit();
    return;
  }
  window.loadURL(url);
});

app.on("window-all-closed", () => app.quit());

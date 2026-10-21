const editor = document.querySelector("#editor");
const preview = document.querySelector("#preview");
const status = document.querySelector("#status");
const sideLabel = document.querySelector("#side-label");
const flipButton = document.querySelector("#flip");
const downloadButton = document.querySelector("#download");

const ROMAN = ["", "I", "II", "III"];

let schema = null;
let cardId = "character";
let side = "front";
let timer = 0;
let requestId = 0;
let lastUrl = "";
const drafts = {};

flipButton.addEventListener("click", () => {
  side = side === "front" ? "back" : "front";
  if (drafts[cardId]) drafts[cardId].side = side;
  sideLabel.textContent = sideText();
  schedule(0);
});

downloadButton.addEventListener("click", async () => {
  status.textContent = "Preparing the full card…";
  const body = new FormData(editor);
  stamp(body);
  body.set("purpose", "download");
  const response = await fetch("/api/preview", { method: "POST", body });
  if (!response.ok || !response.headers.get("content-type")?.includes("image")) {
    status.textContent = "The card could not be saved.";
    return;
  }
  const blob = await response.blob();
  const values = currentValues();
  const name = (values.name || values.title || "card").replace(/[^\w\-]+/g, "-");
  const roman = ascensionRoman();
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${name}${roman ? `-${roman}` : ""}-${side}.png`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1500);
  status.textContent = statusLine();
});

load();

async function load() {
  const response = await fetch("/api/schema");
  schema = await response.json();
  buildForm();
  schedule(0);
}

function card() {
  return schema.cards.find((item) => item.id === cardId);
}

function ensureDraft(item) {
  if (!drafts[item.id]) {
    drafts[item.id] = {
      values: { ...item.defaults, ascension_count: "1", ascension_level: "" },
      levels: { "1": pickStats(item, item.defaults) },
      image: null,
      imageName: "",
      side: "front",
    };
  }
  return drafts[item.id];
}

function pickStats(item, values) {
  const stats = {};
  (item.ascension || []).forEach((id) => {
    stats[id] = values[id] ?? "";
  });
  return stats;
}

function readForm() {
  const values = {};
  new FormData(editor).forEach((value, key) => {
    if (typeof value === "string") values[key] = value;
  });
  return values;
}

function saveDraft() {
  if (!schema || !editor.querySelector("[name]")) return;
  const item = card();
  const draft = ensureDraft(item);
  const count = draft.values.ascension_count || "1";
  const level = draft.values.ascension_level || "";
  draft.values = readForm();
  draft.values.ascension_count = count;
  draft.values.ascension_level = level;
  draft.levels[level || "1"] = pickStats(item, draft.values);
  draft.side = side;
  const input = editor.elements.image;
  const file = input && input.files && input.files[0];
  if (file) {
    draft.image = file;
    draft.imageName = file.name;
  }
}

function rememberForm() {
  const draft = drafts[cardId];
  const count = draft.values.ascension_count || "1";
  const level = draft.values.ascension_level || "";
  draft.values = readForm();
  draft.values.ascension_count = count;
  draft.values.ascension_level = level;
  draft.levels[level || "1"] = pickStats(card(), draft.values);
}

function ascensionOn() {
  const draft = drafts[cardId];
  return !!draft && (draft.values.ascension_count || "1") !== "1";
}

function ascensionRoman() {
  if (!ascensionOn()) return "";
  const level = Number(drafts[cardId].values.ascension_level || "1");
  return ROMAN[level] || "";
}

function sideText() {
  const face = side === "front" ? "Front" : "Back";
  const roman = ascensionRoman();
  return roman ? `${face} · ${roman}` : face;
}

function statusLine() {
  const roman = ascensionRoman();
  if (!roman) return side === "back" ? "Showing the back." : "Showing the front.";
  const face = side === "back" ? "Showing the back" : "Showing the front";
  return `${face}, ascension ${roman}.`;
}

function stamp(body) {
  body.set("card", cardId);
  body.set("side", side);
  const level = ascensionOn() ? (drafts[cardId].values.ascension_level || "1") : "";
  body.set("ascension_level", level);
}

function buildForm() {
  const item = card();
  const draft = ensureDraft(item);
  side = draft.side || "front";
  editor.innerHTML = "";

  const kinds = document.createElement("div");
  kinds.className = "kinds";
  schema.cards.forEach((entry) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = entry.label;
    button.setAttribute("aria-pressed", entry.id === cardId ? "true" : "false");
    button.addEventListener("click", () => {
      if (cardId === entry.id) return;
      saveDraft();
      cardId = entry.id;
      buildForm();
      schedule(0);
    });
    kinds.appendChild(button);
  });
  editor.appendChild(kinds);

  const note = document.createElement("p");
  note.className = "kind-note";
  note.textContent = item.description;
  editor.appendChild(note);

  if (item.ascension && item.ascension.length) editor.appendChild(ascensionControls());

  item.sections.forEach((section) => {
    const block = document.createElement("section");
    const heading = document.createElement("h2");
    heading.textContent = section.title;
    block.appendChild(heading);
    section.fields.forEach((field) => block.appendChild(renderField(field)));
    editor.appendChild(block);
  });

  flipButton.hidden = !item.flip;
  sideLabel.textContent = sideText();
  applyConditions();
  updateAscensionChrome();
  refreshLabels();
}

function ascensionControls() {
  const wrap = document.createElement("div");
  wrap.className = "ascension";

  const counts = document.createElement("div");
  counts.className = "kinds";
  counts.id = "ascension-counts";
  [
    ["1", "No ascension"],
    ["2", "2 levels"],
    ["3", "3 levels"],
  ].forEach(([count, label]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.dataset.count = count;
    button.addEventListener("click", () => setCount(count));
    counts.appendChild(button);
  });
  wrap.appendChild(counts);

  const levels = document.createElement("div");
  levels.className = "kinds";
  levels.id = "ascension-levels";
  ["1", "2", "3"].forEach((level) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `Level ${level}`;
    button.dataset.level = level;
    button.addEventListener("click", () => showLevel(level));
    levels.appendChild(button);
  });
  wrap.appendChild(levels);

  const hint = document.createElement("p");
  hint.className = "ascension-note";
  hint.id = "ascension-note";
  wrap.appendChild(hint);
  return wrap;
}

function setCount(count) {
  const item = card();
  const draft = drafts[cardId];
  if ((draft.values.ascension_count || "1") === count) return;
  const previous = draft.values.ascension_level || "1";
  draft.levels[previous] = pickStats(item, readForm());
  draft.values.ascension_count = count;
  if (count === "1") {
    draft.values.ascension_level = "";
    applyStats(draft.levels["1"] || pickStats(item, item.defaults));
  } else {
    let next = draft.values.ascension_level || "1";
    if (Number(next) > Number(count)) next = count;
    draft.values.ascension_level = next;
    applyStats(levelStats(next));
  }
  rememberForm();
  updateAscensionChrome();
  refreshLabels();
  sideLabel.textContent = sideText();
  schedule(0);
}

function showLevel(level) {
  const item = card();
  const draft = drafts[cardId];
  if ((draft.values.ascension_count || "1") === "1") return;
  if ((draft.values.ascension_level || "1") === level) return;
  const previous = draft.values.ascension_level || "1";
  draft.levels[previous] = pickStats(item, readForm());
  draft.values.ascension_level = level;
  applyStats(levelStats(level));
  rememberForm();
  updateAscensionChrome();
  sideLabel.textContent = sideText();
  schedule(0);
}

function levelStats(level) {
  const draft = drafts[cardId];
  if (!draft.levels[level]) {
    const earlier = String(Math.max(1, Number(level) - 1));
    const source = draft.levels[earlier] || draft.levels["1"] || pickStats(card(), readForm());
    draft.levels[level] = { ...source };
  }
  return draft.levels[level];
}

function applyStats(stats) {
  (card().ascension || []).forEach((id) => {
    const control = editor.elements[id];
    if (control && stats[id] !== undefined) control.value = stats[id];
  });
}

function updateAscensionChrome() {
  const counts = document.querySelector("#ascension-counts");
  if (!counts) return;
  const draft = drafts[cardId];
  const count = draft.values.ascension_count || "1";
  const level = draft.values.ascension_level || "1";
  counts.querySelectorAll("button").forEach((button) => {
    button.setAttribute("aria-pressed", button.dataset.count === count ? "true" : "false");
  });
  const row = document.querySelector("#ascension-levels");
  row.hidden = count === "1";
  row.querySelectorAll("button").forEach((button) => {
    button.hidden = Number(button.dataset.level) > Number(count);
    const pressed = count !== "1" && button.dataset.level === level;
    button.setAttribute("aria-pressed", pressed ? "true" : "false");
  });
  const note = document.querySelector("#ascension-note");
  if (count === "1") {
    note.textContent = "One printing. Choose 2 or 3 levels when the next ascension has better stats.";
  } else {
    note.textContent = `Level ${level} of ${count}. The picture, name, and move names stay with the card. Fields marked this level are saved on this ascension.`;
  }
}

function refreshLabels() {
  const item = card();
  const on = ascensionOn();
  item.sections.forEach((section) => {
    section.fields.forEach((field) => {
      const label = editor.querySelector(`label[for="f-${field.id}"]`);
      if (!label) return;
      const marked = on && (item.ascension || []).includes(field.id);
      label.textContent = marked ? `${field.label} · this level` : field.label;
    });
  });
}

function renderField(field) {
  const wrap = document.createElement("div");
  wrap.className = "field";
  if (field.show_if) {
    wrap.dataset.showField = field.show_if.field;
    wrap.dataset.showValue = field.show_if.value;
  }
  const draft = ensureDraft(card());
  const value = draft.values[field.id] ?? card().defaults[field.id] ?? "";

  if (field.type === "image") {
    const drop = document.createElement("label");
    drop.className = "drop";
    const caption = document.createElement("span");
    caption.style.whiteSpace = "pre-line";
    caption.textContent = draft.imageName || `${field.label}\nPNG, JPG, or WebP`;
    drop.appendChild(caption);
    const input = document.createElement("input");
    input.type = "file";
    input.name = "image";
    input.accept = "image/png,image/jpeg,image/webp";
    if (draft.image) {
      const transfer = new DataTransfer();
      transfer.items.add(draft.image);
      input.files = transfer.files;
    }
    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      caption.textContent = file ? file.name : `${field.label}\nPNG, JPG, or WebP`;
      if (file) {
        draft.image = file;
        draft.imageName = file.name;
      }
      schedule();
    });
    drop.addEventListener("dragover", (event) => {
      event.preventDefault();
      drop.classList.add("over");
    });
    drop.addEventListener("dragleave", () => drop.classList.remove("over"));
    drop.addEventListener("drop", (event) => {
      event.preventDefault();
      drop.classList.remove("over");
      if (event.dataTransfer.files.length) {
        input.files = event.dataTransfer.files;
        caption.textContent = event.dataTransfer.files[0].name;
        draft.image = event.dataTransfer.files[0];
        draft.imageName = event.dataTransfer.files[0].name;
        schedule();
      }
    });
    drop.appendChild(input);
    wrap.appendChild(drop);
    return wrap;
  }

  const label = document.createElement("label");
  label.textContent = field.label;
  label.htmlFor = `f-${field.id}`;
  wrap.appendChild(label);

  let control;
  if (field.type === "textarea") {
    control = document.createElement("textarea");
    control.value = value;
  } else if (field.type === "range") {
    control = document.createElement("input");
    control.type = "range";
    control.min = field.min;
    control.max = field.max;
    control.value = value || field.min;
  } else if (field.type === "rarity" || field.type === "type" || field.type === "select") {
    control = document.createElement("select");
    const options = field.type === "rarity"
      ? schema.rarities.map((id) => ({ id, label: id }))
      : field.type === "type"
        ? schema.types
        : field.options;
    if (field.optional) {
      const blank = document.createElement("option");
      blank.value = "";
      blank.textContent = "None";
      control.appendChild(blank);
    }
    options.forEach((option) => {
      const node = document.createElement("option");
      node.value = option.id;
      node.textContent = option.label;
      control.appendChild(node);
    });
    control.value = value;
  } else {
    control = document.createElement("input");
    control.type = "text";
    control.value = value;
  }
  control.id = `f-${field.id}`;
  control.name = field.id;
  control.addEventListener("input", () => {
    applyConditions();
    schedule();
  });
  wrap.appendChild(control);
  return wrap;
}

function applyConditions() {
  editor.querySelectorAll("[data-show-field]").forEach((node) => {
    const control = editor.elements[node.dataset.showField];
    node.hidden = !control || control.value !== node.dataset.showValue;
  });
}

function currentValues() {
  const values = { card: cardId, side };
  new FormData(editor).forEach((value, key) => {
    if (typeof value === "string") values[key] = value;
  });
  return values;
}

function schedule(delay = 220) {
  clearTimeout(timer);
  timer = setTimeout(refresh, delay);
}

async function refresh() {
  const id = ++requestId;
  status.textContent = "Updating preview…";
  const body = new FormData(editor);
  stamp(body);
  body.set("purpose", "preview");
  const response = await fetch("/api/preview", { method: "POST", body });
  if (id !== requestId) return;
  if (!response.ok || !response.headers.get("content-type")?.includes("image")) {
    let message = "The preview could not be drawn.";
    try {
      const payload = await response.json();
      if (payload.error) message = payload.error;
    } catch (_error) {
      /* keep the fallback message */
    }
    status.textContent = message;
    return;
  }
  const blob = await response.blob();
  if (lastUrl) URL.revokeObjectURL(lastUrl);
  lastUrl = URL.createObjectURL(blob);
  preview.src = lastUrl;
  status.textContent = statusLine();
}

const editor = document.querySelector("#editor");
const preview = document.querySelector("#preview");
const status = document.querySelector("#status");
const sideLabel = document.querySelector("#side-label");
const flipButton = document.querySelector("#flip");
const downloadButton = document.querySelector("#download");

let schema = null;
let cardId = "character";
let side = "front";
let timer = 0;
let requestId = 0;
let lastUrl = "";

flipButton.addEventListener("click", () => {
  side = side === "front" ? "back" : "front";
  sideLabel.textContent = side === "front" ? "Front" : "Back";
  schedule(0);
});

downloadButton.addEventListener("click", () => {
  if (!lastUrl) return;
  const values = currentValues();
  const name = (values.name || values.title || "card").replace(/[^\w\-]+/g, "-");
  const link = document.createElement("a");
  link.href = lastUrl;
  link.download = `${name}-${side}.png`;
  link.click();
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

function buildForm() {
  editor.innerHTML = "";
  const kinds = document.createElement("div");
  kinds.className = "kinds";
  schema.cards.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = item.label;
    button.setAttribute("aria-pressed", item.id === cardId ? "true" : "false");
    button.addEventListener("click", () => {
      if (cardId === item.id) return;
      cardId = item.id;
      side = "front";
      sideLabel.textContent = "Front";
      buildForm();
      schedule(0);
    });
    kinds.appendChild(button);
  });
  editor.appendChild(kinds);

  const note = document.createElement("p");
  note.className = "kind-note";
  note.textContent = card().description;
  editor.appendChild(note);

  card().sections.forEach((section) => {
    const block = document.createElement("section");
    const heading = document.createElement("h2");
    heading.textContent = section.title;
    block.appendChild(heading);
    section.fields.forEach((field) => block.appendChild(renderField(field)));
    editor.appendChild(block);
  });

  flipButton.hidden = !card().flip;
  applyConditions();
}

function renderField(field) {
  const wrap = document.createElement("div");
  wrap.className = "field";
  if (field.show_if) {
    wrap.dataset.showField = field.show_if.field;
    wrap.dataset.showValue = field.show_if.value;
  }
  const value = card().defaults[field.id] ?? "";

  if (field.type === "image") {
    const drop = document.createElement("label");
    drop.className = "drop";
    drop.innerHTML = `<span>${field.label}<br>PNG, JPG, or WebP</span>`;
    const input = document.createElement("input");
    input.type = "file";
    input.name = "image";
    input.accept = "image/png,image/jpeg,image/webp";
    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      drop.querySelector("span").textContent = file ? file.name : `${field.label}\nPNG, JPG, or WebP`;
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
        drop.querySelector("span").textContent = event.dataTransfer.files[0].name;
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
  body.set("card", cardId);
  body.set("side", side);
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
  status.textContent = side === "back" ? "Showing the back." : "Showing the front.";
}

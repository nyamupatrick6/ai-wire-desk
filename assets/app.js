const DATA_URL = "data/latest.json";
const CATEGORY_ORDER = [
  "Model Releases",
  "Funding & Business",
  "Research",
  "Tools & Products",
  "Policy & Safety",
  "Community & Commentary",
];

const state = { report: null, activeFilter: "All" };

function timeAgo(iso) {
  const then = new Date(iso).getTime();
  const diffMin = Math.max(0, Math.round((Date.now() - then) / 60000));
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  return `${Math.round(diffHr / 24)}d ago`;
}

function clockTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function renderTicker(items) {
  const track = document.getElementById("ticker-track");
  if (!items.length) {
    track.textContent = "Waiting on the first run to file a report…";
    return;
  }
  const headlines = items.slice(0, 25).map((it) => escapeHtml(it.title));
  track.innerHTML = headlines.join('<span class="sep">//</span>');
}

function renderStatus(report) {
  const el = document.getElementById("live-status-text");
  if (!report || !report.generated_at) {
    el.textContent = "Awaiting first report";
    return;
  }
  el.textContent = `Live · filed ${timeAgo(report.generated_at)} · ${report.item_count} items on the wire`;
}

function renderFilters(items) {
  const bar = document.getElementById("filters");
  const present = new Set(items.map((it) => it.category));
  const cats = ["All", ...CATEGORY_ORDER.filter((c) => present.has(c))];
  bar.innerHTML = "";
  cats.forEach((cat) => {
    const btn = document.createElement("button");
    btn.className = "chip" + (cat === state.activeFilter ? " active" : "");
    btn.textContent = cat;
    btn.setAttribute("aria-pressed", cat === state.activeFilter);
    btn.addEventListener("click", () => {
      state.activeFilter = cat;
      render();
    });
    bar.appendChild(btn);
  });
}

function renderDesks(items) {
  const main = document.getElementById("desks");
  main.innerHTML = "";

  const filtered =
    state.activeFilter === "All"
      ? items
      : items.filter((it) => it.category === state.activeFilter);

  if (!filtered.length) {
    main.innerHTML = '<p class="empty-state">Nothing filed on this desk yet.</p>';
    return;
  }

  const grouped = {};
  filtered.forEach((it) => {
    const cat = it.category || "Community & Commentary";
    (grouped[cat] = grouped[cat] || []).push(it);
  });

  const orderedCats = CATEGORY_ORDER.filter((c) => grouped[c]);

  orderedCats.forEach((cat) => {
    const deskItems = grouped[cat].sort(
      (a, b) => new Date(b.published_at) - new Date(a.published_at)
    );

    const section = document.createElement("section");
    section.className = "desk";

    const header = document.createElement("div");
    header.className = "desk-header";
    header.innerHTML = `<h2>${escapeHtml(cat)}</h2><span class="desk-count">${deskItems.length}</span>`;
    section.appendChild(header);

    deskItems.forEach((it) => {
      const row = document.createElement("article");
      row.className = "item";
      row.innerHTML = `
        <div class="item-time">${clockTime(it.published_at)}<br>${timeAgo(it.published_at)}</div>
        <div>
          <p class="item-title">${it.signal ? '<span class="signal-flag">SIGNAL</span>' : ""}<a href="${it.url}" target="_blank" rel="noopener noreferrer">${escapeHtml(it.title)}</a></p>
          <p class="item-summary">${escapeHtml(it.summary || "")}</p>
          <p class="item-meta">${escapeHtml(it.source)}</p>
        </div>
      `;
      section.appendChild(row);
    });

    main.appendChild(section);
  });
}

function render() {
  const items = (state.report && state.report.items) || [];
  renderStatus(state.report);
  renderTicker(items);
  renderFilters(items);
  renderDesks(items);
}

async function load() {
  try {
    const res = await fetch(`${DATA_URL}?t=${Date.now()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    state.report = await res.json();
  } catch (e) {
    console.error("Failed to load report:", e);
    document.getElementById("desks").innerHTML =
      '<p class="empty-state">Could not load the latest report. If this is a fresh repo, run the workflow once to file the first one.</p>';
  }
  render();
}

load();

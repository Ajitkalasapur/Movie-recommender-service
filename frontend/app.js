// Screening Room front end (React, no build step). Talks to the API through Nginx at /api.
const { useState, useEffect, useRef } = React;
const h = React.createElement;
const API = "/api";
const SERVICE_DOWN = "The recommendation service didn’t respond. Start it with docker compose up -d, then try again.";
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

async function fetchTimed(url) {
  const started = performance.now();
  let response;
  try {
    response = await fetch(url);
  } catch (err) {
    throw new Error(SERVICE_DOWN);
  }
  if (!response.ok) {
    throw new Error(response.status === 404 ? "That film isn’t in the collection." : SERVICE_DOWN);
  }
  const data = await response.json();
  return { data, ms: Math.max(1, Math.round(performance.now() - started)) };
}

// MovieLens titles look like "Matrix, The (1999)". Show them as "The Matrix", with the year apart.
function splitTitle(raw) {
  const match = raw.match(/^(.*?)\s*\((\d{4})\)\s*$/);
  let name = match ? match[1] : raw;
  const year = match ? match[2] : "";
  const article = name.match(/^(.*), (The|A|An)$/);
  if (article) name = `${article[2]} ${article[1]}`;
  return { name, year };
}

function Meta({ result }) {
  if (!result) return h("p", { className: "meta" });
  const replica = String(result.data.served_by || "").slice(0, 6);
  const source = result.data.cached ? " from the cache" : "";
  return h("p", { className: "meta" }, `Answered by replica ${replica}${source} in ${result.ms} ms.`);
}

function Programme({ items, onSelect, label, revealKey }) {
  return h("ol", { className: "programme reveal", key: revealKey, "aria-label": label },
    items.map((item, i) => {
      const { name, year } = splitTitle(item.title);
      return h("li", { key: item.movieId },
        h("button", {
          className: "film", type: "button", onClick: () => onSelect(item),
          "aria-label": `${name}${year ? `, ${year}` : ""}. Show more like this.`,
        },
          h("span", { className: "rank" }, i + 1),
          h("span", { className: "title" }, name),
          h("span", { className: "year" }, year)));
    }));
}

function Skeleton() {
  const widths = ["62%", "48%", "71%", "55%", "40%", "66%", "52%", "58%", "44%", "69%"];
  return h("ol", { className: "programme skeleton", "aria-hidden": "true" },
    widths.map((w, i) => h("li", { key: i },
      h("div", { className: "film" },
        h("span", { className: "rank" }, i + 1),
        h("span", { className: "bar", style: { "--w": w } }),
        h("span", null)))));
}

function App() {
  const [viewer, setViewer] = useState("1");
  const [programme, setProgramme] = useState(null);
  const [programmeFor, setProgrammeFor] = useState("1");
  const [loadingProgramme, setLoadingProgramme] = useState(false);
  const [programmeError, setProgrammeError] = useState("");

  const [query, setQuery] = useState("");
  const [matches, setMatches] = useState(null);
  const [searchError, setSearchError] = useState("");
  const [similar, setSimilar] = useState(null);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const similarRef = useRef(null);

  async function loadProgramme(id) {
    setLoadingProgramme(true);
    setProgrammeError("");
    try {
      const result = await fetchTimed(`${API}/recommendations/${encodeURIComponent(id)}?k=10`);
      setProgramme(result);
      setProgrammeFor(id);
    } catch (err) {
      setProgrammeError(err.message);
    } finally {
      setLoadingProgramme(false);
    }
  }

  useEffect(() => { loadProgramme("1"); }, []);

  function submitViewer(e) {
    e.preventDefault();
    const id = viewer.trim();
    if (!/^\d+$/.test(id) || Number(id) < 1) {
      setProgrammeError("Enter a viewer number, such as 1 or 250.");
      return;
    }
    loadProgramme(id);
  }

  async function search(e) {
    e.preventDefault();
    const q = query.trim();
    if (!q) {
      setSearchError("Type part of a film title to search.");
      setMatches(null);
      return;
    }
    setSearchError("");
    try {
      const { data } = await fetchTimed(`${API}/movies/search?q=${encodeURIComponent(q)}&limit=8`);
      setMatches({ q, items: data.items });
    } catch (err) {
      setSearchError(err.message);
    }
  }

  async function showSimilar(item) {
    setLoadingSimilar(true);
    setSearchError("");
    setSimilar({ film: item, result: null });
    if (similarRef.current) {
      similarRef.current.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "start" });
    }
    try {
      const result = await fetchTimed(`${API}/similar/${item.movieId}?k=10`);
      setSimilar({ film: item, result });
    } catch (err) {
      setSearchError(err.message);
      setSimilar(null);
    } finally {
      setLoadingSimilar(false);
    }
  }

  const chosen = similar ? splitTitle(similar.film.title) : null;

  return h("div", { className: "page" },
    h("header", { className: "masthead" },
      h("p", { className: "wordmark" }, "Screening Room"),
      h("p", null, "Personal recommendations from 100,836 MovieLens ratings")),

    h("main", null,
      h("h1", null, "Tonight’s programme"),
      h("form", { className: "lede", onSubmit: submitViewer },
        h("label", { htmlFor: "viewer" }, "Ten films chosen for viewer"),
        h("input", {
          id: "viewer", className: "viewer-input", type: "number", min: 1, inputMode: "numeric",
          value: viewer, onChange: (e) => setViewer(e.target.value),
        }),
        h("button", { className: "primary", type: "submit", disabled: loadingProgramme },
          loadingProgramme ? "Choosing films…" : "Show programme")),
      h("p", { className: "hint" }, "Viewers 1 to 610 have rating histories. Select any film to see more like it."),
      programmeError ? h("p", { className: "notice", role: "alert" }, programmeError) : null,
      h("div", { "aria-live": "polite" },
        loadingProgramme
          ? h(Skeleton)
          : programme
            ? h(Programme, {
                items: programme.data.items, onSelect: showSimilar,
                label: `Programme for viewer ${programmeFor}`, revealKey: `p-${programmeFor}-${programme.ms}`,
              })
            : null,
        h(Meta, { result: loadingProgramme ? null : programme })),

      h("section", { ref: similarRef, "aria-labelledby": "similar-title" },
        h("h2", { id: "similar-title" }, "More like a film you love"),
        h("form", { className: "search", onSubmit: search, role: "search" },
          h("label", { htmlFor: "film-search", className: "visually-hidden" }, "Search the collection"),
          h("input", {
            id: "film-search", type: "search", value: query,
            placeholder: "Search the collection, for example Casablanca",
            onChange: (e) => setQuery(e.target.value),
          }),
          h("button", { className: "primary", type: "submit" }, "Search")),
        searchError ? h("p", { className: "notice", role: "alert" }, searchError) : null,
        matches
          ? (matches.items.length
              ? h("ul", { className: "matches", "aria-label": `Films matching ${matches.q}` },
                  matches.items.map((m) => {
                    const t = splitTitle(m.title);
                    return h("li", { key: m.movieId },
                      h("button", { className: "match", type: "button", onClick: () => showSimilar(m) },
                        t.year ? `${t.name} (${t.year})` : t.name));
                  }))
              : h("p", { className: "notice" }, `No films in the collection match “${matches.q}”. Try a shorter title.`))
          : null,
        similar
          ? h("div", { "aria-live": "polite" },
              h("h3", { className: "similar-heading" }, `More like ${chosen.name}`,
                chosen.year ? h("span", { className: "year" }, chosen.year) : null),
              loadingSimilar || !similar.result
                ? h(Skeleton)
                : h(Programme, {
                    items: similar.result.data.items, onSelect: showSimilar,
                    label: `Films like ${chosen.name}`, revealKey: `s-${similar.film.movieId}-${similar.result.ms}`,
                  }),
              h(Meta, { result: loadingSimilar ? null : similar.result }))
          : null)),

    h("footer", null,
      "Recommendations come from collaborative filtering (truncated SVD) trained on MovieLens ratings, and films are listed in the order the model ranks them. Data: GroupLens Research, MovieLens ml-latest-small."));
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));

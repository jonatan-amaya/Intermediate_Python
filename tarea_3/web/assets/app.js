/* Dashboard Tarea 3 - logica interactiva (vanilla JS + Plotly) */
"use strict";

const NOMBRES = {
  ARG: "Argentina", BOL: "Bolivia", BRA: "Brasil", CHL: "Chile",
  COL: "Colombia", CRI: "Costa Rica", DOM: "Rep. Dominicana", ECU: "Ecuador",
  SLV: "El Salvador", GTM: "Guatemala", HND: "Honduras", MEX: "México",
  NIC: "Nicaragua", PAN: "Panamá", PRY: "Paraguay", PER: "Perú",
  URY: "Uruguay", VEN: "Venezuela",
};
const COLOR_PERU = "#e63946";
const COLOR_SERIE = "#4d96ff";
const LAYOUT_BASE = {
  paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: "#e8eef5", size: 12 },
  margin: { t: 14, r: 20, b: 44, l: 56 },
  hoverlabel: { bgcolor: "#17222f", bordercolor: "#27394c" },
};
const CONFIG = { responsive: true, displaylogo: false };

const estado = {
  paises: new Set(["PER", "MEX", "COL", "ARG"]),
  anio: 2024,
  indicador: "pobreza",
  conPromedio: true,
};
let DATOS = null, HALLAZGOS = null;

const $ = (id) => document.getElementById(id);

/* ------------------------------------------------------------ carga */
async function cargar() {
  const [datos, hall] = await Promise.all([
    fetch("data/datos.json").then((r) => r.json()),
    fetch("data/hallazgos.json").then((r) => r.json()),
  ]);
  DATOS = datos; HALLAZGOS = hall;
  pintarKPIs();
  pintarHallazgos();
  armarControles();
  render();
}

/* ------------------------------------------------------------ KPIs */
function pintarKPIs() {
  const k = HALLAZGOS.kpis;
  const delta = (k.pobreza_peru_ult.valor - k.pobreza_peru_prepandemia.valor).toFixed(1);
  const tarjetas = [
    { clase: "roja", valor: `${k.pobreza_peru_ult.valor}%`,
      etiqueta: `Pobreza en Perú (${k.pobreza_peru_ult.anio})`,
      detalle: `${delta > 0 ? "+" : ""}${delta} puntos vs ${k.pobreza_peru_prepandemia.anio} (${k.pobreza_peru_prepandemia.valor}%)` },
    { clase: "", valor: `${k.promedio_region_ult.valor}%`,
      etiqueta: `Promedio regional (${k.promedio_region_ult.anio})`,
      detalle: "media simple de países con datos" },
    { clase: "roja", valor: `${k.pais_mas_pobre.valor}%`,
      etiqueta: `Mayor pobreza: ${k.pais_mas_pobre.pais} (${k.pais_mas_pobre.anio})`,
      detalle: "Línea nacional, % de población" },
    { clase: "azul", valor: `${k.pais_menos_pobre.valor}%`,
      etiqueta: `Menor pobreza: ${k.pais_menos_pobre.pais} (${k.pais_menos_pobre.anio})`,
      detalle: "Línea nacional, % de población" },
    { clase: "", valor: `${k.pobreza_peru_max.valor}%`,
      etiqueta: `Pico histórico de Perú (${k.pobreza_peru_max.anio})`,
      detalle: "Máximo de la serie 2000–2024" },
  ];
  $("kpis").innerHTML = tarjetas.map((t) => `
    <div class="kpi ${t.clase}">
      <div class="valor">${t.valor}</div>
      <div class="etiqueta">${t.etiqueta}</div>
      <div class="detalle">${t.detalle}</div>
    </div>`).join("");
}

function pintarHallazgos() {
  $("hallazgos").innerHTML = HALLAZGOS.hallazgos.map((h) => `
    <div class="hallazgo"><h3>${h.titulo}</h3><p>${h.detalle}</p></div>`).join("");
}

/* ------------------------------------------------------------ controles */
function armarControles() {
  const cont = $("lista-paises");
  cont.innerHTML = Object.keys(NOMBRES).map((iso) => `
    <label><input type="checkbox" value="${iso}"
      ${estado.paises.has(iso) ? "checked" : ""}> ${NOMBRES[iso]}</label>`).join("");
  cont.querySelectorAll("input").forEach((cb) =>
    cb.addEventListener("change", () => {
      cb.checked ? estado.paises.add(cb.value) : estado.paises.delete(cb.value);
      render();
    }));

  $("btn-peru").onclick = () => marcarPaises(["PER"]);
  $("btn-tipica").onclick = () => marcarPaises(["PER", "MEX", "COL", "ARG"]);
  $("btn-todos").onclick = () => marcarPaises(Object.keys(NOMBRES));

  $("rango-anio").oninput = (e) => {
    estado.anio = +e.target.value;
    $("anio-ver").textContent = estado.anio;
    render();
  };
  $("sel-indicador").onchange = (e) => { estado.indicador = e.target.value; render(); };
  $("chk-promedio").onchange = (e) => { estado.conPromedio = e.target.checked; render(); };
  $("btn-csv").onclick = descargarCSV;
}

function marcarPaises(isos) {
  estado.paises = new Set(isos);
  document.querySelectorAll("#lista-paises input").forEach((cb) =>
    cb.checked = estado.paises.has(cb.value));
  render();
}

/* ------------------------------------------------------------ accesos */
function serie(clave, iso) {
  const m = DATOS[clave];
  return m.anios.map((a, i) => ({ anio: a, valor: m.series[iso][i] }));
}
function promedioRegional(clave) {
  const m = DATOS[clave];
  return m.anios.map((a, i) => {
    const vals = Object.values(m.series).map((s) => s[i]).filter((v) => v != null);
    return vals.length ? vals.reduce((x, y) => x + y, 0) / vals.length : null;
  });
}

/* ------------------------------------------------------------ graficos */
function tituloInd(clave) {
  return { pobreza: "Pobreza (%)", gini: "Índice de Gini", pbi_pc: "PBI per cápita (US$)" }[clave];
}

function grafMapa() {
  const m = DATOS[estado.indicador];
  const i = m.anios.indexOf(estado.anio);
  const isos = Object.keys(m.series).filter((iso) => m.series[iso][i] != null);
  const trace = {
    type: "choropleth", locationmode: "ISO-3",
    locations: isos,
    z: isos.map((iso) => m.series[iso][i]),
    text: isos.map((iso) => NOMBRES[iso]),
    hovertemplate: "%{text}: %{z:.1f}<extra>" + tituloInd(estado.indicador) + " · " + estado.anio + "</extra>",
    colorscale: estado.indicador === "pbi_pc" ? "Blues" : "Reds",
    showscale: true, colorbar: { thickness: 12 },
    marker: { line: { color: "#0f1620", width: 0.6 } },
  };
  const layout = Object.assign({}, LAYOUT_BASE, {
    geo: {
      projection: { type: "natural earth", rotation: { lon: -60, lat: -15 } },
      showframe: false, showcountries: true, countrycolor: "#27394c",
      landcolor: "#131c27", oceancolor: "#0f1620", showocean: true,
      bgcolor: "rgba(0,0,0,0)",
    },
    margin: { t: 6, r: 6, b: 6, l: 6 },
  });
  Plotly.newPlot($("graf-mapa"), [trace], layout, CONFIG);
  $("mapa-sub").textContent = `${tituloInd(estado.indicador)} · ${estado.anio}`;
}

function grafLinea() {
  const trazas = [];
  for (const iso of estado.paises) {
    if (!DATOS[estado.indicador].series[iso]) continue;  // pais sin datos del indicador
    const puntos = serie(estado.indicador, iso).filter((p) => p.valor != null);
    trazas.push({
      type: "scatter", mode: "lines+markers",
      x: puntos.map((p) => p.anio), y: puntos.map((p) => p.valor),
      name: NOMBRES[iso],
      line: { color: iso === "PER" ? COLOR_PERU : undefined, width: iso === "PER" ? 3 : 2 },
      hovertemplate: "%{y:.1f}<extra>%{fullData.name} · %{x}</extra>",
    });
  }
  if (estado.conPromedio) {
    const prom = promedioRegional(estado.indicador);
    trazas.push({
      type: "scatter", mode: "lines", name: "Promedio regional",
      x: DATOS[estado.indicador].anios, y: prom,
      line: { color: "#93a5b6", dash: "dash", width: 2 },
      hovertemplate: "%{y:.1f}<extra>Promedio · %{x}</extra>",
    });
  }
  const layout = Object.assign({}, LAYOUT_BASE, {
    xaxis: { title: "Año", gridcolor: "#27394c" },
    yaxis: { title: tituloInd(estado.indicador), gridcolor: "#27394c" },
    legend: { orientation: "h", y: -0.22 },
  });
  Plotly.react($("graf-linea"), trazas, layout, CONFIG);
}

function grafBarras() {
  const m = DATOS[estado.indicador];
  const i = m.anios.indexOf(estado.anio);
  const pares = Object.keys(m.series)
    .map((iso) => [iso, m.series[iso][i]])
    .filter(([, v]) => v != null)
    .sort((a, b) => b[1] - a[1]);
  const trace = {
    type: "bar", orientation: "h",
    y: pares.map(([iso]) => NOMBRES[iso]),
    x: pares.map(([, v]) => v),
    marker: { color: pares.map(([iso]) => iso === "PER" ? COLOR_PERU : "#2a9d8f") },
    hovertemplate: "%{x:.1f}<extra>%{y} · " + estado.anio + "</extra>",
  };
  const layout = Object.assign({}, LAYOUT_BASE, {
    margin: { t: 10, r: 20, b: 36, l: 110 },
    xaxis: { title: tituloInd(estado.indicador), gridcolor: "#27394c" },
    yaxis: { automargin: true },
    showlegend: false,
  });
  Plotly.react($("graf-barras"), [trace], layout, CONFIG);
  $("barras-sub").textContent = `${tituloInd(estado.indicador)} · ${estado.anio}`;
}

function grafDispersion() {
  const mp = DATOS.pobreza, mg = DATOS.pbi_pc;
  const i = mp.anios.indexOf(estado.anio);
  const pares = Object.keys(NOMBRES)
    .map((iso) => [iso, mg.series[iso] ? mg.series[iso][i] : null,
                    mp.series[iso] ? mp.series[iso][i] : null])
    .filter(([, x, y]) => x != null && y != null);
  const trace = {
    type: "scatter", mode: "markers+text",
    x: pares.map(([, x]) => x), y: pares.map(([, , y]) => y),
    text: pares.map(([iso]) => NOMBRES[iso]),
    textposition: "top center",
    marker: {
      size: pares.map(([iso]) => iso === "PER" ? 16 : 10),
      color: pares.map(([iso]) => iso === "PER" ? COLOR_PERU : "#4d96ff"),
      opacity: 0.85,
    },
    hovertemplate: "PBI pc US$ %{x:,.0f}<br>Pobreza %{y:.1f}%<extra>%{text}</extra>",
  };
  const layout = Object.assign({}, LAYOUT_BASE, {
    xaxis: { title: "PBI per cápita (US$)", gridcolor: "#27394c" },
    yaxis: { title: "Pobreza (%)", gridcolor: "#27394c" },
    showlegend: false,
  });
  Plotly.react($("graf-disp"), [trace], layout, CONFIG);
  $("disp-sub").textContent = estado.anio;
}

function pintarTabla() {
  const m = DATOS[estado.indicador];
  const i = m.anios.indexOf(estado.anio);
  const filas = Object.keys(m.series)
    .map((iso) => [iso, m.series[iso][i]])
    .filter(([, v]) => v != null)
    .sort((a, b) => b[1] - a[1]);
  let html = `<thead><tr><th>País</th><th>${tituloInd(estado.indicador)} (${estado.anio})</th></tr></thead><tbody>`;
  html += filas.map(([iso, v]) =>
    `<tr class="${iso === "PER" ? "fila-peru" : ""}"><td>${NOMBRES[iso]}</td><td>${v.toLocaleString("es-PE", { maximumFractionDigits: 1 })}</td></tr>`).join("");
  $("tabla").innerHTML = html + "</tbody>";
  $("tabla-sub").textContent = `${tituloInd(estado.indicador)} · ${estado.anio}`;
}

function descargarCSV() {
  const lineas = ["pais,iso3,anio,indicador,valor"];
  for (const clave of ["pobreza", "gini", "pbi_pc"]) {
    const m = DATOS[clave];
    for (const [iso, serieValores] of Object.entries(m.series)) {
      m.anios.forEach((a, i) => {
        if (serieValores[i] != null)
          lineas.push(`${NOMBRES[iso]},${iso},${a},${clave},${serieValores[i]}`);
      });
    }
  }
  const blob = new Blob(["﻿" + lineas.join("\n")], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "pobreza_latam_panel.csv";
  a.click();
  URL.revokeObjectURL(a.href);
}

function render() {
  grafMapa(); grafLinea(); grafBarras(); grafDispersion(); pintarTabla();
}

cargar().catch((e) => {
  document.body.insertAdjacentHTML("afterbegin",
    `<p style="background:#e63946;color:#fff;padding:10px">Error cargando datos: ${e}</p>`);
});

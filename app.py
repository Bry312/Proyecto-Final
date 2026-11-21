"""Sismicidad en Costa Rica (2015-2025): aplicación web interactiva.

Proyecto final del curso GF-0657 Programación en SIG (II-2026).
Autor: Bryan Ramírez Coria, C16275.
"""

import copy
import math

import branca.colormap as bcm
import folium
import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Sismicidad en Costa Rica",
    layout="wide",
)


# Catálogo sísmico del USGS (servicio FDSN Event Web Service): rectángulo
# delimitador de Costa Rica (incluye la zona marina de subducción), 2015-2025,
# magnitud >= 3.0.
URL_USGS = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query?"
    "format=csv"
    "&starttime=2015-01-01"
    "&endtime=2025-12-31"
    "&minlatitude=8.0"
    "&maxlatitude=11.3"
    "&minlongitude=-86.5"
    "&maxlongitude=-82.5"
    "&minmagnitude=3.0"
    "&orderby=time"
)

# Capa de cantones del IGN, publicada en el repositorio del curso (EPSG:8908)
URL_CANTONES = (
    "https://raw.githubusercontent.com/gf0657-programacionsig/2026-ii/"
    "main/datos/ign/cantones.gpkg"
)

# Mapa base de Esri 
URL_MAPA_BASE = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Street_Map/MapServer/tile/{z}/{y}/{x}"
)

COL_CANTON = "canton"
COL_PROVINCIA = "provincia"
CENTRO_CR = [9.7489, -83.7534]


# ---------------------------------------------------------------------------
# Carga de datos 
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Cargando la capa de cantones…")
def cargar_cantones_crtm05():
    """Cantones del IGN en su SRC original (EPSG:8908, CRTM05)."""
    cantones = gpd.read_file(URL_CANTONES)
    return cantones[[COL_CANTON, COL_PROVINCIA, "geometry"]]


@st.cache_data(show_spinner="Cargando la capa de cantones…")
def cargar_cantones():
    """Cantones reproyectados a WGS84 (EPSG:4326), para el mapa web."""
    return cargar_cantones_crtm05().to_crs("EPSG:4326")


@st.cache_data(show_spinner="Descargando los sismos del catálogo USGS…", ttl=86400)
def cargar_sismos():
    """Sismos del USGS con el cantón en el que ocurrió cada uno.

    La unión espacial (punto en polígono) se hace en EPSG:8908. Los sismos que
    no caen dentro de ningún cantón (en el mar) quedan sin cantón y se
    clasifican como "Marino".
    """
    df = pd.read_csv(
        URL_USGS,
        usecols=["time", "latitude", "longitude", "depth", "mag", "place"],
    )
    df["time"] = pd.to_datetime(df["time"], utc=True).dt.tz_localize(None)
    df["anio"] = df["time"].dt.year

    puntos = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    )
    cantones = cargar_cantones_crtm05()
    unidos = gpd.sjoin(
        puntos.to_crs(cantones.crs), cantones, how="left", predicate="within"
    )
    
    unidos = unidos[~unidos.index.duplicated(keep="first")]

    sismos = pd.DataFrame(unidos.drop(columns=["geometry", "index_right"], errors="ignore"))
    sismos["tipo"] = sismos[COL_CANTON].notna().map({True: "Continental", False: "Marino"})
    return sismos.sort_values("time", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Filtros y mapa
# ---------------------------------------------------------------------------

def filtrar_sismos(df, anios, mag_min, prof_max, provincia, tipo):
    """Aplica a los sismos los mismos filtros en toda la aplicación."""
    mascara = (
        df["anio"].between(anios[0], anios[1])
        & (df["mag"] >= mag_min)
        & (df["depth"] <= prof_max)
    )
    if provincia != "Todas":
        mascara &= df[COL_PROVINCIA] == provincia
    if tipo != "Todos":
        mascara &= df["tipo"] == ("Continental" if tipo == "Continentales" else "Marino")
    return df[mascara]


@st.cache_resource(show_spinner="Construyendo el mapa…")
def construir_mapa(anios, mag_min, prof_max, provincia, tipo):
    """Mapa folium que depende solo de los valores de los controles."""
    sismos = filtrar_sismos(cargar_sismos(), anios, mag_min, prof_max, provincia, tipo)
    cantones = cargar_cantones().copy()

    # Conteo de sismos por cantón en la selección actual
    conteo = sismos.groupby(COL_CANTON).size()
    cantones["numero_sismos"] = cantones[COL_CANTON].map(conteo).fillna(0).astype(int)

    vmax = max(int(cantones["numero_sismos"].max()), 1)
    escala = bcm.LinearColormap(
        ["#fff5eb", "#fdae6b", "#e6550d", "#7f0000"],
        vmin=0,
        vmax=vmax,
        caption="Número de sismos por cantón (selección actual)",
    )

    def estilo(feature):
        n = feature["properties"]["numero_sismos"]
        return {
            "fillColor": "#e0e0e0" if n == 0 else escala(n),
            "color": "#555555",
            "weight": 0.5,
            "fillOpacity": 0.7,
        }

    m = folium.Map(location=CENTRO_CR, zoom_start=8, tiles=None)
    folium.TileLayer(
        tiles=URL_MAPA_BASE, attr="Esri — World Street Map", name="Mapa base"
    ).add_to(m)

    # Capa 1: cantones coloreados según el número de sismos
    folium.GeoJson(
        cantones,
        name="Cantones (sismos por cantón)",
        style_function=estilo,
        tooltip=folium.GeoJsonTooltip(
            fields=[COL_CANTON, COL_PROVINCIA, "numero_sismos"],
            aliases=["Cantón:", "Provincia:", "N.° de sismos:"],
        ),
    ).add_to(m)
    escala.add_to(m)

    # Capas 2 y 3: sismos continentales y marinos, como puntos
    grupos = {
        "Continental": ("Sismos continentales", "#ff0a0ae8"),
        "Marino": ("Sismos marinos", "#2ac0f6"),
    }
    for tipo_sismo, (nombre, color) in grupos.items():
        capa = folium.FeatureGroup(name=nombre)
        for fila in sismos[sismos["tipo"] == tipo_sismo].itertuples():
            canton = getattr(fila, COL_CANTON)
            canton = "Fuera de cantón (mar)" if pd.isna(canton) else canton
            folium.CircleMarker(
                location=[fila.latitude, fila.longitude],
                radius=2 + fila.mag,
                color="#2b2b2b",
                weight=0.5,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(
                    f"<b>Fecha (UTC):</b> {fila.time:%Y-%m-%d %H:%M}<br>"
                    f"<b>Magnitud:</b> {fila.mag:.1f}<br>"
                    f"<b>Profundidad:</b> {fila.depth:.1f} km<br>"
                    f"<b>Cantón:</b> {canton}<br>"
                    f"<b>Lugar (USGS):</b> {fila.place}",
                    max_width=260,
                ),
            ).add_to(capa)
        capa.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

   
    if provincia != "Todas":
        minx, miny, maxx, maxy = cantones[
            cantones[COL_PROVINCIA] == provincia
        ].total_bounds
        m.fit_bounds([[miny, minx], [maxy, maxx]])

    return m


# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------

st.title("Sismicidad en Costa Rica (2015-2025)")
st.markdown(
    """
Esta aplicación permite explorar los sismos de magnitud 3.0 o mayor registrados
en Costa Rica y sus alrededores entre 2015 y 2025, según el catálogo del
Servicio Geológico de los Estados Unidos (USGS), y su relación con la división
cantonal del país (capa de cantones del IGN). Cada sismo se asigna al cantón en
el que ocurrió; los que ocurren en el mar quedan fuera de todo cantón y se
clasifican como *marinos*.

**Cómo usarla:** ajuste los filtros de la barra lateral (años, magnitud mínima,
profundidad máxima, provincia y tipo de sismo). Los indicadores, el mapa, los
gráficos y la tabla se actualizan con la misma selección.
"""
)

# ---------------------------------------------------------------------------
# Datos y controles de la barra lateral
# ---------------------------------------------------------------------------

sismos_todos = cargar_sismos()
cantones = cargar_cantones()

st.sidebar.header("Filtros")

anio_min = int(sismos_todos["anio"].min())
anio_max = int(sismos_todos["anio"].max())
anios = st.sidebar.slider("Rango de años", anio_min, anio_max, (anio_min, anio_max))

mag_limite = math.floor(float(sismos_todos["mag"].min()) * 10) / 10
mag_maxima = math.ceil(float(sismos_todos["mag"].max()) * 10) / 10
mag_min = st.sidebar.slider(
    "Magnitud mínima",
    min_value=mag_limite,
    max_value=mag_maxima,
    value=mag_limite,
    step=0.1,
)

prof_limite = int(math.ceil(float(sismos_todos["depth"].max())))
prof_max = st.sidebar.slider(
    "Profundidad máxima (km)", min_value=0, max_value=prof_limite, value=prof_limite
)

provincias = ["Todas"] + sorted(cantones[COL_PROVINCIA].dropna().unique())
provincia = st.sidebar.selectbox("Provincia", provincias)

tipo = st.sidebar.radio("Tipo de sismo", ["Todos", "Continentales", "Marinos"])
st.sidebar.caption(
    "Al elegir una provincia solo se muestran sismos continentales, porque los "
    "marinos no pertenecen a ningún cantón."
)

sismos = filtrar_sismos(sismos_todos, anios, mag_min, prof_max, provincia, tipo)

if sismos.empty:
    st.warning(
        "Ningún sismo cumple los filtros seleccionados. Amplíe el rango de años, "
        "reduzca la magnitud mínima, aumente la profundidad máxima o cambie la "
        "provincia o el tipo de sismo."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Indicadores
# ---------------------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)
col1.metric("Sismos en la selección", f"{len(sismos):,}")
col2.metric("Magnitud máxima (escala USGS)", f"{sismos['mag'].max():.1f}")
col3.metric("Profundidad media (km)", f"{sismos['depth'].mean():.1f}")
col4.metric(
    "Sismos continentales (%)",
    f"{(sismos['tipo'] == 'Continental').mean() * 100:.0f} %",
)

# ---------------------------------------------------------------------------
# Pestañas: mapa, gráficos y tabla
# ---------------------------------------------------------------------------

tab_mapa, tab_graficos, tab_tabla = st.tabs(["Mapa", "Gráficos", "Tabla"])

with tab_mapa:
    st.subheader("Mapa interactivo de sismos y cantones")
    mapa = construir_mapa(anios, mag_min, prof_max, provincia, tipo)
    
    st_folium(
        copy.deepcopy(mapa),
        height=600,
        use_container_width=True,
        returned_objects=[],
        key="mapa_sismos",
    )
    st.caption(
        "Use el control de capas para activar o desactivar los cantones y los "
        "sismos continentales y marinos. El tamaño de cada punto es "
        "proporcional a la magnitud."
    )

with tab_graficos:
    st.subheader("Cantones con más sismos")
    conteo = (
        sismos.dropna(subset=[COL_CANTON])
        .groupby(COL_CANTON)
        .size()
        .reset_index(name="numero_sismos")
        .sort_values("numero_sismos", ascending=False)
        .head(15)
        .sort_values("numero_sismos")
    )
    if conteo.empty:
        st.info("La selección actual no incluye sismos continentales.")
    else:
        fig_cantones = px.bar(
            conteo,
            x="numero_sismos",
            y=COL_CANTON,
            orientation="h",
            color_discrete_sequence=["#7b2cbf"],
            labels={"numero_sismos": "Número de sismos", COL_CANTON: "Cantón"},
            title="Cantones con mayor número de sismos",
        )
        st.plotly_chart(fig_cantones, width="stretch")

    st.subheader("Profundidad y magnitud")
    fig_dispersion = px.scatter(
        sismos,
        x="mag",
        y="depth",
        color="tipo",
         color_discrete_map={"Continental": "#7b2cbf", "Marino": "#2a9d8f"},
        opacity=0.7,
        hover_data={"time": "|%Y-%m-%d", "mag": ":.1f", "depth": ":.1f"},
        labels={
            "mag": "Magnitud",
            "depth": "Profundidad (km)",
            "tipo": "Tipo de sismo",
            "time": "Fecha (UTC)",
        },
        title="Profundidad vs. magnitud de los sismos",
    )
    fig_dispersion.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_dispersion, width="stretch")

with tab_tabla:
    st.subheader("Sismos de la selección")
    tabla = sismos[
        ["time", "mag", "depth", "latitude", "longitude",
         COL_CANTON, COL_PROVINCIA, "tipo", "place"]
    ].copy()
    tabla[[COL_CANTON, COL_PROVINCIA]] = tabla[[COL_CANTON, COL_PROVINCIA]].fillna("—")

    def color_magnitud(valor):
        if valor >= 5.0:
            return "background-color: #7b2cbf; color: white"
        if valor >= 4.5:
            return "background-color: #c77dff; color: black"
        if valor >= 4.0:
            return "background-color: #e0c3fc; color: black"
        return "background-color: #f3e8ff; color: black"

    def color_tipo(valor):
        if valor == "Continental":
            return "background-color: #ffe5d0; color: black"
        return "background-color: #d0e8ff; color: black"

    tabla_estilo = (
        tabla.style
        .map(color_magnitud, subset=["mag"])
        .map(color_tipo, subset=["tipo"])
    )

    st.dataframe(
        tabla_estilo,
        hide_index=True,
        width="stretch",
        column_config={
            "time": st.column_config.DatetimeColumn(
                "Fecha (UTC)", format="YYYY-MM-DD HH:mm"
            ),
            "mag": st.column_config.NumberColumn("Magnitud", format="%.1f"),
            "depth": st.column_config.NumberColumn("Profundidad (km)", format="%.1f"),
            "latitude": st.column_config.NumberColumn("Latitud (°)", format="%.4f"),
            "longitude": st.column_config.NumberColumn("Longitud (°)", format="%.4f"),
            COL_CANTON: st.column_config.TextColumn("Cantón"),
            COL_PROVINCIA: st.column_config.TextColumn("Provincia"),
            "tipo": st.column_config.TextColumn("Tipo"),
            "place": st.column_config.TextColumn("Lugar (USGS)"),
        },
    )
    st.caption(
        "Color de la magnitud: morado más oscuro = mayor magnitud "
        "(≥ 5,0; 4,5-4,9; 4,0-4,4; < 4,0)."
    )
    st.download_button(
        "Descargar la tabla como CSV",
        data=tabla.to_csv(index=False).encode("utf-8"),
        file_name="sismos_filtrados.csv",
        mime="text/csv",
    )
# ---------------------------------------------------------------------------
# Fuentes
# ---------------------------------------------------------------------------

st.divider()
st.caption(
    "**Fuentes de los datos:** "
    "U.S. Geological Survey. (s. f.). *Earthquake Catalog* [conjunto de datos]. "
    "https://earthquake.usgs.gov/earthquakes/search/ · "
    "Instituto Geográfico Nacional (IGN). *Cantones de Costa Rica* [conjunto de "
    "datos], publicada en el repositorio del curso GF-0657 Programación en SIG "
    "(2026-II). https://github.com/gf0657-programacionsig/2026-ii"
)

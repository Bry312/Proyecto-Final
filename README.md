# Sismicidad en Costa Rica (2015-2025): aplicación web interactiva

**Autor:** Bryan Ramírez Coria
**Curso:** GF-0657 Programación en Sistemas de Información Geográfica, II-2026
**Proyecto final**

## Descripción

Aplicación web desarrollada con streamlit para explorar los sismos de magnitud 3.0 o mayor registrados en Costa Rica y sus alrededores entre 2015 y 2025, y su relación con la división cantonal del país. Cada sismo se asigna, mediante una unión espacial, al cantón en que ocurrió; los sismos que ocurren en el mar quedan fuera de todo cantón y se clasifican como marinos.

## Aplicación publicada

**Enlace:** [https://proyecto-final-bryan.streamlit.app/](https://proyecto-final-bryan.streamlit.app/)

## Fuentes de los datos

- U.S. Geological Survey. (s. f.). *Earthquake Catalog* [conjunto de datos]. Servicio FDSN Event Web Service. https://earthquake.usgs.gov/earthquakes/search/
- Instituto Geográfico Nacional (IGN). *Cantones de Costa Rica* [conjunto de datos]. Publicada en el repositorio del curso GF-0657 Programación en SIG (2026-II). https://github.com/gf0657-programacionsig/2026-ii/blob/main/datos/ign/cantones.gpkg

Los datos se cargan desde esas direcciones al ejecutar la aplicación; el repositorio no incluye archivos de datos.

## Ejecución local

```bash
conda activate geopython
pip install streamlit-folium   # si el ambiente aún no lo tiene
streamlit run app.py
```

## Declaración de uso de asistentes de inteligencia artificial

Se utilizó el asistente **Claude (Anthropic)** comoayuda de orientación en la redacción de la primera versión de `app.py` (funciones de carga con caché, filtros, indicadores, tabla, gráficos de plotly y mapa con streamlit-folium).
También fue de utilidad para resolver los problemas del mapa base de las tareas anteriores (las capas base de CartoDB y de OpenStreetMap exigían llave o bloqueaban el acceso, por lo que se usa la capa de Esri).

El autor declara comprender el funcionamiento de todo el código entregado y estar en capacidad de explicarlo.

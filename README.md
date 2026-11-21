# Sismicidad en Costa Rica (2015-2025): aplicación web interactiva

**Autor:** Bryan Ramírez Coria
**Curso:** GF-0657 Programación en Sistemas de Información Geográfica, II-2026
**Proyecto final, primera entrega**

## Descripción

Aplicación web desarrollada con streamlit para explorar los sismos de magnitud 3.0 o mayor registrados en Costa Rica y sus alrededores entre 2015 y 2025, y su relación con la división cantonal del país. Cada sismo se asigna, mediante una unión espacial, al cantón en que ocurrió; los sismos que ocurren en el mar quedan fuera de todo cantón y se clasifican como marinos.

Con los filtros de la barra lateral (rango de años, magnitud mínima, profundidad máxima, provincia y tipo de sismo), la aplicación actualiza al mismo tiempo los indicadores, un mapa web interactivo, dos gráficos de plotly y una tabla descargable. Continúa el trabajo de las tareas 1, 2 y 3 del curso.

## Aplicación publicada

**Enlace:** [COMPLETAR con la dirección de Streamlit Community Cloud, por ejemplo https://usuario-proyecto-final.streamlit.app]

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

Se utilizó el asistente **Claude (Anthropic)** de la siguiente manera:

- **Generación de código:** redacción de la primera versión de `app.py` (funciones de carga con caché, filtros, indicadores, tabla, gráficos de plotly y mapa con streamlit-folium), a partir del enunciado del proyecto y del código de las tareas 2 y 3, y redacción del `requirements.txt` y de este `README.md`.
- **Depuración:** ayuda para resolver los problemas del mapa base de las tareas anteriores (las capas base de CartoDB y de OpenStreetMap exigían llave o bloqueaban el acceso, por lo que se usa la capa de Esri).
- **Verificación:** [COMPLETAR por el autor: qué se probó, por ejemplo la ejecución con `streamlit run app.py`, `AppTest` y la comparación de la versión publicada con la local].

El autor declara comprender el funcionamiento de todo el código entregado y estar en capacidad de explicarlo.

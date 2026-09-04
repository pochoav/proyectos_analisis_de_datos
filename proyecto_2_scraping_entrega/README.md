# Proyecto 2: Análisis del Mercado de Libros con Scraping

En este proyecto se creó un pipeline de datos que extrae información de una página web (Scraping), limpia la información y genera gráficas útiles conforme a los objetivos de negocio. Esto se hizo con el principal objetivo de evaluar el mercado de libros y dar *insights* acerca de la situación actual.

## Preguntas clave

- ¿Cuántos libros hay en total en el catálogo y cuál es el precio promedio?
- ¿Cuáles son las categorías con los precios promedio más altos y más bajos?
- ¿Qué porcentaje del catálogo cuenta con 5 estrellas de calificación?
- ¿Hay relación entre la calificación del libro y su precio?

## Análisis

Se utilizó la herramienta `scraper.py` (script de Python) para revisar todo el sitio web [Books to Scrape](https://books.toscrape.com) y extraer la información pertinente sobre cada libro (1000 ejemplares).

Posteriormente se analizó la información usando herramientas de Python, para así poder representar gráficamente distintos comportamientos. Se graficaron los precios, las categorías con más libros, el precio promedio, además de un comparativo entre el rating y el precio promedio. A lo largo del documento `notebook_analisis.ipynb` se agregaron pedazos de información pertinente obtenida a raíz del código.

## Ejecución

Para ejecutar el pipeline de datos completo en tu equipo, sigue las siguientes instrucciones:

### 1. Clonar el repositorio

```bash
git clone git@github.com:pochoav/proyecto_2.git
cd proyecto_2
```

### 2. Instalar las librerías necesarias

Este proyecto usa Python 3.x junto con las siguientes librerías:

- `requests`
- `beautifulsoup4`
- `pandas`
- `matplotlib`
- `seaborn`
- `jupyter` / `ipykernel`

Instálalas con:

```bash
pip install requests beautifulsoup4 pandas matplotlib seaborn jupyter ipykernel
```

### 3. Ejecutar el scraper

Desde la raíz del proyecto, corre:

```bash
python src/scraper.py
```

Este script recorre todo el catálogo de Books to Scrape (siguiendo la paginación del sitio), extrae Título, Precio, Rating, Disponibilidad y Categoría de cada uno de los 1000 libros, y guarda el resultado en `data/libros_extraidos.csv`. El proceso tarda un par de minutos, ya que visita tanto las páginas de listado como la página de detalle de cada libro.

### 4. Ejecutar el análisis

Abre `notebook_analisis.ipynb` (por ejemplo, en VSCode o Jupyter Notebook) y ejecuta todas las celdas en orden, de arriba hacia abajo. El notebook:

1. Carga `data/libros_extraidos.csv`.
2. Limpia las columnas `Price` (a número decimal) y `Rating` (a número entero).
3. Valida que no existan valores nulos ni duplicados.
4. Genera las gráficas de distribución de precios, categorías con más libros, precio promedio por categoría, y la comparación entre rating y precio promedio.

## Hallazgos
Tras el análisis dentro de `notebook_analisis.ipynb`, se encontraron piezas clave de información para hacer decisiones de negocio:

1. Hay 1000 libros en el catálogo completo, con precio promedio de £35.07
2. El catálogo tiene  19.6% de libros con 5 estrellas
3. En promedio, el precio de un libro tiende a aumentar conforme sube su calificación
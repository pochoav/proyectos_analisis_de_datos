# Proyecto 1: Ecommerce

Este proyecto se realizó para comprender el estado financiero de la compañía en cuestión y responder ciertas dudas claves.

## Preguntas clave

- ¿Cuál es el Ingreso Total Neto, el volumen de productos vendidos y el Ticket Promedio?
- ¿Cuáles son las 5 categorías de productos más vendidas y las 5 menos rentables?
- ¿Qué región o canal genera mayores ingresos?
- ¿Los descuentos altos están impulsando el volumen de ventas o solo recortando el margen operativo?

## Análisis

Se integró la base de datos en un entorno digital Python para poder entender la información a gran escala.

Se presenta información de ventas por producto, región, por año o por mes.

Las gráficas han sido creadas para apoyar en la visualización de cada celda de código, al igual que las notas explicativas con resultados claros.

## Ejecución

Para ejecutar este proyecto en tu propia computadora, sigue estos pasos:

1. Asegúrate de tener Python 3.x instalado, junto con las siguientes librerías:
   ```
   pip install pandas matplotlib seaborn
   ```
2. Abre la carpeta completa `proyecto_1_ecommerce_entrega/` en tu editor (VS Code, Jupyter, etc.) — es importante abrir la carpeta raíz, no solo el archivo del notebook, para que las rutas relativas a los datos funcionen correctamente.
3. Abre el archivo `notebook_analisis.ipynb`.
4. Ejecuta todas las celdas en orden, de arriba hacia abajo (Kernel > Reiniciar y ejecutar todo, o celda por celda con `Shift + Enter`).
5. Revisa cada gráfico generado junto con sus notas explicativas, ya que cada uno responde a una pregunta clave de negocio distinta.

El notebook lee el archivo `data/dataset_original.csv`, realiza la limpieza correspondiente, y genera automáticamente `data/dataset_limpio.csv` como parte del proceso.
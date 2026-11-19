from pathlib import Path

from graphviz import Digraph

#Ubicación del diagrama
OUTPUT = Path(__file__).resolve().parents[1] / "architecture_diagram"

g = Digraph("pipeline", format="png")
g.attr(
    rankdir="LR", splines="spline", nodesep="0.5", ranksep="0.8",
    fontname="Helvetica", bgcolor="white", pad="0.4", dpi="200", 
    label="Pipeline ELT de calidad del aire: Open-Meteo -> BigQuery -> dbt -> Data Studio\n(orquestado con Apache Airflow)", 
    labelloc="t", fontsize="20",
)
g.attr("node", shape="box", style="rounded,filled", fontname="Helvetica", fontsize="12", margin="0.2,0.12")
g.attr("edge", fontname="Helvetica", fontsize="10", color="#444444")

#Nodos principales
g.node("api", "Open-Meteo API\n\n•Weather (temperatura, humedad)\n• Air Quality (PM2.5, PM10)", fillcolor="#FDE9D9", color="#E36C09")
g.node("script", "Script de Python\nextract_to_warehouse.py\n\n5 ciudades · 192 horas c/u", fillcolor="#DCE6F1", color="#376092")
g.node("looker", "Data Studio\n\nDashboard de 3 páginas\n(alertas OMS · horas pico ·\nclima vs contaminación)", fillcolor="#E4DFEC", color="#60497A")

#Recuadros de Google Cloud y BigQuery
with g.subgraph(name="cluster_gcp") as gcp:
    gcp.attr(label="Google Cloud · BigQuery", style="rounded", color="#4285F4", fontcolor="#4285F4", fontsize="14", fontname="Helvetica")
    with gcp.subgraph(name="cluster_raw") as raw:
        raw.attr(label="dataset air_quality_raw", style="rounded,dashed", color="#7F7F7F", fontsize="11")
        raw.node("raw", "openmeteo_hourly\n(datos crudos)", fillcolor="#EEECE1", color="#7F7F7F")
    with gcp.subgraph(name="cluster_dbt") as dbt:
        dbt.attr(label="dataset air_quality_dbt", style="rounded,dashed", color="#7F7F7F", fontsize="11")
        dbt.node("stg", "staging\nstg_openmeteo_hourly\n(vista)", fillcolor="#E2EFDA", color="#548235")
        dbt.node("marts", "marts (tablas)\n\nmart_air_quality_hourly\nmart_peak_hours\nmart_weather_correlation\nmart_who_exceedances", fillcolor="#E2EFDA", color="#548235")

#Recuadros de Apache Airflow
with g.subgraph(name="cluster_airflow") as af:
    af.attr(label="Apache Airflow · DAG air_quality_elt_pipeline (ejecución manual)",
            style="rounded,dashed", color="#017CEE", fontcolor="#017CEE", fontsize="14")
    af.node("t1", "1. extract_to_warehouse", fillcolor="#FFFFFF", color="#017CEE")
    af.node("t2", "2. dbt run", fillcolor="#FFFFFF", color="#017CEE")
    af.node("t3", "3. dbt test\n(16 pruebas)", fillcolor="#FFFFFF", color="#017CEE")
    af.edge("t1", "t2", color="#017CEE", penwidth="2", minlen="2")
    af.edge("t2", "t3", color="#017CEE", penwidth="2", minlen="1")

#Flujo de información
g.edge("api", "script", label="HTTPS")
g.edge("script", "raw", label="carga (ELT)")
g.edge("raw", "stg", label="dbt")
g.edge("stg", "marts", label="dbt")
g.edge("marts", "looker", label="conector\nBigQuery")

#Orquestración
g.edge("api", "t1", style="invis")  # alinea las tareas bajo el bloque que ejecutan
g.edge("t1", "script", style="dashed", color="#017CEE", constraint="false")
g.edge("t2", "stg", style="dashed", color="#017CEE", constraint="false")
g.edge("t3", "marts", style="dashed", color="#017CEE", constraint="false")

g.render(str(OUTPUT), cleanup=True)
print(f"Diagrama guardado en {OUTPUT}.png")
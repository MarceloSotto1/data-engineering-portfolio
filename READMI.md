# 👋 Hola, soy Marcelo Sotto

**Data Engineer / Analytics Engineer** · Córdoba, Argentina · [LinkedIn](https://www.linkedin.com/in/l-marcelo-sotto/) · [Email](mailto:lmarcelosotto@gmail.com)

Este repositorio reúne proyectos que muestran cómo diseño, construyo y valido pipelines de datos:
ingesta desde APIs y archivos, modelado dimensional, calidad de datos y CI/CD.
Todo corre **gratis y de forma local**, y se puede reproducir con un solo comando.

## 🗂️ Proyectos

| # | Proyecto | Qué demuestra | Stack | Estado |
|---|---|---|---|---|
| 01 | [NYC Taxi & Weather ELT](01-dbt-duckdb-elt) | Ingesta de API y Parquet, modelado dimensional, tests, CI | dbt · DuckDB · Python · GitHub Actions | ✅ |
| 02 | Pipeline batch orquestado | Orquestación, reintentos, idempotencia, backfills | Airflow · Docker · Python | 🔜 |
| 03 | Lakehouse medallion | Arquitectura bronze/silver/gold, cargas incrementales | Databricks · Delta Lake · PySpark | 🔜 |
| 04 | Data platform en la nube | Infraestructura como código, data lake | AWS · Terraform · Athena | 🔜 |

## 🛠️ Stack y habilidades

- **Lenguajes:** SQL (CTEs, window functions), Python
- **Transformación y modelado:** dbt, modelado dimensional (facts / dims)
- **Orquestación:** Airflow *(en progreso)*
- **Datos y nube:** DuckDB, Databricks, AWS *(en progreso)*
- **Calidad y DevOps:** tests de datos, GitHub Actions, Docker, Git

## 🔍 Proyecto destacado: NYC Taxi & Weather

Pipeline ELT con **9,5 millones de viajes reales** y clima horario desde una API.

- Ingesta idempotente desde Parquet y REST
- Modelo estrella con tabla de hechos incremental
- 36 tests genéricos y 2 singulares, más un script de validación con checks automáticos
- CI en GitHub Actions con datos sintéticos

![Linaje del proyecto](01-dbt-duckdb-elt/docs/lineage.png)

👉 [Ver el proyecto completo](01-dbt-duckdb-elt)

## ▶️ Cómo ejecutar un proyecto

Cada carpeta es independiente y tiene su propio README con instrucciones.
Por ejemplo:

```bash
git clone https://github.com/MarceloSotto1/data-engineering-portfolio.git
cd data-engineering-portfolio/01-dbt-duckdb-elt
make setup && source .venv/bin/activate
make run-sample
```

## 📬 Contacto

Estoy abierto a oportunidades como Data Engineer / Analytics Engineer.
Escribime por [LinkedIn](https://www.linkedin.com/in/l-marcelo-sotto/) o a lmarcelosotto@gmail.com.
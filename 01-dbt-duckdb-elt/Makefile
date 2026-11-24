# Uso: make setup && make run-sample   (o)   make setup && make run
START ?= 2024-01
END   ?= 2024-03
DBT    = cd dbt_project && dbt

.PHONY: setup ingest ingest-sample deps build test validate docs serve run run-sample clean

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

ingest:            ## Datos reales: NYC TLC + Open-Meteo
	python ingestion/ingest.py --source real --start $(START) --end $(END)

ingest-sample:     ## Datos sintéticos (offline, rápido, usado en CI)
	python ingestion/ingest.py --source sample --start $(START) --end $(END)

deps:
	$(DBT) deps --profiles-dir .

build:             ## seeds + models + snapshots + tests, en orden de dependencia
	$(DBT) build --profiles-dir . --vars '{data_start_date: "$(START)-01", data_end_date: "$(shell python -c "import datetime as d,sys;y,m=map(int,'$(END)'.split('-'));print(d.date(y+(m==12),m%12+1,1))")"}'

test:
	$(DBT) test --profiles-dir .

validate:          ## Conteos por capa, plausibilidad y checks automáticos
	python ingestion/validate.py

docs:
	$(DBT) docs generate --profiles-dir .

serve: docs
	$(DBT) docs serve --profiles-dir .

run: ingest deps build validate
run-sample: ingest-sample deps build validate

clean:
	rm -rf data/raw data/*.duckdb dbt_project/target dbt_project/dbt_packages

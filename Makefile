install:
	python -m pip install -r requirements.txt

seed:
	cd dbt_loadsmart && dbt seed

run:
	cd dbt_loadsmart && dbt run

test:
	cd dbt_loadsmart && dbt test

build:
	cd dbt_loadsmart && dbt build

docs:
	cd dbt_loadsmart && dbt docs generate

clean:
	cd dbt_loadsmart && dbt clean

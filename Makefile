.PHONY: update analyse

analyse:
	python3 analyse.py

update:
	curl https://www.hetzner.com/_resources/app/data/app/live_data_sb_EUR.json > live_data_sb_EUR.json

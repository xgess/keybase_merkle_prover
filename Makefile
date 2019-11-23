.PHONY: build run shells

IMAGE_NAME=v0_kbhonest

build:
	pipenv lock --requirements > requirements.txt
	docker build -t $(IMAGE_NAME) .

run: build
	docker run --rm -t $(IMAGE_NAME):latest

shell: build
	docker run --rm -ti $(IMAGE_NAME):latest /bin/bash


# this is useful when running locally
kill:
	docker kill `docker ps -a -q --filter ancestor=$(IMAGE_NAME) --format="{{.ID}}"`

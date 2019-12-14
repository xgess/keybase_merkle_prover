.PHONY: build run shell kill setup deploy set_env wipe_env destroy pause logs

ENV_FILE_PATH=./env_file
include $(ENV_FILE_PATH)

build:
	pipenv lock --requirements > requirements.txt
	docker build -t $(IMAGE_NAME) .

run: build
	docker run --rm -t --env-file=$(ENV_FILE_PATH) $(IMAGE_NAME):latest

shell: build
	docker run  --rm -ti --env-file=$(ENV_FILE_PATH) $(IMAGE_NAME):latest /bin/bash

# this is useful when running locally
kill:
	docker kill `docker ps -a -q --filter ancestor=$(IMAGE_NAME) --format="{{.ID}}"`


########## deploying to Fargate ##########

setup: build
	fargate service create $(SERVICE_NAME) \
		--subnet-id $(SUBNET_ID) \
		--security-group-id $(SECURITY_GROUP_ID)

deploy: build
	fargate service deploy $(SERVICE_NAME)
	$(MAKE) set_env
	fargate service scale $(SERVICE_NAME) 1
	@$(MAKE) logs

set_env: wipe_env
	@fargate service env set $(SERVICE_NAME) --env KEYBASE_USERNAME=$(KEYBASE_USERNAME) > /dev/null
	@fargate service env set $(SERVICE_NAME) --env KEYBASE_PAPERKEY="$(KEYBASE_PAPERKEY)" > /dev/null

wipe_env:
	@for env_var in `$(MAKE) list_deployed_env_vars`; do \
		fargate service env unset $(SERVICE_NAME) --key $$env_var; \
	done

list_deployed_env_vars:
	@fargate service env list $(SERVICE_NAME) | awk -F'=' '{print $$1}'

destroy: pause
	fargate service destroy $(SERVICE_NAME)

pause:
	fargate service scale $(SERVICE_NAME) 0

logs:
	fargate service logs $(SERVICE_NAME) --follow

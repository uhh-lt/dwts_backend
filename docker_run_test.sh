#!/bin/bash

docker-compose down -v --remove-orphans
docker-compose up -d
docker-compose exec -T dwts_backend bash /dwts_code/src/start_tests.sh "$@"
docker-compose down -v --remove-orphans

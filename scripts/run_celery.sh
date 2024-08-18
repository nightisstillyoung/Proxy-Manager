#!/bin/bash

if [[ "${1}" == "celery" ]]; then
  celery --app=tasks.tasks:broker worker -l INFO -c "${TASKS}"
elif [[ "${1}" == "flower" ]]; then
  celery --app=tasks.tasks:broker flower
fi
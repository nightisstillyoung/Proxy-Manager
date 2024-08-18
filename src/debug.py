from tasks.manager import *
from tasks.tasks import broker
import json



# inspector = broker.control.inspect()
#
#
# for worker, tasks in active_tasks.items():
#     print(worker)
#     print(len(tasks))
#     print("==============================")
#
#
# for worker, tasks in inspector.registered_tasks().items():
#     print(worker)
#     print(len(tasks))
#     print("==============================")
#
#
# for worker, tasks in inspector.reserved().items():
#     print(worker)
#     print(len(tasks))
#     print("==============================")
#
#
# def scheduled_now() -> int:
#     tasks_tot: int = 0
#
#     for worker, tasks in inspector.active().items():
#         tasks_tot += len(tasks)
#
#     for worker, tasks in inspector.reserved().items():
#         tasks_tot += len(tasks)
#
#     return tasks_tot
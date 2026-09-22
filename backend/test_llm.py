from app.orchestration.planner import Planner

planner = Planner()

plan = planner.create_plan(
    "Build or make a pyramid with '*' in python"
)

for task in plan.tasks:
    print()
    print("ID:", task.id)
    print("Title:", task.title)
    print("Capability:", task.required_capability)
    print("Dependencies:", task.dependencies)
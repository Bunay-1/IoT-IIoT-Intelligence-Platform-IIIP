import random

from fastapi import FastAPI

app = FastAPI()

# Mock data for human cognitive load monitoring
operators = ["operator1", "operator2", "operator3"]
cognitive_loads = {
    "operator1": {"stress_level": 60, "fatigue_level": 70},
    "operator2": {"stress_level": 50, "fatigue_level": 60},
    "operator3": {"stress_level": 70, "fatigue_level": 50},
}


@app.get("/cognitive_load/{ operator_id}")
async def get_cognitive_load(operator_id: str):
    if operator_id in cognitive_loads:
        return {"operator": operator_id, "cognitive_load": cognitive_loads[operator_id]}
    else:
        return {"error": "Operator not found"}


# Example endpoint
@app.get("/")
async def root():
    return {"message": "Human Cognitive Load Monitor"}

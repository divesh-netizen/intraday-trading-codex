from fastapi import APIRouter

from app.main import state
from app.models import AlgoConfig

router = APIRouter(prefix="/algos", tags=["algos"])


@router.get("")
def list_algos():
    return state.algo_manager.list()


@router.post("")
def upsert_algo(config: AlgoConfig):
    state.algo_manager.add(config)
    return {"status": "saved", "algo": config.name}


@router.post("/{name}/pause")
def pause_algo(name: str):
    state.algo_manager.toggle(name, True)
    return {"status": "paused", "algo": name}


@router.post("/{name}/resume")
def resume_algo(name: str):
    state.algo_manager.toggle(name, False)
    return {"status": "running", "algo": name}

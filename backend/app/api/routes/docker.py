from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user

router = APIRouter(prefix="/docker", tags=["docker"], dependencies=[Depends(get_current_user)])


@router.get("/containers")
def containers(stats: bool = True):
    from app.services.docker_service import DockerUnavailable, list_containers

    try:
        return {"available": True, "containers": list_containers(with_stats=stats)}
    except DockerUnavailable as exc:
        return {"available": False, "error": str(exc), "containers": []}


@router.get("/ping")
def docker_ping():
    from app.services.docker_service import ping

    if not ping():
        raise HTTPException(503, "Docker Engine injoignable")
    return {"ok": True}

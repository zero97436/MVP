"""Check `kubernetes` : état d'un cluster via l'API server (token Bearer).

config_json :
  - api_url    : https://cluster:6443 (ou l'IP de l'API server)
  - token      : ServiceAccount token (lecture seule recommandée)
  - verify_ssl : true/false (défaut false — CA interne)
  - mode       : "nodes" (défaut) | "pods" | "deployment"
  - namespace  : pour pods/deployment (défaut "default")
  - name       : nom du deployment (mode deployment)

Statuts :
  - nodes      : CRITICAL si un node NotReady, OK sinon
  - pods       : CRITICAL si pods Failed/CrashLoopBackOff, WARNING si Pending
  - deployment : CRITICAL si 0 replica prêt, WARNING si incomplet, OK si tous prêts
"""
import httpx

from app.checks.base import BaseCheck, CheckContext, CheckResultData
from app.models.enums import CheckStatus

BAD_REASONS = {"CrashLoopBackOff", "ImagePullBackOff", "ErrImagePull", "OOMKilled"}


def _fetch_json(url: str, token: str, verify: bool, timeout: int) -> dict:
    """Isolé pour être mockable en test."""
    r = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, verify=verify, timeout=timeout)
    r.raise_for_status()
    return r.json()


class KubernetesCheck(BaseCheck):
    type = "kubernetes"

    def run(self, ctx: CheckContext) -> CheckResultData:
        api = (ctx.config.get("api_url") or "").rstrip("/")
        token = ctx.config.get("token", "")
        if not api or not token:
            return CheckResultData(status=CheckStatus.UNKNOWN, message="config api_url + token requis")
        verify = bool(ctx.config.get("verify_ssl", False))
        mode = ctx.config.get("mode", "nodes")
        ns = ctx.config.get("namespace", "default")

        try:
            if mode == "nodes":
                return self._nodes(_fetch_json(f"{api}/api/v1/nodes", token, verify, ctx.timeout_seconds))
            if mode == "pods":
                data = _fetch_json(f"{api}/api/v1/namespaces/{ns}/pods", token, verify, ctx.timeout_seconds)
                return self._pods(data, ns)
            if mode == "deployment":
                name = ctx.config.get("name", "")
                if not name:
                    return CheckResultData(status=CheckStatus.UNKNOWN, message="config 'name' requise (deployment)")
                data = _fetch_json(
                    f"{api}/apis/apps/v1/namespaces/{ns}/deployments/{name}", token, verify, ctx.timeout_seconds
                )
                return self._deployment(data, ns)
            return CheckResultData(status=CheckStatus.UNKNOWN, message=f"mode inconnu : {mode}")
        except httpx.HTTPStatusError as exc:
            return CheckResultData(
                status=CheckStatus.CRITICAL,
                message=f"API Kubernetes : HTTP {exc.response.status_code}",
            )
        except Exception as exc:  # noqa: BLE001
            return CheckResultData(
                status=CheckStatus.CRITICAL, message=f"API Kubernetes injoignable : {str(exc)[:100]}"
            )

    def _nodes(self, data: dict) -> CheckResultData:
        items = data.get("items", [])
        not_ready = []
        for node in items:
            conds = {c["type"]: c["status"] for c in node.get("status", {}).get("conditions", [])}
            if conds.get("Ready") != "True":
                not_ready.append(node["metadata"]["name"])
        total = len(items)
        perf = {"nodes": total, "not_ready": len(not_ready)}
        if not_ready:
            return CheckResultData(
                status=CheckStatus.CRITICAL, value=float(total - len(not_ready)), perfdata=perf,
                message=f"{len(not_ready)} node(s) NotReady : {', '.join(not_ready[:5])}",
            )
        return CheckResultData(
            status=CheckStatus.OK, value=float(total), perfdata=perf,
            message=f"{total} node(s) Ready",
        )

    def _pods(self, data: dict, ns: str) -> CheckResultData:
        items = data.get("items", [])
        failed, pending = [], []
        for pod in items:
            phase = pod.get("status", {}).get("phase", "")
            name = pod["metadata"]["name"]
            waiting = [
                (c.get("state", {}).get("waiting") or {}).get("reason", "")
                for c in pod.get("status", {}).get("containerStatuses", [])
            ]
            if phase == "Failed" or any(w in BAD_REASONS for w in waiting):
                failed.append(name)
            elif phase == "Pending":
                pending.append(name)
        perf = {"pods": len(items), "failed": len(failed), "pending": len(pending)}
        if failed:
            return CheckResultData(
                status=CheckStatus.CRITICAL, perfdata=perf,
                message=f"[{ns}] {len(failed)} pod(s) en échec : {', '.join(failed[:5])}",
            )
        if pending:
            return CheckResultData(
                status=CheckStatus.WARNING, perfdata=perf,
                message=f"[{ns}] {len(pending)} pod(s) Pending : {', '.join(pending[:5])}",
            )
        return CheckResultData(
            status=CheckStatus.OK, value=float(len(items)), perfdata=perf,
            message=f"[{ns}] {len(items)} pod(s) sains",
        )

    def _deployment(self, data: dict, ns: str) -> CheckResultData:
        name = data.get("metadata", {}).get("name", "?")
        spec = data.get("spec", {}).get("replicas", 0) or 0
        ready = data.get("status", {}).get("readyReplicas", 0) or 0
        perf = {"replicas": spec, "ready": ready}
        if spec and ready == 0:
            status = CheckStatus.CRITICAL
        elif ready < spec:
            status = CheckStatus.WARNING
        else:
            status = CheckStatus.OK
        return CheckResultData(
            status=status, value=float(ready), perfdata=perf,
            message=f"[{ns}] {name} : {ready}/{spec} replica(s) prêt(s)",
        )

import json
import urllib.error
import urllib.request

from app.config import settings


def notify_report_ready(
    *,
    report_id: str,
    dataset_id: str,
    file_name: str,
    authorization: str | None,
) -> dict:

    if not authorization:
        raise RuntimeError(
            "Authorization header is unavailable."
        )

    url = (
        settings.notification_service_url.rstrip("/")
        + "/notifications/report-ready"
    )

    payload = {
        "report_id": report_id,
        "dataset_id": dataset_id,
        "file_name": file_name,
    }

    body = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=body,
        method="POST",
        headers={
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=15,
        ) as response:

            response_body = (
                response.read()
                .decode("utf-8")
            )

            if not response_body:
                return {
                    "status": response.status
                }

            return json.loads(
                response_body
            )

    except urllib.error.HTTPError as exc:

        error_body = (
            exc.read()
            .decode(
                "utf-8",
                errors="replace",
            )
        )

        raise RuntimeError(
            "Notification Service returned "
            f"HTTP {exc.code}: "
            f"{error_body}"
        ) from exc

    except urllib.error.URLError as exc:

        raise RuntimeError(
            "Unable to connect to "
            f"Notification Service: "
            f"{exc.reason}"
        ) from exc

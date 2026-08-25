import httpx

from fastapi import HTTPException, Request
from fastapi.responses import Response

from app.config import settings


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


async def proxy_request(
    request: Request,
    target_url: str,
):
    body = await request.body()

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }

    query = request.url.query

    if query:
        target_url = f"{target_url}?{query}"

    try:
        async with httpx.AsyncClient(
            timeout=settings.request_timeout,
            follow_redirects=True,
        ) as client:

            upstream = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Target service is unavailable.",
        )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Target service request timed out.",
        )

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gateway communication error: {exc}",
        )

    response_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get(
            "content-type"
        ),
    )

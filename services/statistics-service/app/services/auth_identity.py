import httpx

from fastapi import HTTPException


AUTH_SERVICE_URL = (
    "http://auth-service:8001"
)


async def get_authenticated_user(
    authorization: str,
):
    async with httpx.AsyncClient(
        timeout=20.0,
    ) as client:

        response = await client.get(
            (
                f"{AUTH_SERVICE_URL}"
                f"/auth/me"
            ),
            headers={
                "Authorization":
                    authorization,
            },
        )


    if response.status_code != 200:

        raise HTTPException(
            status_code=401,
            detail=(
                "Unable to identify "
                "authenticated user."
            ),
        )


    payload = response.json()


    user_id = (
        payload.get(
            "id"
        )
        or
        payload.get(
            "user_id"
        )
        or
        payload.get(
            "_id"
        )
    )


    if not user_id:

        raise HTTPException(
            status_code=401,
            detail=(
                "Authenticated user "
                "identifier was not returned."
            ),
        )


    return {
        "user_id":
            str(
                user_id
            ),

        "email":
            payload.get(
                "email"
            ),

        "username":
            payload.get(
                "username"
            ),
    }

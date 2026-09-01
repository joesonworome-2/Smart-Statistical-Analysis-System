from typing import Any

from pydantic import BaseModel, Field


class StatisticalResultSaveRequest(
    BaseModel
):
    dataset_id: str

    dataset_name: str | None = None

    method: str

    title: str

    configuration: dict[
        str,
        Any
    ] = Field(
        default_factory=dict
    )

    tables: list[
        dict[
            str,
            Any
        ]
    ] = Field(
        default_factory=list
    )

    assumptions: (
        dict[
            str,
            Any
        ]
        |
        list[
            dict[
                str,
                Any
            ]
        ]
        |
        None
    ) = None

    interpretation: str | None = None

    apa: str | None = None

    metadata: dict[
        str,
        Any
    ] = Field(
        default_factory=dict
    )

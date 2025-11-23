import time
import pathlib

import docker
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import validate_call

from api.config import config
from api.logger import logger

from .schemas import MinerInput, MinerOutput, DetectionResultPM
from . import utils as ch_utils


# Define source directory - the root of the project
_src_dir = pathlib.Path(__file__).parent.parent.parent.parent.resolve()


def get_task() -> MinerInput:
    """Return a new challenge task."""

    return MinerInput()


@validate_call
def score(request_id: str, miner_output: MinerOutput) -> float:

    _score = 0.0

    # Copy the detection script to the templates directory
    _detections_dir = str(_src_dir / "templates" / "static" / "detections")

    ch_utils.copy_detection_files(
        miner_output=miner_output,
        detections_dir=_detections_dir,
    )

    # Generate a randomized sequence of frameworks to test against
    _target_frameworks = ch_utils.gen_framework_sequence()
    _docker_client = docker.from_env()

    for _index, _framework in enumerate(_target_frameworks):
        _framework_name = _framework.name
        _framework_image = _framework.image
        logger.info(f"[{request_id}] - Running detection against {_framework_name}...")

        _start_time = time.time()
        ch_utils.run_bot_container(
            docker_client=_docker_client,
            container_name=f"{_framework_name}",
            network_name=f"local_network",
            image_name=_framework_image,
            ulimit=config.challenge.docker_ulimit,
        )
        _end_time = time.time()
        _execution_time = _end_time - _start_time

        logger.info(f"[{request_id}] - Calculating score from detection results...")

    return _score


@validate_call(config={"arbitrary_types_allowed": True})
def get_web(request: Request) -> HTMLResponse:
    templates = Jinja2Templates(directory=str(_src_dir / "templates"))
    _abs_result_endpoint = str(config.challenge.result_endpoint)

    html_response = templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"abs_result_endpoint": _abs_result_endpoint},
    )
    return html_response


@validate_call
def set_result(
    request_id: str, order_id: int, detection_result: DetectionResultPM
) -> None:

    logger.info(f"[{request_id}] - Setting detection result...")

    logger.success(f"[{request_id}] - Successfully set detection result.")
    return


__all__ = [
    "get_task",
    "score",
    "get_web",
    "set_result",
]

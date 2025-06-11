import logging


def setup_logger():
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler("info.log", "a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        datefmt="%Y-%m-%d %H:%M:%S",
        fmt="[%(asctime)s.%(msecs)03d] %(filename)18s:%(lineno)-3d %(levelname)-8s - %(message)s"
    )

    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    return log


logger = setup_logger()

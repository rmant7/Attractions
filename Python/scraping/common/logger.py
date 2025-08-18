import logging


def create_logger(name, filepath, console_logging=True):
    logFormatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)8s] %(message)s", datefmt="%d-%b-%Y %H:%M:%S"
    )
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    fileHandler = logging.FileHandler(filename=filepath, mode="a")
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    if console_logging:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        logger.addHandler(consoleHandler)

    return logger


kiwi_logger = create_logger('kiwi_logger', './kiwi.log')

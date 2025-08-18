import argparse
import logging
from pathlib import Path


class FuncException(Exception):
    pass

class NoBodyException(Exception):
    pass


# logging parameters set up and create logger
def logger_setup(name):
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # create file handler which logs even debug messages
    log_handler_file = logging.FileHandler(f'{name}.log', 'w')
    log_handler_file.setLevel(logging.DEBUG)
    
    # create console handler
    # log_handler_console = logging.StreamHandler()
    # log_handler_console.setLevel(logging.ERROR)
    
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
    log_handler_file.setFormatter(formatter)
    # log_handler_console.setFormatter(formatter)
    
    # add the handlers to the logger
    logger.addHandler(log_handler_file)
    # logger.addHandler(log_handler_console)
    
    return logger


logger = logger_setup(f'{Path(__file__).stem}')

# counters
inserted, modified, passed = 0, 0, 0


def insert_metrika(metrika: bytes, page: bytes, file_path: str) -> bytes:
    global inserted; global modified; global passed
    start_comment = b'<!-- Yandex.Metrika counter -->'
    end_comment = b'<!-- /Yandex.Metrika counter -->'
    try:
        body_tag_position = page.rfind(b'</body>')
        if body_tag_position == -1:
            raise NoBodyException(f'{file_path} - Does not contain body tag, insertion failed')
        
        start_position = page.find(start_comment)
        end_position = page.find(end_comment, start_position + len(start_comment))
        
        if start_position != -1 and end_position != -1:
            # Extract the array of bytes between the comments
            extracted_bytes = page[start_position:end_position + len(end_comment)]
            # Compare the extracted bytes with the metrika bytes
            if extracted_bytes == metrika:
                logger.info(f'{file_path} - passed')
                passed += 1
                return page
            # Replace the extracted bytes with the metrika bytes
            modified_page = page[:start_position] + metrika + page[end_position + len(end_comment):]
            logger.info(f'{file_path} - modified')
            modified += 1
            return modified_page
        else:
            inserted_page = page[:body_tag_position] + metrika + b'\n' + page[body_tag_position:]
            logger.info(f'{file_path} - inserted')
            inserted += 1
            return inserted_page
        
    except NoBodyException as err:
        logger.error(err)
        raise FuncException from err
    except Exception as err:
        logger.error(f'{file_path} - {type(err).__name__}: {err}')
        raise FuncException from err


def main(metrika_path: str, target_path: str) -> None:
    metrika_obj, target_obj = map(Path, (metrika_path, target_path))
    try:
        if not metrika_obj.is_file():
            raise Exception(f'Wrong path you provided: "{metrika_path}"')
        if not target_obj.is_dir():
            raise Exception(f'Wrong path you provided: "{target_path}"')
        
        with open(metrika_obj, 'rb') as bf:
            metrika = bf.read()
        
        logger.info(f'Process started...')
        saved, errors, total = 0, 0, 0
        for file_path in target_obj.rglob('*.html'):
            total += 1
            try:
                with open(file_path, 'rb') as binary_file:
                    page = binary_file.read()
                       
                modified_page = insert_metrika(metrika, page, file_path.relative_to(target_path))

                with open(file_path, 'wb') as binary_file:
                    binary_file.write(modified_page)
                    saved += 1
            except FuncException:
                errors += 1
                continue
            except Exception as err:
                errors += 1
                logger.error(f'{file_path.relative_to(target_path)} - {type(err).__name__}: {err}')
                continue
        logger.info(f'Process completed...SUCCESS: inserted={inserted}, modified={modified}, passed={passed}, '
                    f'saved={saved}, errors={errors}, total={total}')
            
    except Exception as err:
        logger.error(f'{type(err).__name__}: {err}')
        logger.info(f'Processing completed...FAIL')
    

if __name__ == '__main__':
    metrika_path = 'yandex_metrika.html'
    target = '.'
    parser = argparse.ArgumentParser(description="Inserts the metrika html block into the body of html page")
    parser.add_argument('-m', type=str, default=metrika_path, help=f'Path to the metrika html file, by default, "{metrika_path}"')
    parser.add_argument('-t', type=str, default=target, help=f'Path to the target folder stores html files, by default, "{target}"')
    args = parser.parse_args()
    
    main(args.m, args.t)
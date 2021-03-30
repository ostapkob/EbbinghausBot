# import logging
from datetime import timedelta
from loguru import logger
token = "1597142066:AAFyj8hBQngSqd3KGAyBqcXyTQSOMGZ5_FY"

intervals = {1: timedelta(minutes=5),
            2: timedelta(minutes= 25),
            3: timedelta(hours=8),
            4: timedelta(hours=24),
            5: timedelta(weeks=2),
            6: timedelta(weeks=8),
            7: timedelta(weeks=8),
            } 

arguments = {"keywords": "",
            "limit":7,
            "format": "jpg",
            "size": ">400*300",
            "print_urls":True,
            "no_download": True,
            # "silent_mode": True,
            } 
# logging.basicConfig(level=logging.DEBUG,
#                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger()
# logger.setLevel(logging.INFO)

db_config = {"HOST" : 'mongodb://localhost:27017',
             "DB": 'EbbinghausBot',
             "colection": 'users',
            }
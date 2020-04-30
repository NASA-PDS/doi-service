import os
import logging
import pandas as pd

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

input_file = os.path.join(os.path.dirname(__file__), 'data', 'example-2020-04-29.xlsx')
input_df = pd.read_excel(input_file)

for index, row in input_df.iterrows():
    logger.info(row)
    logger.info(row['status'])
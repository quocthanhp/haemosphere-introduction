import os
import traceback
from os import listdir
from os.path import isfile, join
import genedataset
import pandas
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
counter = 0
string_dataset = " "
print_read_files = []

# Extracting the Project Root, adding data files and checking if it exists
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = ROOT_DIR + "/data/datasets/F0r3sT/PUBLIC"
if os.path.exists(file_path):
    pass
else:
    print("No Data Directory Found")

# Produce List of Files in the Directory
list_files = []
for file in os.listdir(file_path):
    if file.endswith('h5'):
        list_files.append(file)

# Extracting the keys of the data files and selecting the key[1] particularly to read the data and see if there is an
# exception in reading the data files
for x in range(len(list_files)):
    with pandas.HDFStore(file_path + "/" + list_files[x]) as hdf:
        string_dataset = hdf.keys()
    try:
        print(pandas.read_hdf(file_path + "/" + list_files[x], string_dataset[1]))
        counter += 1
        print_read_files.append(list_files[x] + " read successfully")
    except Exception as ex:
        print("Error at reading", list_files[x])
        logger.exception(ex)
        logger.debug(traceback.format_exc())

if counter != len(list_files):
    print("There is an error in reading some of the data files")
else:
    print("Read Successful")
print("\n".join(print_read_files))
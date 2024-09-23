import os
from .models.hsdataset import HSDataset 
from .models.hsgeneset import HSGeneset
from .models.object_enums import ObjectTypeEnum
from concurrent.futures import ThreadPoolExecutor

object_type_map = {
    ObjectTypeEnum.HSDATASET: HSDataset,
    ObjectTypeEnum.HSGENESET: HSGeneset
}

# def load_dataset(ObjectType, pathToHDF):
#     ObjectType(pathToHDF)

# def preload_datasets(data_directory, object_type, max_workers=4):
#     ObjectType = object_type_map.get(object_type)
    
#     if ObjectType is None:
#         raise ValueError(f"Unknown ObjectType: {object_type}")

#     # List all the dataset files
#     dataset_files = [os.path.join(data_directory, f) for f in os.listdir(data_directory) if f.endswith(".h5")]

#     # Parallelize the loading of datasets
#     with ThreadPoolExecutor(max_workers=max_workers) as executor:
#         executor.map(lambda path: load_dataset(ObjectType, path), dataset_files)


def preload_datasets(data_directory, object_type):
    ObjectType = object_type_map.get(object_type)
    
    if ObjectType is None:
        raise ValueError(f"Unknown ObjectType: {object_type}")

    for filename in os.listdir(data_directory):
        if filename.endswith(".h5"):
            pathToHDF = os.path.join(data_directory, filename)
            ObjectType(pathToHDF)

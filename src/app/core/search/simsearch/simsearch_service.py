from enum import Enum

from app.util.singleton_meta import SingletonMeta

from loguru import logger

class IndexType(str, Enum):
    text = "text"
    image = "image"
    multimodal = "multimodal"



class SimSearchService(metaclass=SingletonMeta):

    def __new__(cls, *args, **kwargs):

        if kwargs["remove_all_indices"] if "remove_all_indices" in kwargs else False:
            logger.warning("Removing all SimSearch indices!")

        return super(SimSearchService, cls).__new__(cls)

    def __load_indices(self):
        faiss.read_index(idx_path)
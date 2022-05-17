from typing import Tuple, Union, List

from loguru import logger
from transformers import CLIPProcessor, CLIPModel

from app.core.data.repo.repo_service import RepoService
from app.core.db.sql_service import SQLService
from app.docprepro.celery.celery_worker import celery_prepro_worker
from app.docprepro.image import PreProImageDoc
from app.docprepro.text.preprotextdoc import PreProTextDoc
from config import conf

sql = SQLService(echo=False)
repo = RepoService()


def _load_clip_model() -> Tuple[CLIPModel, CLIPProcessor]:
    logger.info(f"Loading CLIP model {conf.docprepro.mmsimsearch.default_clip_model}...")
    model = CLIPModel.from_pretrained(conf.docprepro.mmsimsearch.default_clip_model)
    model.eval()
    processor = CLIPProcessor.from_pretrained(conf.docprepro.mmsimsearch.default_clip_model)
    logger.info(f"Loading CLIP model {conf.docprepro.mmsimsearch.default_clip_model}... Done!")
    return model, processor


model, processor = _load_clip_model()


@celery_prepro_worker.task(acks_late=True)
def compute_clip_embeddings(ppds: List[Union[PreProImageDoc, PreProTextDoc]]) -> None:
    raise NotImplementedError

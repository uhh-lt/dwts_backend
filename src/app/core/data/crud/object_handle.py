from typing import Union, Optional

from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.data.crud.annotation_document import crud_adoc
from app.core.data.crud.code import crud_code
from app.core.data.crud.crud_base import CRUDBase, NoSuchElementError
from app.core.data.crud.current_code import crud_current_code
from app.core.data.crud.document_tag import crud_document_tag
from app.core.data.crud.project import crud_project
from app.core.data.crud.source_document import crud_sdoc
from app.core.data.crud.source_document_metadata import crud_sdoc_meta
from app.core.data.crud.span_annotation import crud_span_anno
from app.core.data.crud.span_group import crud_span_group
from app.core.data.crud.user import crud_user
from app.core.data.dto.object_handle import ObjectHandleCreate
from app.core.data.orm.action import ActionORM, ActionTargetORM
from app.core.data.orm.annotation_document import AnnotationDocumentORM
from app.core.data.orm.code import CodeORM, CurrentCodeORM
from app.core.data.orm.document_tag import DocumentTagORM
from app.core.data.orm.filter import FilterORM
from app.core.data.orm.object_handle import ObjectHandleORM
from app.core.data.orm.project import ProjectORM
from app.core.data.orm.query import QueryORM
from app.core.data.orm.source_document import SourceDocumentORM, SourceDocumentMetadataORM
from app.core.data.orm.span_annotation import SpanAnnotationORM
from app.core.data.orm.span_group import SpanGroupORM
from app.core.data.orm.user import UserORM
from app.core.db.sql_service import SQLService


class CRUDObjectHandle(CRUDBase[ObjectHandleORM, ObjectHandleCreate, None]):
    __obj_id_crud_map = {
        "action_id": None,
        "action_target_id": None,
        "annotation_document_id": crud_adoc,
        "code_id": crud_code,
        "current_code_id": crud_current_code,
        "document_tag_id": crud_document_tag,
        "filter_id": None,
        "project_id": crud_project,
        "query_id": None,
        "source_document_id": crud_sdoc,
        "source_document_metadata_id": crud_sdoc_meta,
        "span_annotation_id": crud_span_anno,
        "span_group_id": crud_span_group,
        "user_id": crud_user
    }

    __obj_id_orm_type_map = {
        "action_id": ActionORM,
        "action_target_id": ActionTargetORM,
        "annotation_document_id": AnnotationDocumentORM,
        "code_id": CodeORM,
        "current_code_id": CurrentCodeORM,
        "document_tag_id": DocumentTagORM,
        "filter_id": FilterORM,
        "query_id": QueryORM,
        "project_id": ProjectORM,
        "source_document_id": SourceDocumentORM,
        "source_document_metadata_id": SourceDocumentMetadataORM,
        "span_annotation_id": SpanAnnotationORM,
        "span_group_id": SpanGroupORM,
        "user_id": UserORM
    }

    def create(self, db: Session, *, create_dto: ObjectHandleCreate) -> ObjectHandleORM:
        try:
            super().create(db=db, create_dto=create_dto)
        except IntegrityError as e:
            # Flo: return existing OH when UC constraint fails
            if type(e.orig) == UniqueViolation:
                db.close()  # Flo: close the session because we have to start a new transaction
                with SQLService().db_session() as sess:
                    for (obj_id_key, obj_id_val) in create_dto.dict().items():
                        if obj_id_val:
                            return self.read_by_attached_object_id(db=sess,
                                                                   obj_id_key=obj_id_key,
                                                                   obj_id_val=obj_id_val)
            else:
                # Flo: re-raise Exception since it's not a UC Violation
                raise e

    def read_by_attached_object_id(self,
                                   db: Session,
                                   obj_id_key: str,
                                   obj_id_val: int) -> Optional[ObjectHandleORM]:
        if obj_id_key not in self.__obj_id_orm_type_map.keys():
            raise ValueError("Unknown Object ID!")

        obj_type = self.__obj_id_orm_type_map[obj_id_key]

        db_obj = db.query(self.model).filter(getattr(self.model, obj_id_key) == obj_id_val).first()
        if not db_obj:
            raise NoSuchElementError(obj_type, id=obj_id_val)
        return db_obj

    def resolve_handled_object(self, db: Session, handle: ObjectHandleORM) -> Union[ActionORM,
                                                                                    ActionTargetORM,
                                                                                    AnnotationDocumentORM,
                                                                                    CodeORM,
                                                                                    CurrentCodeORM,
                                                                                    DocumentTagORM,
                                                                                    FilterORM,
                                                                                    QueryORM,
                                                                                    ProjectORM,
                                                                                    SourceDocumentORM,
                                                                                    SourceDocumentMetadataORM,
                                                                                    SpanAnnotationORM,
                                                                                    SpanGroupORM,
                                                                                    UserORM,
                                                                                    None]:

        for target_id in self.__obj_id_crud_map.keys():
            if getattr(handle, target_id):
                return self.__obj_id_crud_map[target_id].read(db=db, id=getattr(handle, target_id))


crud_object_handle = CRUDObjectHandle(ObjectHandleORM)

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.orm.orm_base import ORMBase


class SpanAnnotationORM(ORMBase):
    id = Column(Integer, primary_key=True, index=True)
    begin = Column(Integer, nullable=False, index=True)
    end = Column(Integer, nullable=False, index=True)

    # one to one
    object_handle = relationship("ObjectHandleORM",
                                 uselist=False,
                                 back_populates="span_annotation",
                                 cascade="all, delete",
                                 passive_deletes=True)

    # many to one
    current_code_id = Column(Integer, ForeignKey('currentcode.id', ondelete="CASCADE"), index=True)
    current_code = relationship("UserORM", back_populates="span_annotations")

    annotation_document_id = Column(Integer, ForeignKey('annotationdocument.id', ondelete="CASCADE"), index=True)
    annotation_document = relationship("AnnotationDocumentORM", back_populates="span_annotations")

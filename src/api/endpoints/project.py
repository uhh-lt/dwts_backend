from typing import List, Dict
from typing import Optional

# noinspection PyUnresolvedReferences,PyProtectedMember
from celery import Signature
from fastapi import APIRouter, Depends, UploadFile, HTTPException, File, Query
from sqlalchemy.orm import Session

from api.dependencies import skip_limit_params, get_db_session
from app.core.data.crud.code import crud_code
from app.core.data.crud.document_tag import crud_document_tag
from app.core.data.crud.memo import crud_memo
from app.core.data.crud.project import crud_project
from app.core.data.crud.source_document import crud_sdoc
from app.core.data.dto import ProjectRead, ProjectCreate, ProjectUpdate
from app.core.data.dto.code import CodeRead
from app.core.data.dto.document_tag import DocumentTagRead
from app.core.data.dto.memo import MemoInDB, MemoCreate, AttachedObjectType, MemoRead
from app.core.data.dto.source_document import SourceDocumentRead
from app.core.data.dto.user import UserRead

router = APIRouter(prefix="/project")
tags = ["project"]


@router.put("", tags=tags,
            response_model=ProjectRead,
            summary="Creates a new Project",
            description="Creates a new Project.")
async def create_new_project(*,
                             db: Session = Depends(get_db_session),
                             proj: ProjectCreate) -> ProjectRead:
    db_obj = crud_project.create(db=db, create_dto=proj)
    return ProjectRead.from_orm(db_obj)


@router.get("", tags=tags,
            response_model=List[ProjectRead],
            summary="Returns all Projects of the current user",
            description="Returns all Projects of the current user")
async def read_all(*,
                   db: Session = Depends(get_db_session),
                   skip_limit: Dict[str, str] = Depends(skip_limit_params)) -> List[ProjectRead]:
    # TODO Flo: only return the projects of the current user
    db_objs = crud_project.read_multi(db=db, **skip_limit)
    return [ProjectRead.from_orm(proj) for proj in db_objs]


@router.get("/{proj_id}", tags=tags,
            response_model=Optional[ProjectRead],
            summary="Returns the Project with the given ID",
            description="Returns the Project with the given ID if it exists")
async def read_project(*,
                       db: Session = Depends(get_db_session),
                       proj_id: int) -> Optional[ProjectRead]:
    # TODO Flo: only if the user has access?
    db_obj = crud_project.read(db=db, id=proj_id)
    return ProjectRead.from_orm(db_obj)


@router.patch("/{proj_id}", tags=tags,
              response_model=ProjectRead,
              summary="Updates the Project",
              description="Updates the Project with the given ID.")
async def update_project(*,
                         db: Session = Depends(get_db_session),
                         proj_id: int,
                         proj: ProjectUpdate) -> ProjectRead:
    # TODO Flo: only if the user has access?
    db_obj = crud_project.update(db=db, id=proj_id, update_dto=proj)
    return ProjectRead.from_orm(db_obj)


@router.delete("/{proj_id}", tags=tags,
               response_model=ProjectRead,
               summary="Removes the Project",
               description="Removes the Project with the given ID.")
async def delete_project(*,
                         db: Session = Depends(get_db_session),
                         proj_id: int) -> ProjectRead:
    # TODO Flo: only if the user has access?
    db_obj = crud_project.remove(db=db, id=proj_id)
    return ProjectRead.from_orm(db_obj)


@router.get("/{proj_id}/sdoc", tags=tags,
            response_model=List[SourceDocumentRead],
            summary="Returns all SourceDocuments of the Project that match the query parameters",
            description="Returns all SourceDocuments of the Project with the given ID that match the query parameters")
async def get_project_sdocs(*,
                            proj_id: int,
                            db: Session = Depends(get_db_session),
                            tag_ids: Optional[List[int]] = Query(title="DocumentTag IDs",
                                                                 description="List of DocumentTag IDs",
                                                                 default=None),
                            all_tags: Optional[bool] = Query(title="All or Any DocumentTags",
                                                             description=("If true return SourceDocuments tagged with"
                                                                          " all DocumentTags, or any DocumentTag "
                                                                          "otherwise"),
                                                             default=False)) -> List[SourceDocumentRead]:
    # TODO Flo: only if the user has access?
    if tag_ids is not None:
        sdocs = crud_sdoc.read_by_project_and_document_tags(db=db, proj_id=proj_id, tag_ids=tag_ids, all_tags=all_tags)
    else:
        sdocs = crud_project.read(db=db, id=proj_id).source_documents

    return [SourceDocumentRead.from_orm(sdoc) for sdoc in sdocs]


@router.put("/{proj_id}/sdoc", tags=tags,
            response_model=str,
            summary="Uploads one or multiple SourceDocument to the Project",
            description="Uploads one or multiple SourceDocument to the Project with the given ID if it exists")
# Flo: Since we're uploading a file we have to use multipart/form-data directly in the router method
#  see: https://fastapi.tiangolo.com/tutorial/request-forms-and-files/
#  see: https://fastapi.tiangolo.com/tutorial/request-files/#multiple-file-uploads-with-additional-metadata
async def upload_project_sdoc(*,
                              proj_id: int,
                              doc_files: List[UploadFile] = File(...,
                                                                 description=("File(s) that get uploaded and "
                                                                              "represented by the SourceDocument(s)"))) \
        -> str:
    # TODO Flo: only if the user has access?

    import_uploaded_document = "app.docprepro.process.import_uploaded_document"
    generate_automatic_annotations = "app.docprepro.process.generate_automatic_annotations"
    persist_automatic_annotations = "app.docprepro.process.persist_automatic_annotations"

    for doc_file in doc_files:
        if not doc_file.content_type == "text/plain":
            # TODO Flo: Support other MIME Types
            raise HTTPException(detail="Only plain text files allowed!", status_code=406)

        document_preprocessing = (
                Signature(import_uploaded_document, kwargs={"doc_file": doc_file, "project_id": proj_id}) |
                Signature(generate_automatic_annotations) |
                Signature(persist_automatic_annotations)
        )
        document_preprocessing.apply_async()

    # TODO Flo: How to notify user or system when done?
    return "Upload and preprocessing of Document started in the background!"


@router.delete("/{proj_id}/sdoc", tags=tags,
               response_model=List[int],
               summary="Removes all SourceDocuments of the Project",
               description="Removes all SourceDocuments of the Project with the given ID if it exists")
async def delete_project_sdocs(*,
                               proj_id: int,
                               db: Session = Depends(get_db_session)) -> List[int]:
    # TODO Flo: only if the user has access?
    return crud_sdoc.remove_by_project(db=db, proj_id=proj_id)


@router.patch("/{proj_id}/user/{user_id}", tags=tags,
              response_model=Optional[UserRead],
              summary="Associates the User with the Project",
              description="Associates an existing User to the Project with the given ID if it exists")
async def associate_user_to_project(*,
                                    proj_id: int,
                                    user_id: int,
                                    db: Session = Depends(get_db_session)) -> Optional[UserRead]:
    # TODO Flo: only if the user has access?
    user_db_obj = crud_project.associate_user(db=db, id=proj_id, user_id=user_id)
    return UserRead.from_orm(user_db_obj)


@router.delete("/{proj_id}/user/{user_id}", tags=tags,
               response_model=Optional[UserRead],
               summary="Dissociates the Users with the Project",
               description="Dissociates the Users with the Project with the given ID if it exists")
async def dissociate_user_from_project(*,
                                       proj_id: int,
                                       user_id: int,
                                       db: Session = Depends(get_db_session)) -> Optional[UserRead]:
    # TODO Flo: only if the user has access?
    user_db_obj = crud_project.dissociate_user(db=db, id=proj_id, user_id=user_id)
    return UserRead.from_orm(user_db_obj)


@router.get("/{proj_id}/user", tags=tags,
            response_model=List[UserRead],
            summary="Returns all Users of the Project",
            description="Returns all Users of the Project with the given ID")
async def get_project_users(*,
                            proj_id: int,
                            db: Session = Depends(get_db_session)) -> List[UserRead]:
    # TODO Flo: only if the user has access?
    proj_db_obj = crud_project.read(db=db, id=proj_id)
    return [UserRead.from_orm(user) for user in proj_db_obj.users]


@router.get("/{proj_id}/code", tags=tags,
            response_model=List[CodeRead],
            summary="Returns all Codes of the Project",
            description="Returns all Codes of the Project with the given ID")
async def get_project_codes(*,
                            proj_id: int,
                            db: Session = Depends(get_db_session)) -> List[CodeRead]:
    # TODO Flo: only if the user has access?
    proj_db_obj = crud_project.read(db=db, id=proj_id)
    return [CodeRead.from_orm(code) for code in proj_db_obj.codes]


@router.delete("/{proj_id}/code", tags=tags,
               response_model=List[int],
               summary="Removes all Codes of the Project",
               description="Removes all Codes of the Project with the given ID if it exists")
async def delete_project_codes(*,
                               proj_id: int,
                               db: Session = Depends(get_db_session)) -> List[int]:
    # TODO Flo: only if the user has access?
    return crud_code.remove_by_project(db=db, proj_id=proj_id)


@router.get("/{proj_id}/tag", tags=tags,
            response_model=List[DocumentTagRead],
            summary="Returns all DocumentTags of the Project",
            description="Returns all DocumentTags of the Project with the given ID")
async def get_project_tags(*,
                           proj_id: int,
                           db: Session = Depends(get_db_session)) -> List[DocumentTagRead]:
    # TODO Flo: only if the user has access?
    proj_db_obj = crud_project.read(db=db, id=proj_id)
    return [DocumentTagRead.from_orm(tag) for tag in proj_db_obj.document_tags]


@router.delete("/{proj_id}/tag", tags=tags,
               response_model=List[int],
               summary="Removes all DocumentTags of the Project",
               description="Removes all DocumentTags of the Project with the given ID if it exists")
async def delete_project_tags(*,
                              proj_id: int,
                              db: Session = Depends(get_db_session)) -> List[int]:
    # TODO Flo: only if the user has access?
    return crud_document_tag.remove_by_project(db=db, proj_id=proj_id)


@router.get("/{proj_id}/user/{user_id}/code", tags=tags,
            response_model=List[CodeRead],
            summary="Returns all Codes of the Project from a User",
            description="Returns all Codes of the Project from a User")
async def get_user_codes_of_project(*,
                                    proj_id: int,
                                    user_id: int,
                                    db: Session = Depends(get_db_session)) -> List[CodeRead]:
    # TODO Flo: only if the user has access?
    return [CodeRead.from_orm(code_db_obj) for code_db_obj in
            crud_code.read_by_user_and_project(db=db, user_id=user_id, proj_id=proj_id)]


@router.delete("/{proj_id}/user/{user_id}/code", tags=tags,
               response_model=int,
               summary="Removes all Codes of the Project from a User",
               description="Removes all Codes of the Project from a User. Returns the number of removed Codes.")
async def remove_user_codes_of_project(*,
                                       proj_id: int,
                                       user_id: int,
                                       db: Session = Depends(get_db_session)) -> List[int]:
    # TODO Flo: only if the user has access?
    return crud_code.remove_by_user_and_project(db=db, user_id=user_id, proj_id=proj_id)


@router.get("/{proj_id}/user/{user_id}/memo", tags=tags,
            response_model=List[MemoRead],
            summary="Returns all Memos of the Project from a User",
            description="Returns all Memos of the Project from a User")
async def get_user_memos_of_project(*,
                                    proj_id: int,
                                    user_id: int,
                                    db: Session = Depends(get_db_session)) -> List[MemoRead]:
    # TODO Flo: only if the user has access?
    db_objs = crud_memo.read_by_user_and_project(db=db, user_id=user_id, proj_id=proj_id)
    return [crud_memo.get_memo_read_dto_from_orm(db=db, db_obj=db_obj) for db_obj in db_objs]


@router.delete("/{proj_id}/user/{user_id}/memo", tags=tags,
               response_model=List[int],
               summary="Removes all Memos of the Project from a User",
               description="Removes all Memos of the Project from a User. Returns the number of removed Memos.")
async def remove_user_memos_of_project(*,
                                       proj_id: int,
                                       user_id: int,
                                       db: Session = Depends(get_db_session)) -> List[int]:
    # TODO Flo: only if the user has access?
    return crud_memo.remove_by_user_and_project(db=db, user_id=user_id, proj_id=proj_id)


@router.get("/{proj_id}/memo", tags=tags,
            response_model=Optional[MemoRead],
            summary="Returns the Memo of the current User for the Project.",
            description="Returns the Memo of the current User for the Project with the given ID.")
async def get_memo(*,
                   db: Session = Depends(get_db_session),
                   proj_id: int) -> Optional[MemoRead]:
    proj_db_obj = crud_project.read(db=db, id=proj_id)
    memo_as_in_db_dto = MemoInDB.from_orm(proj_db_obj.object_handle.attached_memo)
    return MemoRead(**memo_as_in_db_dto.dict(exclude={"attached_to"}),
                    attached_object_id=proj_id,
                    attached_object_type=AttachedObjectType.project)


@router.put("/{proj_id}/memo", tags=tags,
            response_model=Optional[MemoRead],
            summary="Adds a Memo of the current User to the Project.",
            description="Adds a Memo of the current User to the Project with the given ID if it exists")
async def add_memo(*,
                   db: Session = Depends(get_db_session),
                   proj_id: int,
                   memo: MemoCreate) -> Optional[MemoRead]:
    db_obj = crud_memo.create_for_project(db=db, project_id=proj_id, create_dto=memo)
    memo_as_in_db_dto = MemoInDB.from_orm(db_obj)
    return MemoRead(**memo_as_in_db_dto.dict(exclude={"attached_to"}),
                    attached_object_id=proj_id,
                    attached_object_type=AttachedObjectType.project)

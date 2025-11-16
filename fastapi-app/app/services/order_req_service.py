"""
Service layer for OrderReq collection operations
"""
from typing import List, Optional
from datetime import datetime
import uuid
import random
import re
from pymongo.errors import DuplicateKeyError

from app.models.documents import OrderReq
from app.models.schemas import OrderReqCreate, OrderReqUpdate, OrderReqResponse, OrderReqNote, OrderReqDocument, OrderReqDocumentUpdate
from app.services.user_service import UserService
from app.core.exceptions import NotFoundError, ConflictError, ValidationError, DatabaseError
from app.core.logging import get_logger
import traceback

logger = get_logger(__name__)


def _filter_deleted_documents(documents: Optional[list]) -> Optional[list]:
    """Filter out soft-deleted documents from Documents array"""
    if not documents:
        return documents
    return [doc for doc in documents if not doc.get('is_deleted', False)]


def _serialize_document_dict(doc_dict: dict) -> dict:
    """Convert datetime objects to ISO format strings for JSON serialization"""
    serialized = {}
    for key, value in doc_dict.items():
        if isinstance(value, datetime):
            serialized[key] = value.isoformat()
        else:
            serialized[key] = value
    return serialized


def _generate_order_req_id(shortname: str) -> str:
    """Generate OrderReqID based on first 2 letters of shortname, julian month, julian day, and random seq 01-10"""
    prefix = (shortname[:2] if shortname else "US").upper()
    now = datetime.utcnow()
    month = f"{now.month:02d}"
    julian = now.timetuple().tm_yday
    seq = f"{random.randint(11,99):02d}"
    # Format: <PR><MM><DDD><SS>
    return f"{prefix}{month}{julian:03d}{seq}"


def _generate_note_followup_id(followup_uuid: Optional[str], order_req_id: str) -> str:
    """
    Generate the canonical FollowUpID using a client supplied UUID placeholder
    or a newly generated UUID when none is provided.

    New format: F-<OrderReqID>-<first_uuid_segment>
    - followup_uuid: optional UUID string supplied by client (placeholder for idempotency)
      If None, a new UUID4 will be generated.
    - We take the first dash-separated segment from the UUID string and embed it.
    """
    try:
        if not followup_uuid:
            followup_uuid = str(uuid.uuid4())
        # Ensure string form
        fu_str = str(followup_uuid)
        first_seg = fu_str.split('-', 1)[0]
        return f"F-{order_req_id}-{first_seg}"
    except Exception as e:
        # Convert to a generic conflict error if something unexpected occurs
        raise ConflictError(f"Failed to generate FollowUpID: {str(e)}")


class OrderReqService:
    @staticmethod
    async def create_order_req(data: OrderReqCreate) -> OrderReqResponse:
        try:
            # derive shortname from RequestorEmailID
            requestor_email = data.RequestorEmailID
            user = await UserService.get_user_by_email(requestor_email)
            if not user:
                raise ValidationError(f"Requestor email {requestor_email} not found", field="RequestorEmailID")
            shortname = user.ShortName
            # generate OrderReqID with uniqueness check
            max_attempts = 9
            attempt = 0
            order_req_id = None
            while attempt < max_attempts:
                candidate = _generate_order_req_id(shortname)
                # check if it already exists
                exists = None
                try:
                    exists = await OrderReqService.get_order_req(candidate)
                except NotFoundError:
                    exists = None

                if not exists:
                    order_req_id = candidate
                    break
                attempt += 1

            if not order_req_id:
                # couldn't generate unique id
                from app.core.exceptions import ExceededLimits
                raise ExceededLimits()

            # Process Notes - generate FollowUpID if Notes are present
            notes_list = None
            if data.Notes:
                notes_list = []
                for note in data.Notes:
                    note_dict = note.model_dump()

                    # If caller provided a FollowUpID, keep it — but ensure it's unique within this OrderReq.
                    incoming_followup = note_dict.get('FollowUpID')
                    if incoming_followup:
                        if any(n.get('FollowUpID') == incoming_followup for n in notes_list):
                            # Duplicate provided by caller — ignore and generate a new one
                            logger.warning(f"Duplicate incoming FollowUpID '{incoming_followup}' detected; generating new FollowUpID")
                            incoming_followup = None

                    followup_id = incoming_followup

                    # If no incoming FollowUpID, generate/transform one using client UUID placeholder
                    if not followup_id:
                        followup_id = _generate_note_followup_id(incoming_followup, order_req_id)

                        if not followup_id:
                            raise ConflictError("Could not generate FollowUpID for note")

                    # Assign the resolved FollowUpID back to the note dict
                    note_dict['FollowUpID'] = followup_id
                    # Ensure AddedTime exists; set to current UTC if missing
                    if 'AddedTime' not in note_dict or note_dict.get('AddedTime') is None:
                        note_dict['AddedTime'] = datetime.utcnow()
                    notes_list.append(note_dict)

            # Process Documents if present
            documents_list = None
            if data.Documents:
                documents_list = []
                for doc in data.Documents:
                    doc_dict = doc.model_dump(by_alias=True)
                    # Ensure timestamps exist
                    if 'created_at' not in doc_dict or doc_dict.get('created_at') is None:
                        doc_dict['created_at'] = datetime.utcnow()
                    if 'updated_at' not in doc_dict or doc_dict.get('updated_at') is None:
                        doc_dict['updated_at'] = datetime.utcnow()
                    documents_list.append(doc_dict)

            # build document
            products_list = [p.model_dump() for p in data.Products]
            # Log key values for diagnostics
            logger.debug(f"Creating OrderReq - requestor_email={requestor_email}, shortname={shortname}, order_req_id={order_req_id}")
            logger.debug(f"Products payload: {products_list}")
            logger.debug(f"DeliveryDate (type={type(data.DeliveryDate)}): {data.DeliveryDate}")

            doc = OrderReq(
                OrderReqID=order_req_id,
                RequestorEmailID=requestor_email,
                Industry=data.Industry,
                OrderReqStatus=data.OrderReqStatus,
                Products=products_list,
                DeliveryDate=data.DeliveryDate,
                SubmissionTime=data.SubmissionTime,
                Notes=notes_list,
                Documents=documents_list,
                Interested_Roles=data.Interested_Roles
            )

            # insert
            await doc.insert()

            logger.info(f"Created OrderReq {order_req_id}")
            # Filter deleted documents before returning response
            doc_dict = doc.model_dump()
            doc_dict['Documents'] = _filter_deleted_documents(doc_dict.get('Documents'))
            return OrderReqResponse.model_validate({**doc_dict, "id": str(doc.id)})

        except DuplicateKeyError as de:
            logger.warning(f"Duplicate OrderReqID conflict: {de}")
            raise ConflictError(f"OrderReqID conflict: {str(de)}")
        except Exception as e:
            # Log full traceback and repr for better diagnostics
            tb = traceback.format_exc()
            logger.error(f"Error creating OrderReq - exception: {repr(e)}\nTraceback:\n{tb}")
            raise DatabaseError(f"Failed to create OrderReq: {repr(e)}")

    @staticmethod
    async def get_order_req(order_req_id: str) -> OrderReqResponse:
        try:
            doc = await OrderReq.find_one(OrderReq.OrderReqID == order_req_id)
            if not doc:
                raise NotFoundError("OrderReq", order_req_id)
            # Filter deleted documents before returning response
            doc_dict = doc.model_dump()
            doc_dict['Documents'] = _filter_deleted_documents(doc_dict.get('Documents'))
            return OrderReqResponse.model_validate({**doc_dict, "id": str(doc.id)})
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error fetching OrderReq {order_req_id}: {str(e)}")
            raise DatabaseError(f"Failed to fetch OrderReq: {str(e)}")

    @staticmethod
    async def list_order_reqs(skip: int = 0, limit: int = 20) -> List[OrderReqResponse]:
        try:
            docs = await OrderReq.find_all().skip(skip).limit(limit).to_list()
            result = []
            for d in docs:
                doc_dict = d.model_dump()
                doc_dict['Documents'] = _filter_deleted_documents(doc_dict.get('Documents'))
                result.append(OrderReqResponse.model_validate({**doc_dict, "id": str(d.id)}))
            return result
        except Exception as e:
            logger.error(f"Error listing OrderReqs: {str(e)}")
            raise DatabaseError(f"Failed to list OrderReqs: {str(e)}")

    @staticmethod
    async def find_by_requestor_and_status(requestor_email: str, status: str | None = None) -> List[OrderReqResponse]:
        """Find OrderReq documents by RequestorEmailID and optional OrderReqStatus"""
        try:
            query = {"RequestorEmailID": requestor_email}
            if status is not None:
                query["OrderReqStatus"] = status

            cursor = OrderReq.get_motor_collection().find(query)
            raw_docs = await cursor.to_list(length=None)
            docs = [OrderReq.model_validate(d) for d in raw_docs]
            result = []
            for d in docs:
                doc_dict = d.model_dump()
                doc_dict['Documents'] = _filter_deleted_documents(doc_dict.get('Documents'))
                result.append(OrderReqResponse.model_validate({**doc_dict, "id": str(d.id)}))
            return result
        except Exception as e:
            logger.error(f"Error searching OrderReqs by requestor/status: {str(e)}")
            raise DatabaseError(f"Failed to search OrderReqs: {str(e)}")

    @staticmethod
    async def update_order_req(order_req_id: str, data: OrderReqUpdate) -> OrderReqResponse:
        try:
            doc = await OrderReq.find_one(OrderReq.OrderReqID == order_req_id)
            if not doc:
                raise NotFoundError("OrderReq", order_req_id)

            update_data = data.model_dump(exclude_none=True)
            # Ensure OrderReqID and RequestorEmailID are not updatable
            update_data.pop('OrderReqID', None)
            update_data.pop('RequestorEmailID', None)

            # Process Products if present
            if 'Products' in update_data:
                update_data['Products'] = [p if isinstance(p, dict) else p.model_dump() for p in update_data['Products']]

            # Process Notes if present - ensure each note has a unique FollowUpID
            if 'Notes' in update_data:
                incoming_notes = [n if isinstance(n, dict) else n.model_dump() for n in update_data['Notes']]
                notes_list = []
                for note_dict in incoming_notes:
                    # If caller provided a FollowUpID, keep it — but ensure it's unique within this update payload.
                    incoming_followup = note_dict.get('FollowUpID')
                    if incoming_followup:
                        if any(n.get('FollowUpID') == incoming_followup for n in notes_list):
                            # Duplicate provided by caller — ignore and generate a new one
                            logger.warning(f"Duplicate incoming FollowUpID '{incoming_followup}' detected in update; generating new FollowUpID")
                            incoming_followup = None

                    followup_id = incoming_followup

                    # If no incoming FollowUpID, generate/transform one using client UUID placeholder
                    if not followup_id:
                        followup_id = _generate_note_followup_id(incoming_followup, order_req_id)

                        if not followup_id:
                            raise ConflictError("Could not generate FollowUpID for note during update")

                    # Assign the resolved FollowUpID back to the note dict
                        note_dict['FollowUpID'] = followup_id
                        # Ensure AddedTime exists for updated notes; set to current UTC if missing
                        if 'AddedTime' not in note_dict or note_dict.get('AddedTime') is None:
                            note_dict['AddedTime'] = datetime.utcnow()
                        notes_list.append(note_dict)

                update_data['Notes'] = notes_list

            # Process Documents if present
            if 'Documents' in update_data:
                incoming_documents = [d if isinstance(d, dict) else d.model_dump(by_alias=True) for d in update_data['Documents']]
                documents_list = []
                for doc_dict in incoming_documents:
                    # Ensure timestamps exist
                    if 'created_at' not in doc_dict or doc_dict.get('created_at') is None:
                        doc_dict['created_at'] = datetime.utcnow()
                    if 'updated_at' not in doc_dict or doc_dict.get('updated_at') is None:
                        doc_dict['updated_at'] = datetime.utcnow()
                    documents_list.append(doc_dict)

                update_data['Documents'] = documents_list

            if update_data:
                update_data['updatedAt'] = datetime.utcnow()
                await doc.update({"$set": update_data})

            updated = await OrderReq.get(doc.id)
            # Filter deleted documents before returning response
            doc_dict = updated.model_dump()
            doc_dict['Documents'] = _filter_deleted_documents(doc_dict.get('Documents'))
            return OrderReqResponse.model_validate({**doc_dict, "id": str(updated.id)})
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error updating OrderReq {order_req_id}: {str(e)}")
            raise DatabaseError(f"Failed to update OrderReq: {str(e)}")

    @staticmethod
    async def append_order_request_notes(order_req_id: str, note: OrderReqNote) -> str:
        """Append a single note to an existing OrderReq. Returns the resolved FollowUpID."""
        try:
            # ensure document exists
            doc = await OrderReq.find_one(OrderReq.OrderReqID == order_req_id)
            if not doc:
                raise NotFoundError("OrderReq", order_req_id)

            # normalize incoming note
            note_dict = note.model_dump() if not isinstance(note, dict) else note
            incoming_followup = note_dict.get('FollowUpID')
            # generate canonical FollowUpID (uses incoming UUID placeholder or generates one)
            followup_id = _generate_note_followup_id(incoming_followup, order_req_id)
            note_dict['FollowUpID'] = followup_id
            # ensure AddedTime
            if 'AddedTime' not in note_dict or note_dict.get('AddedTime') is None:
                note_dict['AddedTime'] = datetime.utcnow()

            # atomic push
            result = await OrderReq.get_motor_collection().update_one(
                {"OrderReqID": order_req_id},
                {"$push": {"Notes": note_dict}, "$set": {"updatedAt": datetime.utcnow()}}
            )
            if result.matched_count == 0:
                raise DatabaseError("Failed to append note: target OrderReq not found/modified")
            return followup_id
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error appending note to OrderReq {order_req_id}: {str(e)}")
            raise DatabaseError(f"Failed to append note: {str(e)}")

    @staticmethod
    async def add_interested_role(order_req_id: str, role: str) -> bool:
        """Add a role string to Interested_Roles array for an OrderReq. No validation performed."""
        try:
            result = await OrderReq.get_motor_collection().update_one(
                {"OrderReqID": order_req_id},
                {"$addToSet": {"Interested_Roles": role}, "$set": {"updatedAt": datetime.utcnow()}}
            )
            if result.matched_count == 0:
                raise NotFoundError(f"OrderReq {order_req_id} not found")
            return True
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error adding Interested_Roles for {order_req_id}: {str(e)}")
            raise DatabaseError(f"Failed to add Interested_Roles: {str(e)}")

    @staticmethod
    async def remove_interested_role(order_req_id: str, role: str) -> bool:
        """Remove a role string from Interested_Roles array for an OrderReq."""
        try:
            result = await OrderReq.get_motor_collection().update_one(
                {"OrderReqID": order_req_id},
                {"$pull": {"Interested_Roles": role}, "$set": {"updatedAt": datetime.utcnow()}}
            )
            if result.matched_count == 0:
                raise NotFoundError(f"OrderReq {order_req_id} not found")
            return True
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error removing Interested_Roles for {order_req_id}: {str(e)}")
            raise DatabaseError(f"Failed to remove Interested_Roles: {str(e)}")

    @staticmethod
    async def get_order_req_by_note_followup_id(followup_id: str) -> Optional[OrderReqResponse]:
        """Get OrderReq by Notes FollowUpID"""
        try:
            # Query using array element matching
            doc = await OrderReq.find_one({"Notes.FollowUpID": followup_id})
            if not doc:
                raise NotFoundError("OrderReq with Notes.FollowUpID", followup_id)
            # Filter deleted documents before returning response
            doc_dict = doc.model_dump()
            doc_dict['Documents'] = _filter_deleted_documents(doc_dict.get('Documents'))
            return OrderReqResponse.model_validate({**doc_dict, "id": str(doc.id)})
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error fetching OrderReq by Notes.FollowUpID {followup_id}: {str(e)}")
            raise DatabaseError(f"Failed to fetch OrderReq: {str(e)}")

    @staticmethod
    async def get_order_reqs_by_audience(proposal_id: str) -> List[OrderReqResponse]:
        """Get all OrderReqs that have the given ProposalID in Notes Audience array"""
        try:
            # Query using array element matching
            docs = await OrderReq.find({"Notes.Audience": proposal_id}).to_list()
            result = []
            for d in docs:
                doc_dict = d.model_dump()
                doc_dict['Documents'] = _filter_deleted_documents(doc_dict.get('Documents'))
                result.append(OrderReqResponse.model_validate({**doc_dict, "id": str(d.id)}))
            return result
        except Exception as e:
            logger.error(f"Error fetching OrderReqs by Notes.Audience {proposal_id}: {str(e)}")
            raise DatabaseError(f"Failed to fetch OrderReqs: {str(e)}")

    @staticmethod
    async def delete_order_req(order_req_id: str) -> bool:
        try:
            doc = await OrderReq.find_one(OrderReq.OrderReqID == order_req_id)
            if not doc:
                raise NotFoundError("OrderReq", order_req_id)
            await doc.delete()
            return True
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error deleting OrderReq {order_req_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete OrderReq: {str(e)}")

    @staticmethod
    async def get_order_req_document_by_s3_key(order_req_id: str, s3_key: str) -> Optional[dict]:
        """Get a specific document from OrderReq by OrderReqID and s3_key (excludes soft-deleted documents)"""
        try:
            # Query to find the OrderReq with matching OrderReqID and Documents array element with matching s3_key
            doc = await OrderReq.find_one(
                {"OrderReqID": order_req_id, "Documents.s3_key": s3_key}
            )
            if not doc:
                raise NotFoundError("OrderReq with Documents.s3_key", f"{order_req_id}/{s3_key}")

            # Find the specific document from the Documents array
            matching_doc = None
            if doc.Documents:
                for document in doc.Documents:
                    if document.get('s3_key') == s3_key:
                        # Check if document is soft-deleted
                        if document.get('is_deleted', False):
                            raise NotFoundError("Document with s3_key (deleted)", s3_key)
                        matching_doc = document
                        break

            if not matching_doc:
                raise NotFoundError("Document with s3_key", s3_key)

            # Serialize datetime objects for JSON response
            return _serialize_document_dict(matching_doc)
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error fetching document by s3_key {s3_key} from OrderReq {order_req_id}: {str(e)}")
            raise DatabaseError(f"Failed to fetch document: {str(e)}")

    @staticmethod
    async def append_order_req_document(order_req_id: str, document: OrderReqDocument) -> dict:
        """Append a single document to an existing OrderReq Documents array. Returns the document dict."""
        try:
            # ensure document exists
            doc = await OrderReq.find_one(OrderReq.OrderReqID == order_req_id)
            if not doc:
                raise NotFoundError("OrderReq", order_req_id)

            # normalize incoming document
            doc_dict = document.model_dump(by_alias=True) if not isinstance(document, dict) else document

            # Ensure timestamps are set
            if 'created_at' not in doc_dict or doc_dict.get('created_at') is None:
                doc_dict['created_at'] = datetime.utcnow()
            if 'updated_at' not in doc_dict or doc_dict.get('updated_at') is None:
                doc_dict['updated_at'] = datetime.utcnow()
            # Ensure is_deleted is False by default
            if 'is_deleted' not in doc_dict:
                doc_dict['is_deleted'] = False

            # atomic push
            result = await OrderReq.get_motor_collection().update_one(
                {"OrderReqID": order_req_id},
                {"$push": {"Documents": doc_dict}, "$set": {"updatedAt": datetime.utcnow()}}
            )
            if result.matched_count == 0:
                raise DatabaseError("Failed to append document: target OrderReq not found/modified")

            # Serialize datetime objects for JSON response
            return _serialize_document_dict(doc_dict)
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error appending document to OrderReq {order_req_id}: {str(e)}")
            raise DatabaseError(f"Failed to append document: {str(e)}")

    @staticmethod
    async def update_order_req_document(order_req_id: str, s3_key: str, update_data: OrderReqDocumentUpdate) -> dict:
        """Update a document's metadata in OrderReq Documents array"""
        try:
            # First verify the document exists and is not deleted
            doc = await OrderReq.find_one(
                {"OrderReqID": order_req_id, "Documents.s3_key": s3_key}
            )
            if not doc:
                raise NotFoundError("OrderReq with Documents.s3_key", f"{order_req_id}/{s3_key}")

            # Check if document is deleted - cannot update deleted documents
            if doc.Documents:
                for document in doc.Documents:
                    if document.get('s3_key') == s3_key:
                        if document.get('is_deleted', False):
                            raise ConflictError(f"Cannot update deleted document with s3_key {s3_key}")
                        break

            # Build update dict with only provided fields
            update_dict = update_data.model_dump(by_alias=True, exclude_none=True)

            if not update_dict:
                raise ValidationError("No fields provided for update", field="update_data")

            # Prefix all fields with Documents.$ for positional update
            positional_update = {f"Documents.$.{key}": value for key, value in update_dict.items()}
            # Always update the updated_at timestamp
            positional_update["Documents.$.updated_at"] = datetime.utcnow()
            positional_update["updatedAt"] = datetime.utcnow()

            # Update using positional operator $
            result = await OrderReq.get_motor_collection().update_one(
                {"OrderReqID": order_req_id, "Documents.s3_key": s3_key},
                {"$set": positional_update}
            )

            if result.matched_count == 0:
                raise NotFoundError("OrderReq with Documents.s3_key", f"{order_req_id}/{s3_key}")
            if result.modified_count == 0:
                # This is OK - might mean no actual changes were made
                logger.info(f"No modifications made to document {s3_key} - values may be unchanged")

            # Fetch and return the updated document
            updated_doc = await OrderReq.find_one(
                {"OrderReqID": order_req_id, "Documents.s3_key": s3_key}
            )
            if updated_doc and updated_doc.Documents:
                for document in updated_doc.Documents:
                    if document.get('s3_key') == s3_key:
                        # Serialize datetime objects for JSON response
                        return _serialize_document_dict(document)

            raise DatabaseError("Failed to retrieve updated document")

        except Exception as e:
            if isinstance(e, (NotFoundError, ConflictError, ValidationError)):
                raise
            logger.error(f"Error updating document {s3_key} in OrderReq {order_req_id}: {str(e)}")
            raise DatabaseError(f"Failed to update document: {str(e)}")

    @staticmethod
    async def soft_delete_order_req_document(order_req_id: str, s3_key: str, deleted_by: str) -> bool:
        """Soft delete a document from OrderReq Documents array by marking it as deleted"""
        try:
            # First verify the document exists and is not already deleted
            doc = await OrderReq.find_one(
                {"OrderReqID": order_req_id, "Documents.s3_key": s3_key}
            )
            if not doc:
                raise NotFoundError("OrderReq with Documents.s3_key", f"{order_req_id}/{s3_key}")

            # Check if document is already deleted
            if doc.Documents:
                for document in doc.Documents:
                    if document.get('s3_key') == s3_key:
                        if document.get('is_deleted', False):
                            raise ConflictError(f"Document with s3_key {s3_key} is already deleted")
                        break

            # Soft delete using positional operator $
            result = await OrderReq.get_motor_collection().update_one(
                {"OrderReqID": order_req_id, "Documents.s3_key": s3_key},
                {
                    "$set": {
                        "Documents.$.is_deleted": True,
                        "Documents.$.deleted_at": datetime.utcnow(),
                        "Documents.$.deleted_by": deleted_by,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            if result.matched_count == 0:
                raise NotFoundError("OrderReq with Documents.s3_key", f"{order_req_id}/{s3_key}")
            if result.modified_count == 0:
                raise DatabaseError("Failed to soft delete document: no modifications made")

            return True
        except Exception as e:
            if isinstance(e, (NotFoundError, ConflictError)):
                raise
            logger.error(f"Error soft deleting document {s3_key} from OrderReq {order_req_id}: {str(e)}")
            raise DatabaseError(f"Failed to soft delete document: {str(e)}")

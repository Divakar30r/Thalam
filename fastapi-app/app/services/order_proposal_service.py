"""
Service layer for OrderProposal collection operations
"""
from typing import List, Optional
from datetime import datetime
import random
import re
import uuid
from pymongo.errors import DuplicateKeyError

from app.models.documents import OrderProposal, OrderReq
from app.models.schemas import OrderProposalCreate, OrderProposalUpdate, OrderProposalResponse, ProposalNote, ProposalUserEdit
from app.core.exceptions import NotFoundError, ConflictError, ValidationError, DatabaseError
from app.core.logging import get_logger
import traceback

logger = get_logger(__name__)


def _generate_proposal_id(order_req_id: str) -> str:
    """
    Generate ProposalID with prefix PRP-<incremental no>-<OrderReqID>
    Format: PRP-<1-10>-<OrderReqID>
    """
    seq = random.randint(1, 10)
    return f"PRP-{seq}-{order_req_id}"


def _generate_proposalnote_followup_id(followup_uuid: Optional[str], proposal_id: str) -> str:
    """
    Generate canonical FollowUpID for Proposal Notes using client UUID placeholder.

    New format: F-<ProposalID>-<first_uuid_segment>
    If `followup_uuid` is None a new uuid4 is generated.
    """
    try:
        if not followup_uuid:
            followup_uuid = str(uuid.uuid4())
        fu_str = str(followup_uuid)
        first_seg = fu_str.split('-', 1)[0]
        return f"F-{proposal_id}-{first_seg}"
    except Exception as e:
        raise ConflictError(f"Failed to generate FollowUpID for proposal note: {str(e)}")


class OrderProposalService:
    @staticmethod
    async def create_order_proposal(data: OrderProposalCreate) -> OrderProposalResponse:
        try:
            # Validate that OrderReqID exists in OrderRequest collection
            order_req = await OrderReq.find_one(OrderReq.OrderReqID == data.OrderReqID)
            if not order_req:
                raise ValidationError(f"OrderReqID {data.OrderReqID} not found in OrderRequest collection", field="OrderReqID")

            # Generate unique ProposalID
            max_attempts = 10
            attempt = 0
            proposal_req_id = None
            
            while attempt < max_attempts:
                candidate = _generate_proposal_id(data.OrderReqID)
                # Check if it already exists
                exists = await OrderProposal.find_one(OrderProposal.ProposalID == candidate)
                if not exists:
                    proposal_req_id = candidate
                    break
                attempt += 1

            if not proposal_req_id:
                raise ConflictError("Could not generate unique ProposalID after 10 attempts")

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
                        followup_id = _generate_proposalnote_followup_id(incoming_followup, proposal_req_id)

                        if not followup_id:
                            raise ConflictError("Could not generate FollowUpID for note")

                    # Assign the resolved FollowUpID back to the note dict
                    note_dict['FollowUpID'] = followup_id
                    # Ensure AddedTime exists; set to current UTC if missing
                    if 'AddedTime' not in note_dict or note_dict.get('AddedTime') is None:
                        note_dict['AddedTime'] = datetime.utcnow()
                    notes_list.append(note_dict)

            # Process UserEdits - validate FollowUpID exists in OrderRequest Notes
            user_edits_list = None
            if data.UserEdits:
                user_edits_list = []
                for edit in data.UserEdits:
                    edit_dict = edit.model_dump()
                    # Validate that FollowUpID exists in the referenced OrderRequest's Notes
                    # This is a business rule validation
                    # For now, we'll accept it as-is, but you can add validation here
                    user_edits_list.append(edit_dict)

            # Build products list
            products_list = [p.model_dump() for p in data.Products]

            # Log key values for diagnostics
            logger.debug(f"Creating OrderProposal - order_req_id={data.OrderReqID}, proposal_req_id={proposal_req_id}")
            logger.debug(f"Products payload: {products_list}")

            # Create document
            doc = OrderProposal(
                ProposalID=proposal_req_id,
                OrderReqID=data.OrderReqID,
                ProposerEmailID=data.ProposerEmailID,
                ProposalStatus=data.ProposalStatus,
                SubmissionTime=data.SubmissionTime,
                Industry=data.Industry,
                Products=products_list,
                TotalAmount=data.TotalAmount,
                DeliveryDate=data.DeliveryDate,
                Notes=notes_list,
                UserEdits=user_edits_list
            )

            # Insert into database
            await doc.insert()

            logger.info(f"Created OrderProposal {proposal_req_id}")
            return OrderProposalResponse.model_validate({**doc.model_dump(), "id": str(doc.id)})

        except DuplicateKeyError as de:
            logger.warning(f"Duplicate ProposalID conflict: {de}")
            raise ConflictError(f"ProposalID conflict: {str(de)}")
        except Exception as e:
            if isinstance(e, (ValidationError, ConflictError)):
                raise
            tb = traceback.format_exc()
            logger.error(f"Error creating OrderProposal - exception: {repr(e)}\nTraceback:\n{tb}")
            raise DatabaseError(f"Failed to create OrderProposal: {repr(e)}")

    @staticmethod
    async def get_proposal_by_id(proposal_id: str) -> OrderProposalResponse:
        """Get OrderProposal by ProposalID"""
        try:
            doc = await OrderProposal.find_one(OrderProposal.ProposalID == proposal_id)
            if not doc:
                raise NotFoundError("OrderProposal", proposal_id)
            return OrderProposalResponse.model_validate({**doc.model_dump(), "id": str(doc.id)})
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error fetching OrderProposal {proposal_id}: {str(e)}")
            raise DatabaseError(f"Failed to fetch OrderProposal: {str(e)}")

    @staticmethod
    async def get_proposals_by_order_req_id(order_req_id: str) -> List[OrderProposalResponse]:
        """Get all OrderProposals for a given OrderReqID"""
        try:
            docs = await OrderProposal.find(OrderProposal.OrderReqID == order_req_id).to_list()
            return [OrderProposalResponse.model_validate({**d.model_dump(), "id": str(d.id)}) for d in docs]
        except Exception as e:
            logger.error(f"Error fetching OrderProposals by OrderReqID {order_req_id}: {str(e)}")
            raise DatabaseError(f"Failed to fetch OrderProposals: {str(e)}")

    @staticmethod
    async def get_proposal_by_note_followup_id(followup_id: str) -> Optional[OrderProposalResponse]:
        """Get OrderProposal by Notes FollowUpID"""
        try:
            # Query using array element matching
            doc = await OrderProposal.find_one({"Notes.FollowUpID": followup_id})
            if not doc:
                raise NotFoundError("OrderProposal with Notes.FollowUpID", followup_id)
            return OrderProposalResponse.model_validate({**doc.model_dump(), "id": str(doc.id)})
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error fetching OrderProposal by Notes.FollowUpID {followup_id}: {str(e)}")
            raise DatabaseError(f"Failed to fetch OrderProposal: {str(e)}")

    @staticmethod
    async def get_proposal_by_useredit_followup_id(followup_id: str) -> Optional[OrderProposalResponse]:
        """Get OrderProposal by UserEdits FollowUpID"""
        try:
            # Query using array element matching
            doc = await OrderProposal.find_one({"UserEdits.FollowUpID": followup_id})
            if not doc:
                raise NotFoundError("OrderProposal with UserEdits.FollowUpID", followup_id)
            return OrderProposalResponse.model_validate({**doc.model_dump(), "id": str(doc.id)})
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error fetching OrderProposal by UserEdits.FollowUpID {followup_id}: {str(e)}")
            raise DatabaseError(f"Failed to fetch OrderProposal: {str(e)}")

    @staticmethod
    async def list_order_proposals(skip: int = 0, limit: int = 20) -> List[OrderProposalResponse]:
        """List all OrderProposals with pagination"""
        try:
            docs = await OrderProposal.find_all().skip(skip).limit(limit).to_list()
            return [OrderProposalResponse.model_validate({**d.model_dump(), "id": str(d.id)}) for d in docs]
        except Exception as e:
            logger.error(f"Error listing OrderProposals: {str(e)}")
            raise DatabaseError(f"Failed to list OrderProposals: {str(e)}")

    @staticmethod
    async def update_order_proposal(proposal_id: str, data: OrderProposalUpdate) -> OrderProposalResponse:
        """Update an OrderProposal by ProposalID"""
        try:
            doc = await OrderProposal.find_one(OrderProposal.ProposalID == proposal_id)
            if not doc:
                raise NotFoundError("OrderProposal", proposal_id)

            update_data = data.model_dump(exclude_none=True)
            # Ensure ProposalID, OrderReqID, and ProposerEmailID are not updatable
            update_data.pop('ProposalID', None)
            update_data.pop('OrderReqID', None)
            update_data.pop('ProposerEmailID', None)

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

                    # If no incoming FollowUpID, generate one (ensure uniqueness within this update payload)
                    if not followup_id:
                        followup_id = _generate_proposalnote_followup_id(incoming_followup, proposal_id)

                        if not followup_id:
                            raise ConflictError("Could not generate FollowUpID for note during update")

                    # Assign the resolved FollowUpID back to the note dict
                        note_dict['FollowUpID'] = followup_id
                        # Ensure AddedTime exists for updated notes; set to current UTC if missing
                        if 'AddedTime' not in note_dict or note_dict.get('AddedTime') is None:
                            note_dict['AddedTime'] = datetime.utcnow()
                        notes_list.append(note_dict)

                update_data['Notes'] = notes_list
 

 
            # Process UserEdits if present
            if 'UserEdits' in update_data:
                update_data['UserEdits'] = [e if isinstance(e, dict) else e.model_dump() for e in update_data['UserEdits']]

            if update_data:
                update_data['updatedAt'] = datetime.utcnow()
                await doc.update({"$set": update_data})

            updated = await OrderProposal.get(doc.id)
            return OrderProposalResponse.model_validate({**updated.model_dump(), "id": str(updated.id)})
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error updating OrderProposal {proposal_id}: {str(e)}")
            raise DatabaseError(f"Failed to update OrderProposal: {str(e)}")

    @staticmethod
    async def append_order_proposal_notes(proposal_id: str, note: ProposalNote) -> str:
        """Append a single note to an existing OrderProposal. Returns the resolved FollowUpID."""
        try:
            # ensure document exists
            doc = await OrderProposal.find_one(OrderProposal.ProposalID == proposal_id)
            if not doc:
                raise NotFoundError("OrderProposal", proposal_id)

            # normalize incoming note
            note_dict = note.model_dump() if not isinstance(note, dict) else note
            incoming_followup = note_dict.get('FollowUpID')
            # generate canonical FollowUpID (uses incoming UUID placeholder or generates one)
            followup_id = _generate_proposalnote_followup_id(incoming_followup, proposal_id)
            note_dict['FollowUpID'] = followup_id
            # ensure AddedTime
            if 'AddedTime' not in note_dict or note_dict.get('AddedTime') is None:
                note_dict['AddedTime'] = datetime.utcnow()

            # atomic push
            result = await OrderProposal.get_motor_collection().update_one(
                {"ProposalID": proposal_id},
                {"$push": {"Notes": note_dict}, "$set": {"updatedAt": datetime.utcnow()}}
            )
            if result.matched_count == 0:
                raise DatabaseError("Failed to append note: target OrderProposal not found/modified")
            return followup_id
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error appending note to OrderProposal {proposal_id}: {str(e)}")
            raise DatabaseError(f"Failed to append note: {str(e)}")

    @staticmethod
    async def append_order_proposal_useredit(proposal_id: str, useredit: ProposalUserEdit) -> dict:
        """Append a single user edit entry to an existing OrderProposal. Returns the appended object (FollowUpID and AddedTime)."""
        try:
            # ensure document exists
            doc = await OrderProposal.find_one(OrderProposal.ProposalID == proposal_id)
            if not doc:
                raise NotFoundError("OrderProposal", proposal_id)

            # normalize incoming useredit
            ue_dict = useredit.model_dump() if not isinstance(useredit, dict) else useredit
            # Accept multiple possible key names for the incoming followup id (be forgiving)
            incoming_followup = None
            #for candidate_key in ('OrderFollowUpID', 'OrderFollowUpId', 'orderFollowUpID', 'FollowUpID', 'followupid'):
               # if candidate_key in ue_dict and ue_dict.get("OrderFollowUpID"):
            incoming_followup = ue_dict.get("OrderFollowUpID")
                   #break

            # Validate FollowUpID present
            if not incoming_followup:
                raise ValidationError('OrderFollowUpID is required for user edits', field='OrderFollowUpID')

            # Server must set AddedTime (ignore any incoming AddedTime if present)
            added_time = datetime.utcnow()
            ue_dict['AddedTime'] = added_time

            # atomic push
            result = await OrderProposal.get_motor_collection().update_one(
                {"ProposalID": proposal_id},
                {"$push": {"UserEdits": ue_dict}, "$set": {"updatedAt": datetime.utcnow()}}
            )
            if result.matched_count == 0:
                raise DatabaseError("Failed to append user edit: target OrderProposal not found/modified")

            # Return the canonical object using the API field name
            return {"OrderFollowUpID": incoming_followup, "AddedTime": added_time}
        except Exception as e:
            if isinstance(e, NotFoundError) or isinstance(e, ValidationError):
                raise
            tb = traceback.format_exc()
            logger.error(f"Error appending user edit to OrderProposal {proposal_id}: {repr(e)}\nTraceback:\n{tb}")
            raise DatabaseError(f"Failed to append user edit: {repr(e)}")

    @staticmethod
    async def delete_order_proposal(proposal_id: str) -> bool:
        """Delete an OrderProposal by ProposalID"""
        try:
            doc = await OrderProposal.find_one(OrderProposal.ProposalID == proposal_id)
            if not doc:
                raise NotFoundError("OrderProposal", proposal_id)
            await doc.delete()
            logger.info(f"Deleted OrderProposal {proposal_id}")
            return True
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error deleting OrderProposal {proposal_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete OrderProposal: {str(e)}")

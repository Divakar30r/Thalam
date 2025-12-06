"""
Service layer for TerminalBase collection operations
"""

from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.models import TerminalBase, TerminalBaseCreate, TerminalBaseUpdate, TerminalBaseResponse
from app.services.role_service import RoleService
from app.core.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    ReferentialIntegrityError,
    DatabaseError
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def _convert_terminal_to_response(terminal: TerminalBase) -> TerminalBaseResponse:
    """Convert TerminalBase document to TerminalBaseResponse with proper id field"""
    return TerminalBaseResponse.model_validate({
        **terminal.model_dump(),
        "id": str(terminal.id)
    })


class TerminalService:
    """Service for TerminalBase operations"""
    
    @staticmethod
    async def create_terminal(terminal_data_Obj: TerminalBaseCreate) -> TerminalBaseResponse:
        """Create a new terminal with validation"""
        try:
            # Validate RoleID exists and has proper format
            if terminal_data_Obj.RoleID:
                role_validation = await RoleService.validate_role_id_integrity(
                    [terminal_data_Obj.RoleID]
                )
                
                if not role_validation.get(terminal_data_Obj.RoleID, False):
                    raise ReferentialIntegrityError(
                        f"Invalid or non-existent role ID: {terminal_data_Obj.RoleID}",
                        referenced_collection="RolesBase"
                    )
            
            # Create terminal document
            terminal_doc = TerminalBase(**terminal_data_Obj.model_dump(exclude_none=True))
            
            # Save to database
            await terminal_doc.insert()
            
            logger.info(f"Created terminal with RoleID: {terminal_data_Obj.RoleID}")
            return _convert_terminal_to_response(terminal_doc)
            
        except Exception as e:
            if isinstance(e, (ValidationError, ReferentialIntegrityError, ConflictError)):
                raise
            logger.error(f"Error creating terminal: {str(e)}")
            raise DatabaseError(f"Failed to create terminalBase record: {str(e)}")
    
    @staticmethod
    async def get_terminal_by_id(terminal_id: str) -> TerminalBaseResponse:
        """Get terminal by ID"""
        try:
            if not ObjectId.is_valid(terminal_id):
                raise ValidationError("Invalid terminal ID format", field="terminal_id")
            
            terminal = await TerminalBase.get(terminal_id)
            if not terminal:
                raise NotFoundError("Terminal", terminal_id)
            
            return _convert_terminal_to_response(terminal)
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            logger.error(f"Error getting terminal {terminal_id}: {str(e)}")
            raise DatabaseError(f"Failed to get terminal: {str(e)}")
    
    @staticmethod
    async def get_terminal_by_roleid(role_id: str) -> List[TerminalBaseResponse]:
        """Get terminals by RoleID"""
        try:
            if not role_id:
                raise ValidationError("RoleID cannot be empty", field="role_id")
            
            terminals = await TerminalBase.find(TerminalBase.RoleID == role_id).to_list()
            
            if not terminals:
                raise NotFoundError("Terminals", f"with RoleID {role_id}")
            
            return [_convert_terminal_to_response(terminal) for terminal in terminals]
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            logger.error(f"Error getting terminals by RoleID {role_id}: {str(e)}")
            raise DatabaseError(f"Failed to get terminals by RoleID: {str(e)}")
    
    @staticmethod
    async def list_terminals(
        skip: int = 0,
        limit: int = 20,
        role_id: Optional[str] = None,
        cold_storage: Optional[bool] = None,
        perishable_scope: Optional[bool] = None
    ) -> List[TerminalBaseResponse]:
        """List terminals with optional filtering"""
        try:
            query = TerminalBase.find({})
            
            # Apply role ID filter
            if role_id:
                query = query.find(TerminalBase.RoleID == role_id)
            
            # Apply cold storage filter
            if cold_storage is not None:
                query = query.find(TerminalBase.ColdStorage == cold_storage)
            
            # Apply perishable scope filter
            if perishable_scope is not None:
                query = query.find(TerminalBase.PerishableScope == perishable_scope)
            
            # Apply pagination
            terminals = await query.skip(skip).limit(limit).to_list()
            
            return [_convert_terminal_to_response(terminal) for terminal in terminals]
            
        except Exception as e:
            logger.error(f"Error listing terminals: {str(e)}")
            raise DatabaseError(f"Failed to list terminals: {str(e)}")
    
    @staticmethod
    async def update_terminal_by_role_id(role_id: str, terminal_id: str, terminal_data: TerminalBaseUpdate) -> TerminalBaseResponse:
        """Update terminal by RoleID and terminal ID - RoleID cannot be changed"""
        try:
            if not ObjectId.is_valid(terminal_id):
                raise ValidationError("Invalid terminal ID format", field="terminal_id")
            
            # Find terminal by both RoleID and document ID to ensure it belongs to the specified role
            terminal = await TerminalBase.find_one({
                "_id": ObjectId(terminal_id),
                "RoleID": role_id
            })
            
            if not terminal:
                raise NotFoundError("Terminal", f"ID={terminal_id} with RoleID={role_id}")
            
            # Update fields (RoleID is excluded from TerminalBaseUpdate schema)
            update_data = terminal_data.model_dump(exclude_unset=True, exclude_none=True)
            await terminal.update({"$set": update_data})
            
            # Fetch updated terminal
            updated_terminal = await TerminalBase.get(terminal_id)
            if not updated_terminal:
                raise NotFoundError("Terminal", terminal_id)
            
            logger.info(f"Updated terminal {terminal_id} with RoleID: {role_id}")
            return _convert_terminal_to_response(updated_terminal)
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            logger.error(f"Error updating terminal {terminal_id} with RoleID {role_id}: {str(e)}")
            raise DatabaseError(f"Failed to update terminal: {str(e)}")
    
    @staticmethod
    async def update_terminal(
        terminal_id: str, 
        terminal_data: TerminalBaseUpdate
    ) -> TerminalBaseResponse:
        """Update terminal (legacy method - consider using update_terminal_by_role_id)"""
        try:
            if not ObjectId.is_valid(terminal_id):
                raise ValidationError("Invalid terminal ID format", field="terminal_id")
            
            terminal = await TerminalBase.get(terminal_id)
            if not terminal:
                raise NotFoundError("Terminal", terminal_id)
            
            # Update fields
            update_data = terminal_data.model_dump(exclude_unset=True, exclude_none=True)
            await terminal.update({"$set": update_data})
            
            # Fetch updated terminal
            updated_terminal = await TerminalBase.get(terminal_id)
            if not updated_terminal:
                raise NotFoundError("Terminal", terminal_id)
            
            logger.info(f"Updated terminal: {terminal_id}")
            return _convert_terminal_to_response(updated_terminal)
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError, ReferentialIntegrityError, ConflictError)):
                raise
            logger.error(f"Error updating terminal {terminal_id}: {str(e)}")
            raise DatabaseError(f"Failed to update terminal: {str(e)}")
    
    @staticmethod
    async def delete_terminal(terminal_id: str) -> bool:
        """Delete terminal"""
        try:
            if not ObjectId.is_valid(terminal_id):
                raise ValidationError("Invalid terminal ID format", field="terminal_id")
            
            terminal = await TerminalBase.get(terminal_id)
            if not terminal:
                raise NotFoundError("Terminal", terminal_id)
            
            await terminal.delete()
            
            logger.info(f"Deleted terminal: {terminal_id}")
            return True
            
        except Exception as e:
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            logger.error(f"Error deleting terminal {terminal_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete terminal: {str(e)}")
    
    @staticmethod
    async def count_terminals() -> int:
        """Count all terminals"""
        try:
            return await TerminalBase.find({}).count()
            
        except Exception as e:
            logger.error(f"Error counting terminals: {str(e)}")
            raise DatabaseError(f"Failed to count terminals: {str(e)}")
    
    @staticmethod
    async def get_terminals_by_role(role_id: str) -> List[TerminalBaseResponse]:
        """Get all terminals managed by a specific role"""
        try:
            terminals = await TerminalBase.find(
                TerminalBase.RoleID == role_id
            ).to_list()
            
            return [_convert_terminal_to_response(terminal) for terminal in terminals]
            
        except Exception as e:
            logger.error(f"Error getting terminals for role {role_id}: {str(e)}")
            raise DatabaseError(f"Failed to get terminals for role: {str(e)}")
    
    @staticmethod
    async def get_terminals_with_cold_storage() -> List[TerminalBaseResponse]:
        """Get all terminals with cold storage capability"""
        try:
            terminals = await TerminalBase.find(TerminalBase.ColdStorage == True).to_list()
            
            return [_convert_terminal_to_response(terminal) for terminal in terminals]
            
        except Exception as e:
            logger.error(f"Error getting terminals with cold storage: {str(e)}")
            raise DatabaseError(f"Failed to get terminals with cold storage: {str(e)}")
    
    @staticmethod
    async def get_terminals_with_perishable_scope() -> List[TerminalBaseResponse]:
        """Get all terminals with perishable goods capability"""
        try:
            terminals = await TerminalBase.find(TerminalBase.PerishableScope == True).to_list()
            
            return [_convert_terminal_to_response(terminal) for terminal in terminals]
            
        except Exception as e:
            logger.error(f"Error getting terminals with perishable scope: {str(e)}")
            raise DatabaseError(f"Failed to get terminals with perishable scope: {str(e)}")
    
    @staticmethod
    async def get_terminal_capacity_stats() -> Dict[str, Any]:
        """Get capacity statistics across all terminals"""
        try:
            terminals = await TerminalBase.find({}).to_list()
            
            if not terminals:
                return {
                    "total_terminals": 0,
                    "total_volume": 0,
                    "total_weight": 0,
                    "average_volume": 0,
                    "average_weight": 0,
                    "cold_storage_count": 0,
                    "perishable_scope_count": 0
                }
            
            total_volume = sum(t.Volume for t in terminals)
            total_weight = sum(t.Weight for t in terminals)
            cold_storage_count = sum(1 for t in terminals if t.ColdStorage)
            perishable_scope_count = sum(1 for t in terminals if t.PerishableScope)
            
            count = len(terminals)
            
            return {
                "total_terminals": count,
                "total_volume": total_volume,
                "total_weight": total_weight,
                "average_volume": total_volume / count,
                "average_weight": total_weight / count,
                "cold_storage_count": cold_storage_count,
                "perishable_scope_count": perishable_scope_count,
                "cold_storage_percentage": (cold_storage_count / count) * 100,
                "perishable_scope_percentage": (perishable_scope_count / count) * 100
            }
            
        except Exception as e:
            logger.error(f"Error getting terminal capacity stats: {str(e)}")
            raise DatabaseError(f"Failed to get terminal capacity stats: {str(e)}")
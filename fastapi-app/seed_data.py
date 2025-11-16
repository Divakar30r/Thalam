"""
Database seeding script for development and testing
"""

import asyncio
from typing import List
from app.core.database import connect_to_database, disconnect_from_database
from app.services import UserService, RoleService, TerminalService
from app.models import (
    UserBaseCreate, RolesBaseCreate, TerminalBaseCreate,
    GeoJSONPoint, TerminalCapacity, TerminalCapabilities
)
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


class DatabaseSeeder:
    """Database seeding for development and testing"""
    
    @staticmethod
    async def seed_sample_data():
        """Seed the database with sample data"""
        try:
            logger.info("🌱 Starting database seeding...")
            
            # Connect to database
            await connect_to_database()
            logger.info("✅ Connected to database")
            
            # Seed users
            users = await DatabaseSeeder.create_sample_users()
            logger.info(f"✅ Created {len(users)} users")
            
            # Seed roles
            roles = await DatabaseSeeder.create_sample_roles(users)
            logger.info(f"✅ Created {len(roles)} roles")
            
            # Seed terminals
            terminals = await DatabaseSeeder.create_sample_terminals(roles)
            logger.info(f"✅ Created {len(terminals)} terminals")
            
            logger.info("🎉 Database seeding completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Database seeding failed: {str(e)}")
            raise
        finally:
            await disconnect_from_database()
    
    @staticmethod
    async def create_sample_users() -> List[str]:
        """Create sample users"""
        sample_users = [
            {
                "ShortName": "John Admin",
                "EmailID": "john.admin@drworkplace.microsoft.com",
                "Location": GeoJSONPoint(coordinates=[77.2090, 28.6139]),  # Delhi
                "Contact": ["+91-9876543210", "+91-9876543211"],
                "AADHAR": "123456789012",
                "Status": "Active"
            },
            {
                "ShortName": "Sarah Manager",
                "EmailID": "sarah.manager@drworkplace.microsoft.com",
                "Location": GeoJSONPoint(coordinates=[72.8777, 19.0760]),  # Mumbai
                "Contact": ["+91-9876543220"],
                "Status": "Active"
            },
            {
                "ShortName": "Mike Operator",
                "EmailID": "mike.operator@drworkplace.microsoft.com",
                "Location": GeoJSONPoint(coordinates=[77.5946, 12.9716]),  # Bangalore
                "Contact": ["+91-9876543230", "+91-9876543231"],
                "AADHAR": "234567890123",
                "Status": "Active"
            },
            {
                "ShortName": "Lisa Terminal",
                "EmailID": "lisa.terminal@drworkplace.microsoft.com",
                "Location": GeoJSONPoint(coordinates=[80.2707, 13.0827]),  # Chennai
                "Contact": ["+91-9876543240"],
                "Status": "Active"
            }
        ]
        
        created_emails = []
        for user_data in sample_users:
            try:
                user_create = UserBaseCreate(**user_data)
                user = await UserService.create_user(user_create)
                created_emails.append(user.EmailID)
                logger.info(f"Created user: {user.ShortName}")
            except Exception as e:
                logger.warning(f"Failed to create user {user_data['ShortName']}: {str(e)}")
        
        return created_emails
    
    @staticmethod
    async def create_sample_roles(user_emails: List[str]) -> List[str]:
        """Create sample roles"""
        if len(user_emails) < 4:
            logger.warning("Not enough users created, skipping role creation")
            return []
        
        sample_roles = [
            {
                "Type": "Admin",
                "Location": GeoJSONPoint(coordinates=[77.2090, 28.6139]),  # Delhi
                "UserEmailID": user_emails[0]
            },
            {
                "Type": "Manager",
                "Location": GeoJSONPoint(coordinates=[72.8777, 19.0760]),  # Mumbai
                "UserEmailID": user_emails[1]
            },
            {
                "Type": "Operator",
                "Location": GeoJSONPoint(coordinates=[77.5946, 12.9716]),  # Bangalore
                "UserEmailID": user_emails[2]
            },
            {
                "Type": "TerminalOwner",
                "Location": GeoJSONPoint(coordinates=[80.2707, 13.0827]),  # Chennai
                "UserEmailID": user_emails[3]
            }
        ]
        
        created_role_ids = []
        for role_data in sample_roles:
            try:
                role_create = RolesBaseCreate(**role_data)
                role = await RoleService.create_role(role_create)
                created_role_ids.append(role.RoleID)
                logger.info(f"Created role: {role.RoleID}")
            except Exception as e:
                logger.warning(f"Failed to create role {role_data['Type']}: {str(e)}")
        
        return created_role_ids
    
    @staticmethod
    async def create_sample_terminals(role_ids: List[str]) -> List[str]:
        """Create sample terminals"""
        if len(role_ids) < 2:
            logger.warning("Not enough roles created, skipping terminal creation")
            return []
        
        sample_terminals = [
            {
                "TerminalID": "TERM-DEL-001",
                "Location": GeoJSONPoint(coordinates=[77.2090, 28.6139]),  # Delhi
                "Capacity": TerminalCapacity(
                    ColdStorageLimit=1000,
                    VolumeLimit=5000,
                    WeightLimit=10000
                ),
                "Capabilities": TerminalCapabilities(
                    Refrigeration=True,
                    Weighing=True,
                    Packaging=True,
                    Sorting=False
                ),
                "RoleIDs": role_ids[:2]  # Admin and Manager
            },
            {
                "TerminalID": "TERM-MUM-001",
                "Location": GeoJSONPoint(coordinates=[72.8777, 19.0760]),  # Mumbai
                "Capacity": TerminalCapacity(
                    ColdStorageLimit=800,
                    VolumeLimit=4000,
                    WeightLimit=8000
                ),
                "Capabilities": TerminalCapabilities(
                    Refrigeration=True,
                    Weighing=True,
                    Packaging=False,
                    Sorting=True
                ),
                "RoleIDs": role_ids[1:3] if len(role_ids) > 2 else role_ids[1:2]  # Manager and Operator
            },
            {
                "TerminalID": "TERM-BLR-001",
                "Location": GeoJSONPoint(coordinates=[77.5946, 12.9716]),  # Bangalore
                "Capacity": TerminalCapacity(
                    ColdStorageLimit=1200,
                    VolumeLimit=6000,
                    WeightLimit=12000
                ),
                "Capabilities": TerminalCapabilities(
                    Refrigeration=False,
                    Weighing=True,
                    Packaging=True,
                    Sorting=True
                ),
                "RoleIDs": role_ids[-1:] if len(role_ids) > 3 else []  # TerminalOwner
            }
        ]
        
        created_terminal_ids = []
        for terminal_data in sample_terminals:
            try:
                terminal_create = TerminalBaseCreate(**terminal_data)
                terminal = await TerminalService.create_terminal(terminal_create)
                created_terminal_ids.append(terminal.TerminalID)
                logger.info(f"Created terminal: {terminal.TerminalID}")
            except Exception as e:
                logger.warning(f"Failed to create terminal {terminal_data['TerminalID']}: {str(e)}")
        
        return created_terminal_ids


async def main():
    """Main seeding function"""
    await DatabaseSeeder.seed_sample_data()


if __name__ == "__main__":
    asyncio.run(main())
from sqlmodel import (
    Field,
    JSON,
    SQLModel,
    create_engine,
    select,
    Session,
    insert,
    update,
    delete,
    func,
)
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional, List, Dict, Any

DATABASE_URL = "sqlite:///database.db"
engine = create_engine(DATABASE_URL)

class ServerConfig(SQLModel,table=True):
    ServerID: Optional[int] = Field(default=None,primary_key=True)
    WelcomeChannelID: Optional[int] = None
    TempChannelID: Optional[int] = None
    ReactionToggle: bool = True
    AutoRoles: List[int] = Field(default_factory=list)
    
class UserConfig(SQLModel,table=True):
    UserID: int = Field(default=None,primary_key=True)
    _starbits: int = 0
    StarbitsNext: int = 0 #  Next unix timestamp when the user can collect Starbits, 0 means 1970/1/1 and that has passed, therefore 0

    @property
    def Starbits(self) -> int:
        """Getter for starbits"""
        return self._starbits
    
    @Starbits.setter
    def Starbits(self,value:int) -> None:
        """Setter for starbits with validation"""
        if not isinstance(value,int):
            raise TypeError("Starbits must be an integer")
        if value < 0:
            raise ValueError("You can't go in debt!!!")
        self._starbits = value
        
    
class TempChannel(SQLModel,table=True):
    ChannelID: int = Field(default=None,primary_key=True)
    GuildID: int
    
class ReactRole(SQLModel,table=True):
    ReactRoleID: int = Field(default=None,primary_key=True)
    MessageID: int
    GuildID: int
    Emoji: int
    RoleID: int

def init_db():
    """Initialize the database tables"""
    with engine.begin() as conn:
        SQLModel.metadata.create_all(conn)
        
def get_session() -> Session:
    """Get a database session"""
    return Session(engine)

class Create:
    def ServerConfig(GuildID:int):
        """Create default server configuration"""
        with Session(engine) as session:
            session.add(ServerConfig(ServerID=GuildID))
            session.commit()
            
    def UserConfig(UserID: int) -> None:
        """Create default user configuration"""
        with Session(engine) as session:
            session.add(UserConfig(UserID=UserID))
            session.commit()
    
    
class Set:
    def ServerWelcomeChannel(GuildID:int, ChannelID: int):
        """Set the Welcome channel"""
        with Session(engine) as session:
            stmt = update(ServerConfig)\
                .where(ServerConfig.ServerID == GuildID)\
                    .values(WelcomeChannel=ChannelID)
            session.exec(stmt)
            session.commit()
            
    def ServerTemphub(GuildID:int, ChannelID: int):
        """Set the Temporary channel Hub"""
        Create.ServerConfig(GuildID)
        with Session(engine) as session:
            stmt = update(ServerConfig)\
                .where(ServerConfig.ServerID == GuildID)\
                    .values(TempChannel=ChannelID)
            session.exec(stmt)
            session.commit()
            
    def ServerReact(GuildID:int,Toggle:bool):
        """Set server reaction toggle"""
        with Session(engine) as session:
            stmt = update(ServerConfig)\
                .where(ServerConfig.ServerID == GuildID)\
                    .values(ReactionToggle=Toggle)
            session.exec(stmt)
            session.commit()
            
    def UserStarbits(UserID: int, Starbits: int) -> None:
        """Set starbits for a user using the setter"""
        with Session(engine) as session:
            user = session.exec(
                select(UserConfig).where(UserConfig.UserID == UserID)
            ).first()
            
            if not user:
                user = UserConfig(UserID)
                session.add(user)
            
            user.starbits = Starbits  # Using the setter
            session.commit()

    def UserAddStarbits(UserID: int, Amount: int) -> None:
        """Add starbits to a user using the setter"""
        with Session(engine) as session:
            user = session.exec(
                select(UserConfig).where(UserConfig.UserID == UserID)
            ).first()
            
            if not user:
                user = UserConfig(UserID=UserID)
                session.add(user)
            
            user.starbits += Amount  # Setter handles validation
            session.commit()
            

class Get:
    def UserConfig(UserID):
        """Return User configuration"""
        with Session(engine) as session:
            query = select(UserConfig).where(UserConfig.UserID == UserID)
            result = session.exec(query).first()
            
            if not result:
                Create.UserConfig(UserID)
                result = session.exec(query).first()
            
            return dict(result)
        
    def ServerConfig(GuildID):
        """Return Server configuration"""
        with Session(engine) as session:
            query = select(ServerConfig).where(ServerConfig.ServerID == GuildID)
            result = session.exec(query).first()
            
            if not result:
                Create.ServerConfig(GuildID)
                result = session.exec(query).first()
            
            return dict(result)
            

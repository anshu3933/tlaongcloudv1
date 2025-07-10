"""
Stage 4: Multi-User Collaboration Tools
Real-time collaboration, commenting, and version control for professional review
"""
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import UUID, uuid4
import json

logger = logging.getLogger(__name__)

class CollaborationEventType(Enum):
    """Types of collaboration events"""
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    COMMENT_ADDED = "comment_added"
    COMMENT_EDITED = "comment_edited"
    COMMENT_RESOLVED = "comment_resolved"
    SECTION_VIEWED = "section_viewed"
    SECTION_EDITED = "section_edited"
    APPROVAL_SUBMITTED = "approval_submitted"
    BOOKMARK_ADDED = "bookmark_added"
    ANNOTATION_CREATED = "annotation_created"

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class UserPresenceStatus(Enum):
    """User presence status"""
    ACTIVE = "active"
    VIEWING = "viewing"
    EDITING = "editing"
    IDLE = "idle"
    AWAY = "away"

@dataclass
class UserPresence:
    """User presence information"""
    user_id: str
    user_name: str
    user_role: str
    status: UserPresenceStatus
    current_section: Optional[str]
    last_activity: datetime
    session_duration: timedelta
    avatar_url: Optional[str] = None

@dataclass
class CollaborationComment:
    """Enhanced comment with collaboration features"""
    id: str
    package_id: str
    section: str
    user_id: str
    user_name: str
    user_role: str
    content: str
    comment_type: str  # suggestion, question, concern, approval
    priority: NotificationPriority
    timestamp: datetime
    position: Optional[Dict[str, Any]]  # Text position/selection
    thread_id: Optional[str]  # For threaded comments
    parent_comment_id: Optional[str]
    mentions: List[str]  # User IDs mentioned
    attachments: List[Dict[str, Any]]
    reactions: Dict[str, List[str]]  # emoji -> list of user_ids
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_timestamp: Optional[datetime] = None
    edit_history: List[Dict[str, Any]] = None

@dataclass
class Annotation:
    """Text annotation with highlighting"""
    id: str
    package_id: str
    section: str
    user_id: str
    user_name: str
    text_selection: Dict[str, Any]  # start, end, selected_text
    annotation_type: str  # highlight, note, question, suggestion
    content: str
    color: str
    timestamp: datetime
    visible_to: List[str]  # User roles/IDs who can see this
    linked_comment_id: Optional[str] = None

@dataclass
class Bookmark:
    """Section bookmark for quick navigation"""
    id: str
    package_id: str
    section: str
    user_id: str
    user_name: str
    title: str
    description: Optional[str]
    color: str
    timestamp: datetime
    shared: bool = False
    shared_with: List[str] = None

@dataclass
class CollaborationEvent:
    """Real-time collaboration event"""
    id: str
    package_id: str
    event_type: CollaborationEventType
    user_id: str
    user_name: str
    data: Dict[str, Any]
    timestamp: datetime
    session_id: str

class CollaborationManager:
    """Manages real-time collaboration features"""
    
    def __init__(self):
        self.presence_manager = PresenceManager()
        self.comment_system = CommentSystem()
        self.annotation_system = AnnotationSystem()
        self.notification_system = NotificationSystem()
        self.version_manager = VersionManager()
        self.real_time_sync = RealTimeSyncManager()
        
        # Active sessions tracking
        self.active_sessions: Dict[str, Set[str]] = {}  # package_id -> set of user_ids
        self.user_sessions: Dict[str, Dict[str, Any]] = {}  # user_id -> session_data
    
    async def join_collaboration_session(
        self,
        package_id: str,
        user_id: str,
        user_name: str,
        user_role: str,
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """User joins collaboration session"""
        
        logger.info(f"User {user_name} joining collaboration session for package {package_id}")
        
        # Initialize package session if not exists
        if package_id not in self.active_sessions:
            self.active_sessions[package_id] = set()
        
        # Add user to session
        self.active_sessions[package_id].add(user_id)
        
        # Track user session
        self.user_sessions[user_id] = {
            "package_id": package_id,
            "user_name": user_name,
            "user_role": user_role,
            "join_time": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "current_section": None,
            "session_data": session_data
        }
        
        # Create presence record
        presence = UserPresence(
            user_id=user_id,
            user_name=user_name,
            user_role=user_role,
            status=UserPresenceStatus.ACTIVE,
            current_section=None,
            last_activity=datetime.utcnow(),
            session_duration=timedelta(0)
        )
        
        await self.presence_manager.update_user_presence(presence)
        
        # Broadcast join event
        join_event = CollaborationEvent(
            id=str(uuid4()),
            package_id=package_id,
            event_type=CollaborationEventType.USER_JOINED,
            user_id=user_id,
            user_name=user_name,
            data={"user_role": user_role, "session_id": session_data.get("session_id")},
            timestamp=datetime.utcnow(),
            session_id=session_data.get("session_id", "")
        )\n        \n        await self.real_time_sync.broadcast_event(join_event)\n        \n        # Get current collaboration state\n        collaboration_state = await self.get_collaboration_state(package_id, user_id)\n        \n        return {\n            "success": True,\n            "session_id": session_data.get("session_id"),\n            "collaboration_state": collaboration_state,\n            "active_users": await self.get_active_users(package_id),\n            "recent_activity": await self.get_recent_activity(package_id, limit=10)\n        }\n    \n    async def leave_collaboration_session(\n        self,\n        package_id: str,\n        user_id: str\n    ) -> Dict[str, Any]:\n        """User leaves collaboration session\"\"\"\n        \n        logger.info(f\"User {user_id} leaving collaboration session for package {package_id}\")\n        \n        # Remove from active sessions\n        if package_id in self.active_sessions:\n            self.active_sessions[package_id].discard(user_id)\n            \n            # Clean up empty sessions\n            if not self.active_sessions[package_id]:\n                del self.active_sessions[package_id]\n        \n        # Get user info before removing\n        user_session = self.user_sessions.get(user_id, {})\n        user_name = user_session.get(\"user_name\", \"Unknown\")\n        \n        # Clean up user session\n        if user_id in self.user_sessions:\n            del self.user_sessions[user_id]\n        \n        # Update presence\n        await self.presence_manager.remove_user_presence(user_id)\n        \n        # Broadcast leave event\n        leave_event = CollaborationEvent(\n            id=str(uuid4()),\n            package_id=package_id,\n            event_type=CollaborationEventType.USER_LEFT,\n            user_id=user_id,\n            user_name=user_name,\n            data={},\n            timestamp=datetime.utcnow(),\n            session_id=user_session.get(\"session_data\", {}).get(\"session_id\", \"\")\n        )\n        \n        await self.real_time_sync.broadcast_event(leave_event)\n        \n        return {\n            \"success\": True,\n            \"remaining_users\": len(self.active_sessions.get(package_id, set()))\n        }\n    \n    async def update_user_activity(\n        self,\n        package_id: str,\n        user_id: str,\n        activity_type: str,\n        activity_data: Dict[str, Any]\n    ) -> Dict[str, Any]:\n        \"\"\"Update user activity and presence\"\"\"\n        \n        if user_id not in self.user_sessions:\n            return {\"success\": False, \"error\": \"User not in active session\"}\n        \n        # Update session data\n        self.user_sessions[user_id][\"last_activity\"] = datetime.utcnow()\n        self.user_sessions[user_id][\"current_section\"] = activity_data.get(\"section\")\n        \n        # Determine presence status\n        status = UserPresenceStatus.VIEWING\n        if activity_type == \"editing\":\n            status = UserPresenceStatus.EDITING\n        elif activity_type == \"navigating\":\n            status = UserPresenceStatus.ACTIVE\n        \n        # Update presence\n        session_data = self.user_sessions[user_id]\n        presence = UserPresence(\n            user_id=user_id,\n            user_name=session_data[\"user_name\"],\n            user_role=session_data[\"user_role\"],\n            status=status,\n            current_section=activity_data.get(\"section\"),\n            last_activity=datetime.utcnow(),\n            session_duration=datetime.utcnow() - session_data[\"join_time\"]\n        )\n        \n        await self.presence_manager.update_user_presence(presence)\n        \n        # Create activity event\n        if activity_type in [\"section_viewed\", \"section_edited\"]:\n            event_type = CollaborationEventType.SECTION_VIEWED if activity_type == \"section_viewed\" else CollaborationEventType.SECTION_EDITED\n            \n            activity_event = CollaborationEvent(\n                id=str(uuid4()),\n                package_id=package_id,\n                event_type=event_type,\n                user_id=user_id,\n                user_name=session_data[\"user_name\"],\n                data=activity_data,\n                timestamp=datetime.utcnow(),\n                session_id=session_data.get(\"session_data\", {}).get(\"session_id\", \"\")\n            )\n            \n            await self.real_time_sync.broadcast_event(activity_event)\n        \n        return {\"success\": True}\n    \n    async def add_comment(\n        self,\n        package_id: str,\n        user_id: str,\n        comment_data: Dict[str, Any]\n    ) -> Dict[str, Any]:\n        \"\"\"Add collaborative comment\"\"\"\n        \n        if user_id not in self.user_sessions:\n            return {\"success\": False, \"error\": \"User not in active session\"}\n        \n        session_data = self.user_sessions[user_id]\n        \n        # Create comment\n        comment = CollaborationComment(\n            id=str(uuid4()),\n            package_id=package_id,\n            section=comment_data.get(\"section\", \"\"),\n            user_id=user_id,\n            user_name=session_data[\"user_name\"],\n            user_role=session_data[\"user_role\"],\n            content=comment_data.get(\"content\", \"\"),\n            comment_type=comment_data.get(\"comment_type\", \"comment\"),\n            priority=NotificationPriority(comment_data.get(\"priority\", \"normal\")),\n            timestamp=datetime.utcnow(),\n            position=comment_data.get(\"position\"),\n            thread_id=comment_data.get(\"thread_id\"),\n            parent_comment_id=comment_data.get(\"parent_comment_id\"),\n            mentions=comment_data.get(\"mentions\", []),\n            attachments=comment_data.get(\"attachments\", []),\n            reactions={},\n            edit_history=[]\n        )\n        \n        # Store comment\n        await self.comment_system.add_comment(comment)\n        \n        # Create collaboration event\n        comment_event = CollaborationEvent(\n            id=str(uuid4()),\n            package_id=package_id,\n            event_type=CollaborationEventType.COMMENT_ADDED,\n            user_id=user_id,\n            user_name=session_data[\"user_name\"],\n            data={\n                \"comment_id\": comment.id,\n                \"section\": comment.section,\n                \"comment_type\": comment.comment_type,\n                \"content_preview\": comment.content[:100]\n            },\n            timestamp=datetime.utcnow(),\n            session_id=session_data.get(\"session_data\", {}).get(\"session_id\", \"\")\n        )\n        \n        await self.real_time_sync.broadcast_event(comment_event)\n        \n        # Send notifications\n        await self.notification_system.send_comment_notifications(\n            comment, self.active_sessions.get(package_id, set())\n        )\n        \n        return {\n            \"success\": True,\n            \"comment\": asdict(comment),\n            \"notifications_sent\": len(comment.mentions) + len(self.active_sessions.get(package_id, set())) - 1\n        }\n    \n    async def add_annotation(\n        self,\n        package_id: str,\n        user_id: str,\n        annotation_data: Dict[str, Any]\n    ) -> Dict[str, Any]:\n        \"\"\"Add text annotation\"\"\"\n        \n        if user_id not in self.user_sessions:\n            return {\"success\": False, \"error\": \"User not in active session\"}\n        \n        session_data = self.user_sessions[user_id]\n        \n        annotation = Annotation(\n            id=str(uuid4()),\n            package_id=package_id,\n            section=annotation_data.get(\"section\", \"\"),\n            user_id=user_id,\n            user_name=session_data[\"user_name\"],\n            text_selection=annotation_data.get(\"text_selection\", {}),\n            annotation_type=annotation_data.get(\"annotation_type\", \"highlight\"),\n            content=annotation_data.get(\"content\", \"\"),\n            color=annotation_data.get(\"color\", \"#fbbf24\"),\n            timestamp=datetime.utcnow(),\n            visible_to=annotation_data.get(\"visible_to\", [\"all\"])\n        )\n        \n        await self.annotation_system.add_annotation(annotation)\n        \n        # Broadcast annotation event\n        annotation_event = CollaborationEvent(\n            id=str(uuid4()),\n            package_id=package_id,\n            event_type=CollaborationEventType.ANNOTATION_CREATED,\n            user_id=user_id,\n            user_name=session_data[\"user_name\"],\n            data={\n                \"annotation_id\": annotation.id,\n                \"section\": annotation.section,\n                \"annotation_type\": annotation.annotation_type,\n                \"selected_text\": annotation.text_selection.get(\"selected_text\", \"\")\n            },\n            timestamp=datetime.utcnow(),\n            session_id=session_data.get(\"session_data\", {}).get(\"session_id\", \"\")\n        )\n        \n        await self.real_time_sync.broadcast_event(annotation_event)\n        \n        return {\n            \"success\": True,\n            \"annotation\": asdict(annotation)\n        }\n    \n    async def add_bookmark(\n        self,\n        package_id: str,\n        user_id: str,\n        bookmark_data: Dict[str, Any]\n    ) -> Dict[str, Any]:\n        \"\"\"Add section bookmark\"\"\"\n        \n        if user_id not in self.user_sessions:\n            return {\"success\": False, \"error\": \"User not in active session\"}\n        \n        session_data = self.user_sessions[user_id]\n        \n        bookmark = Bookmark(\n            id=str(uuid4()),\n            package_id=package_id,\n            section=bookmark_data.get(\"section\", \"\"),\n            user_id=user_id,\n            user_name=session_data[\"user_name\"],\n            title=bookmark_data.get(\"title\", \"\"),\n            description=bookmark_data.get(\"description\"),\n            color=bookmark_data.get(\"color\", \"#3b82f6\"),\n            timestamp=datetime.utcnow(),\n            shared=bookmark_data.get(\"shared\", False),\n            shared_with=bookmark_data.get(\"shared_with\", [])\n        )\n        \n        # Store bookmark (in production, this would go to database)\n        # await self.bookmark_system.add_bookmark(bookmark)\n        \n        # Broadcast bookmark event if shared\n        if bookmark.shared:\n            bookmark_event = CollaborationEvent(\n                id=str(uuid4()),\n                package_id=package_id,\n                event_type=CollaborationEventType.BOOKMARK_ADDED,\n                user_id=user_id,\n                user_name=session_data[\"user_name\"],\n                data={\n                    \"bookmark_id\": bookmark.id,\n                    \"section\": bookmark.section,\n                    \"title\": bookmark.title\n                },\n                timestamp=datetime.utcnow(),\n                session_id=session_data.get(\"session_data\", {}).get(\"session_id\", \"\")\n            )\n            \n            await self.real_time_sync.broadcast_event(bookmark_event)\n        \n        return {\n            \"success\": True,\n            \"bookmark\": asdict(bookmark)\n        }\n    \n    async def get_collaboration_state(\n        self,\n        package_id: str,\n        user_id: str\n    ) -> Dict[str, Any]:\n        \"\"\"Get current collaboration state\"\"\"\n        \n        active_users = await self.get_active_users(package_id)\n        comments = await self.comment_system.get_package_comments(package_id)\n        annotations = await self.annotation_system.get_package_annotations(package_id, user_id)\n        bookmarks = await self.get_user_bookmarks(package_id, user_id)\n        \n        return {\n            \"package_id\": package_id,\n            \"active_users\": active_users,\n            \"total_comments\": len(comments),\n            \"unresolved_comments\": len([c for c in comments if not c.resolved]),\n            \"user_annotations\": len(annotations),\n            \"user_bookmarks\": len(bookmarks),\n            \"real_time_features\": {\n                \"presence_updates\": True,\n                \"live_comments\": True,\n                \"shared_cursors\": True,\n                \"activity_feed\": True\n            }\n        }\n    \n    async def get_active_users(self, package_id: str) -> List[Dict[str, Any]]:\n        \"\"\"Get list of active users in collaboration session\"\"\"\n        \n        active_user_ids = self.active_sessions.get(package_id, set())\n        active_users = []\n        \n        for user_id in active_user_ids:\n            if user_id in self.user_sessions:\n                session_data = self.user_sessions[user_id]\n                presence = await self.presence_manager.get_user_presence(user_id)\n                \n                user_info = {\n                    \"user_id\": user_id,\n                    \"user_name\": session_data[\"user_name\"],\n                    \"user_role\": session_data[\"user_role\"],\n                    \"status\": presence.status.value if presence else \"unknown\",\n                    \"current_section\": presence.current_section if presence else None,\n                    \"last_activity\": session_data[\"last_activity\"].isoformat(),\n                    \"session_duration\": str(datetime.utcnow() - session_data[\"join_time\"])\n                }\n                \n                active_users.append(user_info)\n        \n        return active_users\n    \n    async def get_recent_activity(\n        self,\n        package_id: str,\n        limit: int = 20\n    ) -> List[Dict[str, Any]]:\n        \"\"\"Get recent collaboration activity\"\"\"\n        \n        # This would fetch from event store in production\n        # For now, return mock recent activity\n        recent_activity = [\n            {\n                \"id\": str(uuid4()),\n                \"type\": \"comment_added\",\n                \"user_name\": \"Dr. Smith\",\n                \"action\": \"added a comment\",\n                \"section\": \"Present Levels\",\n                \"timestamp\": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),\n                \"preview\": \"Consider adding more specific data...\"\n            },\n            {\n                \"id\": str(uuid4()),\n                \"type\": \"section_viewed\",\n                \"user_name\": \"Ms. Johnson\",\n                \"action\": \"viewed section\",\n                \"section\": \"Goals\",\n                \"timestamp\": (datetime.utcnow() - timedelta(minutes=10)).isoformat()\n            }\n        ]\n        \n        return recent_activity[:limit]\n    \n    async def get_user_bookmarks(\n        self,\n        package_id: str,\n        user_id: str\n    ) -> List[Dict[str, Any]]:\n        \"\"\"Get user's bookmarks for package\"\"\"\n        \n        # This would fetch from database in production\n        return []\n\n\nclass PresenceManager:\n    \"\"\"Manages user presence information\"\"\"\n    \n    def __init__(self):\n        self.user_presence: Dict[str, UserPresence] = {}\n    \n    async def update_user_presence(self, presence: UserPresence):\n        \"\"\"Update user presence\"\"\"\n        self.user_presence[presence.user_id] = presence\n    \n    async def get_user_presence(self, user_id: str) -> Optional[UserPresence]:\n        \"\"\"Get user presence\"\"\"\n        return self.user_presence.get(user_id)\n    \n    async def remove_user_presence(self, user_id: str):\n        \"\"\"Remove user presence\"\"\"\n        if user_id in self.user_presence:\n            del self.user_presence[user_id]\n\n\nclass CommentSystem:\n    \"\"\"Manages collaborative comments\"\"\"\n    \n    def __init__(self):\n        self.comments: Dict[str, List[CollaborationComment]] = {}  # package_id -> comments\n    \n    async def add_comment(self, comment: CollaborationComment):\n        \"\"\"Add comment to system\"\"\"\n        if comment.package_id not in self.comments:\n            self.comments[comment.package_id] = []\n        \n        self.comments[comment.package_id].append(comment)\n    \n    async def get_package_comments(self, package_id: str) -> List[CollaborationComment]:\n        \"\"\"Get all comments for a package\"\"\"\n        return self.comments.get(package_id, [])\n    \n    async def resolve_comment(self, comment_id: str, resolver_id: str):\n        \"\"\"Resolve a comment\"\"\"\n        for package_comments in self.comments.values():\n            for comment in package_comments:\n                if comment.id == comment_id:\n                    comment.resolved = True\n                    comment.resolved_by = resolver_id\n                    comment.resolved_timestamp = datetime.utcnow()\n                    break\n\n\nclass AnnotationSystem:\n    \"\"\"Manages text annotations\"\"\"\n    \n    def __init__(self):\n        self.annotations: Dict[str, List[Annotation]] = {}  # package_id -> annotations\n    \n    async def add_annotation(self, annotation: Annotation):\n        \"\"\"Add annotation to system\"\"\"\n        if annotation.package_id not in self.annotations:\n            self.annotations[annotation.package_id] = []\n        \n        self.annotations[annotation.package_id].append(annotation)\n    \n    async def get_package_annotations(\n        self, \n        package_id: str, \n        user_id: str\n    ) -> List[Annotation]:\n        \"\"\"Get annotations visible to user\"\"\"\n        package_annotations = self.annotations.get(package_id, [])\n        \n        # Filter annotations based on visibility\n        visible_annotations = []\n        for annotation in package_annotations:\n            if (annotation.user_id == user_id or \n                \"all\" in annotation.visible_to or \n                user_id in annotation.visible_to):\n                visible_annotations.append(annotation)\n        \n        return visible_annotations\n\n\nclass NotificationSystem:\n    \"\"\"Manages collaboration notifications\"\"\"\n    \n    async def send_comment_notifications(\n        self, \n        comment: CollaborationComment, \n        active_users: Set[str]\n    ):\n        \"\"\"Send notifications for new comment\"\"\"\n        \n        # In production, this would send real notifications\n        logger.info(f\"Sending comment notifications for comment {comment.id} to {len(active_users)} users\")\n    \n    async def send_mention_notifications(\n        self, \n        comment: CollaborationComment\n    ):\n        \"\"\"Send notifications for user mentions\"\"\"\n        \n        for mentioned_user in comment.mentions:\n            logger.info(f\"Sending mention notification to user {mentioned_user}\")\n\n\nclass VersionManager:\n    \"\"\"Manages content versions and change tracking\"\"\"\n    \n    def __init__(self):\n        self.versions: Dict[str, List[Dict[str, Any]]] = {}  # package_id -> versions\n    \n    async def create_version(\n        self, \n        package_id: str, \n        content: Dict[str, Any], \n        user_id: str, \n        change_description: str\n    ) -> str:\n        \"\"\"Create new version\"\"\"\n        \n        version_id = str(uuid4())\n        version_data = {\n            \"version_id\": version_id,\n            \"package_id\": package_id,\n            \"content\": content,\n            \"created_by\": user_id,\n            \"created_at\": datetime.utcnow().isoformat(),\n            \"change_description\": change_description,\n            \"version_number\": len(self.versions.get(package_id, [])) + 1\n        }\n        \n        if package_id not in self.versions:\n            self.versions[package_id] = []\n        \n        self.versions[package_id].append(version_data)\n        \n        return version_id\n    \n    async def get_version_history(self, package_id: str) -> List[Dict[str, Any]]:\n        \"\"\"Get version history for package\"\"\"\n        return self.versions.get(package_id, [])\n\n\nclass RealTimeSyncManager:\n    \"\"\"Manages real-time synchronization of collaboration events\"\"\"\n    \n    def __init__(self):\n        self.event_subscribers: Dict[str, Set[str]] = {}  # package_id -> set of user_ids\n        self.event_history: Dict[str, List[CollaborationEvent]] = {}  # package_id -> events\n    \n    async def broadcast_event(self, event: CollaborationEvent):\n        \"\"\"Broadcast event to all subscribers\"\"\"\n        \n        # Store event in history\n        if event.package_id not in self.event_history:\n            self.event_history[event.package_id] = []\n        \n        self.event_history[event.package_id].append(event)\n        \n        # In production, this would use WebSockets or Server-Sent Events\n        logger.info(f\"Broadcasting event {event.event_type.value} for package {event.package_id}\")\n    \n    async def subscribe_to_events(self, package_id: str, user_id: str):\n        \"\"\"Subscribe user to package events\"\"\"\n        if package_id not in self.event_subscribers:\n            self.event_subscribers[package_id] = set()\n        \n        self.event_subscribers[package_id].add(user_id)\n    \n    async def unsubscribe_from_events(self, package_id: str, user_id: str):\n        \"\"\"Unsubscribe user from package events\"\"\"\n        if package_id in self.event_subscribers:\n            self.event_subscribers[package_id].discard(user_id)
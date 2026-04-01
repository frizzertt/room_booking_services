import uuid
from uuid import UUID


class ConferenceService:
    def create_link(self, *, slot_id: UUID, user_id: UUID) -> str:
        return f"https://conference.local/room/{slot_id}?invite={user_id}&meeting={uuid.uuid4()}"


conference_service = ConferenceService()

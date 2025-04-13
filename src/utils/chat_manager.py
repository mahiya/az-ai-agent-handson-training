from dataclasses import dataclass
from abc import ABCMeta, abstractmethod


@dataclass
class AgentChat:
    chat_id: str
    chat_title: str
    user_id: str
    agent_id: str
    thread_id: str
    messages: list[dict]  # For displaying in the UI


class ChatManager(metaclass=ABCMeta):

    @abstractmethod
    def list_chats(self, user_id: str) -> list[AgentChat]:
        """
        List all agents for a user.
        """
        pass

    @abstractmethod
    def set_chat(self, chat_id: str, chat: AgentChat):
        """
        Add an agent for a user.
        """
        pass

    @abstractmethod
    def get_chat(self, chat_id: str) -> AgentChat | None:
        """
        Get the agent for a user.
        """
        pass

    @abstractmethod
    def delete_chat(self, chat_id: str):
        """
        Delete an agent for a user.
        """
        pass


class InMemoryChatManager(ChatManager):

    def __init__(self):
        self.chats = {}  # Key: chat_id, Value: AgentChat object

    def list_chats(self, user_id: str) -> list[AgentChat]:
        """
        List all agents for a user.
        """
        return [chat for chat in self.chats.values() if chat.user_id == user_id]

    def set_chat(self, chat_id: str, chat: AgentChat):
        """
        Add an agent for a user.
        """
        self.chats[chat_id] = chat

    def get_chat(self, chat_id: str) -> AgentChat | None:
        """
        Get the agent for a user.
        """
        return self.chats.get(chat_id)

    def delete_chat(self, chat_id: str):
        """
        Delete an agent for a user.
        """
        if chat_id in self.chats:
            del self.chats[chat_id]

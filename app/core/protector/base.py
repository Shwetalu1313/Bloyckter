from abc import ABC, abstractmethod

class Protector(ABC):
    """
    Abstract Base Class for all protection engines.
    Ensures a consistent interface for local folders, USB drives, 
    and future remote targets.
    """

    @abstractmethod
    def lock(self, target: str, **kwargs) -> tuple[bool, str]:
        """
        Secure the target.
        Returns: (success_bool, message_str)
        """
        pass

    @abstractmethod
    def unlock(self, target: str, password: str) -> tuple[bool, str]:
        """
        Release the target.
        Returns: (success_bool, message_str)
        """
        pass

    @abstractmethod
    def change_password(self, target: str, current_pwd: str, new_pwd: str) -> tuple[bool, str]:
        """
        Update security credentials for the target.
        Returns: (success_bool, message_str)
        """
        pass
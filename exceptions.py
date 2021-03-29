
class ConnectionError(Exception):
    """
    Exception raised when the user is not connected to the Aumax API
    """

    def __init__(self) -> None:
        super().__init__("Please first connect to the Aumax API using the 'connect' method / Merci de vous connecter d'abord en utilisant la méthode 'connect'")


class SensibleOperationsDisabledError(Exception):
    """
    Exception raised when the user has not enabled sensible operations
    """

    def __init__(self) -> None:
        super().__init__("Please first enable sensible operations using the 'enableSensibleOperations' method / Merci d'activer les operations sensibles d'abord en utilisant la méthode 'enableSensibleOperations'")



class Event:

    __instance = None
    __db = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if Event.__instance is None:
            raise Exception("Instantiate first")
        return Event.__instance

    def __init__(self, db):
        if Event.__instance is not None:
            raise Exception("Singleton already initialized")
        else:
            Event.__instance = self

        self.__db = db

    @staticmethod
    def logStateEvent(name, change_from, change_to, opaque=None):
        Event.getInstance().__db.logStateChangeEvent(name, change_from, change_to)

    @staticmethod
    def logOpaqueEvent(name, opaque):
        Event.getInstance().__db.logOpaqueEvent(name, opaque)

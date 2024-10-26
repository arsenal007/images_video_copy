

class CreationTimeExtractor:
    def get_creation_time(self, file):
        """
        Returns the creation time of the file or None if the time cannot be determined.
        """
        raise NotImplementedError("Must be implemented in the subclass")

class ConfigError(Exception):
    """A config a reader must refuse. `code` is one of the conformance error codes."""

    def __init__(self, code, problems):
        self.code = code
        self.problems = list(problems)
        super().__init__(f"{code}: " + "; ".join(self.problems))


class ListingError(Exception):
    """A directory listing that does not follow DirectoryListing.schema.json."""


class GenerationError(Exception):
    """A location that cannot be generated for an entity. `code` is one of the generation error codes."""

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")

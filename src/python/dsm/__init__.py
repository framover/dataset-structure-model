"""Reference reader for Dataset Structure Model configs.

Validate a config, take a directory listing, walk it into entity records, and
compare readers against the conformance fixtures.
"""
from .compare import compare_results
from .config import Config
from .errors import ConfigError, ListingError
from .extract import ExtractorRegistry
from .listing import Listing, Root, load_listing, root_from_directory, root_from_lines
from .records import Issue, LocationEntry, Record, Unmatched, WalkResult
from .report import render_report
from .validate import check_references, load_config, schema_errors, validate_config
from .walk import Walker, walk

__version__ = "0.1.0"

__all__ = [
    "Config", "ConfigError", "ListingError", "ExtractorRegistry",
    "Listing", "Root", "load_listing", "root_from_directory", "root_from_lines",
    "Issue", "LocationEntry", "Record", "Unmatched", "WalkResult",
    "Walker", "walk", "compare_results", "render_report",
    "check_references", "load_config", "schema_errors", "validate_config",
    "__version__",
]

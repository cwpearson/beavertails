"""
Try to import hard-coded version, otherwise, provide it at runtime
"""

try:
    from beavertails._version import GIT_TAG, GIT_BRANCH, GIT_SHA
except ImportError:
    GIT_TAG = ""
    GIT_BRANCH = ""
    GIT_SHA = ""

if GIT_TAG:
    VERSION = GIT_TAG
elif GIT_BRANCH:
    VERSION = f"{GIT_BRANCH}-{GIT_SHA}"
else:
    VERSION = GIT_SHA

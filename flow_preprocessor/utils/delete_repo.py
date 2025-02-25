"""
Simple Util to delete a repository.
"""

import shutil
import os
from typing import Tuple


async def deleteRepo(repo_name: str) -> Tuple[bool, str]:
    """
    Delete a repository locally.
    """
    dir_to_delete = os.path.join('data', repo_name.replace('/', '___'))
    if os.path.exists(dir_to_delete):
        shutil.rmtree(dir_to_delete)
        success = True
    else:
        return False, f"Directory for {repo_name} doesn't exist"

    if success:
        return True, f"Successfully deleted {repo_name}"
    else:
        return False, f"Failed to delete {repo_name}"

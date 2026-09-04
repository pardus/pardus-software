#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 14:53:00 2020

@author: fatih
"""

import os
import pwd
import re
import shutil
import subprocess
import sys

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.][a-zA-Z0-9_.-]*\$?$")


def validate_username(username):
    if not username or not USERNAME_REGEX.match(username):
        sys.stderr.write(f"Error: Invalid username format: '{username}'.\n")
        return False
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        sys.stderr.write(f"Error: User '{username}' does not exist.\n")
        return False


def main():
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: Group.py <add|del> <username>\n")
        sys.exit(1)

    action = sys.argv[1]
    user = sys.argv[2]

    if not validate_username(user):
        sys.exit(1)

    target_group = "pardus-software"

    if action == "add":
        cmd_name = "adduser"
        cmd_path = shutil.which(cmd_name) or (
            f"/usr/sbin/{cmd_name}" if os.path.exists(f"/usr/sbin/{cmd_name}") else None
        )
        if not cmd_path:
            sys.stderr.write(f"Error: Command '{cmd_name}' not found on system.\n")
            sys.exit(1)
        rc = subprocess.call([cmd_path, user, target_group])
        sys.exit(rc)
    elif action == "del":
        cmd_name = "deluser"
        cmd_path = shutil.which(cmd_name) or (
            f"/usr/sbin/{cmd_name}" if os.path.exists(f"/usr/sbin/{cmd_name}") else None
        )
        if not cmd_path:
            sys.stderr.write(f"Error: Command '{cmd_name}' not found on system.\n")
            sys.exit(1)
        rc = subprocess.call([cmd_path, user, target_group])
        sys.exit(rc)
    else:
        sys.stderr.write(f"Error: Unknown action '{action}'. Valid actions are 'add' or 'del'.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

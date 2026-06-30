def can_access(user):
    if user is not None:
        if user.get("active"):
            if not user.get("locked"):
                if "admin" in user.get("roles", []):
                    return True
                if "editor" in user.get("roles", []):
                    if user.get("verified"):
                        return True
    return False

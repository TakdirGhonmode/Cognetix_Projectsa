class User:
    def __init__(self, id=None, username=None, password=None, role=None, created_at=None):
        self.id = id
        self.username = username
        self.password = password
        self.role = role
        self.created_at = created_at

    def __str__(self):
        return (
            f"User("
            f"id={self.id}, "
            f"username='{self.username}', "
            f"role='{self.role}', "
            f"created_at='{self.created_at}')"
        )
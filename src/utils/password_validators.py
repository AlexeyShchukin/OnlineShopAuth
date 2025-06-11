from re import search


def validate_password_strength(pwd: str) -> str:
    if not search(r'[A-Z]', pwd):
        raise ValueError('The password must contain at least one capital letter.')
    if not search(r'[a-z]', pwd):
        raise ValueError('The password must contain at least one lowercase letter.')
    if not search(r'[0-9]', pwd):
        raise ValueError('The password must contain at least one number.')
    if not search(r'[^A-Za-z0-9]', pwd):
        raise ValueError('The password must contain at least one special character.')
    if search(r'\s', pwd):
        raise ValueError('The password cannot contain spaces.')
    return pwd

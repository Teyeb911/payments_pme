import uuid


def generate_reference() -> str:
    """Génère une référence unique pour une transaction."""
    return uuid.uuid4().hex.upper()[:16]


def success_response(data=None, message='Succès', status_code=200) -> dict:
    return {
        'success': True,
        'message': message,
        'data':    data,
    }

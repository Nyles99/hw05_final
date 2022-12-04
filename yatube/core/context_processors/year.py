from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    year: int = datetime.now().year
    return {
        'year': year
    }

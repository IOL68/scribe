"""
Reportador automático de errores a GitHub Issues
"""

import platform
import traceback
import requests
from . import __version__

# Token con permisos solo para crear issues en IOL68/scribe
GITHUB_TOKEN = "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"
REPO = "IOL68/scribe"


def report_error(error: Exception, context: str = ""):
    """
    Reporta un error automáticamente a GitHub Issues.

    Args:
        error: La excepción que ocurrió
        context: Contexto adicional (ej: "transcribiendo audio", "UI")
    """
    try:
        title = f"[Auto] {type(error).__name__}: {str(error)[:50]}"

        body = f"""## Error automático reportado

**Error:** `{type(error).__name__}`
**Mensaje:** {str(error)}
**Contexto:** {context or "No especificado"}

### Sistema
- **OS:** {platform.platform()}
- **Python:** {platform.python_version()}
- **Scribe:** {__version__}

### Stack Trace
```
{traceback.format_exc()}
```

---
*Este issue fue creado automáticamente por Scribe*
"""

        response = requests.post(
            f"https://api.github.com/repos/{REPO}/issues",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
            },
            json={
                "title": title,
                "body": body,
                "labels": ["bug", "auto-reported"]
            },
            timeout=10
        )

        if response.status_code == 201:
            return True, "Error reportado automáticamente"
        else:
            return False, f"No se pudo reportar: {response.status_code}"

    except Exception:
        # Si falla el reporte, no queremos otro error
        return False, "No se pudo reportar el error"

"""Una carpeta remota por serie; el valor histórico sigue siendo compatible."""
import re

def workspace_root(env):
    path = env.get('workspace_root', '/Shared/ianbal-genie-iac').rstrip('/')
    if not re.fullmatch(r'/Shared/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*', path):
        raise ValueError('workspace_root debe ser /Shared/nombre-unico, sin espacios ni .. ni prefijo /Workspace')
    return path

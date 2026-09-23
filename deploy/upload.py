"""Reutiliza código remoto solo si coincide byte a byte con la revisión Git."""
def ensure_file(workspace, path, content):
    from databricks.sdk.errors import ResourceDoesNotExist
    from databricks.sdk.service.workspace import ImportFormat
    try:
        existing = workspace.download(path).read()
    except ResourceDoesNotExist:
        workspace.upload(path, content, format=ImportFormat.AUTO, overwrite=False)
        return
    if existing != content:
        raise ValueError('El archivo remoto difiere de la revisión Git: ' + path)

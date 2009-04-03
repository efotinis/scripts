// Replace a path extension or add one if missing.
// 'ext' may be '' to remove extension; its leading dot is optional.
function replaceExt(path, ext) {
    if (ext && ext[0] != '.') ext = '.' + ext;
    return fso.BuildPath(
        fso.GetParentFolderName(path), 
        fso.GetBaseName(path) + ext);
}
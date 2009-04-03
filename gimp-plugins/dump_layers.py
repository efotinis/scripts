import os
from gimpfu import *


#gettext.install("gimp20-python", gimp.locale_directory, unicode=True)


def _make_unique(s):
    """Modify file path by adding an index in parens,
    if needed, to obtain a non-existing name."""
    base, ext = os.path.splitext(s)
    i = 2
    while os.path.exists(s):
        s = '%s (%d)%s' % (base, i, ext)
        i += 1
    return s


def dump_layers(img, drawable, outdir, use_layer_names, keep_alpha):
    save_bmp = gimp.pdb.file_bmp_save
    flatten_layer = gimp.pdb['gimp-layer-flatten']

    try:
        gimp.context_push()
        img.undo_group_start()

        for i, layer in enumerate(img.layers):
            name = layer.name if use_layer_names else str(i + 1)
            if name[-4:].lower() != '.bmp':
                name += '.bmp'
            fpath = _make_unique(os.path.join(outdir, name))
            if layer.has_alpha and not keep_alpha:
                temp_layer = layer.copy()
                flatten_layer(temp_layer)
                save_bmp(img, temp_layer, fpath, fpath)
                gimp.delete(temp_layer)
            else:
                save_bmp(img, layer, fpath, fpath)
    finally:
        img.undo_group_end()
        gimp.context_pop()


register(
    "python-fu-dumplayers",
    "Dump image layers to BMPs",
    "Dumps all the layers of an image to BMP files.",
    "Elias Fotinis",
    "Elias Fotinis",
    "2008",
    "Dump _Layers...",
    "RGB*, GRAY*",
    [
        (PF_IMAGE,      "image",            "Input image",      None),
        (PF_DRAWABLE,   "drawable",         "Input drawable",   None),
        (PF_STRING,     "outdir",           "_Output dir",      ""),
        (PF_BOOL,       "use_layer_names",  "_Use layer names", True),
        (PF_BOOL,       "keep_alpha",       "_Keep alpha (save 32-bit)", False),
    ],
    [],
    dump_layers,
    menu="<Image>/Image",
    domain=("gimp20-python", gimp.locale_directory)
    )


main()

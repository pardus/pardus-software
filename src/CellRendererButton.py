from gi.repository import GObject, Gtk


class CellRendererButton(Gtk.CellRenderer):
    __gsignals__ = {
        'clicked': (GObject.SignalFlags.RUN_FIRST,
                    None,
                    (GObject.TYPE_STRING,))
    }

    text = GObject.property(type=str, default='')

    def __init__(self, text=''):
        GObject.GObject.__init__(self)
        self._xpad = 6
        self._ypad = 2
        self.props.mode = Gtk.CellRendererMode.ACTIVATABLE
        self.props.text = text

    def do_get_size(self, widget, *args):
        context = widget.get_pango_context()
        metrics = context.get_metrics(widget.get_style().font_desc,
                                      context.get_language())
        row_height = metrics.get_ascent() + metrics.get_descent()
        height = (row_height + 512 >> 10) + self._ypad * 2

        layout = widget.create_pango_layout(self.props.text)
        (row_width, layout_height) = layout.get_pixel_size()
        width = row_width + self._xpad * 2

        return (0, 0, width, height)

    def do_render(self, cr, widget, background_area, cell_area, flags):
        style = widget.get_style()
        state = widget.get_state()

        layout = widget.create_pango_layout(self.props.text)
        (layout_width, layout_height) = layout.get_pixel_size()
        layout_xoffset = (cell_area.width - layout_width) / 2 + cell_area.x
        layout_yoffset = (cell_area.height - layout_height) / 2 + cell_area.y

        Gtk.paint_box(style, cr, state, Gtk.ShadowType.OUT,
                      widget, 'button',
                      cell_area.x, cell_area.y,
                      cell_area.width, cell_area.height)
        Gtk.paint_layout(style, cr, state, True,
                         widget, "cellrenderertext", layout_xoffset,
                         layout_yoffset, layout)

    def do_activate(self, event, widget, path, background_area, cell_area, flags):
        self.emit('clicked', path)


GObject.type_register(CellRendererButton)

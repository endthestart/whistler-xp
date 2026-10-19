/*
 * xptrayedge - the dark/light bevel on the left edge of the XP notification
 * area. Place it immediately before the systray plugin.
 */
#include <gtk/gtk.h>
#include <libxfce4panel/libxfce4panel.h>

static const double stops[][4] = {
    { 0.00, 0x0C, 0x59, 0xB9 }, { 0.06, 0x13, 0x9E, 0xE9 }, { 0.10, 0x18, 0xB5, 0xF2 },
    { 0.14, 0x13, 0x9B, 0xEB }, { 0.19, 0x12, 0x90, 0xE8 }, { 0.63, 0x0D, 0x8D, 0xEA },
    { 0.81, 0x0D, 0x9F, 0xF1 }, { 0.88, 0x0F, 0x9E, 0xED }, { 0.91, 0x11, 0x9B, 0xE9 },
    { 0.94, 0x13, 0x92, 0xE2 }, { 0.97, 0x13, 0x7E, 0xD7 }, { 1.00, 0x09, 0x5B, 0xC9 },
};

#define EDGE_IMAGE "/usr/share/whistler/assets/current/panel/tray-edge.png"

static gboolean
on_draw (GtkWidget *widget, cairo_t *cr, gpointer data)
{
    GdkPixbuf *edge = data;
    gint w = gtk_widget_get_allocated_width (widget);
    gint h = gtk_widget_get_allocated_height (widget);
    cairo_pattern_t *pat;
    guint i;

    if (edge != NULL) {
        /* imported original artwork: draw it stretched to the panel height */
        gdouble sy = (gdouble) h / gdk_pixbuf_get_height (edge);
        cairo_save (cr);
        cairo_scale (cr, 1.0, sy);
        gdk_cairo_set_source_pixbuf (cr, edge, 0, 0);
        cairo_paint (cr);
        cairo_restore (cr);
        return FALSE;
    }

    pat = cairo_pattern_create_linear (0, 0, 0, h);

    for (i = 0; i < G_N_ELEMENTS (stops); i++)
        cairo_pattern_add_color_stop_rgb (pat, stops[i][0], stops[i][1] / 255.0,
                                          stops[i][2] / 255.0, stops[i][3] / 255.0);
    cairo_set_source (cr, pat);
    cairo_rectangle (cr, 0, 0, w, h);
    cairo_fill (cr);
    cairo_pattern_destroy (pat);

    cairo_set_source_rgb (cr, 0x10 / 255.0, 0x42 / 255.0, 0xAF / 255.0);
    cairo_rectangle (cr, 0, 0, 1, h);
    cairo_fill (cr);
    cairo_set_source_rgba (cr, 0x18 / 255.0, 0xBB / 255.0, 0xFF / 255.0, 0.9);
    cairo_rectangle (cr, 1, 1, 1, h - 1);
    cairo_fill (cr);
    return FALSE;
}

static void
xptrayedge_construct (XfcePanelPlugin *plugin)
{
    GtkWidget *area = gtk_drawing_area_new ();
    GdkPixbuf *edge = gdk_pixbuf_new_from_file (EDGE_IMAGE, NULL);
    gtk_widget_set_name (area, "xp-tray-edge");
    gtk_widget_set_size_request (area, edge ? gdk_pixbuf_get_width (edge) : 4, -1);
    g_signal_connect (area, "draw", G_CALLBACK (on_draw), edge);
    gtk_container_add (GTK_CONTAINER (plugin), area);
    xfce_panel_plugin_set_shrink (plugin, FALSE);
    gtk_widget_show_all (GTK_WIDGET (plugin));
}

XFCE_PANEL_PLUGIN_REGISTER (xptrayedge_construct);

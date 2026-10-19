/*
 * xpstart - the XP-style "start" button for xfce4-panel.
 *
 * Clicking the button activates the "toggle" action of the start menu
 * service (org.whistler.StartMenu, a GtkApplication) over D-Bus, falling
 * back to spawning `whistler-startmenu --toggle` when it is not running.
 * The menu broadcasts org.whistler.StartMenu.VisibilityChanged(b) so the
 * button stays pressed while the menu is open, like on XP.
 */
#include <gtk/gtk.h>
#include <libxfce4panel/libxfce4panel.h>

#define MENU_BUS_NAME "org.whistler.StartMenu"
#define MENU_PATH     "/org/whistler/StartMenu"

typedef struct {
    XfcePanelPlugin *plugin;
    GtkWidget *button;
    GDBusConnection *bus;
    guint signal_id;
    gboolean syncing;
} XpStart;

static void
set_pressed (XpStart *xs, gboolean pressed)
{
    xs->syncing = TRUE;
    gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (xs->button), pressed);
    xs->syncing = FALSE;
}

static void
spawn_menu (XpStart *xs)
{
    gchar *argv[] = { (gchar *) "whistler-startmenu", (gchar *) "--toggle", NULL };
    GError *err = NULL;
    if (!g_spawn_async (NULL, argv, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL, NULL, &err)) {
        g_warning ("xpstart: cannot launch start menu: %s", err->message);
        g_error_free (err);
        set_pressed (xs, FALSE);
    }
}

static void
on_activate_done (GObject *source, GAsyncResult *res, gpointer data)
{
    XpStart *xs = data;
    GError *err = NULL;
    GVariant *ret = g_dbus_connection_call_finish (G_DBUS_CONNECTION (source), res, &err);
    if (ret != NULL) {
        g_variant_unref (ret);
        return;
    }
    g_error_free (err);
    spawn_menu (xs);
}

static void
toggle_menu (XpStart *xs)
{
    if (xs->bus == NULL) {
        spawn_menu (xs);
        return;
    }
    g_dbus_connection_call (xs->bus, MENU_BUS_NAME, MENU_PATH, "org.gtk.Actions", "Activate",
                            g_variant_new ("(s@av@a{sv})", "toggle",
                                           g_variant_new_array (G_VARIANT_TYPE_VARIANT, NULL, 0),
                                           g_variant_new_array (G_VARIANT_TYPE ("{sv}"), NULL, 0)),
                            NULL, G_DBUS_CALL_FLAGS_NO_AUTO_START, 2000, NULL, on_activate_done, xs);
}

static void
on_toggled (GtkToggleButton *button, XpStart *xs)
{
    if (xs->syncing)
        return;
    /* Look pressed until the menu reports back. */
    set_pressed (xs, TRUE);
    toggle_menu (xs);
}

static void
on_visibility (GDBusConnection *bus, const gchar *sender, const gchar *path, const gchar *iface,
               const gchar *signal, GVariant *params, gpointer data)
{
    gboolean visible = FALSE;
    g_variant_get (params, "(b)", &visible);
    set_pressed ((XpStart *) data, visible);
}

static gboolean
on_remote_event (XfcePanelPlugin *plugin, const gchar *name, const GValue *value, XpStart *xs)
{
    if (g_strcmp0 (name, "popup") == 0) {
        toggle_menu (xs);
        return TRUE;
    }
    return FALSE;
}

static gboolean
on_size_changed (XfcePanelPlugin *plugin, gint size, XpStart *xs)
{
    if (xfce_panel_plugin_get_orientation (plugin) == GTK_ORIENTATION_HORIZONTAL)
        gtk_widget_set_size_request (GTK_WIDGET (plugin), -1, size);
    else
        gtk_widget_set_size_request (GTK_WIDGET (plugin), size, -1);
    return TRUE;
}

static void
on_free_data (XfcePanelPlugin *plugin, XpStart *xs)
{
    if (xs->bus != NULL) {
        if (xs->signal_id)
            g_dbus_connection_signal_unsubscribe (xs->bus, xs->signal_id);
        g_object_unref (xs->bus);
    }
    g_slice_free (XpStart, xs);
}

static void
xpstart_construct (XfcePanelPlugin *plugin)
{
    XpStart *xs = g_slice_new0 (XpStart);
    GtkWidget *box, *image, *label;

    xs->plugin = plugin;
    xs->bus = g_bus_get_sync (G_BUS_TYPE_SESSION, NULL, NULL);
    if (xs->bus != NULL)
        xs->signal_id = g_dbus_connection_signal_subscribe (xs->bus, NULL, "org.whistler.StartMenu",
                                                            "VisibilityChanged", MENU_PATH, NULL,
                                                            G_DBUS_SIGNAL_FLAGS_NONE, on_visibility,
                                                            xs, NULL);

    xs->button = gtk_toggle_button_new ();
    gtk_widget_set_name (xs->button, "xp-start-button");
    gtk_button_set_relief (GTK_BUTTON (xs->button), GTK_RELIEF_NONE);
    gtk_widget_set_focus_on_click (xs->button, FALSE);
    gtk_widget_set_tooltip_text (xs->button, "Click here to begin");

    box = gtk_box_new (GTK_ORIENTATION_HORIZONTAL, 0);
    image = gtk_image_new_from_icon_name ("whistler-start-logo", GTK_ICON_SIZE_LARGE_TOOLBAR);
    gtk_image_set_pixel_size (GTK_IMAGE (image), 22);
    gtk_widget_set_name (image, "xp-start-logo");
    label = gtk_label_new ("start");
    gtk_widget_set_name (label, "xp-start-label");
    gtk_box_pack_start (GTK_BOX (box), image, FALSE, FALSE, 0);
    gtk_box_pack_start (GTK_BOX (box), label, FALSE, FALSE, 0);
    gtk_container_add (GTK_CONTAINER (xs->button), box);
    gtk_container_add (GTK_CONTAINER (plugin), xs->button);

    xfce_panel_plugin_add_action_widget (plugin, xs->button);
    xfce_panel_plugin_set_shrink (plugin, FALSE);
    xfce_panel_plugin_set_small (plugin, FALSE);

    g_signal_connect (xs->button, "toggled", G_CALLBACK (on_toggled), xs);
    g_signal_connect (plugin, "remote-event", G_CALLBACK (on_remote_event), xs);
    g_signal_connect (plugin, "size-changed", G_CALLBACK (on_size_changed), xs);
    g_signal_connect (plugin, "free-data", G_CALLBACK (on_free_data), xs);

    gtk_widget_show_all (GTK_WIDGET (plugin));
}

XFCE_PANEL_PLUGIN_REGISTER (xpstart_construct);

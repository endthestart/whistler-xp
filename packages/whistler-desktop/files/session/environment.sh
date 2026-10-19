# Whistler: put the XP-style configuration first in the XDG search paths.
case ":${XDG_CONFIG_DIRS}:" in
    *:/etc/xdg/whistler:*) ;;
    *) export XDG_CONFIG_DIRS="/etc/xdg/whistler:${XDG_CONFIG_DIRS:-/etc/xdg}" ;;
esac
case ":${XDG_DATA_DIRS}:" in
    *:/usr/share/whistler/xdg-data:*) ;;
    *) export XDG_DATA_DIRS="/usr/share/whistler/xdg-data:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}" ;;
esac

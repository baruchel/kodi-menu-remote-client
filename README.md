# Kodi menu remote client

_A tool (written in Python) for browsing the menu of any running Kodi on a network and selecting an item to be played._

## Adding new hosts

Before any operation, at least one host has to be registered:

    kodi-menu register myradio 192.168.0.24 8080

The list of known hosts is:

    kodi-menu hosts

## Basic operations

We assume an host called `myradio` has been previously registered:

    kodi-menu myradio addons
    kodi-menu myradio sources

will display a list of available resources.

The last displayed menu (list of items) can be quickly displayed with:

    kodi-menu last
    kodi-menu ls

without using an HTTP request again (previous menu was stored in a database).

Some information concerning an item may be available with:

    kodi-menu details 5
    kodi-menu info 5

where the number points to the relevant item from the last displayed menu.

An item may be played with:

    kodi-menu myradio 5

If at least one item was played, the following command may also be used:

    kodi-menu recent

for displaying a new meny with recently played items.

The most recently played item can be played again with:

    kodi-menu myradio again

Finally some basic operations for controlling Kodi are available:

    kodi-menu myradio volume
    kodi-menu myradio volume 85
    kodi-menu myradio stop
    kodi-menu myradio mute

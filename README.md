Mtop
====

Yet another top like tool.
Mtop aggregates values by users, and send them to Carbon.

Use it
------

Choose a place with a carbon server. For testing purpose, use "-", values will be sent to STDOUT.

Mtop is polite, it's nice itself to -20.

This script should work with python-psutil package. You can use pip version too.

    ./mtop.py CARBON_SERVER USER1 USER2 USER3…

Licence
-------

GPLv3 © Mathieu Lecarme 2014

galaxyutils / Universal Galaxy 2.0 Integration Utilities
============================================================

.. toctree::
   :maxdepth: 2
   :includehidden:

   config_parser
   time_tracker

This module contains some utilities that Galaxy 2.0 plugin developers may find useful.
The utilities are designed to be platform- and operating system-independent.

Features
--------
Currently, the features of this module include the following:

* Internal Play Time Tracker (``time_tracker.py``): Keep track of a user's play time for each game manually, and save it
  locally to the user's disk.
* Configuration File Support (``config_parser.py``): Create and utilize a customized config.cfg file, which can contain
  settings that users and developers can alter to affect how a plugin functions.
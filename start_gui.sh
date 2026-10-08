#!/bin/bash

if pgrep -f gui_main > /dev/null
then
   echo "GUI already running"
else
   cd /home/rpinoon/PROJECT_AUTO
   python3 -m gui.gui_main
fi

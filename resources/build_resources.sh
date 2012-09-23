#!/usr/bin/env bash
# 
# Copyright (c) 2008 Shotgun Software, Inc
# ----------------------------------------------------

echo "building user interfaces..."
pyside-uic --from-imports dialog.ui > ../python/tk_motionbuilder/ui/dialog.py

echo "building resources..."
pyside-rcc resources.qrc > ../python/tk_motionbuilder/ui/resources_rc.py

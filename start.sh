#!/bin/sh
git pull origin master
python3 pre_deletion_notice.py -pt:0
python3 post_deletion_notice.py -pt:0

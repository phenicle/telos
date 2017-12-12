#!/usr/bin/env python

# faux_get_i.py
import sys
import os
import time

sys.path.insert(0, '%s/../lib' \
	% (os.path.dirname(os.path.realpath(__file__))))
from telos import TransferProfile

t = TransferProfile(
	'faux_get_i',
	'/usr/local/src/c/d/%s' % (time.strftime('%Y%m%d'))
	)

try:
	t.beam_me_down('ReceiveData/ReceiveBOLs/tabs.txt')
except Exception, e:
	print str(e)
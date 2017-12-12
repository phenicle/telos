#!/usr/bin/env python

# faux_get_k.py
import sys
import os
import time

sys.path.insert(0, '%s/../lib' \
	% (os.path.dirname(os.path.realpath(__file__))))
from telos import TransferProfile

t = TransferProfile(
	'faux_get_k2',
	'/data/c/k/%s' % (time.strftime('%Y%m%d'))
	)

try:
	t.beam_me_down('*.csv')
except Exception, e:
	print str(e)


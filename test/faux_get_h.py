#!/usr/bin/env python

# faux_get_k.py
import sys
import os
import time

sys.path.insert(0, '%s/../lib' \
	% (os.path.dirname(os.path.realpath(__file__))))
from telos import TransferProfile

t = TransferProfile(
	'faux_get_h',
	'/data/p/h/%s' % (time.strftime('%Y%m%d'))
	)

try:
	t.beam_me_down( '*%s*' % (today) )
except Exception, e:
	print str(e)


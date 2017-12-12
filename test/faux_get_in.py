#!/usr/bin/env python

# faux_get_in.py
import sys
import os
import time

sys.path.insert(0, '%s/../lib' \
	% (os.path.dirname(os.path.realpath(__file__))))
from telos import TransferProfile

t = TransferProfile(
	'faux_get_in',
	'/usr/local/src/c/d/%s' % (time.strftime('%Y%m%d'))
	)

try:
	t.beam_me_down('*')
except Exception, e:
	print str(e)

# post-processing:
# concatenate all of the *INF* or *IN2* files into $workdir/inv.$today

# concatenate all of the *BOL* files into $workdir/bol.$today


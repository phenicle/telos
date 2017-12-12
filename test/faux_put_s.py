#!/usr/bin/env python

# faux_put_s.py
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, '%s/../lib' \
	% (os.path.dirname(os.path.realpath(__file__))))
from telos import TransferProfile

# putting to the cwd (the login landing directory)
# therefore the sink_path is '.'
t = TransferProfile('faux_put_s','.')

two_days_ago = date.today() - timedelta(1)
two_days_ago_formatted_string = two_days_ago.strftime('%Y%m%d')
try:
	t.beam_me_up('/data/p/saw_%s.CCM' % (two_days_ago_formatted_string))
except Exception, e:
	print str(e)
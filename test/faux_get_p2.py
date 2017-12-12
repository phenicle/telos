#!/usr/bin/env python

# faux_get_p2.py
import sys
import os
from datetime import date

sys.path.insert(0, '%s/../lib' \
	% (os.path.dirname(os.path.realpath(__file__))))
from telos import TransferProfile

today = date.today()
this_month = today.strftime('%m')
this_year = today.strftime('%y')
today_formatted_string = today.strftime('%Y%m%d')

t = TransferProfile(
	'faux_get_p2',
	'/usr/local/src/c/d/%s/%s/%s' % (this_year, this_month, today_formatted_string)
	)

try:
	t.beam_me_down('*')
except Exception, e:
	print str(e)
#!/usr/bin/env python

# faux_get_pn.py
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, '%s/../lib' \
	% (os.path.dirname(os.path.realpath(__file__))))
from telos import TransferProfile

#run this at 3AM to pick up all PDFs from yesterday
#set today [exec date --date=yesterday +%Y%m%d]

yesterday = date.today() - timedelta(1)
yesterday_formatted_string = yesterday.strftime('%Y%m%d')

t = TransferProfile(
	'faux_get_pn',
	'/usr/local/src/caryoil/dtn_new/%s/pdf' % (yesterday_formatted_string)
	)

try:
	t.beam_me_down('*')
except Exception, e:
	print str(e)
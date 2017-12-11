# Telos.py
import sys
import os
import stat
import io
import arrow
import pprint
import yaml
from jinja2 import Template
import pexpect
from collections import deque

ME = 'telos'
DEBUGGING = True
IS_DRY_RUN_ONLY = False
MAXREAD = 4096

def get_properties():

	data = None
	hdir = os.path.expanduser("~")
	propsfilespec = "%s/.%s" % (hdir,ME)

	with io.open(propsfilespec, 'r') as infile:
		try:
			data = yaml.load(infile)
		except Exception, e:
			print(e)
		else:
			pass
		finally:
			pass

	return data

class Vars(object):

	def __init__(self, properties):

		self.__dict__ = properties

	def __repr__(self):
		s = ''
		for k in self.__dict__.keys():
			s += '%30s: %s\n' % (k,self.__dict__[k])

		return s

class Protocol(object):

	def __init__(self, properties):

		self.__dict__ = properties
		self.use_multiget = False

	def __repr__(self):
		s = ''
		for k in self.__dict__.keys():
			s += '%30s: %s\n' % (k,self.__dict__[k])

		return s

class Whert(object):

	def __init__(self, properties):

		self.__dict__ = properties
		self.lpath = None
		self.rpath = None

	def __repr__(self):
		s = ''
		for k in self.__dict__.keys():
			s += '%30s: %s\n' % (k,self.__dict__[k])

		return s

class Commands(object):

	def __init__(self, properties):

		self.__dict__ = properties

	def __repr__(self):
		s = ''
		for k in self.__dict__.keys():
			s += '%30s: %s\n' % (k,self.__dict__[k])

		return s


class Telos(object):

	def __init__(self, transfer_profile_identifier, modifier_constant=None):

		# first, set our own properties from the yaml
		data = get_properties()
		if not transfer_profile_identifier in data:
			# throw a bad transfer profile identifier exception!
			raise ValueError('transfer_profile identified by %s is not defined in yaml file' \
				% transfer_profile_identifier)

		my_data = data[transfer_profile_identifier]

		if 'vars' in my_data:
			self.vars = Vars(my_data['vars'])

		# 'protocol' and 'whert' are required for every transfer profile
		if not 'protocol' in my_data:
			raise ValueError('the {%s} transfer profile has no {protocol} block' \
				% (transfer_profile_identifier))
		self.protocol = Protocol(my_data['protocol'])

		if not 'whert' in my_data:
			raise ValueError('the {%s} transfer profile has no {whert} block' \
				% (transfer_profile_identifier))
		self.whert = Whert(my_data['whert'])

		#self.__dict__ = data[transfer_profile_identifier]

		# we give ourselves a pretty printer
		self.pp = pprint.PrettyPrinter(indent=4)
		self.todaydate = arrow.now().format('YYYYMMDD')

		self.finalize_whert_path_patterns()
		self.is_filename_or_fullpath()
		self.one_or_many_files()
		self.build_command_set()
		self.build_the_command_plan()

	def __repr__(self):

		#property_names = list(self.__dict__.keys())
		s = ''
		if 'vars' in self.__dict__:
			s += 'VARS:\n'
			for k in self.vars.__dict__:
				s += "%5s%20s: %s\n" % (' ',k, self.vars.__dict__[k])
			s += '\n'

		# impossible to reach here w/o the required sections
		s += 'PROTOCOL:\n'
		for k in self.protocol.__dict__:
			s += "%5s%20s: %s\n" % (' ',k, self.protocol.__dict__[k])
		s += '\n'

		s += 'WHERT:\n'
		for k in self.whert.__dict__:
			s += "%5s%20s: %s\n" % (' ',k, self.whert.__dict__[k])
		s += '\n'

		if 'commands' in self.__dict__:
			s += 'COMMANDS:\n'
			for k in self.commands.__dict__:
				s += "%5s%20s: %s\n" % (' ',k, self.commands.__dict__[k])

		if 'command_plan' in self.__dict__:
			s += 'PLAN:\n'
			s += str(self.command_plan)

		return s

	def get_render_params(self):

		return self.vars.__dict__

	def finalize_whert_path_patterns(self):
		'''
		this method is used in case whert path patterns 
		depend on variable substitution
		'''

		# if no vars, can't do variable substitution
		if not 'vars' in self.__dict__:
			return

		# otherwise, continue
		# if there's a variable named todaydate, resolve it
		vars = self.vars
		if 'todaydate' in vars.__dict__:
			self.vars.todaydate = arrow.now().format(self.vars.todaydate)
			if DEBUGGING:
				print "todaydate: %s" % (self.vars.todaydate)

		# local_path_pattern and remote_path_pattern are required
		if not 'local_path_pattern' in self.whert.__dict__:
			raise ValueError('local_path_pattern is missing from whert in .telos')

		render_params = self.get_render_params()
		lpath_template = Template(self.whert.local_path_pattern)
		self.whert.lpath = lpath_template.render(render_params)
		if DEBUGGING:
			print "lpath: %s" % (self.whert.lpath)

		if not 'remote_path_pattern' in self.whert.__dict__:
			raise ValueError('remote_path_pattern is missing from whert in .telos')

		rpath_template = Template(self.whert.remote_path_pattern)
		self.whert.rpath = rpath_template.render(render_params)
		if DEBUGGING:
			print "rpath: %s" % (self.whert.rpath)


	def is_filename_or_fullpath(self):

		(self.whert.rdirectory, self.whert.rfilepattern) = os.path.split(self.whert.rpath)
		if DEBUGGING:
			print "head: %s" % (self.whert.rdirectory)
			print "tail: %s" % (self.whert.rfilepattern)

	def one_or_many_files(self):

		self.protocol.use_multiget = False
		if '*' in self.whert.rfilepattern:
			self.protocol.use_multiget = True

	def build_command_set(self):

		cmds = {}
		cmds['connect'] = "%s %s@%s" % \
			(self.protocol.program,self.protocol.user,self.protocol.host)

		if self.whert.rdirectory:
			cmds['changedir'] = "cd %s" % (self.whert.rdirectory)

		if self.protocol.use_multiget:
			cmds['get'] = "mget %s" % (self.whert.rfilepattern)
		else:
			cmds['get'] = "get %s" % (self.whert.rfilepattern)

		self.commands = Commands(cmds)


	def build_the_command_plan(self):

		plan = deque()
		plan.append(self.commands.connect)

		if self.whert.rdirectory:
			plan.append(self.commands.changedir)

		plan.append(self.commands.get)

		self.command_plan = plan

	def prepare_localdir(self):

		if not os.path.exists(self.whert.lpath):
			os.makedirs(self.whert.lpath)
		os.chmod(self.whert.lpath, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)

	def beam_me_down(self):

		program_args = [ "%s@%s" % ( self.protocol.user, self.protocol.host ) ]
		if DEBUGGING:
			print "program_args:"
			self.pp.pprint(program_args)

		self.prepare_localdir()
		os.chdir(self.whert.lpath)

		# if self.command_plan[0] == 'connect'
		connect_command = self.command_plan.popleft()
		if 'timeout' in self.protocol.__dict__:
			p = pexpect.spawn( self.protocol.program, args=program_args, maxread=MAXREAD, timeout=self.protocol.timeout )
		else:
			p = pexpect.spawn( self.protocol.program, args=program_args, maxread=MAXREAD )

		p.logfile = sys.stdout
		p.expect(self.protocol.password_prompt)

		p.sendline(self.protocol.password)
		p.expect(self.protocol.prompt)

		while (len(self.command_plan) > 0):
			command = self.command_plan.popleft()
			p.sendline(command)
			p.expect(self.protocol.prompt)

		p.sendline('bye')
		sys.exit(0)
		# if self.command_plan[1] == 'changedir'


if __name__ == '__main__':

	# t = Telos('test-transfer-profile')
	t = Telos('get_hps')
	t.pp.pprint(t)

	t.beam_me_down()

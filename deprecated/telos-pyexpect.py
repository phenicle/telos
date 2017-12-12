# Telos.py
import sys
import os
import stat
import io
import re
import arrow
import pprint
import yaml
from jinja2 import Template
import pexpect
from collections import deque
import tempfile
import shutil
import glob
import logging

ME = 'telos'
DEBUGGING = True
IS_DRY_RUN_ONLY = False
MAXREAD = 4096
# set this to true to link stdout to the pexpect child's terminal session
VIEW_SESSION = True

tempdir = None

realpath = os.path.dirname(os.path.realpath(__file__))
modpath = '%s/%s' % (realpath, 'ComSenSec')

this_script_filename = os.path.basename(os.path.realpath(__file__))
this_script_filename_parts = os.path.splitext(this_script_filename)
appname = this_script_filename_parts[0]
if DEBUGGING:
        print "appname: %s" % (appname)

logger = logging.getLogger()

logfilespec = "%s/%s.log" % (realpath,appname)
logfilemode = 'w'
logencoding = 'utf-8'
handler = logging.FileHandler(logfilespec, logfilemode, logencoding)
formatter = logging.Formatter(
        fmt='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m/%d/%Y %H:%M'
        )
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

logger.info("starting %s" % (appname))

if DEBUGGING:
        logger.setLevel(logging.DEBUG)

def cleanup():

	if not tempdir == None:
		shutil.rmtree(tempdir)

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

		self.name = None
		self.use_multiget = False
		self.rollover_source_files_after_transfer = False
		self.__dict__ = properties

	def __repr__(self):
		s = ''
		for k in self.__dict__.keys():
			s += '%30s: %s\n' % (k,self.__dict__[k])

		return s

class Whert(object):

	def __init__(self, properties):

		self.lpath = None
		self.rpath = None
		self.__dict__ = properties

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

	def __init__(self, transfer_profile_identifier, source_path_pattern, sink_path_pattern ):

		logger.debug("initializing Telos instance with transfer profile %s" % (transfer_profile_identifier))
		# first, set our own properties from the yaml
		data = get_properties()
		if not transfer_profile_identifier in data:
			# throw a bad transfer profile identifier exception!
			raise ValueError('transfer_profile identified by %s is not defined in yaml file' \
				% transfer_profile_identifier)

		self.transfer_profile_identifier = transfer_profile_identifier
		my_data = data[transfer_profile_identifier]

		if 'vars' in my_data:
			self.vars = Vars(my_data['vars'])

		# 'protocol' and 'whert' are required for every transfer profile
		if not 'protocol' in my_data:
			raise ValueError('the {%s} transfer profile has no {protocol} block' \
				% (transfer_profile_identifier))
		self.protocol = Protocol(my_data['protocol'])
		self.protocol.name = self.get_protocol_from_program()

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
		self.build_command_set_and_plan()
		#self.build_the_command_plan()

	def __repr__(self):

		s = ''
		s += 'TRANSFER PROFILE NAME: %s\n' % self.transfer_profile_identifier
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

	def get_protocol_from_program(self):

		return os.path.basename(self.protocol.program)

	def is_protocol_ftp(self):

		if self.get_protocol_from_program() == 'ftp':
			return True
		return False

	def is_protocol_sftp(self):

		if self.get_protocol_from_program() == 'sftp':
			return True
		return False		

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

	def build_command_set_and_plan(self):

		cmds = {}
		plan = deque()
		cmds['connect'] = "%s %s@%s" % \
			(self.protocol.program,self.protocol.user,self.protocol.host)
		plan.append(cmds['connect'])

		if self.whert.rdirectory:
			cmds['changedir'] = "cd %s" % (self.whert.rdirectory)
			plan.append(cmds['changedir'])	

		# if protocol is ftp and mode is specified, set mode
		if self.is_protocol_ftp and 'mode' in self.protocol.__dict__:
			cmds['mode'] = self.protocol.mode
		# if protocol is ftp and using mget, set prompt off
		if self.is_protocol_ftp and self.protocol.use_multiget:
			cmds['prompt_off'] = "prompt off"
			plan.append(cmds['prompt_off'])

		if self.protocol.use_multiget:
			cmds['get'] = "mget %s" % (self.whert.rfilepattern)
		else:
			cmds['get'] = "get %s" % (self.whert.rfilepattern)
		plan.append(cmds['get'])

		self.commands = Commands(cmds)
		self.command_plan = plan


#	def build_the_command_plan(self):

#		plan = deque()
#		plan.append(self.commands.connect)

#		if self.whert.rdirectory:
#			plan.append(self.commands.changedir)

#		plan.append(self.commands.get)

#		self.command_plan = plan

	def prepare_localdir(self):

		if not os.path.exists(self.whert.lpath):
			os.makedirs(self.whert.lpath)
		os.chmod(self.whert.lpath, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)

	def do_commands(self, p):

		while (len(self.command_plan) > 0):
			command = self.command_plan.popleft()
			p.sendline(command)
			p.expect(self.protocol.prompt)

	# returns session handle
	def do_sftp_login(self):

		logger.debug("logging in with SFTP")

		program_args = [ "%s@%s" % ( self.protocol.user, self.protocol.host ) ]
		if DEBUGGING:
			print "program_args:"
			self.pp.pprint(program_args)

		# self.command_plan[0] == 'connect'
		connect_command = self.command_plan.popleft()
		if 'timeout' in self.protocol.__dict__:
			p = pexpect.spawn( self.protocol.program, args=program_args, maxread=MAXREAD, timeout=self.protocol.timeout )
		else:
			p = pexpect.spawn( self.protocol.program, args=program_args, maxread=MAXREAD )

		if VIEW_SESSION:
			p.logfile = sys.stdout

		p.expect(self.protocol.password_prompt)

		p.sendline(self.protocol.password)
		p.expect(self.protocol.prompt)

		return p

	# returns session handle
	def do_ftp_login(self):

		# precondition(s) for ftp login: self.protocol.username_prompt
		logger.debug("logging in with FTP")

		program_args = [ self.protocol.host ]
		if DEBUGGING:
			print "program_args:"
			self.pp.pprint(program_args)

		connect_command = self.command_plan.popleft()
		if 'timeout' in self.protocol.__dict__:
			p = pexpect.spawn( self.protocol.program, args=program_args, maxread=MAXREAD, timeout=self.protocol.timeout )
		else:
			p = pexpect.spawn( self.protocol.program, args=program_args, maxread=MAXREAD )

		if VIEW_SESSION:
			p.logfile = sys.stdout
		p.expect(self.protocol.username_prompt)

		p.sendline(self.protocol.user)
		p.expect(self.protocol.password_prompt)

		p.sendline(self.protocol.password)
		p.expect(self.protocol.prompt)

		return p

	# returns session handle
	def login(self):

		p = None
		# if protocol is ftp, login to host, then send username
		if self.protocol.name == 'sftp':
			p = self.do_sftp_login()

		elif self.protocol.name == 'ftp':
			p = self.do_ftp_login()

		else:
			raise ValueError('unrecognized/unsupported protocol: %s' \
				% (os.path.basename(self.protocol.program)))

		return p


	def beam_me_down_with_rollover(self):

		logger.debug("beaming down WITH rollover")
		sys.stdout.write("beaming down WITH rollover\n")

		program_args = [ "%s@%s" % ( self.protocol.user, self.protocol.host ) ]
		if DEBUGGING:
			print "program_args:"
			self.pp.pprint(program_args)

		# rollover strategy: download to tempdir,
		# use contents of tempdir to generate list of files to rename
		# rename source files at origin
		# move files from tempdir to target (sink) dir
		tempdir = tempfile.mkdtemp()
		os.chdir(tempdir)
		session_handle = self.login()
		self.do_commands(session_handle)
		# now do rollover.
		# ought to assert that file extension specified in remote_path_pattern
		# matches rollover_extensions: original
		orig_ext_pattern = re.compile(r'\.%s$' % (self.protocol.rollover_extensions['original']))
		rename_commands = []
		for fname in glob.glob('*.%s' % (self.protocol.rollover_extensions['original'])):
			logger.debug("moving %s to %s" % (os.path.join(tempdir,fname),self.whert.lpath))
			sys.stdout.write("moving %s to %s\n" % (os.path.join(tempdir,fname),self.whert.lpath))
			# WARNING! This only works if lpath is a DIRECTORY. Must test if it's a directory or file before doing this!
			# Note that if we specify only directory name as move destination, won't automatically overwrite existing files
			shutil.move(os.path.join(tempdir,fname), os.path.join(self.whert.lpath,fname))
			new_filename = re.sub(orig_ext_pattern,'.%s' % (self.protocol.rollover_extensions['rolled']),fname)
			rename_commands.append("rename %s %s" % (fname,new_filename))
			session_handle.sendline("rename %s %s" % (fname,new_filename))
			session_handle.expect(self.protocol.prompt)

		session_handle.sendline('bye')
		session_handle.close()
		shutil.rmtree(tempdir)
		if DEBUGGING:
			print "WHEW"
			self.pp.pprint(rename_commands)


	def beam_me_down_without_rollover(self):

		logger.debug("beaming down WITHOUT rollover")
		sys.stdout.write("beaming down WITHOUT rollover\n")
		self.prepare_localdir()
		os.chdir(self.whert.lpath)
		session_handle = self.login()
		self.do_commands(session_handle)
		# not rolling over, so after doing commands, logout
		session_handle.sendline('bye')
		session_handle.close()
		sys.exit(0)
		# if self.command_plan[1] == 'changedir'

	def beam_me_down(self):

		if self.protocol.rollover_source_files_after_transfer:

			self.beam_me_down_with_rollover()

		else:

			self.beam_me_down_without_rollover()



if __name__ == '__main__':

	# t = Telos('test-transfer-profile')
	# t = Telos('get_hps')
	t = Telos('get_test')
	t.pp.pprint(t)

	t.beam_me_down()

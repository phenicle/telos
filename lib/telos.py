# -*- coding: utf-8 -*-
# Telos.py

# Placeholder for license
'''
Telos: it slices, it dices. It makes jullienne fries.
'''

from ftplib import FTP
import pysftp
import sys
import os
import stat
import io
import re
import arrow
import pprint
import yaml
from jinja2 import Template
from collections import deque
import tempfile
import shutil
import glob
import logging

DEBUGGING = True
TYPE_UNKNOWN = 0
TYPE_DOWNLOAD = 1
TYPE_UPLOAD = 2

# we fully expect to remove this entirely
pp = pprint.PrettyPrinter(indent=4)

# gotta be global so we can cleanup if interrupted
tempdir = None

def cleanup():

	if not tempdir == None:
		shutil.rmtree(tempdir)

def get_transfer_profiles():

	transfer_profiles = None
	this_file = os.path.basename(__file__)
	this_file_sans_extension = os.path.splitext(this_file)[0]
	CFG = '%s/.%s.yaml' \
	 % (os.path.expanduser("~"),
	 	this_file_sans_extension)

	with io.open(CFG, 'r') as infile:
		try:
			transfer_profiles = yaml.load(infile)
		except Exception, e:
			print(e)
		else:
			pass
		finally:
			pass

	return transfer_profiles


class TransferProfile(object):

	def __init__( self, transfer_profile_name, sink_path ):

		all_transfer_profiles = get_transfer_profiles()

		# preconditions
		# transfer profile name value must appear among transfer profiles
		if not transfer_profile_name in all_transfer_profiles:
			raise ValueError('transfer_profile %s is not defined in yaml file' \
			  % transfer_profile_name)

		self.type = TYPE_UNKNOWN
		self.transfer_profile_name = transfer_profile_name
		self.source_path = None
		self.rollover_source_files_after_transfer = False
		self.rollover_clean_after_download = False
		self.rollover_extensions = None
		self.__dict__ = all_transfer_profiles[transfer_profile_name]
		self.name = transfer_profile_name
		self.sink_path = sink_path
		#pp.pprint(os.environ)
		if not 'password' in self.__dict__:
			transfer_profile_password_variable_name = '%s_password' % (transfer_profile_name)
			# we want to detect regardless of case!
			if transfer_profile_password_variable_name in os.environ:
				self.password = os.environ['%s_password' % (transfer_profile_name)]
			else:
				raise ValueError(
					"password not in transfer profile and there is no env variable named '%s_password'" \
					% (transfer_profile_name))

	def __repr__(self):

		s = '\n'
		for k in self.__dict__:
			s += "%5s%20s: %s\n" % (' ',k, self.__dict__[k])
		#s += '\n'

		# protocol properties: prot, host, user
		#s += 'PROTOCOL:\n'
		#for k in self.protocol.__dict__:
		#	s += "%5s%20s: %s\n" % (' ',k, self.protocol.__dict__[k])
		#s += '\n'

		# 'whert' properties: 
		# source_path_pattern, sink_path_pattern,
		# source_path, sink_path

		# command set
		#if 'commands' in self.__dict__:
		#	s += 'COMMANDS:\n'
		#	for k in self.commands.__dict__:
		#		s += "%5s%20s: %s\n" % (' ',k, self.commands.__dict__[k])

		# command sequence
		#if 'command_plan' in self.__dict__:
		#	s += 'PLAN:\n'
		#	s += str(self.command_plan)

		return s

	def is_filename_or_fullpath(self):

		(self.source_directory, self.source_filepattern) = os.path.split(self.source_path)
		if DEBUGGING:
			print "head: %s" % (self.source_directory)
			print "tail: %s" % (self.source_filepattern)

	def one_or_many_files(self):

		self.use_multiget = False
		if '*' in self.source_filepattern:
			self.use_multiget = True

	def prepare_localdir(self):
		""" this should be called ONLY when using 'beam_me_down' """

		if not self.type == TYPE_DOWNLOAD:
			raise ValueError("'prepare_localdir' called when not downloading!")

		# TODO: we want to be able to deal with 'sink_path' that's a filespec 
		# instead of directory. Otherwise need to make it a precondition that
		# 'sink_path' needs to be a directory identifier. How? In the ambiguous
		# case we simply assume it's a directory identifier.
		if not os.path.exists(self.sink_path):
			try:
				os.makedirs(self.sink_path)
			except Exception, e:
				print str(e)
		# TODO: okay for this to DEFAULT to 777, but ought to be configurable!
		try:
			os.chmod(self.sink_path, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
		except Exception, e:
			print str(e)

	def use_ftp_to_beam_me_down_with_rollover(self):

		if DEBUGGING:
			print "beaming down WITH rollover" 


	def use_ftp_to_beam_me_down_without_rollover(self):

		if DEBUGGING:
			print "beaming down WITHOUT rollover" 

		ftp = FTP(self.host)
		ftp.login(self.user,self.password)
		ftp.dir()
		ftp.quit()

	def use_ftp_to_beam_me_down(self):
		""" using ftp to download """

		if DEBUGGING:
			print "using FTP (%s@%s) to beam down" \
			  % (self.user,self.host)

		if self.rollover_source_files_after_transfer:
			self.use_ftp_to_beam_me_down_with_rollover()
		else:
			self.use_ftp_to_beam_me_down_without_rollover()

	def use_sftp_to_beam_me_down_with_rollover(self):
		""" using sftp to download with rollover """

		if DEBUGGING:
			print "beaming down WITH rollover" 

	def use_sftp_to_beam_me_down_without_rollover(self):
		""" using sftp to download without rollover """

		if DEBUGGING:
			print "beaming down WITHOUT rollover" 

		cnopts = pysftp.CnOpts()
		cnopts.hostkeys = None  
		try:

			with pysftp.Connection(self.host, username=self.user, password=self.password, cnopts=cnopts) as sftp:
				#client = sftp.sftp_client
				for item in sftp.listdir('.'):
					print item

			# connection closes automatically at end of 'with' block

		except Exception, e:
			print str(e)

	def use_sftp_to_beam_me_down(self):
		""" using sftp to download """

		if DEBUGGING:
			print "using SFTP (%s@%s/%s) to beam down" \
			  % (self.user,self.host,self.password)

		if self.rollover_source_files_after_transfer:
			self.use_sftp_to_beam_me_down_with_rollover()
		else:
			self.use_sftp_to_beam_me_down_without_rollover()


	def beam_me_down(self, source_path):
		""" download requested """

		self.source_path = source_path
		self.type = TYPE_DOWNLOAD

		self.is_filename_or_fullpath()
		self.one_or_many_files()

		if DEBUGGING:
			pp.pprint(self)
			print " Using %s to transfer %s to %s" \
			  % (self.prot, self.source_path, self.sink_path)

		self.prepare_localdir()

		if self.prot == 'ftp':

			self.use_ftp_to_beam_me_down()

		elif self.prot == 'sftp':

			self.use_sftp_to_beam_me_down()

		else:
			raise ValueError('unrecognized/unsupported protocol: %s' \
				% (self.prot))

	def use_ftp_to_beam_me_up(self):
		""" using ftp to upload """

		if DEBUGGING:
			print "using FTP (%s@%s) to beam up" \
			  % (self.user,self.host)

		ftp = FTP(self.host)
		ftp.login(self.user,self.password)
		ftp.dir()
		ftp.quit()


	def use_sftp_to_beam_me_up(self):
		""" using sftp to upload """

		if DEBUGGING:
			print "using SFTP (%s@%s/%s) to beam up" \
			  % (self.user,self.host,self.password)

		cnopts = pysftp.CnOpts()
		cnopts.hostkeys = None  
		try:

			with pysftp.Connection(self.host, username=self.user, password=self.password, cnopts=cnopts) as sftp:
				#client = sftp.sftp_client
				for item in sftp.listdir('.'):
					print item

			# connection closes automatically at end of 'with' block

		except Exception, e:
			print str(e)

	def beam_me_up(self, source_path):
		""" upload requested """

		self.source_path = source_path
		self.type = TYPE_UPLOAD

		if DEBUGGING:
			pp.pprint(self)
			print " Using %s to transfer %s to %s" \
			  % (self.prot, self.source_path, self.sink_path)

		if self.prot == 'ftp':

			self.use_ftp_to_beam_me_up()

		elif self.prot == 'sftp':

			self.use_sftp_to_beam_me_up()

		else:
			raise ValueError('unrecognized/unsupported protocol: %s' \
				% (self.prot))



if __name__ == '__main__':

	# t = Telos('test-transfer-profile')
	# t = Telos('get_hps')
	t = Telos('dummy', '/source-path-pattern', '/sink-path-pattern')
	pp.pprint(t)

	#t.beam_me_down()


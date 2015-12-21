# -*- coding: utf-8 -*-
"""
Created on Wed Sep 23 10:57:37 2015

@author: rdi

The dedicated content manager for the virtual filesystem fileManager
"""

from IPython.html.services.contents.manager import ContentsManager
import nbformat
from itertools import chain
from base64 import (
    b64decode,
    b64encode,
)
from nbformat import (
    reads,
    writes,
)

from tornado.web import HTTPError
import mimetypes
from datetime import datetime
import fileManager

NBFORMAT_VERSION = 4

def  base_model(path):
     if path[-1]=='/':
        name=path.rsplit('/', 2)[-2]
     else:
        name=path.rsplit('/',1)[-1]
     return {
    "name": name,
    "path": path,
    "writable": True,
    "last_modified": None,
    "created": None,
    "content": None,
    "format": None,
    "mimetype": None,
}

def base_directory_model(path):
    m = base_model(path)
    m.update(
        type='directory',
        last_modified=DUMMY_CREATED_DATE,
        created=DUMMY_CREATED_DATE,
    )
    return m   
        

class NoSuchDirectory(Exception):
    pass


class NoSuchFile(Exception):
    pass


class NoSuchCheckpoint(Exception):
    pass


class PathOutsideRoot(Exception):
    pass


class FileExists(Exception):
    pass


class DirectoryExists(Exception):
    pass


class DirectoryNotEmpty(Exception):
    pass


class FileTooLarge(Exception):
    pass

DUMMY_CREATED_DATE = datetime.fromtimestamp(0)

def writes_base64(nb, version=NBFORMAT_VERSION):
    """
    Write a notebook as base64.
    """
    return b64encode(writes(nb, version=version).encode('utf-8'))

def reads_base64(nb, as_version=NBFORMAT_VERSION):
    """
    Read a notebook from base64.
    """
    return reads(b64decode(nb).decode('utf-8'), as_version=as_version)

def _decode_text_from_base64(path, bcontent):
    content = b64decode(bcontent)
    try:
        return (content.decode('utf-8'), 'text')
    except UnicodeError:
        raise HTTPError(
            400,
            "%s is not UTF-8 encoded" % path, reason='bad format'
        )


def _decode_unknown_from_base64(path, bcontent):
    """
    Decode base64 data of unknown format.
    Attempts to interpret data as utf-8, falling back to ascii on failure.
    """
    content = b64decode(bcontent)
    try:
        return (content.decode('utf-8'), 'text')
    except UnicodeError:
        pass
    return bcontent.decode('ascii'), 'base64'


def to_b64(content, fmt):
    allowed_formats = {'text', 'base64'}
    if fmt not in allowed_formats:
        raise ValueError(
            "Expected file contents in {allowed}, got {fmt}".format(
                allowed=allowed_formats,
                fmt=fmt,
            )
        )
    if fmt == 'text':
        # Unicode -> bytes -> base64-encoded bytes.
        return b64encode(content.encode('utf8'))
    else:
        return content.encode('ascii')

def from_b64(path, bcontent, format):
    """
    Decode base64 content for a file.
    format:
      If 'text', the contents will be decoded as UTF-8.
      If 'base64', do nothing.
      If not specified, try to decode as UTF-8, and fall back to base64
    Returns a triple of decoded_content, format, and mimetype.
    """
    decoders = {
        'base64': lambda path, bcontent: (bcontent.decode('ascii'), 'base64'),
        'text': _decode_text_from_base64,
        None: _decode_unknown_from_base64,
    }
    content, real_format = decoders[format](path, bcontent)

    default_mimes = {
        'text': 'text/plain',
        'base64': 'application/octet-stream',
    }
    mimetype = mimetypes.guess_type(path)[0] or default_mimes[real_format]

    return content, real_format, mimetype

class SharedContentsManager(ContentsManager):

	def __init__(self, *args, **kwargs):     
         super(SharedContentsManager,self).__init__(*args, **kwargs)

	def guess_type(self, path, allow_directory=True):
		if path=='':
			path='/'
		if path[0]!='/':
			path='/'+path
		"""
		Guess the type of a file.
		If allow_directory is False, don't consider the possibility that the
		file is a directory.
		"""
		if path.endswith('.ipynb'):
			return 'notebook'
		elif allow_directory and self.dir_exists(path):
			return 'directory'
		else:
			return 'file'
	
	def dir_exists(self, path):
		with fileManager.session_scope() as session:
			if path=='':
				path='/'
			if path[0]!='/':
				path='/'+path
			return self.fm.dir_exists(path,session)
		
	def is_hidden(self, path):
		return False
            
	def file_exists(self, path):
		with fileManager.session_scope() as session:
		    if path=='':
		    	path='/'
		    if path[0]!='/':
		    	path='/'+path
		    return self.fm.file_exists(path,session)
		    
	def get(self, path, content=True, type=None, format=None):
		if path=='':
			path='/'
		if path[0]!='/':
			path='/'+path
		if type is None:
			type = self.guess_type(path)
		try:
			fn = {
				'notebook': self._get_notebook,
				'directory': self._get_directory,
				'file': self._get_file,
			}[type]
		except KeyError:
			raise ValueError("Unknown type passed: '{}'".format(type))
		return fn(path=path, content=content, format=format)
		
	def _get_notebook(self, path, content, format):
		"""
		Get a notebook from the database.
		"""

		with fileManager.session_scope() as session:
			try:
				record = self.fm.get_file(path, session,content=content)
			except NoSuchFile:
				self.no_such_entity(path)
			return self._notebook_model_from_db(record, content)
		  
		
	def _notebook_model_from_db(self, record, content):
		"""
		Build a notebook model from database record.
		"""
		
		path = record.name
		model = base_model(path)
		model['type'] = 'notebook'
		model['last_modified'] = record.modified
		model['created'] = record.created
		if content:
			content = reads_base64(record.content)
			self.mark_trusted_cells(content, path)
			model['content'] = content
			model['format'] = 'json'
			self.validate_notebook_model(model)
		return model       
		
	def _get_directory(self, path, content, format):
		"""
		Get a directory from the database.
		"""
		
		with fileManager.session_scope() as session:
			try:
				record = self.fm.get_directory(path, content,session)
			except NoSuchDirectory:
				if self.file_exists(path):
				   raise HTTPError(400, "Wrong type: %s" % path)
				else:
					self.no_such_entity(path)   
			return self._directory_model_from_db(record, content,session)
		
	def _directory_model_from_db(self, record, content,session):
		"""
		Build a directory model from database directory record.
		"""
		model = base_directory_model(record.name)
		#print record
		if content:
			model['format'] = 'json'

			model['content'] = list(
				chain(
					self._convert_file_records(record.files),
					(
						self._directory_model_from_db(subdir, False)
						for subdir in self.fm.getsubdirs(record,session)
					),
				)
			)

		return model

	def _convert_file_records(self, file_records):
		"""
		Apply _notebook_model_from_db or _file_model_from_db to each entry
		in file_records, depending on the result of `guess_type`.
		"""
		for record in file_records:
			type_ = self.guess_type(record.name, allow_directory=False)
			if type_ == 'notebook':
				yield self._notebook_model_from_db(record, False)
			elif type_ == 'file':
				yield self._file_model_from_db(record, False, None)
			else:
				raise HTTPError(500,"Unknown file type %s" % type_)

	def _file_model_from_db(self, record, content, format):
		"""
		Build a file model from database record.
		"""
		path = record.name
		#raise HTTPError(500, '+++++++++++++++++++++++  '+path[-3:-1])
		model = base_model(path)
		model['type'] = 'file'
		model['last_modified'] = record.modified
		model['created'] = record.created
		if content:
		   # content, format = self._get_file(path,content, format)
			bcontent = record.content

			model['content'], model['format'], model['mimetype'] = from_b64(
				path,
				bcontent,
				format,
			)

		return model

	def _get_file(self, path, content, format):
		with fileManager.session_scope() as session:
			try:
				record = self.fm.get_file(path, session,content=content)
			except NoSuchFile:
				if self.dir_exists(path):
					raise HTTPError (400,u"Wrong type: %s" % path)
				else:
					raise HTTPError (400,u"Not found: %s" % path)
			return self._file_model_from_db(record, content, format)

	def _save_notebook(self,  model, path):
		"""
		Save a notebook.
		Returns a validation message.
		"""
		with fileManager.session_scope() as session:
			nb_contents = nbformat.from_dict(model['content'])
			self.check_and_sign(nb_contents, path)
			self.fm.save_file(path, writes_base64(nb_contents),session)
			# It's awkward that this writes to the model instead of returning.
			self.validate_notebook_model(model)
			return model.get('message')

	def _save_file(self,  model, path):
		"""
		Save a non-notebook file.
		"""
		with fileManager.session_scope() as session:
			self.fm.save_file(path,
				to_b64(model['content'], model.get('format', None),session)
							)
			return None

	def _save_directory(self, path):
		"""
		'Save' a directory.
		"""
		with fileManager.session_scope() as session:
			self.fm.save_directory(path,session)

	def save(self, model, path):
		if path=='':
			path='/'
		if path[0]!='/':
			path='/'+path
		if 'type' not in model:
			raise HTTPError(400, u'No model type provided')
		if 'content' not in model and model['type'] != 'directory':
			raise HTTPError(400, u'No file content provided')
		print '++++++>'+path
		#path = path.strip('/')

		# Almost all of this is duplicated with FileContentsManager :(.
		self.log.debug("Saving %s", path)
		if model['type'] not in ('file', 'directory', 'notebook'):
			raise HTTPError(400,"Unhandled contents type: %s" % model['type'])
		try:
			if model['type'] == 'notebook':
				validation_message = self._save_notebook(model, path)
			elif model['type'] == 'file':
				validation_message = self._save_file( model, path)
			else:
				validation_message = self._save_directory( path)
		except (HTTPError, PathOutsideRoot):
			raise
		except FileTooLarge:
			self.file_too_large(path)
		except Exception as e:
			self.log.error(u'Error while saving file: %s %s',
						   path, e, exc_info=True)
			raise HTTPError(500,
				u'Unexpected error while saving file: %s %s' % (path, e)
			)

		model = self.get(path, type=model['type'], content=False)
		if validation_message is not None:
			model['message'] = validation_message
		return model

	def rename_file(self, old_path, path):
		"""
		Rename object from old_path to path.
		NOTE: This method is unfortunately named on the base class.  It
		actually moves a file or a directory.
		"""
		with fileManager.session_scope() as session:
			try:
				if self.file_exists(old_path):
					self.fm.rename_file( old_path, path,session)
				elif self.dir_exists(old_path):
					self.fm.rename_directory(old_path, path,session)
				else:
					print "it does not work!"
			except (FileExists, DirectoryExists):
				self.already_exists(path)

	def _delete_non_directory(self, path):
		with fileManager.session_scope() as session:
			deleted_count = self.fm.delete_file(path,session)
			if not deleted_count:
				print "Problem with deleting"

	def _delete_directory(self, path):
		with fileManager.session_scope() as session:
			try:
				deleted_count = self.fm.delete_directory( path,session)
			except DirectoryNotEmpty:
				self.not_empty(path)
			if not deleted_count:
				self.no_such_entity(path)

	def delete_file(self, path):
		"""
		Delete object corresponding to path.
		"""
		if self.file_exists(path):
			self._delete_non_directory(path)
		elif self.dir_exists(path):
			self._delete_directory(path)
		else:
			self.no_such_entity(path)

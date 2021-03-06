"""Allows Seshat to use the Google App Engine datastore."""

from __future__ import with_statement
from google.appengine.api import files

import logging
import datetime
import webapp2
import pickle
from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
import math

class factory:
    """A factory that produces database-linked objects."""
    
    def produce(self, type):
        if type == "Paper":
            return GooglePaper()
        if type == "Corpus":
            return GoogleCorpus()
        if type == "Getter":
            return GoogleGetter()
        if type == "Generic":
            return GoogleGeneric()
        if type == "Token":
            return GoogleToken()
        if type == "Blob":
            return GoogleBlob()
        if type == "Creator":
            return GoogleCreator()
        if type == "AuthorMap":
            return GoogleAuthorMap()

class GooglePaper:
    """Maps Papers onto Google Datastore entities."""
    
    def __init__(self):
        """Get started, yo."""
        self.entity = paper_entity()
        
    def load(self, id=None):
        """Get a Google Datastore paper_entity, and map Paper fields onto Google Datastore paper entity."""

        if id is not None:
            logging.debug("GooglePaper: Loading paper_entity for Paper with id " + str(id))
            key = db.Key.from_path(self.entity.kind(), int(id))
#            logging.debug("GooglePaper: paper_entity key is " + str(key))
            self.entity = db.get(key)
        
            if self.entity is not None:
                logging.debug("GooglePaper: paper_entity loaded, updating properties.")
                self.data = {
                                'title':    (self.entity.title, self.entity.title_validated),
                                'citation': ({
                                                'journal': (self.entity.journal, self.entity.journal_validated),
                                                'volume': (self.entity.volume, self.entity.volume_validated),
                                                'pages': (self.entity.pages, self.entity.pages_validated)
                                             }
                                        , self.entity.citation_validated),
                                'date': (self.entity.date, self.entity.date_validated),
                                'description': (self.entity.description, self.entity.description_validated),
                                'source': (
                                               {
                                                    'source': (self.entity.source_name, self.entity.source_name_validated),
                                                    'uri': (self.entity.source_uri, self.entity.source_uri_validated)
                                               }
                                           , self.entity.source_validated),
                                'abstract': (self.entity.abstract, self.entity.abstract_validated),
                                'pdf': (self.entity.pdf, self.entity.pdf_validated),
                                'full_text': (self.entity.full_text, self.entity.full_text_validated),
                                'date_digitized': (self.entity.date_digitized, self.entity.date_digitized_validated),
                                'rights': (
                                                {
                                                    'rights': (self.entity.rights_value, self.entity.rights_value_validated),
                                                    'holder': (self.entity.rights_holder, self.entity.rights_holder_validated)
                                                }
                                        , self.entity.rights_validated),
                                'references_text': (self.entity.references_text, self.entity.references_text_validated),
                                'language': (self.entity.language, self.entity.language_validated),
                                'type': (self.entity.type, self.entity.type_validated),
                                'creators': (self.entity.creators, self.entity.creators_validated),
                                'uri': self.entity.uri
                            }
                return True
            else:
                logging.debug("GooglePaper: paper_entity with id " + id + " not found.")
                return False
        else:
            logging.debug("GooglePaper: Creating new paper_entity.")
            self.entity = paper_entity()
            
    def delete(self):
        """Deletes the paper from the datastore."""
        
        if self.entity is not None:
            self.entity.delete()
        return None

    def update(self, object):
        """Map Paper fields onto Google Datastore paper entity, and put it."""

        self.entity.title, self.entity.title_validated = object.title
        self.entity.journal, self.entity.journal_validated = object.citation[0]['journal']
        self.entity.volume, self.entity.volume_validated = object.citation[0]['volume']
        self.entity.pages, self.entity.pages_validated = object.citation[0]['pages']
        self.entity.citation_validated = object.citation[1]
        self.entity.date, self.entity.date_validated = object.date
        self.entity.description, self.entity.description_validated = object.description
        self.entity.source_name, self.entity.source_name_validated = object.source[0]['source']
        self.entity.source_uri, self.entity.source_uri_validated = object.source[0]['uri']
        self.entity.source_validated = object.source[1]
        self.entity.abstract, self.entity.abstract_validated = object.abstract
        self.entity.pdf, self.entity.pdf_validated = object.pdf
        self.entity.full_text, self.entity.full_text_validated = object.full_text
        self.entity.date_digitized, self.entity.date_digitized_validated = object.date_digitized
        self.entity.rights_value, self.entity.rights_value_validated = object.rights[0]['rights']
        self.entity.rights_holder, self.entity.rights_holder_validated = object.rights[0]['holder']
        self.entity.references_text, self.entity.references_text_validated = object.references_text
        self.entity.language, self.entity.language_validated = object.language
        self.entity.type, self.entity.type_validated = object.type
        self.entity.uri = object.uri
        self.entity.creators, self.entity.creators_validated = object.creators
        
        self.entity.creators_validated = object.creators[1]

        return self.entity.put().id()


class GoogleCorpus:
    def __init__(self):
        self.entity = corpus_entity()

    def load(self, id=None):
        if id is not None:
            key = db.Key.from_path(self.entity.kind(), int(id))
            self.entity = db.get(key)
            self.data = {
                'title': self.entity.title,
                'papers': self.entity.papers
            }
            return True

    def update(self, object):
        """Map Corpus fields onto Google Datastore corpus entity, and put it."""

        self.entity.title = object.title
        self.entity.papers = object.papers
        return self.entity.put().id()
        
    def delete(self):
        """Deletes the corpus from the datastore."""
        
        self.entity.delete()
        return None

class GoogleCreator:
    def __init__(self):
        self.entity = creator_entity()
        
    def load(self, id=None):
        if id is not None:
            key = db.Key.from_path(self.entity.kind(), int(id))
            self.entity = db.get(key)
            
            self.data = {
                'name': self.entity.name,
                'uri': self.entity.uri
            }
            return True
            
    def update(self, object):
        self.entity.name = object.name
        self.entity.uri = object.uri
        return self.entity.put().id()

    def delete(self):
        """Deletes the creator from the datastore."""
        
        self.entity.delete()
        return None

class GoogleGetter:
    """For grabbing bunches of things out of the Google datastore."""

    def __init__(self):
        """Nothing to do."""
        
        self.data = {}
        
        return None
    
    def retrieve_all(self, type=None):
        """Returns a list of ids (float)."""
        result = []
        if type == "Corpus":
            corpora = db.GqlQuery("SELECT * FROM corpus_entity")
            for c in corpora:
                result.append(c.key().id())
        if type == "Token":
            tokens = token_entity.query()
            result = [ t.key.id() for t in tokens ]

        return result
        
    def retrieve_only(self, type, field, value):
        """Searches for entities of type with field == value"""
        logging.error(value)
        if type == 'Creator':
            return [ match.key().id() for match in db.GqlQuery("SELECT * FROM creator_entity WHERE " + field + " = '" + value + "'") ]
        
class GoogleGeneric:
    """For storing anything."""
    def __init__(self):
        self.entity = generic_entity()

    def load(self, generic_key=None):
        """generic_key is the value in the key column for a particular entity, NOT the Google datastore key.
        
        Sets self.entity, self.key and self.value, given key."""
        
        self.generic_key = generic_key

        if self.generic_key is not None:
            result = db.GqlQuery("SELECT * FROM generic_entity WHERE generic_key='"+self.generic_key+"'")
            self.value = result[0].value
            self.entity = db.get(result[0].key())

    def update(self, object):
        """Maps generic fields onto Google datastore generic entity, and puts it. Returns entity id."""
        
        self.entity.generic_key = object.generic_key
        self.entity.value = object.value
        return self.entity.put().id()

class GoogleToken:
    """For storing tokens."""

    def __init__(self):
        self.entity = token_entity()

    def load(self, id=None):
        if id is not None:
            self.id = id
            key = ndb.Key("token_entity", int(id))
            self.entity = key.get()

            self.data = {
                'account_key': self.entity.account_key,
                'account': self.entity.account
            }

    def update(self, object):
        try: self.entity.account = object.account
        except: pass
        try: self.entity.account_key = object.account_key
        except: pass
        return self.entity.put().id()

class GoogleBlob:
    """For storing blobs directly to the blobstore."""

    def __init__(self):
        pass

    def write(self, data, type="application/octet-stream"):
        """Save the blob to the blobstore, and return key."""
        
        self.file_name = files.blobstore.create(mime_type=type)
        with files.open(self.file_name, 'a') as f:
            f.write(data)
        files.finalize(self.file_name)
        return files.blobstore.get_blob_key(self.file_name)

class GoogleAuthorMap:
    """Stores mappings from creator strings to recognized authors."""

    def __init__(self):
        self.entity = authormap_entity()

    def load(self, id=None):

        if id is not None:
            key = db.Key.from_path("authormap_entity", int(id))
            self.entity = db.get(key)
            self.data = {
                'name': self.entity.name,
                'strings': self.entity.strings,
                'uri': self.entity.uri
            }
            
    def update(self, object):

        self.entity.name = object.name
        self.entity.strings = object.strings
        self.entity.uri = object.uri
        return self.entity.put().id()
    
class authormap_entity(db.Model):    
    name = db.StringProperty()
    strings = db.ListProperty(basestring)
    uri = db.StringProperty()    

class creator_entity(db.Model):
    name = db.StringProperty()
    uri = db.StringProperty()

class paper_entity(db.Model):
    """The Google datastore model for the Paper object."""
        
    title = db.StringProperty(required=False)
    title_validated = db.BooleanProperty(required=False)
        
    journal = db.StringProperty(required=False)
    journal_validated = db.BooleanProperty(required=False)
    
    volume = db.StringProperty(required=False)
    volume_validated = db.BooleanProperty(required=False)

    pages = db.StringProperty(required=False)
    pages_validated = db.BooleanProperty(required=False)

    citation_validated = db.BooleanProperty(required=False)

    date = db.StringProperty(required=False)
    date_validated = db.BooleanProperty(required=False)
        
    description = db.StringProperty(required=False)
    description_validated = db.BooleanProperty(required=False)

    source_name = db.StringProperty(required=False)
    source_name_validated = db.BooleanProperty(required=False)
    source_uri = db.StringProperty(required=False)
    source_uri_validated = db.BooleanProperty(required=False)
    source_validated = db.BooleanProperty(required=False)
                                   
    abstract = db.TextProperty(required=False)
    abstract_validated = db.BooleanProperty(required=False)
    
    creators = db.ListProperty(int)
    creators_validated = db.BooleanProperty(required=False)
    
    pdf = db.StringProperty(required=False)
    pdf_validated = db.BooleanProperty(required=False)

    full_text = db.StringProperty(required=False)
    full_text_validated = db.BooleanProperty(required=False)
    
    date_digitized = db.StringProperty(required=False)
    date_digitized_validated = db.BooleanProperty(required=False)

    rights_value = db.StringProperty(required=False)
    rights_value_validated = db.BooleanProperty(required=False)
    rights_holder = db.StringProperty(required=False)
    rights_holder_validated = db.BooleanProperty(required=False)
    rights_validated = db.BooleanProperty(required=False)
    
    references_text = db.StringProperty(required=False)
    references_text_validated = db.BooleanProperty(required=False)

    language = db.StringProperty(required=False)
    language_validated = db.BooleanProperty(required=False)

    type = db.StringProperty(required=False)
    type_validated = db.BooleanProperty(required=False)

    uri = db.StringProperty(required=False)

class corpus_entity(db.Model):
    """The Google Datastore model for a Corpus."""
    
    title = db.StringProperty(required=False)
    papers = db.ListProperty(basestring)

class generic_entity(db.Model):
    """Stores anything, given string key and string value."""

    generic_key = db.StringProperty(required=False)
    value = db.StringProperty(required=False)


class token_entity(ndb.Model):
    """Stores tokens."""
    
    account_key = ndb.StringProperty(required=False)
    account = ndb.PickleProperty(required=False)

def main():
    print "Nothing to see here."
    
if __name__ == '__main__':
    status = main()
    sys.exit(status)
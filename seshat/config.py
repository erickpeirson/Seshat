import os
from google.appengine.api import urlfetch
urlfetch.set_default_fetch_deadline(400)


template_path = os.path.join(os.path.dirname(__file__), "Web/templates/")
seshat_home = "http://chps-corpora.appspot.com"
seshat_root = os.path.dirname(__file__)

licenses = [
                "Closed",
                "Another license",
                "A third license"
            ]
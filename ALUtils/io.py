import json
import pathlib

ROOTDIR = pathlib.Path(__file__).resolve().parent

CONFIGFILE = (ROOTDIR/"config.json").resolve()

def getLocalDir(file = None):
    if file is None: file = __file__
    return pathlib.Path(file).resolve().parent

class AppData(dict):
    """ A Dictionary subclass which also handles IO.

        AppData is constructed via AppData::loadfromfile
    
        Attributes:
            file - The json-file associated with this instance
    """
    file: pathlib.Path = None
    @classmethod
    @property
    def defaultdata(cls):
        """ Provides default items for the AppData"""
        return {}
    @classmethod
    def loadfromfile(cls,file = None):
        if file is None: file = CONFIGFILE
        ad = cls(**cls.defaultdata)
        ad.file = file
        if not file.exists():
            ad.save()
        with open(file, 'r') as f:
            data = json.load(f)
        ad.update(data)
        return ad
    def save(self, encoder = None):
        with open(self.file, 'w') as f:
            json.dump(self, f, cls=encoder)
    
class ObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        return obj.__dict__
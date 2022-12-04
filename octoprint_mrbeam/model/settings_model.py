class SettingsModel:
    """
    Data object containing information about the settings to be used on the jinja2 templates
    """
    def __init__(self):
        self.material_store = None
        self.about = None

    def __repr__(self):
        return 'SettingsModel(material_store=%s, about=%s)' % (repr(self.material_store), repr(self.about))


class AboutModel:
    """
    Data object containing information corresponding to the about section to be used on the jinja2 templates
    """

    def __init__(self, support_documents=[]):
        self.support_documents = support_documents

    def __repr__(self):
        return 'About(support_documents=%s)' % (','.join([repr(document) for document in self.support_documents]))


class MaterialStoreModel:
    """
        Data object containing information corresponding to the material store section to be used on the jinja2 templates
        """

    def __init__(self, enabled=False, url=""):
        self.enabled = enabled
        self.url = url

    def __repr__(self):
        return 'MaterialStore(enabled=%s, url=%s)' % (self.enabled, self.url)

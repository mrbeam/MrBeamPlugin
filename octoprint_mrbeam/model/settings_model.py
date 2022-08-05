class SettingsModel:
    """
    Data object containing information about the settings to be used on the jinja2 templates
    """
    def __init__(self):
        self.about = None

    def __repr__(self):
        return 'SettingsModel(about=%s)' % (repr(self.about))


class AboutModel:
    """
    Data object containing information corresponding to the about section to be used on the jinja2 templates
    """
    def __init__(self, support_documents=[]):
        self.support_documents = support_documents

    def __repr__(self):
        return 'About(support_documents=%s)' % (','.join([repr(document) for document in self.support_documents]))

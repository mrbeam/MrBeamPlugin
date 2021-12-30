class SettingsModel:
    def __init__(self):
        self.about = None

    def __repr__(self):
        return 'SettingsModel(about=%s)' % (repr(self.about))


class About:
    def __init__(self, support_documents):
        self.support_documents = support_documents

    def __repr__(self):
        return 'About(support_documents=%s)' % (','.join([repr(document) for document in self.support_documents]))


class Document:
    def __init__(self, title, document_links):
        self.title = title
        self.document_links = document_links

    def __repr__(self):
        return 'Document(title=%s, document_links=%s)' % (
            self.title, ','.join([repr(document_link) for document_link in self.document_links]))


class DocumentLink:
    def __init__(self, language, url):
        self.language = language
        self.url = url

    def __repr__(self):
        return 'DocumentLink(language=%s, url=%s)' % (self.language, self.url)

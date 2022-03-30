class DocumentModel:
    """
    Data object containing information documents to be used on the jinja2 templates
    """
    def __init__(self, title, document_links):
        self.title = title
        self.document_links = document_links

    def __repr__(self):
        return 'Document(title=%s, document_links=%s)' % (
            self.title, ','.join([repr(document_link) for document_link in self.document_links]))


class DocumentSimpleModel:
    """
    Data object containing a simplified version of the information about documents to be used on the jinja2 templates
    """
    def __init__(self, title, document_link):
        self.title = title
        self.document_link = document_link

    def __repr__(self):
        return 'Document(title=%s, document_link=%s)' % (self.title, repr(self.document_link))


class DocumentLinkModel:
    """
    Data object containing information to be able to display a link to a document on the jinja2 templates
    """
    def __init__(self, language, url):
        self.language = language
        self.url = url

    def __repr__(self):
        return 'DocumentLink(language=%s, url=%s)' % (self.language, self.url)

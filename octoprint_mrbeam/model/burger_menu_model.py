
class BurgerMenuModel:
    """
    Data object containing information to be displayed under the burger menu to be used on the jinja2 templates
    """
    def __init__(self):
        self.documents = set()

    def add_document(self, document):
        self.documents.add(document)

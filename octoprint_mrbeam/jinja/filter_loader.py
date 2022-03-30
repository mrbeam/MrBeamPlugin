import jinja2

from octoprint_mrbeam.jinja.filter.sort_filters import sort_enum


class FilterLoader:
    def __init__(self):
        pass

    @staticmethod
    def load_custom_jinja_filters():
        jinja2.filters.FILTERS['sort_enum'] = sort_enum

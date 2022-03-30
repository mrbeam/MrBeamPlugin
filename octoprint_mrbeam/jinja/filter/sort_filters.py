def sort_enum(list, attribute=None):
    def find_value_for(value):
        enum = value
        if attribute:
            for attr in attribute.split('.'):
                enum = getattr(enum, attr)
        return enum.value

    return sorted(list, key=lambda element: find_value_for(element))

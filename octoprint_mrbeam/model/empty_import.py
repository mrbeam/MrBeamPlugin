class EmptyImport(object):

    def __init__(self, module, default_return=None):
        super(EmptyImport, self).__init__()
        self.default_return = default_return
        self.error_message = 'Error occurred trying to import module {module}'.format(module=module)
        self.log_error()

    def log_error(self):
        try:
            from octoprint_mrbeam import mrb_logger
            logger = mrb_logger("octoprint.plugins.mrbeam.model.EmptyImport")
            logger.error(self.error_message)
        except ImportError:
            return False
        return True

    def __call__(self, **kwargs):
        return self.default_return

    def __getattr__(self, name):
        return self

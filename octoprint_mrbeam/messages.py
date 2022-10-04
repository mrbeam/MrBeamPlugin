import os
import yaml

from octoprint_mrbeam.mrb_logger import mrb_logger

# singleton
_instance = None


def messages(plugin):
    global _instance
    if _instance is None:
        _instance = Messages(plugin)
    return _instance


class Messages(object):
    FILE_CUSTOM_MESSAGES = "messages.yaml"

    def __init__(self, plugin):
        self._logger = mrb_logger("octoprint.plugins.mrbeam.messages")
        self.plugin = plugin
        self.custom_messages_file = os.path.join(
            self.plugin._settings.getBaseFolder("base"), self.FILE_CUSTOM_MESSAGES
        )

        self.messages = dict()
        self.custom_messages_loaded = False

    def get_custom_messages(self):
        """
        Get list of currently saved custom messages
        :return:
        """
        self._load()
        return self.messages

    def put_custom_message(self, key, message):
        """Put message. If key exists, message will be overwritten.

        :param key: String unique message key
        :param message: Dict of message data
        :return: Boolean success
        """
        self._load()
        res = None

        try:
            self.messages[key.strip()] = message
            res = True
        except:
            self._logger.exception(
                "Exception while putting messages: key: %s, data: %s", key, message
            )
            res = False
        if res:
            res = self._save()
        return res

    def _load(self, force=False):
        if not self.custom_messages_loaded or force:
            try:
                if os.path.isfile(self.custom_messages_file):
                    with open(self.custom_messages_file) as yaml_file:
                        tmp = yaml.safe_load(yaml_file)
                        self.messages = (
                            tmp["messages"] if tmp and "messages" in tmp else dict()
                        )
                    self._logger.debug(
                        "Loaded %s custom messages from file %s",
                        len(self.messages),
                        self.custom_messages_file,
                    )
                else:
                    self.messages = dict()
                    self._logger.debug(
                        "No custom messages yet. File %s does not exist.",
                        self.custom_messages_file,
                    )
                self.custom_messages_loaded = True
            except Exception as e:
                self._logger.exception(
                    "Exception while loading custom messages from file {}".format(
                        self.custom_messages_file
                    )
                )
                self.messages = dict()
                self.custom_messages_loaded = False
        return self.messages

    def _save(self, force=False):
        if not self.custom_messages_loaded and not force:
            raise Exception("You need to load custom_messages before trying to save.")
        try:
            data = dict(messages=self.messages)
            with open(self.custom_messages_file, "w") as new_yaml:
                yaml.safe_dump(
                    data,
                    new_yaml,
                    default_flow_style=False,
                    indent=2,
                    allow_unicode=True,
                )
            self.custom_messages_loaded = True
            self._logger.debug(
                "Saved %s custom messages (in total) to file %s",
                len(self.messages),
                self.custom_messages_file,
            )
        except:
            self._logger.exception(
                "Exception while writing custom messages to file %s",
                self.custom_messages_file,
            )
            self.custom_messages_loaded = False
            return False
        return True

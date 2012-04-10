# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack LLC
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import ConfigParser

DEF_SECTION = 'default'


class IgnoreMissingConfigParser(ConfigParser.RawConfigParser):
    DEF_INT = 0
    DEF_FLOAT = 0.0
    DEF_BOOLEAN = False
    DEF_BASE = None

    def __init__(self, fns, cs=True):
        ConfigParser.RawConfigParser.__init__(self)
        # Make option names case sensitive
        if cs:
            self.optionxform = str
        # Load!
        self.read(fns)

    def getdef(self, section, option, default=''):
        value = self.get(section, option)
        if value is None:
            return default
        return value

    def __str__(self):
        return "%s" % (self.dictify())

    def dictify(self):
        options = dict()

        def format_key(section, key):
            return "%s/%s" % (section, key)

        for (k, v) in self.defaults().items():
            options[format_key(DEF_SECTION, k)] = v

        for sec in self.sections():
            for (k, v) in self.items(sec):
                options[format_key(sec, k)] = v

        return options

    def __getattr__(self, attr):
        if self.has_option(DEF_SECTION, attr):
            return self.get(DEF_SECTION, attr)
        else:
            raise AttributeError("%r object has no attribute %r in the %r section" %
                         (type(self).__name__, attr, DEF_SECTION))

    def get(self, section, option):
        value = IgnoreMissingConfigParser.DEF_BASE
        try:
            value = ConfigParser.RawConfigParser.get(self, section, option)
        except ConfigParser.NoSectionError:
            pass
        except ConfigParser.NoOptionError:
            pass
        return value

    def getboolean(self, section, option):
        if not self.has_option(section, option):
            return IgnoreMissingConfigParser.DEF_BOOLEAN
        return ConfigParser.RawConfigParser.getboolean(self, section, option)

    def getfloat(self, section, option):
        if not self.has_option(section, option):
            return IgnoreMissingConfigParser.DEF_FLOAT
        return ConfigParser.RawConfigParser.getfloat(self, section, option)

    def getint(self, section, option):
        if not self.has_option(section, option):
            return IgnoreMissingConfigParser.DEF_INT
        return ConfigParser.RawConfigParser.getint(self, section, option)

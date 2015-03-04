# -*- coding: utf-8 -*-

# Copyright 2015 Spanish National Research Council
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

from ooi.occi.core import attribute


class Category(object):
    """OCCI Category."""

    def __init__(self, scheme, term, title, attributes=None, location=None):
        self.scheme = scheme
        self.term = term
        self.title = title

        if attributes is None:
            self.attributes = attribute.AttributeCollection()
        elif not isinstance(attributes, attribute.AttributeCollection):
            raise TypeError("attributes must be an AttributeCollection")

        self.attributes = attributes
        self.location = location

    def __str__(self):
        d = {
            "term": self.term,
            "scheme": self.scheme,
            "class": self.__class__.__name__.lower()
        }

        return "Category: %(term)s; scheme=%(scheme)s; class=%(class)s" % d
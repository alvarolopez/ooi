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

import collections
import copy
import shlex

from ooi import exception
from ooi.occi import helpers


_MEDIA_TYPE_MAP = collections.OrderedDict([
    ('text/plain', 'text'),
    ('text/occi', 'header')
])


class BaseParser(object):
    def __init__(self, headers, body):
        self.headers = headers
        self.body = body

    def parse(self):
        raise NotImplemented

    def _validate_kind(self, kind):
        try:
            if kind.type_id != self.parsed_obj["kind"]:
                raise exception.OCCISchemaMismatch(
                    expected=kind.type_id, found=self.parsed_obj["kind"])
        except KeyError:
            raise exception.OCCIMissingType(
                type_id=kind.type_id)

    def _compare_schemes(self, expected_type, actual):
        actual_scheme, actual_term = helpers.decompose_type(actual)
        if expected_type.scheme != actual_scheme:
            return False
        try:
            if expected_type.term != actual_term:
                return False
        except AttributeError:
            # ignore the fact the type does not have a term
            pass
        return True

    def _validate_mandatory_mixins(self, mixins, unmatched):
        for m in mixins:
            for um in unmatched:
                if self._compare_schemes(m, um):
                    unmatched[um] -= 1
                    break
            else:
                raise exception.OCCIMissingType(type_id=m.scheme)
        return unmatched

    def _validate_optional_mixins(self, mixins, unmatched):
        for m in mixins:
            for um in unmatched:
                if self._compare_schemes(m, um):
                    unmatched[um] -= 1
                    break
        return unmatched

    def validate(self, schema):
        self.parsed_obj = self.parse()
        if "kind" in schema:
            self._validate_kind(schema["kind"])
        unmatched = copy.copy(self.parsed_obj["mixins"])
        unmatched = self._validate_mandatory_mixins(
            schema.get("mixins", []), unmatched)
        unmatched = self._validate_optional_mixins(
            schema.get("optional_mixins", []), unmatched)
        unexpected = [m for m in unmatched if unmatched[m]]
        if unexpected:
            raise exception.OCCISchemaMismatch(expected="",
                                               found=unexpected)
        return True


class TextParser(BaseParser):
    pass


def _lexize(s, separator, ignore_whitespace=False):
    lex = shlex.shlex(instream=s, posix=True)
    lex.commenters = ""
    if ignore_whitespace:
        lex.whitespace = separator
    else:
        lex.whitespace += separator
    lex.whitespace_split = True
    return list(lex)


class HeaderParser(BaseParser):
    def parse_categories(self):
        kind = None
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        try:
            categories = self.headers["Category"]
        except KeyError:
            raise exception.OCCIInvalidSchema("No categories")
        for ctg in _lexize(categories, separator=",", ignore_whitespace=True):
            ll = _lexize(ctg, ";")
            d = {"term": ll[0]}  # assumes 1st element => term's value
            d.update(dict([i.split('=') for i in ll[1:]]))
            ctg_class = d.get("class", None)
            ctg_type = '%(scheme)s%(term)s' % d
            if ctg_class == "kind":
                if kind is not None:
                    raise exception.OCCIInvalidSchema("Duplicated Kind")
                kind = ctg_type
            elif ctg_class == "mixin":
                mixins[ctg_type] += 1
            schemes[d["scheme"]].append(d["term"])
        return {
            "kind": kind,
            "mixins": mixins,
            "schemes": schemes,
        }

    def parse_attributes(self):
        attrs = {}
        try:
            header_attrs = self.headers["X-OCCI-Attribute"]
            for attr in _lexize(header_attrs, separator=",",
                                ignore_whitespace=True):
                n, v = attr.split('=', 1)
                attrs[n.strip()] = v
        except KeyError:
            pass
        return attrs

    def parse(self):
        obj = self.parse_categories()
        obj['attributes'] = self.parse_attributes()
        return obj


_PARSERS_MAP = {
    "text": TextParser,
    "header": HeaderParser,
}


def get_media_map():
    return _MEDIA_TYPE_MAP


def get_default_parsers():
    return _PARSERS_MAP


def get_supported_content_types():
    return _MEDIA_TYPE_MAP.keys()

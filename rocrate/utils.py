#!/usr/bin/env python

## Copyright 2019-2020 The University of Manchester, UK
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

import collections
from datetime import date, datetime

def first(iterable):
    for e in iterable:
        return e
    return None

def flatten(single_or_multiple):
    if len(single_or_multiple) == 1:
        return single_or_multiple[0]
    return single_or_multiple # might be empty!

def as_list(list_or_other):
    if list_or_other is None:
        return []
    if (isinstance(list_or_other, collections.Sequence) 
        and not isinstance(list_or_other, str)): # FIXME: bytes?
        return list_or_other
    return [list_or_other]

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

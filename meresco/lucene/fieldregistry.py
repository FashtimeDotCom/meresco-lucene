## begin license ##
#
# "Meresco Lucene" is a set of components and tools to integrate Lucene (based on PyLucene) into Meresco
#
# Copyright (C) 2014-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
#
# This file is part of "Meresco Lucene"
#
# "Meresco Lucene" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Lucene" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Lucene"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from org.apache.lucene.document import TextField, StringField, NumericDocValuesField, Field, FieldType, IntField, LongField
from org.apache.lucene.index import FieldInfo
from org.apache.lucene.facet import FacetsConfig, DrillDownQuery


IDFIELD = '__id__'
SORTED_PREFIX = "sorted."
UNTOKENIZED_PREFIX = "untokenized."
KEY_PREFIX = "__key__."
NUMERIC_PREFIX = "__numeric__."

class FieldRegistry(object):
    def __init__(self, drilldownFields=None):
        self._fieldDefinitions = {
            IDFIELD: _FieldDefinition.define(type=StringField.TYPE_STORED, name=IDFIELD),
        }
        self._drilldownFieldNames = set()
        self._hierarchicalDrilldownFieldNames = set()
        self._multivaluedDrilldownFieldNames = set()
        self.facetsConfig = FacetsConfig()
        for field in (drilldownFields or []):
            self.registerDrilldownField(field.name, hierarchical=field.hierarchical, multiValued=field.multiValued)

    def createField(self, fieldname, value, mayReUse=False):
        return self._getFieldDefinition(fieldname).createField(value, mayReUse=mayReUse)

    def createIdField(self, value):
        return self.createField(IDFIELD, value)

    def register(self, fieldname, fieldType=None, fieldDefinition=None):
        if fieldType:
            self._fieldDefinitions[fieldname] = _FieldDefinition.define(type=fieldType, name=fieldname)
        else:
            self._fieldDefinitions[fieldname] = fieldDefinition(fieldname)

    def phraseQueryPossible(self, fieldname):
        return self._getFieldDefinition(fieldname).phraseQueryPossible

    def isUntokenized(self, fieldname):
        return self._getFieldDefinition(fieldname).isUntokenized

    def registerDrilldownField(self, fieldname, hierarchical=False, multiValued=True):
        self._drilldownFieldNames.add(fieldname)
        if hierarchical:
            self._hierarchicalDrilldownFieldNames.add(fieldname)
        if multiValued:
            self._multivaluedDrilldownFieldNames.add(fieldname)
        self.facetsConfig.setMultiValued(fieldname, multiValued)
        self.facetsConfig.setHierarchical(fieldname, hierarchical)

    def isDrilldownField(self, fieldname):
        return fieldname in self._drilldownFieldNames

    def isHierarchicalDrilldown(self, fieldname):
        return fieldname in self._hierarchicalDrilldownFieldNames

    def isMultivaluedDrilldown(self, fieldname):
        return fieldname in self._multivaluedDrilldownFieldNames

    def makeDrilldownTerm(self, fieldname, path):
        indexFieldName = self.facetsConfig.getDimConfig(fieldname).indexFieldName;
        return DrillDownQuery.term(indexFieldName, fieldname, path)

    def pythonType(self, fieldname):
        return self._getFieldDefinition(fieldname).pythonType

    def _getFieldDefinition(self, fieldname):
        fieldDefinition = self._fieldDefinitions.get(fieldname)
        if fieldDefinition is not None:
            return fieldDefinition
        fieldDefinitionCreator = TEXTFIELD
        if fieldname.startswith(SORTED_PREFIX) or fieldname.startswith(UNTOKENIZED_PREFIX):
            fieldDefinitionCreator = STRINGFIELD
        if fieldname.startswith(KEY_PREFIX) or fieldname.startswith(NUMERIC_PREFIX):
            fieldDefinitionCreator = NUMERICFIELD
        fieldDefinition = fieldDefinitionCreator(name=fieldname)
        self._fieldDefinitions[fieldname] = fieldDefinition
        return fieldDefinition

class _FieldDefinition(object):
    def __init__(self, type, pythonType, field, update, create):
        self.type = type
        self.pythonType = pythonType
        positionsStored = self.type.indexOptions() in [FieldInfo.IndexOptions.DOCS_ONLY, FieldInfo.IndexOptions.DOCS_AND_FREQS]
        self.phraseQueryPossible = not positionsStored
        self.isUntokenized = not self.type.tokenized()
        self._field = field
        self._update = update
        self._create = create

    def createField(self, value, mayReUse):
        if mayReUse:
            self._update(self._field, value)
        else:
            self._field = self._create(value)
        return self._field

    @classmethod
    def define(cls, type, name):
        create = lambda value: Field(name, value, type)
        return cls(
            type=type,
            field=create(""),
            pythonType=str,
            create=create,
            update=lambda field, value: field.setStringValue(value)
        )


STRINGFIELD = lambda name: _FieldDefinition.define(type=StringField.TYPE_NOT_STORED, name=name)
NUMERICFIELD = lambda name: _FieldDefinition(
    type=NumericDocValuesField.TYPE,
    pythonType=long,
    field=NumericDocValuesField(name, long(0)),
    create=lambda value: NumericDocValuesField(name, long(value)),
    update=lambda field, value: field.setLongValue(long(value)),
)
TEXTFIELD = lambda name: _FieldDefinition.define(type=TextField.TYPE_NOT_STORED, name=name)
INTFIELD = lambda name: _FieldDefinition(
    type=IntField.TYPE_NOT_STORED,
    pythonType=int,
    field=IntField(name, int(0), IntField.TYPE_NOT_STORED),
    create=lambda value: IntField(name, int(value), IntField.TYPE_NOT_STORED),
    update=lambda field, value: field.setIntValue(int(value)),
)
LONGFIELD = lambda name: _FieldDefinition(
    type=LongField.TYPE_NOT_STORED,
    pythonType=long,
    field=LongField(name, long(0), LongField.TYPE_NOT_STORED),
    create=lambda value: LongField(name, long(value), LongField.TYPE_NOT_STORED),
    update=lambda field, value: field.setIntValue(long(value)),
)


def _createNoTermsFrequencyFieldType():
    f = FieldType()
    f.setIndexed(True)
    f.setTokenized(True)
    f.setOmitNorms(True)
    f.setIndexOptions(FieldInfo.IndexOptions.DOCS_ONLY)
    f.freeze()
    return f

NO_TERMS_FREQUENCY_FIELDTYPE = _createNoTermsFrequencyFieldType()


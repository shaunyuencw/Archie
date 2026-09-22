"""Strict OpenAI transport for sparse edits, without JSON embedded in strings.

JSON Schema requires closed objects with required properties. Key/value entries
let an edit omit unchanged fields while retaining explicit nulls. The adapter
converts these entries to the existing internal envelope; there is no second
architecture model and no attempt to guess or repair malformed JSON.
"""
from __future__ import annotations

import json
from copy import deepcopy
from typing_extensions import TypeAliasType
from pydantic import create_model, model_validator

from ..domain.models import Record
from .contracts import Envelope, WireOperation, WireClaim
from .instructions import SYSTEM_PROMPT


class ObjectValue(Record):
    fields: list[ValueField]

    @model_validator(mode='after')
    def unique_keys(self):
        if len({field.key for field in self.fields}) != len(self.fields):
            raise ValueError('Each object field must appear exactly once')
        return self


StructuredValue = TypeAliasType('StructuredValue',
    str | int | float | bool | None | list['StructuredValue'] | ObjectValue)


class ValueField(Record):
    key: str
    value: StructuredValue


ObjectValue.model_rebuild()


def _transport_model(model, **replacements):
    fields = {name: (field.annotation, deepcopy(field))
              for name, field in model.model_fields.items()
              if name != 'value_json' and name not in replacements}
    return create_model('Structured' + model.__name__, __base__=Record, **fields, **replacements)


StructuredOperation = _transport_model(WireOperation, value=(ObjectValue, ...))
StructuredClaim = _transport_model(WireClaim, value=(StructuredValue, ...))
StructuredEnvelope = _transport_model(Envelope,
    operations=(list[StructuredOperation], ...), claims=(list[StructuredClaim], ...))


def structured_schema():
    result = StructuredEnvelope.model_json_schema()
    def strict(node):
        if isinstance(node, dict):
            node.pop('default', None)
            if node.get('type') == 'object':
                node['required'] = list(node['properties'])
                node['additionalProperties'] = False
            for value in node.values():
                strict(value)
        elif isinstance(node, list):
            for value in node:
                strict(value)
    strict(result)
    return result


def _unpack(value):
    if isinstance(value, ObjectValue):
        return {field.key: _unpack(field.value) for field in value.fields}
    if isinstance(value, list):
        return [_unpack(item) for item in value]
    return value


def parse_structured(text):
    parsed = StructuredEnvelope.model_validate_json(text, strict=True)
    body = parsed.model_dump(exclude={'operations', 'claims'})
    for name in ('operations', 'claims'):
        body[name] = [{**record.model_dump(exclude={'value'}),
                       'value_json': json.dumps(_unpack(record.value), separators=(',', ':'), allow_nan=False)}
                      for record in getattr(parsed, name)]
    return Envelope.model_validate(body)


def structured_envelope(envelope):
    """Serialize saved/internal envelopes in the same format as new responses."""
    def pack(value):
        if isinstance(value, dict):
            return {'fields': [{'key': key, 'value': pack(item)} for key, item in value.items()]}
        if isinstance(value, list):
            return [pack(item) for item in value]
        return value
    body = envelope.model_dump()
    for name in ('operations', 'claims'):
        for record in body[name]:
            record['value'] = pack(json.loads(record.pop('value_json')))
    return body


STRUCTURED_SYSTEM_PROMPT = SYSTEM_PROMPT.replace(
    'value_json is a JSON object string; omit defaults.',
    'Operation value is {"fields":[{"key":"name","value":"Example"}]}. '
    'Use native JSON values, never JSON text. Nested objects also use fields. '
    'Omit unchanged/default fields; explicit null clears a field. '
    'Claims use native value, usually null for record quotes.')

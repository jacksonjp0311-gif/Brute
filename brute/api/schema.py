"""brute.api/1.0 types and validation. The JSON files in schema/ are the source of truth.

The validator implements the small JSON-Schema subset those files use
(type, enum, const, required, properties, additionalProperties, items, minimum, maximum).
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from brute.core.learner import Status as _CoreStatus,Reason,ScopeAttestation
from enum import Enum

API_VERSION='brute.api/1.0'
_DIR=Path(__file__).with_name('schema')
REQUEST_SCHEMA=json.loads((_DIR/'request.v1.json').read_text())
RESPONSE_SCHEMA=json.loads((_DIR/'response.v1.json').read_text())


class Status(str,Enum):
    ACKNOWLEDGED='ACKNOWLEDGED'   # non-predict op succeeded; carries no claim
    CERTIFIED='CERTIFIED'
    POSSIBLE_SET='POSSIBLE_SET'
    ABSTAIN='ABSTAIN'
    OUT_OF_FAMILY='OUT_OF_FAMILY'
    ERROR='ERROR'


class SchemaError(ValueError):pass

_TYPES={'object':dict,'array':list,'string':str,'boolean':bool,'null':type(None)}


def _is(value,t):
    if t=='integer':return isinstance(value,int) and not isinstance(value,bool)
    if t=='number':return isinstance(value,(int,float)) and not isinstance(value,bool)
    return isinstance(value,_TYPES[t])


def _validate(value,schema,path='$'):
    if 'const' in schema and value!=schema['const']:raise SchemaError(f'{path}: expected {schema["const"]!r}')
    if 'enum' in schema and value not in schema['enum']:raise SchemaError(f'{path}: {value!r} not in enum')
    if 'type' in schema:
        types=schema['type'] if isinstance(schema['type'],list) else [schema['type']]
        if not any(_is(value,t) for t in types):raise SchemaError(f'{path}: wrong type {type(value).__name__}')
    if isinstance(value,(int,float)) and not isinstance(value,bool):
        if 'minimum' in schema and value<schema['minimum']:raise SchemaError(f'{path}: below minimum')
        if 'maximum' in schema and value>schema['maximum']:raise SchemaError(f'{path}: above maximum')
    if isinstance(value,dict):
        for key in schema.get('required',()):
            if key not in value:raise SchemaError(f'{path}: missing {key}')
        props=schema.get('properties',{});extra=schema.get('additionalProperties',True)
        for key,v in value.items():
            if not isinstance(key,str):raise SchemaError(f'{path}: non-string key')
            if key in props:_validate(v,props[key],f'{path}.{key}')
            elif extra is False:raise SchemaError(f'{path}: unexpected field {key}')
            elif isinstance(extra,dict):_validate(v,extra,f'{path}.{key}')
    if isinstance(value,list) and 'items' in schema:
        for i,v in enumerate(value):_validate(v,schema['items'],f'{path}[{i}]')


def validate_request(req):_validate(req,REQUEST_SCHEMA);return req
def validate_response(resp):_validate(resp,RESPONSE_SCHEMA);return resp


@dataclass(frozen=True)
class Certificate:
    value:dict
    kind:str
    conditional_on:str


__all__=['API_VERSION','Status','Reason','ScopeAttestation','Certificate','SchemaError','validate_request','validate_response']

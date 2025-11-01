import json
import copy

def resolve_refs(schema, ignore_refs=None, seen=None, depth=0):
    if ignore_refs is None:
        ignore_refs = set()
    if seen is None:
        seen = set()
        
    if isinstance(schema, dict):
        if '$ref' in schema:
            ref = schema['$ref']
            if ref in ignore_refs:
                return schema
            if ref in seen:
                return schema # prevent recursive loops
            seen.add(ref)
            
            #follow the ref path
            path = ref.lstrip('#/').split('/')
            node = root
            for p in path:
                node = node[p]
            
            return resolve_refs(copy.deepcopy(node), ignore_refs, seen, depth+1)
        else:
            #resolve children
            return {k: resolve_refs(v, ignore_refs, seen, depth+1) for k, v in schema.items()}
        
    elif isinstance(schema, list):
        return [resolve_refs(i, ignore_refs, seen, depth+1) for i in schema]
    else:
        return schema


# load global root
with open('item_components.json', 'r') as f:
    root = json.load(f)

resolved_schema = resolve_refs(root, ignore_refs={'#/components'})

def get_schema():
    ''' Returns a deep copy of the resolved schema '''
    return copy.deepcopy(resolved_schema)

def resolve_component_ref():
    '''explicitly resolve the #/components ref section on-demand'''
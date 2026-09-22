"""Zoning context and presentation helpers; these never call a provider."""
import re

from ..domain.models import Operation


ZONING_QUERY = re.compile(r'\b(?:zones|zoning|segmentation|segregation)\b|\b(?:assign|create|propose|add|design|implement)\b.{0,40}\bzone\b', re.I)
ZONING_REQUIREMENT = re.compile(r'\b(?:cyber\w*|security|application|compute|field|video|network)\s*(?:/\s*\w+\s*)?zones?\b|\bzoning\b|\bsegmentation\b|\bdeployment\b', re.I)


def supporting_sources(project, query):
    """Retrieve bounded saved passages for an explicit zoning edit."""
    if not ZONING_QUERY.search(query):
        return []
    remaining = 6000
    result = []
    for source in project.sources:
        if source.kind not in ('document', 'prompt'):
            continue
        passages = []
        for passage in source.passages:
            if remaining and ZONING_REQUIREMENT.search(passage.text):
                text = passage.text[:remaining]
                passages.append(passage.model_copy(update={'text': text}))
                remaining -= len(text)
        if passages:
            result.append(source.model_copy(update={'passages': passages}))
    return result


def new_zone_layout(before, candidate):
    """Pack new zone families while keeping unrelated saved families in place."""
    from ..domain.layout import compact_geometry, GEOMETRY, bounds, PADDING, HEADER
    from ..domain.views import view_graph

    new_zones = {z.id for z in candidate.zones} - {z.id for z in before.zones}
    operations = []
    if not new_zones or not before.components:
        return operations
    for kind in ('logical', 'sv2'):
        graph = view_graph(candidate, kind, route_edges=False)
        # Locks here constrain planning only; they are not persisted.
        nodes = [dict(n, locked=True) if not n.get('parentId') and n['id'] not in new_zones else dict(n)
                 for n in graph['nodes']]
        previous = {n['id']: n for n in view_graph(before, kind, route_edges=False)['nodes']}
        # Reparent in world coordinates first, so pins/manual route endpoints
        # remain fixed when the compact planner freezes their new family.
        for zone in (n for n in nodes if n['id'] in new_zones):
            children = [n for n in nodes if n.get('parentId') == zone['id']]
            absolute = []
            for child in children:
                old = previous.get(child['id'])
                parent = previous.get(old.get('parentId'), {'x': 0, 'y': 0}) if old else zone
                node = old or child
                absolute.append(dict(child, x=node['x']+parent['x'], y=node['y']+parent['y']))
            box = bounds(absolute)
            if box:
                zone.update(x=box['x']-PADDING, y=box['y']-HEADER,
                            width=min(4000, max(240, box['width']+2*PADDING)),
                            height=min(4000, box['height']+HEADER+PADDING))
                for child, world in zip(children, absolute):
                    child.update(x=world['x']-zone['x'], y=world['y']-zone['y'])
        geometry = compact_geometry(nodes, graph['edges'])
        for node in graph['nodes']:
            patch = {key: geometry[node['id']][key] for key in GEOMETRY
                     if geometry[node['id']][key] != node[key]}
            if patch:
                operations.append(Operation(op='placement', id=node['id'], view=kind, value=patch))
    return operations

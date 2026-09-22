"""Bounded, deterministic presentation layout. Never changes architecture facts."""
from math import ceil, sqrt

GEOMETRY = ('x', 'y', 'width', 'height')
GAP = 64
PADDING = 24
HEADER = 64


def bounds(nodes):
    if not nodes:
        return None
    left = min(n['x'] for n in nodes)
    top = min(n['y'] for n in nodes)
    return dict(x=left, y=top,
                width=max(n['x'] + n['width'] for n in nodes) - left,
                height=max(n['y'] + n['height'] for n in nodes) - top)


def _overlap(a, b):
    return (a['x'] < b['x'] + b['width'] + GAP and
            a['x'] + a['width'] + GAP > b['x'] and
            a['y'] < b['y'] + b['height'] + GAP and
            a['y'] + a['height'] + GAP > b['y'])


def _pack(items, fixed, width):
    """Bottom-left packing around pinned rectangles; at most 50 components."""
    result = dict(fixed)
    left = min(40, *(n['x'] for n in fixed.values())) if fixed else 40
    top = min(60, *(n['y'] for n in fixed.values())) if fixed else 60
    for ident, size in items:
        occupied = list(result.values())
        xs = sorted({left, *(n['x'] + n['width'] + GAP for n in occupied)})
        ys = sorted({top, *(n['y'] + n['height'] + GAP for n in occupied)})
        placed = None
        for y in ys:
            for x in xs:
                if x + size['width'] > left + width:
                    continue
                candidate = dict(size, x=x, y=y)
                if not any(_overlap(candidate, other) for other in occupied):
                    placed = candidate
                    break
            if placed is not None:
                break
        # The last y lies below every obstacle, so there is always a free slot.
        assert placed is not None
        result[ident] = placed
    return result


def compact_geometry(nodes, edges, aspect_ratio=1.5):
    """Fit unlocked zones to their children, then pack visible root families.

    A pin on a zone or child freezes that whole family in world coordinates.
    Endpoints of manual routes also stay put, keeping their saved bends useful.
    Existing component dimensions, styles, routes and semantic membership survive.
    """
    by_id = {n['id']: n for n in nodes}
    roots = [n for n in nodes if not n.get('parentId')]
    families = {n['id']: [n] for n in roots}
    for node in nodes:
        if node.get('parentId') in families:
            families[node['parentId']].append(node)
    root_for = {n['id']: ident for ident, family in families.items() for n in family}
    frozen = {ident for ident, family in families.items() if any(n.get('locked') for n in family)}
    for edge in edges:
        route = edge.get('route')
        if route and (route.locked or (route.points and not route.automatic)):
            frozen.update(root_for[end] for end in (edge['source'], edge['target']) if end in root_for)

    geometry = {n['id']: {key: n[key] for key in GEOMETRY} for n in nodes}
    for root in roots:
        ident = root['id']
        if ident in frozen or root['role'] != 'zone':
            continue
        children = families[ident][1:]
        # Use actual component sizes; a long zone title also needs some width.
        title_width = max(240, min(360, len(root['label']) * 7 + PADDING * 2))
        columns = max(1, ceil(sqrt(len(children) / 1.5)))
        rows = [children[i:i + columns] for i in range(0, len(children), columns)]
        child_geometry = {}
        y = HEADER
        width = title_width
        for row in rows:
            x = PADDING
            for child in row:
                child_geometry[child['id']] = dict(geometry[child['id']], x=x, y=y)
                x += child['width'] + GAP
            width = max(width, x - GAP + PADDING)
            y += max(child['height'] for child in row) + GAP
        height = y - GAP + PADDING if rows else 128
        if width > 4000 or height > 4000:
            frozen.add(ident)
            continue
        geometry.update(child_geometry)
        geometry[ident].update(width=width, height=height)

    # Obstacles include children deliberately dragged outside a pinned zone.
    fixed = {}
    for ident in frozen:
        root = by_id[ident]
        fixed[ident] = bounds([root, *(dict(n, x=n['x'] + root['x'], y=n['y'] + root['y'])
                                       for n in families[ident][1:])])
    movable = [n for n in roots if n['id'] not in frozen]
    order = {n['id']: i for i, n in enumerate(roots)}
    movable.sort(key=lambda n: (-geometry[n['id']]['width'] * geometry[n['id']]['height'], order[n['id']]))
    items = [(n['id'], geometry[n['id']]) for n in movable]
    if items:
        area = sum(n['width'] * n['height'] for n in [*fixed.values(), *(size for _, size in items)])
        minimum = max(size['width'] for _, size in items)
        ideal = sqrt(area * aspect_ratio)
        widths = sorted({max(minimum, ceil(ideal * factor)) for factor in (.7, .85, 1, 1.15, 1.35, 1.6, 2)})
        links = [(root_for.get(e['source']), root_for.get(e['target'])) for e in edges]

        def cost(packed):
            box = bounds(list(packed.values()))
            # Minimise the viewport needed at the current canvas aspect ratio.
            fit_area = max(box['width'] / aspect_ratio, box['height']) ** 2 * aspect_ratio
            wire_length = 0
            for a, b in links:
                if a == b or a not in packed or b not in packed:
                    continue
                first, last = packed[a], packed[b]
                wire_length += abs(first['x'] + first['width'] / 2 - last['x'] - last['width'] / 2)
                wire_length += abs(first['y'] + first['height'] / 2 - last['y'] - last['height'] / 2)
            return fit_area + 8 * wire_length, box['width'] * box['height']

        packed = min((_pack(items, fixed, width) for width in widths), key=cost)
        for ident, _ in items:
            geometry[ident].update(x=packed[ident]['x'], y=packed[ident]['y'])

    return geometry

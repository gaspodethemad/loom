import uuid
import html2text
import numpy as np
import re
import random
from datetime import datetime

def new_node(node_id=None, text='', mutable=True):
    if not node_id:
        node_id = str(uuid.uuid1())
    node = {"id": node_id,
            "text": text,
            "children": [],
            "mutable": mutable}
    return node


# Height of d, root has the greatest height, minimum is 1
def height(d):
    return 1 + max([0, *[height(c) for c in d["children"]]])


# Depth of d, root is 0 depth
def depth(d, node_dict):
    return 0 if "parent_id" not in d else (1 + depth(node_dict[d["parent_id"]], node_dict))


def num_descendents(root, filter=None):
    return len(subtree_list(root, filter))


def generate_conditional_tree(root, filter=None):
    return {d["id"]: d for d in flatten_tree(tree_subset(root=root,
                                                         filter=filter),
                                             )}


def filtered_children(node, filter=None):
    if filter:
        return [child for child in node['children'] if filter(child)]
    else:
        return node['children']

def antifiltered_children(self, node, filter=None):
    return [child for child in node['children'] if not filter(child)] if filter else []


def subtree_list(root, filter=None, depth_limit=None):
    if depth_limit == 0:
        return []
    sub_list = [root]
    children = filtered_children(root, filter)
    for child in children:
        sub_list += subtree_list(child, filter, depth_limit - 1 if depth_limit else None)
    return sub_list


def depth_limited_tree(root, depth_limit):
    new_root = {'id': root['id'], 'children': []}
    if depth_limit == 0:
        return new_root
    if 'children' in root:
        for child in root['children']:
            new_root['children'].append(depth_limited_tree(child, depth_limit - 1))
    return new_root


def limited_branching_tree(ancestry, root, depth_limit):
    # returns a subset of tree which only contains nodes no more than depth_limit levels from a node in ancestry
    if len(ancestry) <= 1:
        return depth_limited_tree(root, depth_limit)
    child_in_ancestry = ancestry[1]
    new_root = {'id': root['id'], 'children': []}
    for child in root['children']:
        if child['id'] == child_in_ancestry['id']:
            new_root['children'].append(limited_branching_tree(ancestry[1:], child, depth_limit))
        elif depth_limit > 0:
            new_root['children'].append(depth_limited_tree(child, depth_limit-1))
    return new_root

# TODO option for no depth limit
def collapsed_wavefunction(ancestry, root, current_node, depth_limit):
    if len(ancestry) <= 1 or root['id'] == current_node['id']:
        return depth_limited_tree(root, depth_limit)
    child_in_ancestry = ancestry[1]
    new_root = {'id': root['id'], 'children': []}
    for child in root['children']:
        if child['id'] == child_in_ancestry['id']:
            new_root['children'].append(collapsed_wavefunction(ancestry[1:], child, current_node, depth_limit))
    return new_root

def limited_distance_tree(root, reference_node, distance_limit, node_dict):
    condition = lambda node: path_distance(reference_node, node, node_dict) <= distance_limit
    if not condition(root):
        # root is node in reference node's ancestry distance_limit removed
        ancestry = node_ancestry(reference_node, node_dict)
        root = ancestry[-(distance_limit + 1)]
    return tree_subset(root, condition)

# given a root node and include condition, returns a new tree which contains only nodes who satisfy
# the condition and whose ancestors also all satisfy the condition
# nodes in the new tree contain only their ids and a childlist
# this generates a copy
# TODO copy contains no data except id(same as old tree) and children - will cause problems?
# TODO modify this function or make new function that copies all of tree?
# TODO existing python function to filter/copy dictionary?

# this assumes the root satisfies the condition
def tree_subset(root, filter=None, copy_attributes=None):
    if not filter:
        return root
    if not copy_attributes:
        copy_attributes = []
    new_root = {'id': root['id'], 'children': []}
    if 'children' in root:
        for child in filtered_children(root, filter):
            new_root['children'].append(tree_subset(child, filter, copy_attributes))
    for attribute in copy_attributes:
        if attribute in root:
            new_root[attribute] = root[attribute]
    return new_root


def stochastic_transition(node, mode='descendents', filter=None):
    transition_probs = subtree_weights(node, mode, filter)
    choice = random.choices(node['children'], transition_probs, k=1)
    return choice[0]


def subtree_weights(node, mode='descendents', filter=None):
    weights = []
    if 'children' in node:
        for child in node['children']:
            if not filter or filter(child):
                if mode == 'descendents':
                    weights.append(num_descendents(child, filter))
                elif mode == 'leaves':
                    descendents = subtree_list(child, filter)
                    leaf_descendents = [d for d in descendents if 'children' not in d or len(d['children']) == 0]
                    weights.append(len(leaf_descendents))
                elif mode == 'uniform':
                    weights.append(1)
                else:
                    print('invalid mode for subtree weights')
            else:
                weights.append(0)
    #print(weights)
    norm = np.linalg.norm(weights, ord=1)
    normalized_weights = weights / norm
    #print(normalized_weights)
    return normalized_weights

#################################
#   Ancestry
#################################

# Returns a list of ancestor nodes beginning with the progenitor
def node_ancestry(node, node_dict):
    ancestry = [node]
    while "parent_id" in node:
        if node['parent_id'] in node_dict:
            node = node_dict[node["parent_id"]]
            ancestry.insert(0, node)
        else:
            break
    return ancestry

# returns node ancestry starting from root
def ancestry_in_range(root, node, node_dict):
    ancestry = node_ancestry(node, node_dict)
    #print([n['id'] for n in ancestry])
    i = 0
    while ancestry[i]['id'] != root['id']:
        i += 1
    return ancestry[i:]

def ancestor_text_indices(ancestry=None, text_callback=None):
    indices = []
    #end_indices = []
    start_index = 0
    for node in ancestry:
        text = text_callback(node) if text_callback else node['text']
        #text.append(node["text"])
        indices.append((start_index, start_index + len(text)))
        start_index += len(text)
    return indices

def ancestor_text_end_indices(ancestry=None, text_callback=None):
    return [ind[1] for ind in ancestor_text_indices(ancestry, text_callback)]

def ancestor_text_start_indices(ancestry=None, text_callback=None):
    return [ind[0] for ind in ancestor_text_indices(ancestry, text_callback)]
    
def ancestor_text_list(ancestry, text_callback=None):
    if text_callback:
        return [text_callback(node) for node in ancestry]
    else:
        return [node['text'] for node in ancestry]

def ancestry_plaintext(ancestry, text_callback=None):
    if text_callback:
        return "".join(ancestor_text_list(ancestry, text_callback))
    else:
        return "".join(ancestor_text_list(ancestry))

def nearest_common_ancestor(node_a, node_b, node_dict):
    ancestry_a = node_ancestry(node_a, node_dict)
    ancestry_b = node_ancestry(node_b, node_dict)
    #print('ancestry a:', [n['id'] for n in ancestry_a])
    #print('ancestry b:', [n['id'] for n in ancestry_b])
    for i in range(1, len(ancestry_a)):
        if i > (len(ancestry_b) - 1) or ancestry_a[i] is not ancestry_b[i]:
            return ancestry_a[i-1], i-1
    return ancestry_a[-1], len(ancestry_a) - 1

def path_distance(node_a, node_b, node_dict):
    nca, _ = nearest_common_ancestor(node_a, node_b, node_dict)
    #print('nca:', nca['id'])
    a_distance = len(ancestry_in_range(nca, node_a, node_dict))
    b_distance = len(ancestry_in_range(nca, node_b, node_dict))
    return (a_distance - 1) + (b_distance - 1)

# Returns True if a is ancestor of b
def in_ancestry(a, b, node_dict):
    ancestry = node_ancestry(b, node_dict)
    return a in ancestry

def node_index(node, node_dict):
    return len(node_ancestry(node, node_dict)) - 1


# returns whether node_a was created before node_b
# TODO for old nodes, extract date from generation metadata...?
def created_before(node_a, node_b):
    try:
        timestamp1 = node_a['meta']['creation_timestamp']
        timestamp2 = node_b['meta']['creation_timestamp']
    except KeyError:
        print(node_a['meta'])
        print(node_b['meta'])
        print('error: one or more of the nodes has no timestamp attribute')
        return None
    t1 = datetime.strptime(timestamp1, "%Y-%m-%d-%H.%M.%S")
    t2 = datetime.strptime(timestamp2, "%Y-%m-%d-%H.%M.%S")
    return t1 <= t2

def get_inherited_attribute(attribute, node, tree_node_dict):
    for lineage_node in reversed(node_ancestry(node, tree_node_dict)):
        if attribute in lineage_node:
            return lineage_node[attribute]
    return None

# recursively called on subtree
def overwrite_subtree(node, attribute, new_value, old_value=None, force_overwrite=False):
    if force_overwrite or (attribute not in node) or old_value is None or (node[attribute] == old_value) \
            or (node[attribute] == new_value):
        node[attribute] = new_value
        terminal_nodes_list = []
        for child in node['children']:
            terminal_nodes_list += overwrite_subtree(child, attribute, new_value, old_value, force_overwrite)
        return terminal_nodes_list
    else:
        return [node]





# TODO regex, tags
def search(root, pattern, text=True, text_attribute_name='text', tags=False, case_sensitive=False, regex=False,
           filter_set=None, max_depth=None):
    matches = []
    if not (text or tags) \
            or (filter_set is not None and root['id'] not in filter_set)\
            or max_depth == 0:
        return []
    if text:
        matches_iter = re.finditer(pattern, root[text_attribute_name]) if case_sensitive \
            else re.finditer(pattern, root[text_attribute_name], re.IGNORECASE)
        for match in matches_iter:
            matches.append({'node_id': root['id'],
                            'span': match.span(),
                            'match': match.group()})
    if tags:
        # search for pattern in root['tags']
        pass
    for child in root['children']:
        matches += search(child, pattern, text, text_attribute_name, tags, case_sensitive, regex, filter_set,
                          max_depth-1 if max_depth else None)
    return matches



# {
#   root: {
#       text: ...
#       children: [
#           {
#               text: ...
#               children: ...
#           },
#       ]
#   }
#   generation_settings: {...}
# }
# Adds an ID field and a parent ID field to each dict in a recursive tree with "children"
def flatten_tree(d, reverse=False):
    if "id" not in d:
        d["id"] = str(uuid.uuid1())

    children = d.get("children", [])
    flat_children = []
    for child in (reversed(children) if reverse else children):
        child["parent_id"] = d["id"]
        flat_children.extend(flatten_tree(child, reverse))

    return [d, *flat_children]


def flatten_tree_revisit_parents(d, parent=None):
    if "id" not in d:
        d["id"] = str(uuid.uuid1())

    children = d.get("children", [])
    flat_children = []
    for child in children:
        child["parent_id"] = d["id"]
        flat_children.extend(flatten_tree_revisit_parents(child, d))

    return [d, *flat_children] if parent is None else [d, *flat_children, parent]


# Remove html and random double newlines from Miro
def fix_miro_tree(flat_data):
    # Otherwise it will randomly insert line breaks....
    h = html2text.HTML2Text()
    h.body_width = 0

    id_to_node = {d["id"]: d for d in flat_data}
    for d in flat_data:
        # Only fix miro text
        if "text" not in d or all([tag not in d["text"] for tag in ["<p>", "</p"]]):
            continue

        d["text"] = h.handle(d["text"])

        # p tags lead to double newlines
        d["text"] = d["text"].replace("\n\n", "\n")

        # Remove single leading and trailing newlines added by p tag wrappers
        if d["text"].startswith("\n"):
            d["text"] = d["text"][1:]
        if d["text"].endswith("\n"):
            d["text"] = d["text"][:-1]

        # No ending spaces, messes with generation
        d["text"] = d["text"].rstrip(" ")

        # If the text and its parent starts without a new line, it needs a space:
        if not d["text"].startswith("\n") and \
                ("parent_id" not in d or not id_to_node[d["parent_id"]]["text"].endswith("\n")):
            d["text"] = " " + d["text"]


def add_immutable_root(tree):
    if tree['root'].get('mutable', True):
        old_root = tree['root']
        tree['root'] = {
            "mutable": False,
            "visited": True,
            "text": "",
            "id": str(uuid.uuid1()),
            "children": [old_root],
        }


def make_simple_tree(tree):
    if 'root' in tree:
        tree = tree['root']
    simple_tree = {}
    simple_tree['text'] = tree['text']
    simple_tree['children'] = [make_simple_tree(child) for child in tree['children']]
    return simple_tree

# add empty children attribute to nodes without children
def fix_tree(tree):
    if 'root' in tree:
        tree = tree['root']
    if 'children' not in tree:
        tree['children'] = []
    if 'parentId' in tree:
        tree['parent_id'] = tree['parentId']
        del tree['parentId']
    else:
        for child in tree['children']:
            fix_tree(child)

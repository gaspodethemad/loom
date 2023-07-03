# Utilities for working with Multiloom servers
import requests
import time
from . import util_tree

def get_timestamp():
    """
    Get the current time as a timestamp
    :return: The current time as a timestamp
    """
    return time.strftime('%Y-%m-%d %H:%M:%S')

def post_node(node, author, server, port, tree_id, password):
    """
    Post a node to a Multiloom server
    :param node: The node to post
    :param author: The author of the node
    :param server: The server to post to
    :param port: The port to post to
    :param password: The password to post with
    :return: The response from the server
    """
    data = {
        "id": node["id"],
        "parentId": node["parent_id"],
        "text": node["text"],
        "children": [child["id"] for child in node["children"]] if len(node["children"]) > 0 else list(),
        "author": author,
        "timestamp": get_timestamp()
    }
    headers = {
        "Authorization": password,
        "Tree-Id": tree_id
    }
    response = requests.post(f'http://{server}:{port}/nodes', json=data, headers=headers)
    return response

def post_nodes(nodes, author, server, port, tree_id, password):
    """
    Post nodes to a Multiloom server
    :param nodes: The nodes to post
    :param author: The author of the nodes
    :param server: The server to post to
    :param port: The port to post to
    :param password: The password to post with
    :return: The response from the server
    """
    data = list()
    for node in nodes:
        data.append({
            "id": node["id"],
            "parentId": node["parent_id"] if "parent_id" in node else None,
            "text": node["text"],
            "children": [child["id"] for child in node["children"]] if len(node["children"]) > 0 else list(),
            "author": author,
            "timestamp": get_timestamp()
        })
    headers = {
        "Authorization": password,
        "Tree-Id": tree_id
    }
    response = requests.post(f'http://{server}:{port}/nodes/batch', json=data, headers=headers)
    return response

def update_node(node, author, server, port, tree_id, password):
    """
    Update a node on a Multiloom server
    :param node: The node to update
    :param server: The server to update on
    :param port: The port to update on
    :param password: The password to update with
    :return: The response from the server
    """
    data = {
        "parentId": node["parent_id"] if "parent_id" in node else None,
        "text": node["text"],
        "children": [child["id"] for child in node["children"]] if len(node["children"]) > 0 else list(),
        "author": author,
        "timestamp": get_timestamp()
    }
    headers = {
        "Authorization": password,
        "Tree-Id": tree_id
    }
    # Check if the node exists on the server
    response = get_node(node.id, server, port, tree_id, password)
    if response.status_code == 404:
        # If it doesn't, post it
        return post_node(node, author, server, port, tree_id, password)
    response = requests.put(f'http://{server}:{port}/nodes/{node.id}', json=data, headers=headers)
    return response

def update_nodes(nodes, author, server, port, tree_id, password):
    """
    Update nodes on a Multiloom server
    :param nodes: The nodes to update
    :param server: The server to update on
    :param port: The port to update on
    :param password: The password to update with
    :return: The response from the server
    """
    data = list()
    for node in nodes:
        data.append({
            "id": node["id"],
            "parentId": node["parent_id"] if "parent_id" in node else None,
            "text": node["text"],
            "children": [child["id"] for child in node["children"]] if len(node["children"]) > 0 else list(),
            "author": author,
            "timestamp": get_timestamp()
        })
    headers = {
        "Authorization": password,
        "Tree-Id": tree_id
    }
    response = requests.put(f'http://{server}:{port}/nodes/batch', json=data, headers=headers)
    return response

def delete_node(node_id, server, port, tree_id, password):
    """
    Delete a node from a Multiloom server
    :param node_id: The id of the node to delete
    :param server: The server to delete from
    :param port: The port to delete from
    :param password: The password to delete with
    :return: The response from the server
    """
    headers = {
        "Authorization": password,
        "Tree-Id": tree_id
    }
    response = requests.delete(f'http://{server}:{port}/nodes/{node_id}', headers=headers)
    return response

def delete_nodes(node_ids, server, port, tree_id, password):
    """
    Delete nodes from a Multiloom server
    :param node_ids: The ids of the nodes to delete
    :param server: The server to delete from
    :param port: The port to delete from
    :param password: The password to delete with
    :return: The response from the server
    """
    headers = {
        "Authorization": password,
        "Tree-Id": tree_id
    }
    response = requests.delete(f'http://{server}:{port}/nodes/batch', json=node_ids, headers=headers)
    return response

def get_node(node_id, server, port, tree_id, password):
    """
    Get a node from a Multiloom server
    :param node_id: The id of the node to get
    :param server: The server to get from
    :param port: The port to get from
    :param password: The password to get with
    :return: The response from the server
    """

    headers = {
        "Authorization": password,
        "Tree-Id": tree_id
    }
    response = requests.get(f'http://{server}:{port}/nodes/{node_id}', headers=headers)
    return response

def get_node_count(server, port, tree_id, password):
    """
    Get the number of nodes on a Multiloom server
    :param server: The server to get from
    :param port: The port to get from
    :param password: The password to get with
    :return: The response from the server
    """
    headers = {
        "Authorization": password,
        "Tree-Id": tree_id
    }
    response = requests.get(f'http://{server}:{port}/nodes/count', headers=headers)
    return response

def get_nodes(
    server,
    port,
    tree_id,
    password,
    timestamp="",
):
    """
    Get nodes from a Multiloom server
    :param server: The server to get from
    :param port: The port to get from
    :param password: The password to get with
    :param timestamp: The timestamp to get nodes after (blank for all)
    :return: The response from the server
    """
    headers = {
        "Authorization": password,
        "Tree-Id": tree_id
    }
    if timestamp == "":
        response = requests.get(f'http://{server}:{port}/nodes', headers=headers)
    else:
        response = requests.get(f'http://{server}:{port}/nodes/get/{timestamp}', headers=headers)
    return response

def get_root_node(server, port, tree_id, password):
    """
    Get the root node from a Multiloom server
    :param server: The server to get from
    :param port: The port to get from
    :param password: The password to get with
    :return: The response from the server
    """
    headers = {
        "Authorization": password,
        "Tree-Id": tree_id
    }
    response = requests.get(f'http://{server}:{port}/nodes/root', headers=headers)
    return response

def get_history(
    server,
    port,
    tree_id,
    password,
    timestamp="",
):
    """
    Get the history of a Multiloom server
    :param server: The server to get from
    :param port: The port to get from
    :param tree_id: The id of the tree to get history for
    :param password: The password to get with
    :param timestamp: The timestamp to get history after (blank for all)
    :return: The response from the server
    """
    headers = {
        "Authorization": password,
        "Tree-Id": tree_id
    }
    if timestamp == "":
        response = requests.get(f'http://{server}:{port}/history', headers=headers)
    else:
        response = requests.get(f'http://{server}:{port}/history/{timestamp}', headers=headers)
    return response

def get_node_exists(
        server,
        port,
        tree_id,
        password,
        node_id
):
    """
    Get whether a node exists on a Multiloom server
    :param server: The server to get from
    :param port: The port to get from
    :param tree_id: The id of the tree to check
    :param password: The password to get with
    :param node_id: The id of the node to check
    :return: The response from the server
    """
    headers = {
        "Authorization": password,
        "Tree-Id": tree_id
    }
    response = requests.get(f'http://{server}:{port}/nodes/exists/{node_id}', headers=headers)
    return response

def get_nodes_exist(
        server,
        port,
        tree_id,
        password,
        node_ids
):
    """
    Get whether nodes exist on a Multiloom server
    :param server: The server to get from
    :param port: The port to get from
    :param tree_id: The id of the tree to check
    :param password: The password to get with
    :param node_ids: The list of ids of the nodes to check
    :return: The response from the server
    """
    headers = {
        "Authorization": password,
        "Tree-Id": tree_id
    }
    data = {
        "nodeIds": node_ids
    }
    response = requests.post(f'http://{server}:{port}/nodes/exists', json=data, headers=headers)
    return response

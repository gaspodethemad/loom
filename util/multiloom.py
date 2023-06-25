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

def post_node(node, author, server, port, password):
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
        "parentId": node.parent_id,
        "text": node.text,
        "children": node.children.keys(),
        "author": author,
        "timestamp": get_timestamp()
    }
    headers = {
        "Authorization": password
    }
    response = requests.post(f'http://{server}:{port}/nodes', json=data, headers=headers)
    return response

def update_node(node, author, server, port, password):
    """
    Update a node on a Multiloom server
    :param node: The node to update
    :param server: The server to update on
    :param port: The port to update on
    :param password: The password to update with
    :return: The response from the server
    """
    data = {
        "parentId": node.parent_id,
        "text": node.text,
        "children": node.children.keys(),
        "author": author,
        "timestamp": get_timestamp()
    }
    headers = {
        "Authorization": password
    }
    # Check if the node exists on the server
    response = get_node(node.id, server, port, password)
    if response.status_code == 404:
        # If it doesn't, post it
        return post_node(node, author, server, port, password)
    response = requests.put(f'http://{server}:{port}/nodes/{node.id}', json=data, headers=headers)
    return response

def delete_node(node_id, server, port, password):
    """
    Delete a node from a Multiloom server
    :param node_id: The id of the node to delete
    :param server: The server to delete from
    :param port: The port to delete from
    :param password: The password to delete with
    :return: The response from the server
    """
    headers = {
        "Authorization": password
    }
    response = requests.delete(f'http://{server}:{port}/nodes/{node_id}', headers=headers)
    return response

def get_node(node_id, server, port, password):
    """
    Get a node from a Multiloom server
    :param node_id: The id of the node to get
    :param server: The server to get from
    :param port: The port to get from
    :param password: The password to get with
    :return: The response from the server
    """

    headers = {
        "Authorization": password
    }
    response = requests.get(f'http://{server}:{port}/nodes/{node_id}', headers=headers)
    return response

def get_node_count(server, port, password):
    """
    Get the number of nodes on a Multiloom server
    :param server: The server to get from
    :param port: The port to get from
    :param password: The password to get with
    :return: The response from the server
    """
    headers = {
        "Authorization": password
    }
    response = requests.get(f'http://{server}:{port}/nodes/count', headers=headers)
    return response

def get_nodes(
    server,
    port,
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
        "Authorization": password
    }
    if timestamp == "":
        response = requests.get(f'http://{server}:{port}/nodes', headers=headers)
    else:
        response = requests.get(f'http://{server}:{port}/nodes/get/{timestamp}', headers=headers)
    return response

def get_root_node(server, port, password):
    """
    Get the root node from a Multiloom server
    :param server: The server to get from
    :param port: The port to get from
    :param password: The password to get with
    :return: The response from the server
    """
    headers = {
        "Authorization": password
    }
    response = requests.get(f'http://{server}:{port}/nodes/root', headers=headers)
    return response

def get_history(
    server,
    port,
    password,
    timestamp="",
):
    """
    Get the history of a Multiloom server
    :param server: The server to get from
    :param port: The port to get from
    :param password: The password to get with
    :param timestamp: The timestamp to get history after (blank for all)
    :return: The response from the server
    """
    headers = {
        "Authorization": password
    }
    if timestamp == "":
        response = requests.get(f'http://{server}:{port}/history', headers=headers)
    else:
        response = requests.get(f'http://{server}:{port}/history/{timestamp}', headers=headers)
    return response

class Multiloom:
    """
    A class for interacting with a Multiloom server
    """
    def __init__(self, server, port, password, author):
        self.server = server
        self.port = port
        self.password = password
        self.author = author

    def get_node(self, node_id):
        """
        Get a node from this Multiloom server
        :param node_id: The id of the node to get
        :return: The node
        """
        response = get_node(node_id, self.server, self.port, self.password)
        if response.status_code == 404:
            return None
        return util_tree.node_from_dict(response.json())

    def get_nodes(self, timestamp=""):
        """
        Get nodes from this Multiloom server
        :param timestamp: The timestamp to get nodes after (blank for all)
        :return: The nodes
        """
        response = get_nodes(self.server, self.port, self.password, timestamp)
        return util_tree.nodes_from_dicts(response.json())

    def post_node(self, node):
        """
        Post a node to this Multiloom server
        :param node: The node to post
        :return: The response from the server
        """
        return post_node(node, self.author, self.server, self.port, self.password)

    def update_node(self, node):
        """
        Update a node on this Multiloom server
        :param node: The node to update
        :return: The response from the server
        """
        return update_node(node, self.author, self.server, self.port, self.password)

    def delete_node(self, node_id):
        """
        Delete a node from this Multiloom server
        :param node_id: The id of the node to delete
        :return: The response from the server
        """
        return delete_node(node_id, self.server, self.port, self.password)
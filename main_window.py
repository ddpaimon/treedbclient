from tkinter import *
from tkinter import ttk
import uuid
import requests
import json
import threading
from popup_window import PopupWindow
from events import EventsManager, AddEvent, DeleteEvent, EditEvent

server = 'https://treedb.herokuapp.com/'


def run_in_thread(fn):
    def run(*k, **kw):
        thread = threading.Thread(target=fn, args=k, kwargs=kw)
        thread.start()
        return thread
    return run


def get_all_tree():
    r = requests.get(server + 'tree')
    return json.loads(r.text)['tree']


def get_node(node_id):
    r = requests.get(server + 'tree/' + str(node_id))
    return json.loads(r.text)


def update(tree):
    r = requests.post(server + 'tree/update/', json=tree)
    return json.loads(r.text)['tree']


def update_events(events):
    r = requests.post(server + 'tree/update/events/', json=events)
    return json.loads(r.text)['nodes']


class MainWindow(object):
    db_tree_data = list()
    cached_tree_data = list()
    entry_window = object

    def __init__(self, root):
        self.events_manager = EventsManager()

        self.root = root

        # Base layer
        self.cachedTreeFrame = ttk.Frame(root, borderwidth=2, relief=GROOVE)
        self.cachedTreeFrame.grid(row=0, column=0, sticky=W+N+E+S)

        self.dbTreeFrame = ttk.Frame(root, borderwidth=2, relief=GROOVE)
        self.dbTreeFrame.grid(row=0, column=2, sticky=N+W+E+S)

        self.buttonsFrame = ttk.Frame(root, borderwidth=2)
        self.buttonsFrame.grid(row=1, column=0, sticky=W)

        # Buttons
        self.buttonsFrame.addButton = ttk.Button(self.buttonsFrame, text='+', command=self.add_node)
        self.buttonsFrame.addButton.grid(row=1, column=1)

        self.buttonsFrame.getButton = ttk.Button(self.root, text='<<<', command=self.get_node_from_db)
        self.buttonsFrame.getButton.grid(row=0, column=1)

        self.buttonsFrame.deleteButton = ttk.Button(self.buttonsFrame, text='-', command=self.delete_node)
        self.buttonsFrame.deleteButton.grid(row=1, column=2)

        self.buttonsFrame.resetButton = ttk.Button(self.buttonsFrame, text='Reset', command=self.reset)
        self.buttonsFrame.resetButton.grid(row=2, column=3)

        self.buttonsFrame.editButton = ttk.Button(self.buttonsFrame, text='Edit', command=self.edit)
        self.buttonsFrame.editButton.grid(row=1, column=3)

        self.buttonsFrame.applyButton = ttk.Button(self.buttonsFrame, text='Apply', command=self.apply)
        self.buttonsFrame.applyButton.grid(row=2, column=1)

        self.buttonsFrame.applyEventsButton = ttk.Button(self.buttonsFrame, text='Apply events', command=self.apply_events)
        # self.buttonsFrame.applyEventsButton.grid(row=3, column=1)

        # Trees
        self.cachedTreeFrame.cachedTree = ttk.Treeview(self.cachedTreeFrame)
        self.cachedTreeFrame.cachedTree.heading('#0', text='Cached tree')
        self.cachedTreeFrame.cachedTree.pack(fill=BOTH, expand=1)

        self.dbTreeFrame.dbTree = ttk.Treeview(self.dbTreeFrame)
        self.dbTreeFrame.dbTree.heading('#0', text='Database tree')
        self.dbTreeFrame.dbTree.pack(fill=BOTH, expand=1)

        # Initialize
        self.root.after(1000, self.load_db_data)

    def popup(self, node_name):
        self.entry_window = PopupWindow(self.root, node_name)
        self.buttonsFrame.addButton["state"] = "disabled"
        self.root.wait_window(self.entry_window.top)
        self.buttonsFrame.addButton["state"] = "normal"

    @run_in_thread
    def load_db_data(self):
        self.db_tree_data = get_all_tree()
        self.redraw_db()

    def _redraw(self, subtree, widget_tree):
        """
        Clear tree and render
        :param subtree:
        :param widget_tree:
        :return:
        """
        for i in widget_tree.get_children():
            widget_tree.delete(i)
        self.render_tree(subtree, widget_tree)

    def redraw_cached(self):
        self._redraw(self.cached_tree_data, self.cachedTreeFrame.cachedTree)

    def redraw_db(self):
        self._redraw(self.db_tree_data, self.dbTreeFrame.dbTree)

    def render_tree(self, subtree, widget_tree, root_node_uuid=""):
        """
        Render tree
        :param subtree:
        :param widget_tree:
        :type widget_tree: ttk.Treeview
        :param root_node_uuid:
        :return:
        """
        for child in subtree:
            if 'uuid' not in child:
                child['uuid'] = str(uuid.uuid4())
            node = child['node']
            tag = 'normal' if node['deleted'] else 'deleted'
            if child['node']['id'] is None:
                child['node']['id'] = child['uuid']
                child['new'] = True
            widget_tree.insert(
                root_node_uuid,
                0,
                child["uuid"],
                text=node['name'],  # + " - " + child['uuid'] + " - " + str(child['node']['id']),
                values=child["uuid"],
                open=True,
                tag=tag)
            widget_tree.tag_configure('deleted', font='Times 10 normal')
            widget_tree.tag_configure('normal', font='Times 10 italic')
            widget_tree = self.render_tree(child['children'], widget_tree, root_node_uuid=child["uuid"])
        return widget_tree

    def append_to_cache(self, node):
        rnid = node['root']
        nid = node['id']
        children = list()
        to_delete = list()
        for child in self.cached_tree_data:
            if child['node']['root'] == nid and child['node']['root'] is not None:
                to_delete.append(child)
                children.append(child)
        for ditem in to_delete:
            self.cached_tree_data.pop(self.cached_tree_data.index(ditem))
        if nid is not None and self.find_node_data_by_id(nid, self.cached_tree_data) is not None:
            return
        cached_root_node = self.find_node_data_by_id(rnid, self.cached_tree_data)
        if cached_root_node:
            cached_root_node['children'].append({'node': node, 'children': children})
            if cached_root_node['node']['deleted'] and not node['deleted']:
                self.delete_subtree({'node': node, 'children': children})
        else:
            self.cached_tree_data.append({'node': node, 'children': children})
        self.redraw_cached()

    def find_node_data_by_uuid(self, node_uuid, subtree):
        res = None
        for child in subtree:
            if child['uuid'] == node_uuid:
                res = child
                break
            else:
                res = self.find_node_data_by_uuid(node_uuid, child['children'])
                if res is not None:
                    break
        # print(res)
        return res

    def find_node_data_by_id(self, node_id, subtree):
        res = None
        for child in subtree:
            if child['node']['id'] == node_id:
                res = child
                break
            else:
                res = self.find_node_data_by_id(node_id, child['children'])
                if res is not None:
                    break
        # print(res)
        return res

    def node_exists(self, node_id, subtree):
        """
        Check if node exists in tree
        :param node_id:
        :param subtree:
        :return:
        """
        return False if self.find_node_data_by_id(node_id, subtree) is None else True

    def delete_subtree(self, node):
        node['node']['deleted'] = True
        res = dict()
        res['node'] = node['node']
        res['children'] = list()
        for child in node['children']:
            if not child['node']['deleted']:
                res['children'].append(self.delete_subtree(child))
        return res

    def add_node(self):
        cache_selected_items = self.cachedTreeFrame.cachedTree.selection()
        if len(cache_selected_items) != 0:
            self.popup('')
            if len(self.entry_window.value) == 0:
                return
            item = self.cachedTreeFrame.cachedTree.item(cache_selected_items[0])
            node_name = self.entry_window.value
            node_id = str(uuid.uuid4())
            root_node_data = self.find_node_data_by_uuid(item['values'][0], self.cached_tree_data)
            self.events_manager.append_event(AddEvent(node_id, root_node_data['node']['id'], node_name))
            if not root_node_data['node']['deleted']:
                node_data = {'name': node_name, 'root': root_node_data['node']['id'], 'id': node_id, 'deleted': False}
                self.append_to_cache(node_data)

    @run_in_thread
    def get_node_from_db(self):
        db_selected_items = self.dbTreeFrame.dbTree.selection()
        if len(db_selected_items) != 0:
            item = self.dbTreeFrame.dbTree.item(db_selected_items[0])
            db_node_data = self.find_node_data_by_uuid(item['values'][0], self.db_tree_data)['node']
            if not db_node_data['deleted']:
                nid = db_node_data['id']
                if not self.node_exists(nid, self.cached_tree_data):
                    res_node = get_node(nid)
                    self.append_to_cache(res_node)

    def delete_node(self):
        cache_selected_items = self.cachedTreeFrame.cachedTree.selection()
        if len(cache_selected_items) == 0:
            return
        item = self.cachedTreeFrame.cachedTree.item(cache_selected_items[0])
        node_data = self.find_node_data_by_uuid(item['values'][0], self.cached_tree_data)
        self.events_manager.append_event(DeleteEvent(node_data['node']['id']))
        if not node_data['node']['deleted']:
            self.delete_subtree(node_data)
            self.redraw_cached()

    def reset(self):
        self.cached_tree_data = list()
        self.redraw_cached()

    def edit(self):
        cache_selected_items = self.cachedTreeFrame.cachedTree.selection()
        if len(cache_selected_items) != 0:
            item = self.cachedTreeFrame.cachedTree.item(cache_selected_items[0])
            # print(item['text'])
            self.popup(item['text'])
            if len(self.entry_window.value) == 0:
                return
            node_name = self.entry_window.value
            node_data = self.find_node_data_by_uuid(item['values'][0], self.cached_tree_data)
            node_data['node']['name'] = node_name
            self.events_manager.append_event(EditEvent(node_data['node']['id'], node_name))
            self.redraw_cached()

    def _refill_new(self, children):
        for child in children:
            if 'new' in child:
                child['node']['id'] = None
                child['node']['root'] = None
            self._refill_new(child['children'])

    @run_in_thread
    def apply(self):
        self._refill_new(self.cached_tree_data)

        self.cached_tree_data = update(self.cached_tree_data)

        self.db_tree_data = get_all_tree()
        self.redraw_db()

        self.redraw_cached()

    @run_in_thread
    def apply_events(self):
        events = self.events_manager.serialize_events()
        print(events)
        # self.cached_tree_data = update_events(events)
        update_events(events)

        self.db_tree_data = get_all_tree()
        self.redraw_db()

        self.redraw_cached()

        self.events_manager.clear()

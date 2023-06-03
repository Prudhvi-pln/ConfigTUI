# Description: To view/edit yaml files in TUI
# Requires config-tui.css in the same folder level
__author__ = 'PrudhviCh'
__version__ = '1.0'

import os
import sys
import yaml

from rich.text import Text
from rich.highlighter import ReprHighlighter

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Footer, Input, Tree
from textual.widgets.tree import TreeNode


CSS_FILE = 'config-tui.css'
edit_dict_keys = False
allow_value_data_type_changes = True


class AlertScreen(ModalScreen[bool]):
    """Screen for a Dialog Box.

    Returns:
        boolean status of user's confirmation
    """

    CSS_PATH = CSS_FILE

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.message = kwargs['message']

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(f"{self.message}", id="dialog-msg"),
            Button("Yes", variant="success", id="yes"),
            Button("No", variant="primary", id="no"),
            id="dialog-box",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'yes':
            self.dismiss(True)
        else:
            self.dismiss(False)


class SaveScreen(ModalScreen):
    """Screen with a dialog to Save file as."""

    CSS_PATH = CSS_FILE

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.new_json_data = kwargs['data']
        self.input_yml = kwargs['input_yml']

    def compose(self) -> ComposeResult:
        self.out_file_name = Input(placeholder="Enter file name...", id="save-input", value=self.input_yml)
        self.out_file_name.border_title = 'Save as'
        yield Grid(
            self.out_file_name,
            Button("Save", variant="success", id="yes"),
            Button("Cancel", variant="primary", id="no"),
            id="dialog-box",
        )

    def save_file(self) -> None:
        # save configuration & exit
        out_file = self.out_file_name.value
        with open(out_file, 'w') as out:
            yaml.dump(self.new_json_data, out, allow_unicode=False, sort_keys=False, indent=4)
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'no':
            self.app.pop_screen()
        else:
            self.save_file()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self.save_file()


class ConfigurationEditor(App):

    # TITLE = 'Configuration Editor'
    # SUB_TITLE = 'Edit your configuration files'

    BINDINGS = [
        ("o", "toggle_dark", "Toggle dark mode"),
        ("x", "toggle", "Expand/Collapse All"),
        ("i", "insert_node", "Insert Node"),
        ("d", "delete_node", "Delete Node"),
        ("e", "edit", "Edit Value"),
        ("r", "reload", "Reload"),
        ("s", "save", "Save"),
        ("q", "quit", "Quit"),
    ]

    CSS_PATH = CSS_FILE

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.config_file = kwargs['config_file']
        self.delimiter = ': '
        self.edit_node_help = "Select a node to edit..."
        self.add_node_help = "Provide input in json/dict format. [Ex: {'key1': 'val1', 'key2': [1, 2]}]"

    def compose(self) -> ComposeResult:
        self.edit_box = Input(placeholder=self.edit_node_help, id="edit-node")
        self.edit_box.border_title = 'Enter new value'
        self.json_tree = Tree('ROOT')
        yield Label("Configuration Editor", id='header')
        yield Footer()
        yield self.json_tree
        yield self.edit_box

    def update_tree(self, name: str, node: TreeNode, data: object) -> None:
        """Adds a node to the tree.

        Args:
            name (str): Name of the node.
            node (TreeNode): Parent node.
            data (object): Data associated with the node.
        """
        if node.is_root:
            abs_key = ''
        elif node.parent.data.get('abs_key') == '':
            abs_key = f"{name}"
        else:
            abs_key = f"{node.parent.data.get('abs_key')}.{name}"
        val_type = str(type(data)).split("'")[1]
        node.data = {
            'key': name,
            'value': name,
            'type': val_type,
            'abs_key': abs_key
        }
        if isinstance(data, dict):
            node.set_label(Text(f"{{}} {name}"))
            node.data.update({
                'editable': edit_dict_keys
            })
            for key, value in data.items():
                new_node = node.add("")
                self.update_tree(key, new_node, value)
        elif isinstance(data, list):
            node.set_label(Text(f"[] {name}"))
            node.data.update({
                'editable': False
            })
            for index, value in enumerate(data):
                new_node = node.add("")
                self.update_tree(str(index), new_node, value)
        else:
            node.allow_expand = False
            # add both key and value to label for displaying
            if name:
                label = Text.assemble(
                    Text.from_markup(f"[b]{name}[/b]{self.delimiter}"), ReprHighlighter()(repr(data))
                )
            else:
                label = Text(repr(data))
            node.set_label(label)
            # add data separately to node
            node.data.update({
                'value': data,
                'editable': True
            })

    def load_file(self) -> None:
        """Load the YAML file as JSON."""
        with open(self.config_file, "r") as yml:
            try:
                self.json_data = yaml.safe_load(yml)
            except yaml.YAMLError as exc:
                print(f'Failed to load YAML with: {exc}')
                exit(1)

    def on_mount(self) -> None:
        """Load the JSON when the app starts."""
        # load file
        self.load_file()
        # load into tree
        self.update_tree('ROOT', self.json_tree.root, self.json_data)
        # self.json_tree.show_root = False
        # self.cur_node = self.json_tree.get_node_at_line(0)
        self.edit_box.disabled = True
        self.cur_node = self.json_tree.root.expand()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_toggle(self) -> None:
        """An action to show/hide entire configuration."""
        if self.json_tree.root.is_expanded:
            self.json_tree.root.collapse_all()
        else:
            self.json_tree.root.expand_all()

    def action_reload(self) -> None:
        """Reload the configuration file."""
        # clear tree first
        tree = self.json_tree
        tree.clear()
        # re-load file
        self.load_file()
        # re-create tree
        self.update_tree('ROOT', tree.root, self.json_data)

    def action_edit(self) -> None:
        # do not edit if it is root or node is not editable
        if self.cur_node.data.get('value') is None and not self.cur_node.data.get('editable'):
            return

        # change focus to input box for editing
        self.edit_box.focus()

    def invalid_input_handler(self, err_msg) -> None:
        """Handle error inputs in edit field."""
        self.edit_box.border_subtitle = f'{err_msg}'
        self.edit_box.styles.animate(attribute='background', value='red', duration=1.0, final_value=None)

    def update_value(self) -> bool:
        """Update the value in a node.

        Returns:
            boolean status whether update is successful
        """

        old_label = self.cur_node.label
        new_value = self.edit_box.value

        if self.cur_node.data.get('type') == 'dict':
            new_label = Text(f"{{}} {new_value}")
        elif self.cur_node.data.get('type') == 'list':
            new_label = Text(f"[] {new_value}")
        else:
            if allow_value_data_type_changes:
                # infer value type
                exprsn = f'{new_value}'
            elif self.cur_node.data.get('type') == 'str':
                # keep it in quotes to evalute as string
                exprsn = f'"{new_value}"'
            else:
                # cast value to it's originial type
                exprsn = f"{self.cur_node.data.get('type')}({new_value})"
            try:
                new_value = eval(exprsn)
            except Exception as e:
                if allow_value_data_type_changes:
                    pass
                else:
                    self.invalid_input_handler(f'INVALID VALUE. Error: {e}')
                    return False    # do not make any changes if conversion failed

            new_label = Text.assemble(
                Text.from_markup(f"[b]{self.cur_node.label.split(':')[0]}[/b]{self.delimiter}"), ReprHighlighter()(repr(new_value))
            )

        if old_label != new_label:
            # update key for expandable data
            if self.cur_node.data.get('type') in ['dict', 'list']:
                self.cur_node.data['key'] = new_value
            self.cur_node.data['value'] = new_value
            self.cur_node.set_label(new_label)

        return True

    def action_save(self) -> None:
        """Save the configuration changes."""
        root_node = self.json_tree.root

        def export_tree_to_json(node):
            """
            Export a tree to JSON data.

            Args:
                node (TreeNode): Root node of the tree.

            Returns:
                str: JSON data representing the tree.
            """
            if not node.allow_expand:
                # Leaf node, return the data directly
                return node.data.get('value')
            else:
                # Non-leaf node, build a dictionary or list depending on the node type
                if node.data['type'] == 'dict':
                    data = {}
                else:
                    data = []

                for child in node.children:
                    # Recursively export each child and add it to the dictionary or list
                    child_data = export_tree_to_json(child)
                    if node.data['type'] == 'dict':
                        key = child.data['key']
                        data[key] = child_data
                    else:
                        data.append(child_data)

                return data

        # convert tree to json data
        json_data = export_tree_to_json(root_node)

        # send user to Save As popup
        self.push_screen(SaveScreen(data=json_data, input_yml=self.config_file))

    def add_new_node(self) -> bool:
        """Add a new node to the tree.

        Returns:
            boolean status whether insertion is successful
        """
        data = self.edit_box.value
        try:
            data = eval(data)
        except Exception as e:
            self.invalid_input_handler(f'INVALID FORMAT. Error: {e}')
            return False
        # convert leaf node to expandable
        self.cur_node.allow_expand = True
        self.update_tree(self.cur_node.data['key'], self.cur_node, data)

        return True

    @on(Tree.NodeHighlighted)
    def toggle_edit_field(self, event: Tree.NodeHighlighted) -> None:
        event.stop()
        # track the current node in the tree
        self.cur_node = event.node
        # update node value in edit box
        self.edit_box.border_subtitle = ''
        self.edit_box.placeholder = self.edit_node_help
        self.edit_box.tooltip = None
        if self.cur_node.data.get('editable'):
            self.edit_box.value = str(self.cur_node.data.get('value'))
            self.edit_box.disabled = False
        else:
            self.edit_box.value = ''
            self.edit_box.disabled = True

    @on(Input.Submitted)
    def edit_field_handler(self, event: Input.Submitted) -> None:
        event.stop()
        # check for input type: edit or add
        if self.edit_box.placeholder == self.edit_node_help:
            status = self.update_value()
        elif self.edit_box.placeholder == self.add_node_help:
            status = self.add_new_node()

        # remove any previous error message
        if status:
            self.edit_box.border_subtitle = ''
            # once input submitted change focus to tree for viewing
            self.json_tree.focus()

    def action_insert_node(self) -> None:
        """Add new nodes under the selected node"""
        # set edit field properties
        self.edit_box.value = ''
        self.edit_box.placeholder = self.add_node_help
        self.edit_box.tooltip = self.add_node_help
        self.edit_box.disabled = False
        # change focus to input box for editing
        self.edit_box.focus()

    def action_delete_node(self) -> None:
        """Remove the selected node."""
        # do not delete root node
        if self.cur_node.data.get('abs_key') == '':
            return
        
        def get_return_status(status: bool) -> None:
            """Called when AlertScreen is dismissed."""
            if status:
                # delete the node on confirmation
                try:
                    self.cur_node.remove()
                except TreeNode.RemoveRootError as rre:
                    pass
                # reset cursor to root to update the cur_node
                self.json_tree.action_scroll_home()

        confirm_screen = AlertScreen(message=f"Delete node \[{self.cur_node.data['abs_key']}] ?")
        self.push_screen(confirm_screen, get_return_status)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f'Usage: python {sys.argv[0]} [yaml-file-to-be-edited]')
        exit(1)
    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f'Config file [{input_file}] not found')
        exit(1)
    ce_tui = ConfigurationEditor(config_file=input_file)
    ce_tui.run()

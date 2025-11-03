# menus.py
import json
from copy import deepcopy

'''
def print_options(options):
    """Print numbered options for user selection"""
    if not isinstance(options, (list, dict)):
        root_keys = list(options)
    else:
        root_keys = options
    display_options = [k for k in root_keys]
    for i, key in enumerate(display_options, 1):
        print(f"{i}. {key}")


def choose_option(options):
    """Let user select a number"""
    while True:
        choice = input(
            "Select an option (or 'b' to go back, 'q' to quit, 'r' to return to root): ")
        if choice.lower() == 'q':
            exit(0)
        if choice.lower() == 'b':
            return None
        if choice.lower() == 'r':
            return 'ROOT'
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("Invalid choice, try again.")


def traverse(node, path=None, schema=None):
    """Recursive traversal of schema node"""
    if path is None:
        path = []

    # Lazy resolve refs if present
    if isinstance(node, dict) and node.get('$ref') == '#/components':
        print("Resolving lazy #/components reference...")
        node = resolve_lazy_components(node)

    # Show dict keys
    if isinstance(node, dict):
        while True:
            print(f"\nCurrent path: {'/'.join(path) if path else 'root'}")
            print("Available keys:")
            print_options(node.keys())

            choice = choose_option(list(node.keys()))
            if choice is None:
                return  # back
            if choice == 'ROOT':
                traverse(schema, schema=schema)
            traverse(node[choice], path + [choice], schema=schema)

    # Show list elements
    elif isinstance(node, list):
        while True:
            print(
                f"\nCurrent path: {'/'.join(path)} (list with {len(node)} elements)")
            print("Select index to traverse:")
            print_options([node[i] for i in range(len(node))])

            choice = choose_option(list(range(len(node))))
            if choice is None:
                return
            if choice == 'ROOT':
                traverse(schema, schema=schema)
            traverse(node[choice], path + [str(choice)], schema=schema)

    # Leaf node
    else:
        print(f"\nReached leaf at {'/'.join(path)}: {node}")
        input("Press Enter to go back...")
'''



class Schema():
    def __init__(self, path=None):
        self.load_schema(path)
        self.root = self.schema[list(self.schema.keys())[0]]

    def load_schema(self, path):
        try:
            with open(path) as f:
                self.schema = json.load(f)
        except Exception as e:
            print(f"Encountered error while loading schema: {e}\nExiting...")
            return

    def traverse_lazy(self, node):
        path = node.get("$ref").lstrip("#/").split("/")
        try:
            ref = self.root
            for child in path:
                if ref is not None:
                    ref = ref.get(child)
                else:
                    raise AttributeError("ref not found")
            node.pop("$ref")
            node.update(deepcopy(ref))
        except Exception as e:
            print(f"encountered error, stopping: {e}")
            return


def traverse(node, schema, path=None):
    '''Recursive traversal of schema
    
    important features:
    - back to root
    - back to previous (parent)
    - undo 
    '''
    if path is None:
        path = []
    '''resolve ref is exists'''
    if node.get("type") == "object" and node.get("$ref") is not None:
        schema.traverse_lazy(node)

    match node.get("type"):
        case value if value == "object": # another dict object with subcomponents
            display_options(node, value)
        case value if value == "list":
            print(node.get("type"))
            while True:
                choice = display_options(node, value)
                match choice:
                    case value if 0 <= value < len(node["fields"]):
                        traverse(node["fields"][list(node["fields"].keys())[value]], schema)
        case "int" | "long" | "float": # single text input
            print("boogie woogie")
        case value if value == "str":
            if node.get("choices") is not None: # dropdown for every choice
                display_options(node, value)
            else: # single text input
                print(node.get("type"), "single")
        case "bool": # binary dropdown for T/F
            print(node.get("type"))

        case value if isinstance(value, list): # multiple types, depends on user choice
            print(node.get("type"))
        case _: # If procced, then malformed JSON somewhere
            print(value, "exiting")
            return
    print("continue")

def display_options(node, type):
    match type:
        case "object" | "list":
            options = {i + 1:k for (i, k) in enumerate(node["fields"].keys())}
            for i in options:
                print(f"{i}: {options[i]}")
            choice = input("choose a component\n")

        case "str":
            options = {i + 1:v for (i, v) in enumerate(node["choices"])}
            for i in options:
                print(f"{i}: {options[i]}")




if __name__ == "__main__":
    schema = Schema("../schema/item_components.json")
    print("Interactive schema explorer starting at root...")
    traverse(node=schema.root, schema=schema)

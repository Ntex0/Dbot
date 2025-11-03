# menus.py
from discord.ui import Select, View, Button
import discord
from copy import deepcopy
import json

PER_PAGE = 25


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


class DynamicSelect(Select):
    def __init__(self, user_id, options_list, page=0, path=None, on_select=None):
        self.user_id = user_id
        self.options_list = options_list
        self.page = page
        self.path = path or []
        self.on_select = on_select  # callback to call when a leaf is selected

        page_options = options_list[page*PER_PAGE: (page+1)*PER_PAGE]

        super().__init__(
            placeholder=f"Select an option (Page {page+1})",
            options=[discord.SelectOption(label=str(o)) for o in page_options],
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        # call the provided callback with the selected value and current path
        if self.on_select:
            await self.on_select(interaction, self.path + [choice])


class DynamicMenu(View):
    def __init__(self, user_id, schema_node, path=None, on_select=None):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.path = path or []
        self.schema_node = schema_node
        self.on_select = on_select
        self.current_page = 0
        self.options_list = list(schema_node.keys()) if isinstance(
            schema_node, dict) else schema_node
        self.add_item(DynamicSelect(user_id, self.options_list,
                      self.current_page, self.path, self.on_select))

        if len(self.options_list) > PER_PAGE:
            self.add_item(
                Button(label="Prev", style=discord.ButtonStyle.secondary, custom_id="prev"))
            self.add_item(
                Button(label="Next", style=discord.ButtonStyle.secondary, custom_id="next"))

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.user_id

    async def update_select(self, interaction: discord.Interaction):
        self.clear_items()
        self.add_item(DynamicSelect(self.user_id, self.options_list,
                      self.current_page, self.path, self.on_select))
        if len(self.options_list) > PER_PAGE:
            self.add_item(
                Button(label="Prev", style=discord.ButtonStyle.secondary, custom_id="prev"))
            self.add_item(
                Button(label="Next", style=discord.ButtonStyle.secondary, custom_id="next"))
        await interaction.response.edit_message(view=self)


async def open_menu(interaction, schema_node, path=None):
    """
    Launch a dynamic menu starting from `schema_node`.
    Resolves lazy refs on-demand.
    Returns selected data in a dict.
    """

    selected_data = {}

    async def on_select(i: discord.Interaction, current_path):
        # Traverse the schema node according to path
        node = schema_node
        for key in current_path:
            node = node[key] if isinstance(node, dict) else node[int(key)]

        # Lazy resolve if $ref
        if isinstance(node, dict) and '$ref' in node:
            node = resolve_lazy_components(node)

        if isinstance(node, dict):
            # If it's a dict, open a new menu for subkeys
            await i.response.edit_message(content=f"Select from {current_path[-1]}", view=DynamicMenu(i.user.id, node, current_path, on_select))
        else:
            # Leaf node, store selection
            parent = selected_data
            for k in current_path[:-1]:
                parent = parent.setdefault(k, {})
            parent[current_path[-1]] = node
            await i.response.send_message(f"Selected: {current_path[-1]} -> {node}", ephemeral=True)
            await i.message.delete()  # close previous menu

    await interaction.response.send_message("Select an option:", view=DynamicMenu(interaction.user.id, schema_node, path, on_select), ephemeral=True)
    return selected_data

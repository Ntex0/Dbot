import asyncio
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


class DynamicMenuView(View):
    def __init__(self, schema):
        super().__init__(timeout=5)
        self.future = asyncio.get_event_loop().create_future()
        self.schema = schema
        self.msg: discord.webhook.async_.WebhookMessage = None

    async def cancel_menu(self):
        if not self.future.done():
            self.future.cancel()
        try:
            await self.msg.edit(content="***cancelled***", view=None)
            await asyncio.sleep(2)
            await self.msg.delete()
        except Exception as e:
            print(f"cancel menu error: {e}")
    
    
    
    
    
    @discord.ui.button(label="Submit", style=discord.ButtonStyle.success)
    async def submit(self, interaction: discord.Interaction, button:Button):
        pass
    
    
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button:Button):
        await interaction.response.defer()
        await self.cancel_menu()
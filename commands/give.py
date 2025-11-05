import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select, Button, Modal
from menus.menus import Schema, DynamicMenuView
from main import ROOT
import os
import asyncio

class GiveCommand():
    def __init__(self, target=None, item_id=None, components=None, amount=None):
        self.target = target
        self.item_id = item_id
        self.components = components
        self.amount = amount
    
    def parse_output(self):
        pass
    
    def __str__(self):
        return f"**Target:** `{self.target}`\n**Id:** `{self.item_id}`\n**Amount:** `{self.amount}`\n**Components:** ```{self.components}```"

''' _______ START OF GIVE UI LOGIC ___________'''
class GiveItemView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.future = asyncio.get_event_loop().create_future()
        self.give = GiveCommand()
        self.add_item(AddParameters())
        component_file = os.path.join(ROOT,"schema","item_components.json")
        self.schema = Schema(component_file)
    
    def update_message(self):
        embed = discord.Embed(
            colour=discord.Color.dark_blue(),
            title="Command Overview",
            description=f"{self.give}",
        )
        #return f"# You've selected:\n```Target: {self.give.target}\nAmount: {self.give.amount}\nItem: {self.give.item_id}\nItem components: {self.give.components}```"
        return embed

    @discord.ui.button(label="Finish", style=discord.ButtonStyle.success)
    async def finish(self, interaction: discord.Interaction, button:Button):
        if not all([bool(self.give.amount), bool(self.give.item_id), bool(self.give.target)]):
            await interaction.response.send_message("***You must first set Parameters or press `Cancel`***", ephemeral=True)
            await asyncio.sleep(3)
            await interaction.delete_original_response()
            return
        if getattr(self, "component_view", None):
            await interaction.response.send_message("***Component select menu is still open***\n`Either submit it first or Cancel it`", ephemeral=True)
            await asyncio.sleep(3)
            await interaction.delete_original_response()
            return
        if not self.future.done():
            self.future.set_result(self.give)
            '''^^^^^REPLACE WITH COMPLETED COMMAND^^^^'''
        
        await interaction.response.defer()
        await asyncio.sleep(3)
        await interaction.delete_original_response()
        

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button:Button):
        if not self.future.done():
            self.future.cancel()
        
        await interaction.response.edit_message(content="***Cancelled***", view=None)
        if getattr(self, "component_view", None):
            try:
                await self.component_view.cancel_menu()
            except Exception as e:
                print(f"Error: {e}")
        await asyncio.sleep(3)
        await interaction.delete_original_response()        
    
class AddParameters(Button):
    def __init__(self, label="Set Parameters"):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
    
    async def callback(self, interaction: discord.Interaction):
        view: GiveItemView = self.view
        await interaction.response.send_modal(AddParametersModal(view))
        view.remove_item(self)
        for child in view.children:
            if isinstance(child, ComponentsMenu):
                view.remove_item(child)

        view.add_item(ComponentsMenu())
        view.add_item(AddParameters(label="Change Parameters"))

        await interaction.response.edit_message(view=self.view)    


class AddParametersModal(Modal, title="Set Command Parameters"):
    target = discord.ui.TextInput(
        label="Target Player", placeholder="e.g. @p")
    amount = discord.ui.TextInput(
        label="Amount", placeholder="e.g. 1")
    item_id = discord.ui.TextInput(
        label="Item ID", placeholder="e.g. minecraft:diamond_sword")
    
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view: GiveItemView = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        self.parent_view.give.amount = self.amount
        self.parent_view.give.target = self.target
        self.parent_view.give.item_id = self.item_id
        
        await interaction.response.edit_message(embed=self.parent_view.update_message(), view=self.parent_view)

class ComponentsMenu(Button):
    def __init__(self):
        super().__init__(label="Add Components", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        parent_view: GiveItemView = self.view
        component_view = DynamicMenuView(parent_view.schema)
        await interaction.response.edit_message(view=self.view)
        msg = await interaction.followup.send("# ⚙️ Select Item Components", ephemeral=True, view=component_view)
        component_view.msg = msg
        parent_view.component_view = component_view
        
        
        '''Wait for components view to return future: selected data'''
        try:
            selected_data = await asyncio.wait_for(component_view.future, timeout=None)
            parent_view.component_view = None
        except Exception as e:
            parent_view.component_view = None


'''_____________START OF GIVE COMMAND LOGIC__________________'''
class Give(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="give", description="Give a custom item to a player")
    async def give_command(self, interaction: discord.Interaction):
        '''
        regular give item command
        if components is selected: launch dynamic menu
        '''
        view = GiveItemView()
        await interaction.response.send_message(content="# Construct your /give command\n", view=view, ephemeral=True)
        try:
            command_data: GiveCommand = await asyncio.wait_for(view.future, timeout=None)
        except Exception as e:
            msg = interaction.followup.send(
                content="Cancelled, exiting", ephemeral=True)
            await asyncio.sleep(3)
            await interaction.delete_original_response()
            await msg.delete()
            return
        
        # selected_data will contain a nested dict of the final selection
        print("User selection:", command_data)

        # Here, construct your item/give command from selected_data
        # Example:
        # give_item(player, selected_data)
        msg = await interaction.followup.send(f"**Final command:**\n```/give {command_data.target} {command_data.item_id}[{"" if command_data.components is None else command_data.components}] {command_data.amount}```", ephemeral=True)
        
        
        response = self.bot.mcr(f"give {command_data.target} {command_data.item_id}[{"" if command_data.components is None else command_data.components}] {command_data.amount}")
        
        
        await asyncio.sleep(15)
        await interaction.delete_original_response()
        await msg.delete()



async def setup(bot):
    await bot.add_cog(Give(bot))

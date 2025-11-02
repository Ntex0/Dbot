import discord
from discord import app_commands
from discord.ext import commands
import asyncio

# ---- Category → Enchantment mapping ----
ENCHANTMENT_CATEGORIES = {
    "Armor": [
        "aqua_affinity", "blast_protection", "depth_strider", "feather_falling",
        "fire_protection", "frost_walker", "projectile_protection", "protection",
        "respiration", "soul_speed", "swift_sneak", "thorns"
    ],
    "Weapons": [
        "bane_of_arthropods", "fire_aspect", "knockback", "looting", "sharpness",
        "smite", "sweeping_edge"
    ],
    "Tools": [
        "efficiency", "fortune", "silk_touch", "unbreaking", "mending"
    ],
    "Ranged": [
        "flame", "infinity", "power", "punch", "quick_charge", "piercing", "multishot"
    ],
    "Trident": [
        "channeling", "impaling", "loyalty", "riptide"
    ],
    "Curse": [
        "binding_curse", "vanishing_curse"
    ],
    "Other": [
        "luck_of_the_sea", "lure", "density", "breach", "wind_burst"
    ]
}

# --- Enchantment dropdown (depends on category) ---
class EnchantmentSelect(discord.ui.Select):
    def __init__(self, parent_view, category_name: str):
        self.parent_view = parent_view
        enchantments = ENCHANTMENT_CATEGORIES[category_name]
        options = [discord.SelectOption(label=ench.replace(
            "_", " ").title(), value=ench) for ench in enchantments]
        super().__init__(
            placeholder=f"Select an enchantment ({category_name})...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        await interaction.response.send_modal(AddEnchantmentLevelModal(self.parent_view, selected))

# --- Category dropdown (first step) ---
class CategorySelect(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(label=name, value=name)
            for name in ENCHANTMENT_CATEGORIES.keys()
        ]
        super().__init__(
            placeholder="Choose an enchantment category...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        
        # Remove category selector from view
        self.parent_view.remove_item(self)
        
        # Add enchantment selector to view for that category
        ench_select = EnchantmentSelect(self.parent_view, category)
        self.parent_view.add_item(ench_select)
        
        # Update the message
        await interaction.response.edit_message(
            content=f"**Category:** {category}\nNow pick an enchantment.",
            view=self.parent_view
        )

# --- Modal for enchantments level ---
class AddEnchantmentLevelModal(discord.ui.Modal, title="Set Enchantment level"):
    enchantment_level = discord.ui.TextInput(
        label="Enchantment Level", placeholder="e.g. 5 (max: 255)")

    def __init__(self, parent_view, enchantment_name):
        super().__init__()
        self.parent_view = parent_view
        self.enchantment_name = enchantment_name

    async def on_submit(self, interaction: discord.Interaction):
        lvl = str(self.enchantment_level.value)
        ench = (self.enchantment_name, lvl)
        # if enchantment already exists, update level
        if self.parent_view.enchantments:
            for i, (name, _) in enumerate(self.parent_view.enchantments):
                if name == self.enchantment_name:
                    self.parent_view.enchantments[i] = ench
                    break
                else:
                    self.parent_view.enchantments.append(ench)
                    break
        else:
            self.parent_view.enchantments.append(ench)
        await interaction.response.edit_message(content=self.parent_view.update_full_text(), view=self.parent_view)

# --- Modal for parameters (target, amount, item_id) ---
class SetParametersModal(discord.ui.Modal, title="Set Give Command Parameters"):
    target_player = discord.ui.TextInput(
        label="Target Player", placeholder="e.g. @p", default="@p")
    amount = discord.ui.TextInput(
        label="Amount", placeholder="e.g. 1", default="1")
    item_id = discord.ui.TextInput(
        label="Item ID", placeholder="e.g. diamond_sword", default="stick")

    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        self.parent_view.target_player = self.target_player.value
        self.parent_view.amount = int(self.amount.value)
        self.parent_view.item_id = self.item_id.value
        await interaction.response.edit_message(content=self.parent_view.update_full_text(), view=self.parent_view)

# --- View for the give command ---
class GiveItemView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.enchantments = []
        self.modifiers = []
        self.target_player = None
        self.amount = 1
        self.item_id = None
        
        # start with category selector
        self.category_select = CategorySelect(self)
        self.add_item(self.category_select)

        # Add a future that will hold the result
        self.future = asyncio.get_event_loop().create_future()

    def update_enchant_text(self):
        if not self.enchantments:
            enchants_display = "No enchantments selected yet"
        else:
            enchants_display = "\n".join(
                f"- {name}: {level}" for name, level in self.enchantments)
        return f"**Enchantments:**\n{enchants_display}"
    
    def update_param_text(self):
        target = self.target_player if self.target_player else "@p"
        amount = self.amount if self.amount else 1
        item_id = self.item_id if self.item_id else "stick"
        return f"**Parameters:**\n- Target Player: {target}\n- Amount: {amount}\n- Item ID: minecraft:{item_id}"
    
    def update_full_text(self):
        return f"{'\n'.join(text for text in [self.update_param_text(), self.update_enchant_text()])}"
        
    
    # Complete the command and return the final give command
    @discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
    async def submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        ench_nbt = ""
        modifiers_nbt = ""
        target_nbt = "@p"
        amount_nbt = 1
        item_id_nbt = "minecraft:stick"
        
        if self.modifiers:
            modifiers_nbt = f"attribute_modifiers=[{{{', '.join(f'type: {mod}, amount: {val}, operation: {op}, id: {uid}, slot: {slot}' for mod, val, op, uid, slot in self.modifiers)}}}]"
        # attribute_modifiers=[{type:'step_height', amount:10.0, operation:'add_value', id:'example:custom_step_height', slot:'feet'}]
        if self.item_id:
            item_id_nbt = f"minecraft:{self.item_id}"
        
        if self.enchantments:
            ench_nbt = f"enchantments={{{', '.join(f'{enchant}:{level}' for enchant, level in self.enchantments)}}}"
        
        if self.amount != 1:
            amount_nbt = self.amount
        
        # --------NBT CONSTRUCTION--------
        components = [attr for attr in [modifiers_nbt, ench_nbt] if attr] # add components if exists
        item_data = f"{item_id_nbt}[{', '.join(components)}]"
        command = f"give {target_nbt} {item_id_nbt}[{', '.join(components)}] {amount_nbt}"

        # Set the result in the future
        if not self.future.done():
            self.future.set_result(command)
        await interaction.response.send_message(f"Executing command:\n```{command}```", ephemeral=True)
        await asyncio.sleep(15)
        await interaction.delete_original_response()

    @discord.ui.button(label="Set parameters", style=discord.ButtonStyle.primary)
    async def set_parameters(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetParametersModal(self))
    
    @discord.ui.button(label="Enter attributes", style=discord.ButtonStyle.primary)
    async def enter_attributes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Attribute entry not implemented yet.", ephemeral=True)
        
    @discord.ui.button(label="Switch Enchantment Category", style=discord.ButtonStyle.secondary)
    async def switch_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Remove all EnchantmentSelect items
        for child in list(self.children):
            if isinstance(child, EnchantmentSelect):
                self.remove_item(child)

        # Add category select back
        if not any(isinstance(child, CategorySelect) for child in self.children):
            self.add_item(self.category_select)

        await interaction.response.edit_message(
            content="Select a category to change enchantments.",
            view=self
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.future.done():
            self.future.set_result(None)
        

class Give(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="give", description="Give a custom item to a player")
    async def give_command(self, interaction: discord.Interaction):
        view = GiveItemView()
        await interaction.response.send_message(content="Pick enchantments and parameters", view=view, ephemeral=True)
        try: 
            command = await asyncio.wait_for(view.future, timeout=300)
        except asyncio.TimeoutError:
            await interaction.followup.send("timed out, no command generated", ephemeral=True)
        if command is None:
            # delete the view
            msg = await interaction.followup.send("Give command cancelled.", ephemeral=True)
            await asyncio.sleep(3)
            await interaction.delete_original_response()
            await msg.delete()
            return
        await interaction.delete_original_response()

        if not self.bot.rcon_connected:
            msg = await interaction.followup.send("Not connected to server", ephemeral=True)
            await asyncio.sleep(3)
            await msg.delete()
            return
        try:
            response = self.bot.mcr.command(command)
            msg = await interaction.followup.send(f"Successful: {response}", ephemeral=True)
            await asyncio.sleep(3)
            await msg.delete()
        except Exception as e:
            msg = await interaction.followup.send(f"Error: {e}", ephemeral=True)
            await asyncio.sleep(3)
            await msg.delete()
        
        await asyncio.sleep(3)
        await interaction.delete_original_response()
        await msg.delete()

async def setup(bot):
    await bot.add_cog(Give(bot))

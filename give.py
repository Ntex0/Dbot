import discord

# --- Modal for adding enchantments ---
class AddEnchantmentModal(discord.ui.Modal, title="Add Enchantment"):
    enchantment_name = discord.ui.TextInput(label="Enchantment Name", placeholder="e.g. sharpness")
    enchantment_level = discord.ui.TextInput(label="Enchantment Level", placeholder="e.g. 5 (max: 255)")

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        name = str(self.enchantment_name.value)
        lvl = str(self.enchantment_level.value)
        self.view.enchantments.append((name, lvl))

        await interaction.response.edit_message(content=self.view.build_message_text(), view=self.view)

# --- View for the give command ---
class GiveItemView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.enchantments = []

    def build_message_text(self):
        if not self.enchantments:
            enchants_display = "No enchantments selected yet"
        else:
            enchants_display = "\n".join(f"- {name}: {level}" for name, level in self.enchantments)
        return f"**Selected Enchantments:**\n{enchants_display}"
    
    @discord.ui.button(label="Continue", style=discord.ButtonStyle.primary)
    async def submit(self, interaction: discord.Interaction, button: discord.ui.Button): 
        ench_nbt = ""
        if self.enchantments:
            ench_nbt = f"enchantments={{{','.join(f'{enchant}:{level}' for enchant,level in self.enchantments)}}}"
        command = f'give @p minecraft:diamond_sword[{ench_nbt}] 1'
        
        await interaction.response.send_message(f"Executing command:\n```{command}```")

    @discord.ui.button(label="Add Enchantment", style=discord.ButtonStyle.secondary)
    async def add_enchantment_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddEnchantmentModal(self))
        
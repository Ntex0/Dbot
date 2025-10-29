import discord

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
        else:
            self.parent_view.enchantments.append(ench)
        await interaction.response.edit_message(content=self.parent_view.build_message_text(), view=self.parent_view)

# --- View for the give command ---
class GiveItemView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.enchantments = []
        
        # start with category selector
        self.category_select = CategorySelect(self)
        self.add_item(self.category_select)

    def build_message_text(self):
        if not self.enchantments:
            enchants_display = "No enchantments selected yet"
        else:
            enchants_display = "\n".join(
                f"- {name}: {level}" for name, level in self.enchantments)
        return f"**Selected Enchantments:**\n{enchants_display}"

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.primary)
    async def submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        ench_nbt = ""
        if self.enchantments:
            ench_nbt = f"enchantments={{{', '.join(f'{enchant}:{level}' for enchant, level in self.enchantments)}}}"
        command = f'give @p minecraft:diamond_sword[{ench_nbt}] 1'

        await interaction.response.send_message(f"Executing command:\n```{command}```")

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

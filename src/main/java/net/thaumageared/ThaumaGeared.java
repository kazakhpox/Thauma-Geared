package net.thaumageared;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * Thauma-Geared: Thaumaturge's thaumium and void metal forged on Overgeared's anvils. The Arcane Anvil is Overgeared's own
 * Tier A smithing anvil (above iron), dressed in dark purple and gold and made from a smithing anvil with Salis Mundus; the metals'
 * plates, tool heads and armour need it. This mod adds the heated ingots and the tool heads; the rest is data.
 */
@Mod(ThaumaGeared.MOD_ID)
public final class ThaumaGeared {
    public static final String MOD_ID = "thaumageared";
    public static final String[] METALS = {"thaumium", "void_metal"};
    public static final String[] HEADS = {"sword_blade", "pickaxe_head", "axe_head", "shovel_head", "hoe_head"};

    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(MOD_ID);
    public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MOD_ID);
    private static final List<DeferredItem<Item>> ALL = new ArrayList<>();

    static {
        for (String metal : METALS) {
            ALL.add(ITEMS.registerSimpleItem("heated_" + metal + "_ingot"));
            for (String head : HEADS) {
                ALL.add(ITEMS.registerSimpleItem(metal + "_" + head));
            }
        }
    }

    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> TAB = TABS.register("thaumageared", () -> CreativeModeTab.builder()
            .withTabsBefore(ResourceLocation.fromNamespaceAndPath("overgeared", "overgeared_tab"))
            .icon(() -> new ItemStack(ALL.get(1).get()))
            .title(Component.translatable("itemGroup.thaumageared"))
            .displayItems((parameters, output) -> ALL.forEach(item -> output.accept(item.get())))
            .build());

    public ThaumaGeared(IEventBus modBus) {
        ITEMS.register(modBus);
        TABS.register(modBus);
    }
}

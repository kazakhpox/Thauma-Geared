package net.thaumageared;

import net.minecraft.core.registries.Registries;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.AbstractCookingRecipe;
import net.minecraft.world.item.crafting.CookingBookCategory;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.SimpleCookingSerializer;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * Heating magic metal, which only Thaumaturge's Infernal Furnace does: a cooking recipe of its own type, so furnaces and blast
 * furnaces never see it ({@link net.thaumageared.mixin.InfernalFurnaceMixin} lets the Infernal Furnace look it up).
 */
public final class InfernalHeatingRecipe extends AbstractCookingRecipe {
    public static final DeferredRegister<RecipeType<?>> TYPES = DeferredRegister.create(Registries.RECIPE_TYPE, ThaumaGeared.MOD_ID);
    public static final DeferredRegister<RecipeSerializer<?>> SERIALIZERS =
            DeferredRegister.create(Registries.RECIPE_SERIALIZER, ThaumaGeared.MOD_ID);
    public static final DeferredHolder<RecipeType<?>, RecipeType<InfernalHeatingRecipe>> TYPE =
            TYPES.register("infernal_heating", () -> RecipeType.simple(ThaumaGeared.id("infernal_heating")));
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<InfernalHeatingRecipe>> SERIALIZER =
            SERIALIZERS.register("infernal_heating", () -> new SimpleCookingSerializer<>(InfernalHeatingRecipe::new, 200));

    public InfernalHeatingRecipe(String group, CookingBookCategory category, Ingredient ingredient, ItemStack result, float experience,
                                 int time) {
        super(TYPE.get(), group, category, ingredient, result, experience, time);
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return SERIALIZER.get();
    }

    @Override
    public ItemStack getToastSymbol() {
        return new ItemStack(Items.BLAZE_POWDER);
    }
}

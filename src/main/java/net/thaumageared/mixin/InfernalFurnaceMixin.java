package net.thaumageared.mixin;

import java.util.Optional;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.AbstractCookingRecipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.SingleRecipeInput;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.thaumageared.InfernalHeatingRecipe;

/** Thaumaturge's Infernal Furnace smelts what a furnace smelts, and also heats magic metal ({@link InfernalHeatingRecipe}). */
@Mixin(targets = "com.leclowndu93150.thaumaturge.content.infernalfurnace.BlockEntityInfernalFurnace", remap = false)
public abstract class InfernalFurnaceMixin {
    @Inject(method = "getCookingRecipe", at = @At("RETURN"), cancellable = true)
    private void thaumageared$heatMagicMetal(ItemStack stack, CallbackInfoReturnable<Optional<AbstractCookingRecipe>> cir) {
        if (cir.getReturnValue().isPresent() || stack.isEmpty()) {
            return;
        }
        Level level = ((BlockEntity) (Object) this).getLevel();
        if (level == null) {
            return;
        }
        level.getRecipeManager().getRecipeFor(InfernalHeatingRecipe.TYPE.get(), new SingleRecipeInput(stack), level)
                .map(RecipeHolder::value).ifPresent(recipe -> cir.setReturnValue(Optional.of(recipe)));
    }
}

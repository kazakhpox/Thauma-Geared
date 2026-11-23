package net.thaumageared.devtools;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.Comparator;
import java.util.Deque;
import java.util.Optional;
import java.util.function.BooleanSupplier;

import org.joml.Vector2f;
import org.lwjgl.glfw.GLFW;

import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Difficulty;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.LevelSettings;
import net.minecraft.world.level.WorldDataConfiguration;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.WorldOptions;
import net.minecraft.world.level.levelgen.presets.WorldPresets;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.common.NeoForge;



/**
 * Builds a flat test world, dresses the player in Knights & Heraldry armour and looks at their first-person arms (Punchy!), saving screenshots along the way to the folder in the system property {@code handson.shots}. Then quits.
 */
@Mod(value = "thaumageared_devtools", dist = net.neoforged.api.distmarker.Dist.CLIENT)
public final class ShotDriver {
    private static final String WORLD = "handson_shots";
    
    private final Deque<Step> steps = new ArrayDeque<>();
    private int wait;
    
    private record Step(String name, BooleanSupplier until, Runnable action) {
    }

    public ShotDriver(IEventBus modBus) {
        if (System.getProperty("handson.shots") == null) {
            return;
        }
        NeoForge.EVENT_BUS.addListener(ClientTickEvent.Post.class, event -> tick());
        plan();
    }

    private void then(String name, int ticks, Runnable action) {
        steps.add(new Step(name, () -> true, action));
        steps.add(new Step(name + " wait", null, () -> wait = ticks));
    }

    private void when(String name, BooleanSupplier until, Runnable action) {
        steps.add(new Step(name, until, action));
    }

    private static ItemStack item(String id) {
        return new ItemStack(net.minecraft.core.registries.BuiltInRegistries.ITEM.get(net.minecraft.resources.ResourceLocation.parse(id)));
    }

    private static BlockState block(String id) {
        return net.minecraft.core.registries.BuiltInRegistries.BLOCK.get(net.minecraft.resources.ResourceLocation.parse(id)).defaultBlockState();
    }

    private void plan() {
        when("title", () -> Minecraft.getInstance().screen instanceof TitleScreen, this::createWorld);
        when("in world", () -> Minecraft.getInstance().player != null && Minecraft.getInstance().getSingleplayerServer() != null
                && Minecraft.getInstance().screen == null, () -> wait = 80);
        then("setup", 60, () -> server(player -> {
            ServerLevel level = player.serverLevel();
            player.server.getCommands().performPrefixedCommand(player.createCommandSourceStack().withPermission(4), "thaumaturge research @a everything");
            level.setBlockAndUpdate(new BlockPos(-2, -60, 3), block("overgeared:iron_smithing_anvil"));
            level.setBlockAndUpdate(new BlockPos(0, -60, 3), block("overgeared:iron_smithing_anvil"));
            level.setBlockAndUpdate(new BlockPos(2, -60, 3), block("overgeared:tier_a_smithing_anvil"));
            String[] hotbar = {"thaumageared:heated_thaumium_ingot", "thaumageared:thaumium_sword_blade", "thaumageared:thaumium_pickaxe_head",
                    "thaumageared:heated_void_metal_ingot", "thaumageared:void_metal_sword_blade", "thaumageared:void_metal_axe_head",
                    "thaumaturge:plate_thaumium", "thaumaturge:salis_mundus", "overgeared:tier_a_smithing_anvil"};
            for (int i = 0; i < hotbar.length; i++) {
                player.getInventory().setItem(i, item(hotbar[i]));
            }
            player.getInventory().selected = 7;
            player.teleportTo(level, 0.5, -59, -0.5, 0.0F, 30.0F);
        }));
        then("furnace", 20, () -> server(player -> {
            BlockPos at = new BlockPos(4, -60, 3);
            player.serverLevel().setBlockAndUpdate(at, block("overgeared:nether_alloy_furnace"));
            var be = (net.minecraft.world.Container) player.serverLevel().getBlockEntity(at);
            be.setItem(0, item("thaumaturge:ingot_void"));
            try {
                Object recipe = be.getClass().getMethod("getCurrentRecipe").invoke(be);
                System.out.println("[shots] nether furnace with void ingot: " + recipe);
            } catch (ReflectiveOperationException e) {
                e.printStackTrace();
            }
        }));
        then("before", 5, () -> shot("00_before"));
        then("dust", 60, () -> server(player -> {
            var hit = new net.minecraft.world.phys.BlockHitResult(new Vec3(0.5, -59, 3.5), Direction.UP, new BlockPos(0, -60, 3), false);
            ItemStack dust = player.getInventory().getItem(7);
            var result = dust.useOn(new net.minecraft.world.item.context.UseOnContext(player, net.minecraft.world.InteractionHand.MAIN_HAND, hit));
            System.out.println("[shots] salis mundus on anvil: " + result + " -> " + player.serverLevel().getBlockState(new BlockPos(0, -60, 3)));
        }));
        then("after", 5, () -> shot("01_after_dust"));
        then("close", 30, () -> server(player -> player.teleportTo(player.serverLevel(), 2.5, -59.3, 1.6, 0.0F, 35.0F)));
        then("close shot", 5, () -> shot("02_arcane_close"));
        then("handson look", 40, () -> server(player -> {
            player.getInventory().setItem(4, ItemStack.EMPTY);
            player.getInventory().setItem(0, item("overgeared:iron_hammer"));
            player.teleportTo(player.serverLevel(), 0.5, -59, 1.9, 0.0F, 38.0F);
        }));
        then("handson use", 40, ShotDriver::use);
        then("handson shot", 5, () -> shot("04_handson_station"));
        then("close station", 20, () -> Minecraft.getInstance().setScreen(null));
        then("book", 60, () -> {
            try {
                Object api = Class.forName("vazkii.patchouli.api.PatchouliAPI").getMethod("get").invoke(null);
                api.getClass().getMethod("openBookGUI", net.minecraft.resources.ResourceLocation.class)
                        .invoke(api, net.minecraft.resources.ResourceLocation.parse("thaumageared:smithing_guide"));
            } catch (ReflectiveOperationException e) {
                e.printStackTrace();
            }
        });
        then("book shot", 5, () -> shot("05_book"));
        then("book entry", 40, () -> {
            try {
                Object api = Class.forName("vazkii.patchouli.api.PatchouliAPI").getMethod("get").invoke(null);
                api.getClass().getMethod("openBookEntry", net.minecraft.resources.ResourceLocation.class,
                        net.minecraft.resources.ResourceLocation.class, int.class).invoke(api,
                        net.minecraft.resources.ResourceLocation.parse("thaumageared:smithing_guide"),
                        net.minecraft.resources.ResourceLocation.parse("thaumageared:finishing/assembly"), 0);
            } catch (ReflectiveOperationException e) {
                e.printStackTrace();
            }
        });
        then("entry shot", 5, () -> shot("06_book_entry"));
        then("inv", 40, () -> Minecraft.getInstance().setScreen(new net.minecraft.client.gui.screens.inventory.InventoryScreen(Minecraft.getInstance().player)));
        then("inv shot", 5, () -> shot("03_items"));
        then("quit", 5, () -> Minecraft.getInstance().stop());
    }

    private void tick() {
        if (wait > 0) {
            wait--;
            return;
        }
        Step step = steps.peek();
        if (step == null) {
            return;
        }
        if (step.until() == null) {
            steps.poll();
            step.action().run();
            return;
        }
        if (step.until().getAsBoolean()) {
            steps.poll();
            System.out.println("[shots] " + step.name());
            step.action().run();
        }
    }

    private void createWorld() {
        Minecraft mc = Minecraft.getInstance();
        Path saves = mc.gameDirectory.toPath().resolve("saves").resolve(WORLD);
        try {
            if (Files.exists(saves)) {
                try (var walk = Files.walk(saves)) {
                    walk.sorted(Comparator.reverseOrder()).map(Path::toFile).forEach(File::delete);
                }
            }
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        GameRules rules = new GameRules();
        rules.getRule(GameRules.RULE_DAYLIGHT).set(false, null);
        rules.getRule(GameRules.RULE_WEATHER_CYCLE).set(false, null);
        rules.getRule(GameRules.RULE_DOMOBSPAWNING).set(false, null);
        LevelSettings settings = new LevelSettings(WORLD, GameType.CREATIVE, false, Difficulty.PEACEFUL, true, rules,
                WorldDataConfiguration.DEFAULT);
        mc.createWorldOpenFlows().createFreshLevel(WORLD, settings, new WorldOptions(1L, false, false),
                registries -> registries.registryOrThrow(Registries.WORLD_PRESET).getHolderOrThrow(WorldPresets.FLAT).value()
                        .createWorldDimensions(), mc.screen);
    }

    /** A right click at what the crosshair is on, with an empty hand: the player uses the anvil as anybody would. */
    private static void use() {
        Minecraft mc = Minecraft.getInstance();
        mc.player.getInventory().selected = 4;
        System.out.println("[shots] looking at " + mc.hitResult);
        try {
            Method method = Minecraft.class.getDeclaredMethod("startUseItem");
            method.setAccessible(true);
            method.invoke(mc);
        } catch (ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }

    private static void server(java.util.function.Consumer<ServerPlayer> action) {
        Minecraft mc = Minecraft.getInstance();
        var server = mc.getSingleplayerServer();
        server.execute(() -> action.accept(server.getPlayerList().getPlayers().get(0)));
    }

    private static void shot(String name) {
        Minecraft mc = Minecraft.getInstance();
        File dir = new File(System.getProperty("handson.shots"));
        dir.mkdirs();
        Screenshot.grab(dir, name + ".png", mc.getMainRenderTarget(), message -> System.out.println("[shots] " + message.getString()));
    }
}

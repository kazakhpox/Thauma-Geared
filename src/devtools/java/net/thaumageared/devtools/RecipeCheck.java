package net.thaumageared.devtools;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

import net.minecraft.resources.ResourceLocation;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/** Dev only: at server start, every recipe file of the mod must be a loaded recipe of the type it names; then the server stops. */
@Mod("thaumageared_devtools")
public final class RecipeCheck {
    public RecipeCheck() {
        if (System.getProperty("thaumageared.check") == null) {
            return;
        }
        NeoForge.EVENT_BUS.addListener(ServerStartedEvent.class, event -> {
            var manager = event.getServer().getRecipeManager();
            Path data = Path.of(System.getProperty("thaumageared.check"));
            List<String> missing = new ArrayList<>();
            int found = 0;
            try (Stream<Path> files = Files.walk(data)) {
                for (Path file : files.filter(p -> p.toString().endsWith(".json") && p.toString().contains("/recipe/")).toList()) {
                    Path rel = data.relativize(file);
                    String ns = rel.getName(0).toString();
                    String path = rel.subpath(2, rel.getNameCount()).toString().replace(".json", "");
                    var id = ResourceLocation.fromNamespaceAndPath(ns, path);
                    var recipe = manager.byKey(id);
                    if (recipe.isEmpty()) {
                        missing.add(id.toString());
                    } else {
                        found++;
                    }
                }
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
            System.out.println("[thaumageared.check] loaded " + found + ", missing " + missing.size() + " " + missing);
            event.getServer().halt(false);
        });
    }
}

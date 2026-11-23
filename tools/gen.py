#!/usr/bin/env python3
"""
Writes Thauma-Geared's assets and data: the textures (recoloured from Overgeared's own iron ones and Thaumaturge's metals), the
item models and names, the Arcane Anvil's look, and the recipes.

Usage: gen.py <overgeared jar> <thaumaturge jar> <resources dir> [minecraft client jar]

The Arcane Anvil is Overgeared's Tier A smithing anvil (a tier above iron that Overgeared ships for modpacks to fill): its model
is pointed at a dark purple texture with a gold rim, its name changed, and Thaumaturge's Salis Mundus makes it from an Overgeared
smithing anvil (a dust trigger, as a crafting table becomes the Arcane Workbench). Everything forged from thaumium or void metal
asks for that tier.
"""
import io
import json
import os
import shutil
import sys
import zipfile

from PIL import Image

NS = 'thaumageared'
OG = 'overgeared:'
TH = 'thaumaturge:'

# Each metal: its name in Thaumaturge's ids, its tag, the research that opens its forging, how hard it is to hammer.
METALS = {
    'thaumium': {'ingot': TH + 'ingot_thaumium', 'plate': TH + 'plate_thaumium', 'tag': 'c:ingots/thaumium', 'tools': 'thaumium',
                 'hammering': 5, 'en': 'Thaumium', 'ru': 'Таумиевый', 'ru_ingot': 'таумиевый слиток'},
    'void_metal': {'ingot': TH + 'ingot_void', 'plate': TH + 'plate_void', 'tag': 'c:ingots/void_metal', 'tools': 'void',
                   'hammering': 6, 'en': 'Void Metal', 'ru': 'Пустотный', 'ru_ingot': 'слиток пустотного металла'},
}
# Overgeared's tool heads: its own patterns and blueprints, forged here from the heated magic metal.
HEADS = {
    'sword_blade': ('sword', [['#', '#']], 'Sword Blade', 'клинок меча'),
    'pickaxe_head': ('pickaxe', [['###']], 'Pickaxe Head', 'оголовье кирки'),
    'axe_head': ('axe', [['##', '# '], ['##', ' #']], 'Axe Head', 'лезвие топора'),
    'shovel_head': ('shovel', [['#']], 'Shovel Head', 'штык лопаты'),
    'hoe_head': ('hoe', [['##']], 'Hoe Head', 'лезвие мотыги'),
}
TOOLS = {'sword_blade': 'sword', 'pickaxe_head': 'pickaxe', 'axe_head': 'axe', 'shovel_head': 'shovel', 'hoe_head': 'hoe'}
# Overgeared's steel armour patterns, from the metal's plates.
ARMOUR = {'helm': ['###', '# #'], 'chest': ['# #', '###', '###'], 'legs': ['###', '# #', '# #'], 'boots': ['# #', '# #']}
TIER = 'above_a'


def read_image(jar, path):
    return Image.open(io.BytesIO(jar.read(path))).convert('RGBA')


def luminance(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def palette_of(image):
    colours = sorted({p for p in image.getdata() if p[3] > 0}, key=luminance)
    return [c[:3] for c in colours]


def recolour(source, palette):
    """Every opaque pixel takes the palette colour at its brightness's rank among the source's own brightnesses."""
    levels = sorted({round(luminance(p)) for p in source.getdata() if p[3] > 0})
    out = Image.new('RGBA', source.size)
    for y in range(source.height):
        for x in range(source.width):
            p = source.getpixel((x, y))
            if p[3] == 0:
                continue
            rank = levels.index(round(luminance(p))) / max(1, len(levels) - 1)
            c = palette[min(len(palette) - 1, round(rank * (len(palette) - 1)))]
            out.putpixel((x, y), c + (p[3],))
    return out


# Metal heated past white-hot into blue: deep blue in the shadows, bright cyan and almost white on the highlights.
GLOW = {
    'thaumium': [(14, 60, 160), (22, 95, 215), (35, 135, 245), (60, 175, 255), (110, 210, 255), (190, 240, 255)],
    'void_metal': [(20, 22, 130), (30, 55, 200), (40, 95, 240), (65, 140, 255), (110, 185, 255), (180, 225, 255)],
}


def arcane_anvil(texture, model, gold_ingot):
    """Overgeared's anvil in dark purple, every face of the model rimmed with gold shaded as Minecraft's gold ingot is."""
    purple = [(22, 10, 34), (34, 16, 52), (46, 22, 68), (58, 30, 84), (72, 40, 100), (88, 52, 118)]
    gold = recolour(texture, [c for c in palette_of(gold_ingot) if c[2] < 150])  # its pale-white glints left out
    out = recolour(texture, purple)
    scale = texture.width / 16.0  # the model's UVs are on the 16 grid, its texture 64 wide
    for element in model['elements']:
        for face in element['faces'].values():
            u0, v0, u1, v1 = face['uv']
            x0, x1 = sorted((round(u0 * scale), round(u1 * scale)))
            y0, y1 = sorted((round(v0 * scale), round(v1 * scale)))
            if x1 - x0 < 2 or y1 - y0 < 2:
                continue
            for x in range(x0, x1):
                for y in range(y0, y1):
                    if 0 <= x < out.width and 0 <= y < out.height and (x in (x0, x1 - 1) or y in (y0, y1 - 1)):
                        p = out.getpixel((x, y))
                        if p[3] > 0:
                            out.putpixel((x, y), gold.getpixel((x, y)))
    return out


def forging(pattern, key, result, hammering, category, extra=None):
    recipe = {'type': OG + 'forging', 'category': category, 'hammering': hammering, 'tier': TIER, 'pattern': pattern,
              'key': key, 'result': {'count': 1, 'id': result}, 'show_notification': False}
    recipe.update(extra or {})
    return recipe


def main(og_jar, th_jar, resources, mc_jar='/root/.gradle/caches/neoformruntime/artifacts/minecraft_1.21.1_client.jar'):
    mc = zipfile.ZipFile(mc_jar)
    og = zipfile.ZipFile(og_jar)
    th = zipfile.ZipFile(th_jar)
    assets = os.path.join(resources, 'assets')
    data = os.path.join(resources, 'data')
    for folder in (os.path.join(assets, NS, 'textures'), os.path.join(assets, NS, 'models'), os.path.join(assets, 'overgeared'),
                   os.path.join(data, NS), os.path.join(data, 'thaumaturge'), os.path.join(data, 'overgeared')):
        shutil.rmtree(folder, ignore_errors=True)
    files = {}
    lang = {'en_us': {'itemGroup.thaumageared': 'Thauma-Geared', 'book.thaumageared.smithing_guide.name': 'Smithing Guide',
                      'book.thaumageared.smithing_guide.landing': 'A smith\'s notes on Overgeared: hammers and anvils, forging, finishing, '
                                                                  'metals, and the Arcane Anvil.'},
            'ru_ru': {'itemGroup.thaumageared': 'Thauma-Geared', 'book.thaumageared.smithing_guide.name': 'Руководство кузнеца',
                      'book.thaumageared.smithing_guide.landing': 'Записки кузнеца об Overgeared: молоты и наковальни, ковка, отделка, '
                                                                  'металлы и Магическая наковальня.'}}

    def write(path, value):
        files[path] = value

    textures = {}
    for metal, info in METALS.items():
        palette = palette_of(read_image(th, 'assets/thaumaturge/textures/item/' + info['ingot'].split(':')[1] + '.png'))
        textures['heated_%s_ingot' % metal] = recolour(read_image(og, 'assets/overgeared/textures/item/heated_iron_ingot.png'),
                                                       GLOW[metal])
        lang['en_us']['item.%s.heated_%s_ingot' % (NS, metal)] = 'Heated %s Ingot' % info['en']
        lang['ru_ru']['item.%s.heated_%s_ingot' % (NS, metal)] = 'Раскалённый ' + info['ru_ingot']
        for head, (_, _, en, ru) in HEADS.items():
            source = 'iron_' + head
            textures['%s_%s' % (metal, head)] = recolour(read_image(og, 'assets/overgeared/textures/item/%s.png' % source), palette)
            lang['en_us']['item.%s.%s_%s' % (NS, metal, head)] = '%s %s' % (info['en'], en)
            ru_metal = 'таумиевое' if metal == 'thaumium' else 'пустотное'
            if head == 'sword_blade':
                ru_metal = 'таумиевый' if metal == 'thaumium' else 'пустотный'
            elif head == 'shovel_head':
                ru_metal = 'таумиевый' if metal == 'thaumium' else 'пустотный'
            lang['ru_ru']['item.%s.%s_%s' % (NS, metal, head)] = (ru_metal + ' ' + ru).capitalize()
    for name, image in textures.items():
        write('assets/%s/textures/item/%s.png' % (NS, name), image)
        write('assets/%s/models/item/%s.json' % (NS, name),
              {'parent': 'minecraft:item/generated', 'textures': {'layer0': '%s:item/%s' % (NS, name)}})

    # The Arcane Anvil: Overgeared's Tier A anvil, its model on the purple and gold texture, its name.
    model = json.loads(og.read('assets/overgeared/models/block/tier_a_smithing_anvil.json'))
    write('assets/%s/textures/block/arcane_anvil.png' % NS,
          arcane_anvil(read_image(og, 'assets/overgeared/textures/block/smithing_anvil.png'), model,
                       read_image(mc, 'assets/minecraft/textures/item/gold_ingot.png')))
    model['textures'] = {'0': NS + ':block/arcane_anvil', 'particle': NS + ':block/arcane_anvil'}
    write('assets/overgeared/models/block/tier_a_smithing_anvil.json', model)
    overgeared_lang = {
        'en_us': {'block.overgeared.tier_a_smithing_anvil': 'Arcane Anvil', 'gui.overgeared.tier.tier_a': 'Arcane Anvil',
                  'gui.overgeared.tier_a_smithing_anvil': 'Arcane Anvil'},
        'ru_ru': {'block.overgeared.tier_a_smithing_anvil': 'Магическая наковальня', 'gui.overgeared.tier.tier_a': 'Магическая наковальня',
                  'gui.overgeared.tier_a_smithing_anvil': 'Магическая наковальня'},
    }
    for code, values in overgeared_lang.items():
        write('assets/overgeared/lang/%s.json' % code, values)
    for code, values in lang.items():
        write('assets/%s/lang/%s.json' % (NS, code), values)

    # Salis Mundus on an Overgeared smithing anvil makes the Arcane Anvil, once metallurgy is known.
    write('data/%s/recipe/dust_trigger/smithing_anvil_to_arcane_anvil.json' % NS, {
        'type': TH + 'dust_trigger_simple', 'research': {'entry': TH + 'metallurgy', 'stage': 0},
        'result': {'count': 1, 'id': OG + 'tier_a_smithing_anvil'}, 'target': OG + 'iron_smithing_anvil'})

    heated = []
    heads = []
    for metal, info in METALS.items():
        hot = '%s:heated_%s_ingot' % (NS, metal)
        heated.append(hot)
        # Magic metal takes no common fire: it is heated in Overgeared's nether alloy furnace; cooled back in water.
        write('data/%s/recipe/heated_%s_ingot.json' % (NS, metal), {
            'type': OG + 'nether_alloy_smelting', 'category': 'misc', 'group': 'misc', 'cookingtime': 200, 'experience': 0.5,
            'ingredients': [{'tag': info['tag']}], 'result': {'count': 1, 'id': hot}})
        write('data/%s/recipe/%s_ingot_from_cooling.json' % (NS, metal), {
            'type': OG + 'cooling', 'input': {'item': hot}, 'output': {'id': info['ingot']}})
        # The metal's plates, hammered out of a cold ingot on the Arcane Anvil (replacing Thaumaturge's crafting).
        plate = info['plate'].split(':')[1]
        write('data/thaumaturge/recipe/%s.json' % plate, forging(['#'], {'#': {'tag': info['tag']}}, info['plate'], 4, 'misc', {
            'has_quality': False, 'needs_minigame': False, 'need_quenching': False, 'has_polishing': False}))
        # Tool heads from the heated metal, as Overgeared's own, and the tools put together from them (replacing Thaumaturge's).
        for head, (blueprint, patterns, _, _) in HEADS.items():
            item = '%s:%s_%s' % (NS, metal, head)
            heads.append(item)
            for index, pattern in enumerate(patterns):
                suffix = '' if index == 0 else '_%d' % (index + 1)
                write('data/%s/recipe/%s_%s%s.json' % (NS, metal, head, suffix), forging(
                    pattern, {'#': {'item': hot}}, item, info['hammering'], 'TOOL_HEADS', {'blueprint': [blueprint]}))
            tool = '%s_%s' % (info['tools'], TOOLS[head])
            write('data/thaumaturge/recipe/%s.json' % tool, {
                'type': OG + 'crafting_shapeless', 'category': 'equipment',
                'ingredients': [{'item': item}, {'tag': 'c:rods/wooden'}], 'result': {'count': 1, 'id': TH + tool}})
        # Armour from the metal's plates, as Overgeared's steel armour (replacing Thaumaturge's).
        for piece, pattern in ARMOUR.items():
            armour = '%s_%s' % (info['tools'], piece)
            write('data/thaumaturge/recipe/%s.json' % armour, forging(pattern, {'#': {'item': info['plate']}}, TH + armour,
                                                                     info['hammering'], 'ARMORS', {'has_polishing': False, 'need_quenching': False}))
    write('data/overgeared/tags/item/heated_metals.json', {'replace': False, 'values': heated})
    write('data/overgeared/tags/item/tool_parts.json', {'replace': False, 'values': heads})

    for path, value in files.items():
        file = os.path.join(resources, path)
        os.makedirs(os.path.dirname(file), exist_ok=True)
        if isinstance(value, Image.Image):
            value.save(file)
        else:
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(value, f, indent=2, ensure_ascii=False)
                f.write('\n')
    print(len(files), 'files')


if __name__ == '__main__':
    main(*sys.argv[1:5])

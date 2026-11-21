#!/usr/bin/env python3
"""
Writes the Patchouli guide to Overgeared's smithing (and Thauma-Geared's magic metals), in English and Russian.

Usage: gen_book.py <resources dir>

Patchouli is optional: without it the book and its recipe simply do not load.
"""
import json
import os
import shutil
import sys

NS = 'thaumageared'
BOOK = 'smithing_guide'

# category id: (icon, sort, {lang: (name, description)})
CATEGORIES = {
    'basics': ('overgeared:smithing_hammer', 0, {
        'en_us': ('Basics', 'Hammers, anvils, tongs and hot metal.'),
        'ru_ru': ('Основы', 'Молоты, наковальни, клещи и раскалённый металл.')}),
    'forging': ('overgeared:iron_smithing_anvil', 1, {
        'en_us': ('Forging', 'Working metal on the anvil, quality and blueprints.'),
        'ru_ru': ('Ковка', 'Работа на наковальне, качество и чертежи.')}),
    'finishing': ('minecraft:grindstone', 2, {
        'en_us': ('Finishing', 'Polishing, quenching and putting tools together.'),
        'ru_ru': ('Отделка', 'Полировка, закалка и сборка инструментов.')}),
    'metals': ('overgeared:alloy_furnace', 3, {
        'en_us': ('Metals', 'Steel, alloys and casting.'),
        'ru_ru': ('Металлы', 'Сталь, сплавы и литьё.')}),
    'arcane': ('overgeared:tier_a_smithing_anvil', 4, {
        'en_us': ('Arcane Smithing', 'Thaumium and void metal on the Arcane Anvil.'),
        'ru_ru': ('Магическая ковка', 'Таумиум и пустотный металл на Магической наковальне.')}),
}


def text(t, title=None):
    page = {'type': 'patchouli:text', 'text': t}
    if title:
        page['title'] = title
    return page


def spot(item, t, title=None):
    page = {'type': 'patchouli:spotlight', 'item': item, 'text': t}
    if title:
        page['title'] = title
    return page


def craft(recipe, t=None):
    page = {'type': 'patchouli:crafting', 'recipe': recipe}
    if t:
        page['text'] = t
    return page


# entry id: (category, icon, sort, {lang: (name, pages)})
ENTRIES = {
    'hammers': ('basics', 'overgeared:smithing_hammer', 0, {
        'en_us': ('Smithing Hammers', [
            text('Everything in Overgeared is forged with a $(item)smithing hammer$(). The first one is knapped from stone: right-click stone '
                 'with $(item)flint$() to chip off $(item)rock$(), hold rock in both hands and knap a stone hammer head, then put it on a stick.'),
            text('Better hammers come from the anvil: a $(item)copper$() head, and the $(item)steel smithing hammer$() from two heated steel '
                 'ingots. A hammer only works on anvils and recipes its tier allows: "Incorrect hammer tier" means you need a better one.'),
            craft('overgeared:smithing_hammer')]),
        'ru_ru': ('Кузнечные молоты', [
            text('В Overgeared всё куётся $(item)кузнечным молотом$(). Первый делается из камня: ПКМ $(item)кремнем$() по камню откалывает '
                 '$(item)осколок породы$(), с осколками в обеих руках можно обтесать каменное оголовье молота и насадить его на палку.'),
            text('Молоты получше куются на наковальне: $(item)медный$() и $(item)стальной$() (оголовье из двух раскалённых стальных слитков). '
                 'Молот работает только на наковальнях и рецептах своего уровня: «Incorrect hammer tier» значит, что нужен молот лучше.'),
            craft('overgeared:smithing_hammer')])}),
    'anvils': ('basics', 'overgeared:iron_smithing_anvil', 1, {
        'en_us': ('Smithing Anvils', [
            text('Sneak and right-click $(item)stone$() with a smithing hammer to make a $(item)Stone Smithing Anvil$(); sneak and right-click '
                 'a vanilla $(item)anvil$() to make an iron $(item)Smithing Anvil$().'),
            text('Every forging recipe has a $(thing)tier$(): stone, iron, then the tiers above iron. An anvil forges its own tier and those '
                 'below it. The $(l:thaumageared:arcane/arcane_anvil)Arcane Anvil$() is the tier above iron.'),
            spot('overgeared:iron_smithing_anvil', 'Right-click with the hammer to start forging, right-click away from the anvil to stop. '
                 'One anvil, one smith at a time.')]),
        'ru_ru': ('Кузнечные наковальни', [
            text('Shift+ПКМ молотом по $(item)камню$() превращает его в $(item)каменную наковальню$(); Shift+ПКМ по обычной '
                 '$(item)наковальне$() делает из неё железную $(item)кузнечную наковальню$().'),
            text('У каждого рецепта ковки есть $(thing)уровень$(): каменный, железный и уровни выше железа. Наковальня куёт рецепты своего '
                 'уровня и ниже. $(l:thaumageared:arcane/arcane_anvil)Магическая наковальня$() — уровень выше железа.'),
            spot('overgeared:iron_smithing_anvil', 'ПКМ молотом по наковальне начинает ковку, ПКМ мимо наковальни — останавливает. '
                 'Одной наковальней пользуется один кузнец.')])}),
    'heat': ('basics', 'overgeared:heated_iron_ingot', 2, {
        'en_us': ('Hot Metal and Tongs', [
            text('Most metal is forged hot. Put ingots in a $(item)blast furnace$() (or furnace) to get $(item)heated ingots$(). A heated '
                 'ingot cools back down after a while, and dropped in water it cools at once.'),
            text('Hot metal burns the hand that holds it. Hold $(item)tongs$() in the other hand to carry it safely: wooden tongs are made '
                 'from sticks, iron and steel ones are forged as two halves and joined.'),
            craft('overgeared:wooden_tongs')]),
        'ru_ru': ('Раскалённый металл и клещи', [
            text('Почти весь металл куётся горячим. Слитки в $(item)доменной печи$() (или обычной) становятся $(item)раскалёнными$(). '
                 'Раскалённый слиток со временем остывает, а брошенный в воду остывает сразу.'),
            text('Раскалённый металл обжигает руку. Держите во второй руке $(item)клещи$(), чтобы носить его без вреда: деревянные '
                 'делаются из палок, железные и стальные куются из двух половинок и соединяются.'),
            craft('overgeared:wooden_tongs')])}),
    'forging': ('forging', 'overgeared:iron_sword_blade', 0, {
        'en_us': ('Forging', [
            text('Lay the pieces on the anvil in the recipe\'s pattern (as on a crafting table), the blueprint in its slot if the recipe '
                 'wants one, and right-click with the hammer.'),
            text('Each recipe needs some number of hits. Where the minigame is on, a marker sweeps across a bar: strike when it is in the '
                 'middle. $(thing)Perfect$() and $(thing)good$() hits raise the quality, $(thing)misses$() lower it.'),
            text('With $(item)Hands-On Overgeared$() the pieces lie on the anvil itself and you strike in rhythm with the hammer in your hand. '
                 'Sneak-click for Overgeared\'s own screen.')]),
        'ru_ru': ('Ковка', [
            text('Разложите материал на наковальне по схеме рецепта (как на верстаке), чертёж — в его ячейку, если рецепт его требует, '
                 'и ПКМ молотом.'),
            text('Каждому рецепту нужно сколько-то ударов. Если включена мини-игра, по шкале бегает метка: бейте, когда она в середине. '
                 '$(thing)Идеальные$() и $(thing)хорошие$() удары поднимают качество, $(thing)промахи$() — снижают.'),
            text('С $(item)Hands-On Overgeared$() материал лежит прямо на наковальне, а бить нужно в ритм молотом в руке. '
                 'Shift+ПКМ открывает обычное меню Overgeared.')])}),
    'quality': ('forging', 'overgeared:iron_pickaxe_head', 1, {
        'en_us': ('Quality', [
            text('Forged pieces come out $(thing)Poorly$(), $(thing)Well$(), $(thing)Expertly$() or $(thing)Perfectly Forged$(), or as a '
                 '$(thing)Masterwork$(). Better quality makes better tools and armour, and it carries over from a head to the finished tool.'),
            text('Some recipes (plates, steel) have no quality: they come out the same however you strike.')]),
        'ru_ru': ('Качество', [
            text('Откованная вещь бывает $(thing)плохой$(), $(thing)хорошей$(), $(thing)отличной$(), $(thing)идеальной$() или '
                 '$(thing)шедевром$(). Чем выше качество, тем лучше инструмент или броня, и с оголовья оно переходит на готовый инструмент.'),
            text('У некоторых рецептов (пластины, сталь) качества нет: результат одинаков, как ни бей.')])}),
    'blueprints': ('forging', 'overgeared:empty_blueprint', 2, {
        'en_us': ('Blueprints', [
            text('Tool heads need a $(item)blueprint$() of their type (sword, pickaxe, axe...). Draw one on a $(item)drafting table$() '
                 'from an empty blueprint.'),
            text('A blueprint caps the quality of what it forges, and it improves as you use it: Poorly, Well, Expertly, Perfectly Designed, '
                 'Masterwork.'),
            craft('overgeared:empty_blueprint'),
            craft('overgeared:drafting_table')]),
        'ru_ru': ('Чертежи', [
            text('Оголовьям инструментов нужен $(item)чертёж$() их вида (меч, кирка, топор...). Начертите его на $(item)чертёжном столе$() '
                 'из пустого чертежа.'),
            text('Чертёж ограничивает качество выкованного, а сам улучшается от использования: от плохого до шедевра.'),
            craft('overgeared:empty_blueprint'),
            craft('overgeared:drafting_table')])}),
    'polishing': ('finishing', 'minecraft:grindstone', 0, {
        'en_us': ('Polishing', [
            text('A freshly forged head is $(thing)Unpolished$(). Use it on a $(item)grindstone$() to polish it; an unpolished part cannot '
                 'be made into a tool. The grindstone also grinds a diamond into a $(item)diamond shard$().')]),
        'ru_ru': ('Полировка', [
            text('Только что выкованное оголовье $(thing)не отполировано$(). Используйте его на $(item)точиле$(), чтобы отполировать; '
                 'из неотполированной детали инструмент не собрать. Ещё точило стачивает алмаз в $(item)алмазный осколок$().')])}),
    'quenching': ('finishing', 'minecraft:water_bucket', 1, {
        'en_us': ('Quenching', [
            text('A forged piece comes off the anvil hot. Cool it in $(item)water$() to quench it before it is put together: an unquenched '
                 'part is refused. Armour and plates need no quenching.')]),
        'ru_ru': ('Закалка', [
            text('Выкованная деталь снимается с наковальни горячей. Остудите её в $(item)воде$(), чтобы закалить: незакалённую деталь '
                 'собрать нельзя. Броне и пластинам закалка не нужна.')])}),
    'assembly': ('finishing', 'minecraft:iron_pickaxe', 2, {
        'en_us': ('Putting Tools Together', [
            text('A polished, quenched head and a stick on a crafting table make the tool, with the head\'s quality. Armour is forged whole '
                 'from plates, which are hammered out of ingots.'),
            craft('minecraft:iron_pickaxe')]),
        'ru_ru': ('Сборка инструментов', [
            text('Отполированное и закалённое оголовье с палкой на верстаке дают инструмент того же качества. Броня куётся целиком из '
                 'пластин, а пластины выбиваются из слитков.'),
            craft('minecraft:iron_pickaxe')])}),
    'steel': ('metals', 'overgeared:steel_ingot', 0, {
        'en_us': ('Steel', [
            text('Three iron ingots and a coal in an $(item)alloy furnace$() give two $(item)crude steel$(). Heat the crude steel and hammer '
                 'it on the anvil into a $(item)heated steel ingot$(), then cool it.'),
            craft('overgeared:alloy_furnace')]),
        'ru_ru': ('Сталь', [
            text('Три железных слитка и уголь в $(item)плавильне сплавов$() дают две $(item)черновые стали$(). Раскалите черновую сталь, '
                 'проковайте на наковальне в $(item)раскалённый стальной слиток$() и остудите.'),
            craft('overgeared:alloy_furnace')])}),
    'nether_alloy': ('metals', 'overgeared:netherite_alloy', 1, {
        'en_us': ('Nether Alloys', [
            text('The $(item)nether alloy furnace$() makes steel faster, and melts netherite scrap with gold into $(item)netherite alloy$(), '
                 'forged like the other metals.')]),
        'ru_ru': ('Незерские сплавы', [
            text('$(item)Незерская плавильня$() варит сталь быстрее и сплавляет незеритовый лом с золотом в $(item)незеритовый сплав$(), '
                 'который куётся как остальные металлы.')])}),
    'casting': ('metals', 'overgeared:casting_furnace', 2, {
        'en_us': ('Casting', [
            text('Instead of forging, heads can be cast. Make a $(item)clay tool cast$(), fire it in a furnace, fill it by right-clicking '
                 'it with the metal, then smelt it (or use the $(item)casting furnace$()). Right-click a cast to take its metal back.'),
            craft('overgeared:casting_furnace')]),
        'ru_ru': ('Литьё', [
            text('Оголовья можно не ковать, а отлить. Сделайте $(item)глиняную форму$(), обожгите её в печи, заполните (ПКМ металлом по '
                 'форме) и переплавьте (или используйте $(item)литейную печь$()). ПКМ по форме возвращает металл.'),
            craft('overgeared:casting_furnace')])}),
    'arcane_anvil': ('arcane', 'overgeared:tier_a_smithing_anvil', 0, {
        'en_us': ('The Arcane Anvil', [
            spot('overgeared:tier_a_smithing_anvil', 'Sprinkle $(item)Salis Mundus$() on an iron Smithing Anvil once you know '
                 '$(thing)Metallurgy$(). The Arcane Anvil forges everything an iron one does, and thaumium and void metal.')]),
        'ru_ru': ('Магическая наковальня', [
            spot('overgeared:tier_a_smithing_anvil', 'Посыпьте $(item)солью мира$() железную кузнечную наковальню, изучив '
                 '$(thing)Металлургию$(). Магическая наковальня куёт всё то же, что железная, а ещё таумиум и пустотный металл.')])}),
    'magic_metals': ('arcane', 'thaumageared:heated_thaumium_ingot', 1, {
        'en_us': ('Thaumium and Void Metal', [
            text('Heat thaumium and void metal ingots in a blast furnace: they glow blue. Forge them into heads with the iron patterns and '
                 'blueprints, polish, quench, and put on a stick.'),
            text('Plates: one cold ingot each. Armour from plates: helmet 5, chestplate 8, leggings 7, boots 4, in the steel armour '
                 'patterns. These replace Thaumaturge\'s crafting-table recipes.')]),
        'ru_ru': ('Таумиум и пустотный металл', [
            text('Раскалите слитки таумиума и пустотного металла в доменной печи — они светятся голубым. Куйте из них оголовья по железным '
                 'схемам и чертежам, полируйте, закаляйте и насаживайте на палку.'),
            text('Пластины: по одной из холодного слитка. Броня из пластин: шлем 5, нагрудник 8, поножи 7, ботинки 4, по схемам стальной '
                 'брони. Эти рецепты заменяют верстачные рецепты Thaumaturge.')])}),
}


def main(resources):
    data = os.path.join(resources, 'data', NS, 'patchouli_books', BOOK)
    assets = os.path.join(resources, 'assets', NS, 'patchouli_books', BOOK)
    shutil.rmtree(data, ignore_errors=True)
    shutil.rmtree(assets, ignore_errors=True)
    files = {}
    files[os.path.join(data, 'book.json')] = {
        'name': 'book.%s.%s.name' % (NS, BOOK), 'landing_text': 'book.%s.%s.landing' % (NS, BOOK), 'i18n': True,
        'use_resource_pack': True, 'version': 1, 'model': 'patchouli:book_brown',
        'show_progress': False}
    for lang in ('en_us', 'ru_ru'):
        for cid, (icon, sort, names) in CATEGORIES.items():
            name, desc = names[lang]
            files[os.path.join(assets, lang, 'categories', cid + '.json')] = {
                'name': name, 'description': desc, 'icon': icon, 'sortnum': sort}
        for eid, (cat, icon, sort, langs) in ENTRIES.items():
            name, pages = langs[lang]
            files[os.path.join(assets, lang, 'entries', cat, eid + '.json')] = {
                'name': name, 'icon': icon, 'category': '%s:%s' % (NS, cat), 'sortnum': sort, 'pages': pages}
    # A book and an iron ingot make the guide.
    files[os.path.join(resources, 'data', NS, 'recipe', 'smithing_guide.json')] = {
        'neoforge:conditions': [{'type': 'neoforge:mod_loaded', 'modid': 'patchouli'}],
        'type': 'minecraft:crafting_shapeless', 'category': 'misc',
        'ingredients': [{'item': 'minecraft:book'}, {'item': 'minecraft:iron_ingot'}],
        'result': {'count': 1, 'id': 'patchouli:guide_book', 'components': {'patchouli:book': '%s:%s' % (NS, BOOK)}}}
    for path, value in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(value, f, indent=2, ensure_ascii=False)
            f.write('\n')
    print(len(files), 'files')


if __name__ == '__main__':
    main(sys.argv[1])

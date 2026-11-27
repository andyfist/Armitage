"""Category rules for the Armitage funnel. Edit these lists; nothing else needs to change.

classify(title, description) returns one of:
  ('exclude', reason)      never scanned or priced: large furniture, whitegoods, motor vehicles (Andy, 21 Oct 2026),
                           and anything heavy or bulky (Andy, 7 Nov 2026); every one goes on a "left out" list
  ('always_look', reason)  goes straight to the photo scan, skipping the title pass: categories
                           where collectors chase value the catalogue never mentions
  ('title_pass', '')       everything else: the title pass decides whether photos get looked at

On the 21 Oct 2026 sale (1,890 lots) this sends about 5% to exclude, 30% straight to the
photo scan and leaves 65% for the title pass.
"""
import re

# Large furniture, whitegoods and motor vehicles are out, unless a word that marks real antique or
# designer value appears (a Huon pine chest or a Featherston chair is not "large furniture").
EXCLUDE = [
    ('large furniture', r'\b(lounge|sofa|couch|settee|recliner|wardrobe|robe|dresser|tallboy|sideboard|buffet|bookcase|bookshelf|'
                        r'dining (table|suite|setting)|bed(head|side)?s?\b|mattress|chest of drawers|lowboy|entertainment unit|tv unit|'
                        r'desk|filing cabinet|display cabinet|china cabinet|kitchen (dresser|cabinet)|hutch|ottoman|bar stools?|'
                        r'outdoor setting|coffee table|hall table|side table|lamp table|nest of tables)\b'),
    ('whitegoods', r'\b(fridge|refrigerator|freezer|washing machine|washer|clothes dryer|dishwasher|microwave|electric oven|gas oven|'
                   r'stove|cooktop|range hood|air ?con(ditioner)?|vacuum cleaner|electric heater|gas heater|dehumidifier)\b'),
    ('motor vehicle', r'\b(toyota|holden|ford|mazda|nissan|hyundai|kia|subaru|honda|mitsubishi|suzuki|volkswagen|vw|bmw|mercedes|audi|'
                      r'isuzu|jayco|caravan|camper|trailer|sedan|hatchback|station wagon|motorcycle|motorbike|scooter|ride.on mower|'
                      r'lawn ?mower|rego|registered|unregistered|odometer|vin\b|\d{2,3},?\d{3} ?kms?)\b'),
]
VALUE_WORDS = (r'\b(huon|blackwood|cedar|colonial|georgian|regency|victorian|edwardian|art deco|arts and crafts|mid.century|danish|'
               r'featherston|parker|fler|chiswell|eames|tessa|snelling|windsor|campaign|apothecary|pedal car|model|toy|diecast|'
               r'matchbox|corgi|dinky|tin ?plate|vintage|antique|oil|watercolour|painting|signed)\b')

# Heavy or bulky (Andy, 7 Nov 2026: rugs, generators, compressors, band saws, fountains, train layouts; mainland freight
# and carting kill the margin). Judged on the title only, and with no value-word escape, so a Persian rug is out too.
# Worded carefully: a fountain pen, a match safe, a travel rug, a toy piano, a gravy boat and a mantel clock stay in.
# Every excluded lot goes on the "left out" list in the Chrome pack so Andy can put one back (chrome_brief.py --add).
BULKY = (r"(?<!travel )(?<!picnic )(?<!knee )(?<!car )(?<!throw )\brugs?\b|\bcarpets?\b|\b(floor|hall) runners?\b|\bgenerators?\b|"
         r"\bcompressors?\b|\bband ?saws?\b|\btable ?saws?\b|\bdrop ?saws?\b|\bmitre ?saws?\b|\bthicknessers?\b|\bjointers?\b|"
         r"\blathes?\b|\bdrill press(es)?\b|\bwelders?\b|\blog splitters?\b|\bcement mixers?\b|\bwheel ?barrows?\b(?! wheels?)|"
         r"\bmowers?\b|\bpressure washers?\b|\bwater tanks?\b|\bsheds?\b|\bgazebos?\b|\btrampolines?\b|\bspa (bath|pool)s?\b|"
         r"\b(pool|billiard|snooker|table tennis|ping pong) tables?\b|(?<!toy )(?<!childs )(?<!child's )\bpianos?\b(?! (accordion|rolls?|music|book|sconces?|shaped|parts))|"
         r"\bpianolas?\b|\b(pump|reed|church|electric) organs?\b|\bharmoniums?\b|\b(train|railway) layouts?\b|"
         r"\bfountains?\b(?! ?pens?)|\bbird ?baths?\b|\bslabs? of\b|\btimber slabs?\b|\btyres\b|"
         r"\bbikes?\b(?! (covers?|parts|racks?|lamps?|lights?|bells?|badges?|horns?|pumps?|locks?|seats?|helmets?|stands?))|"
         r"\bbicycles?\b(?! (lamps?|lights?|bells?|badges?|horns?|pumps?|locks?|seats?|helmets?))|\btreadmills?\b|\browing machines?\b|"
         r"\bcross trainers?\b|\bbarbers? chairs?\b|\bwork ?bench(es)?\b|\bkilns?\b|\bmangles?\b|"
         r"(?<!match )(?<!vesta )(?<!toy )(?<!money )\bsafes?\b|\bclothes ?lines?\b|\boutboards?\b|\b(diesel|petrol|stationary|air cooled) (engines?|motors?)\b|"
         r"\bdinghy|\bdinghies\b|\bkayaks?\b|\bcanoes?\b|\btinnies\b|\bgantry\b|\bengine (hoist|crane|stand)s?\b|"
         r"\b(fire|fireplace) surrounds?\b|\bmantelpieces?\b|\bbath ?tubs?\b|\bcast iron baths?\b|\bbbqs?\b|\bbarbecues?\b|"
         r"\bpay ?phones?\b|\boutdoor (setting|seat|chair|table|bench)e?s?\b|\b\d{2} ?(\"|inch|in\b) ?(tv|television)\b|"
         r"\b(flat screen|smart|led|lcd|plasma) (tv|television)s?\b")


def title_text(title, description=''):
    """The lot's title; Armitage cuts long titles with '...', so then the description's first sentence stands in."""
    text = (title or '').lower()
    if text.endswith('...') and description:
        text = re.split(r'\. ', description, maxsplit=1)[0].lower()
    return text


def is_bulky(title, description=''):
    return bool(re.search(BULKY, title_text(title, description)))


# Lots that always get the photo scan. The 21 Oct 2026 sale showed why: four axe lots (a Hytest Racer
# head among them) were passed over until a bidder from Bouvard, WA started on them.
ALWAYS_LOOK = [
    ('books and paper', r'\b(\w*books?|novels?|hardcovers?|hardbacks?|paperbacks?|bibles?|encyclop\w+|annuals?|almanacs?|'
                        r'bibliograph\w*|1st ed\w*|first ed\w*|signed copy|volumes?|vols?\b|atlas|folio|manuscripts?|letters|diary|diaries|journals?|maps?|etchings?|'
                        r'engravings?|lithographs?|posters?|lobby cards?|ephemera|postcards?|stamps?|comics?)\b'),
    ('coins and banknotes', r'\b(coins?|bank ?notes?|sovereigns?|florins?|shillings?|pennies|penny|tokens?|medallions?|'
                            r'proof|uncirculated|mint set|bullion|ingot)\b'),
    ('tools and axes', r'\b(axe|axes|axe heads?|hatchet|adze|hand planes?|wood(en)? planes?|block plane|chisels?|anvil|hand tools|'
                       r'tool chest|stanley|hytest|keech|tuatahi|plumb|disston|lathe|blacksmith)\b'),
    ('watches and clocks', r'\b(watch|watches|wristwatch|pocket watch|chronograph|rolex|omega|tudor|longines|seiko|tissot|clock|'
                           r'clocks|barometer|chronometer)\b'),
    ('jewellery, gold and silver', r'\b(gold|silver|sterling|9ct|9k|14ct|18ct|22ct|hallmark(ed)?|platinum|diamonds?|sapphires?|'
                                   r'rub(y|ies)|emeralds?|opals?|pearls?|brooch|bracelet|necklace|earrings|pendant|cufflinks|'
                                   r'jewellery|jewelry|fob|locket)\b'),
    ('militaria', r'\b(militar\w*|army|naval|royal navy|raaf|aif|anzac|ww1|ww2|wwi|wwii|bayonet|uniform|badges?|medals?|sword|'
                  r'dagger|cannon|shell case|trench art|regiment|battalion)\b'),
    ('art', r'\b(oil|watercolour|watercolor|acrylic|gouache|pastel|paintings?|artwork|signed|bronze|sculpture|carving|aboriginal|'
            r'bark|tapa|artist|forrest|mcwilliams|glover|piguenit|boyd|nolan)\b'),
    ('pottery and glass', r'\b(pottery|stoneware|studio|campbell|mclaren|remued|bendigo|lithgow|doulton|moorcroft|shelley|'
                          r'clarice cliff|carlton ware|meissen|limoges|murano|lalique)\b'),
    ('whisky, wine and spirits', r'\b(whisky|whiskey|scotch|bourbon|cognac|brandy|rum|wines?|penfolds|grange|macallan|lark|'
                                 r'sullivans? cove)\b'),
    ('cameras, hi-fi and records', r'\b(cameras?|lens|lenses|leica|nikon|hasselblad|rolleiflex|turntable|amplifier|records?|vinyl|'
                                   r'lps?\b|78s\b|radiogram|gramophone)\b'),
    ('vague lot', r'\b(box(es)? of|bulk|sundry|sundries|unknown|unmarked|unsigned|as found)\b'),
]


# Lots that come first in every stage: all of them are photo-scanned in smaller batches, every candidate
# among them gets the cloud price research whatever its score, and they head the emails, the Chrome brief
# and the viewing list. Andy, 5 Nov 2026: "focus on the books and scan every title". Only real books count
# (not the maps, stamps and postcards in "books and paper"). Set PRIORITY to None to treat every lot the same.
PRIORITY = (r'\b(\w*books?|novels?|hardcovers?|hardbacks?|paperbacks?|bibles?|encyclop\w+|annuals?|almanacs?|bibliograph\w*|'
            r'1st ed\w*|first ed\w*|signed copy|volumes?|vols?\b|atlas|folio|manuscripts?|diary|diaries)\b')
NOT_PRIORITY = (r'\b(macbook|chromebook|notebook (computer|pc)|laptop|map drawers?|plan drawers?|book ?cases?|book ?shel\w*|'
                r'book ?ends?|book ?match\w*|book cover|with (a |its |the )?(instruction |service )?book|atlas copco)\b')


def is_priority(title, description=''):
    """Judged on the title only, as descriptions mention books in passing (a rug's 'book cover design', a radio 'with
    book'). Armitage cuts long titles with '...', so then the description's first sentence stands in for the title."""
    text = title_text(title, description)
    return bool(PRIORITY and re.search(PRIORITY, text) and not re.search(NOT_PRIORITY, text))


def priority_cdids(sale_dir):
    """cdids of the sale's priority (book) lots that go to the photo scan, from its lots.json (written by prep)."""
    import json
    import os
    f = os.path.join(sale_dir, 'lots.json')
    if not os.path.exists(f):
        return set()
    return {r['cdid'] for r in json.load(open(f)) if r.get('cls') == 'always_look' and is_priority(r.get('title'), r.get('description'))}


# Every lot with photos gets the photo scan; the title pass is skipped (Andy, 6 Nov 2026: on the 11 Nov sale it
# dropped 390 lots unseen). Set to False to bring the title pass back.
PHOTO_SCAN_ALL = True


# Art lots (Andy, 16 Nov 2026: "treat art like books"): every one gets the deep Chrome check on Opus, every
# picture in a group lot priced. Oil cans, oil lamps and lamp oil are petroliana, not paintings.
ART = (r'\b(oil on (canvas|board|panel|paper|linen|card)|oils? paintings?|oil sketch|watercolou?rs?|acrylics? on|gouache|pastels?|'
       r'paintings?|artworks?|etchings?|lithographs?|engravings?|woodcuts?|wood cuts?|linocuts?|screen ?prints?|serigraphs?|'
       r'aquatints?|mezzotints?|drypoints?|limited edition prints?|signed prints?|art prints?|framed prints?|prints? signed|'
       r'sketch(es)?|drawings?|charcoal (drawing|sketch|on|study)|ink and wash|pen and ink|bronzes?|sculptures?|carvings?|aboriginal|bark paintings?|'
       r'dot paintings?|tapa|portrait|still life|landscape|seascape|signed (lower|l\.?\s?[lr]\.?|bottom|verso|on (the )?(back|verso))|'
       r'framed (picture|art|oil|watercolour)|oil\b(?! ?(can|cans|tin|tins|lamps?|lanterns?|bottles?|jugs?|drums?|filters?|pumps?|heaters?|stoves?|burners?|signs?|cloth))|'
       r'battarbee|namatjira|hermannsburg|pro hart|kenneth jack|piguenit|glover|mcwilliams|boyd|nolan|streeton|heysen|norman lindsay)\b')


# petroliana and tools that say "oil" (a Castrol gallon oil tin, oil and grease tins, an oil box of tools)
NOT_ART_OIL = (r'\b(motor|engine|gallon|quart|pint|litre|lubricating|machine|gear|lamp|castrol|mobil|mobiloil|shell|ampol|caltex|'
               r'golden fleece|vacuum|esso|plume|atlantic|neptune|valvoline|penrite|bp)\b[^.,]{0,25}?\boil\b|\boil (&|and) grease\b|\boil box\b')


def is_art(title, description=''):
    text = re.sub(NOT_ART_OIL, ' ', f'{title or ""} {description or ""}'.lower())
    return bool(re.search(ART, text))


def classify(title, description=''):
    text = f'{title or ""} {description or ""}'.lower()
    if is_bulky(title, description):  # Andy, 7 Nov 2026: nothing heavy or bulky, whatever it is
        return 'exclude', 'heavy or bulky'
    for reason, pat in ALWAYS_LOOK:  # a tool box with a heater in it is still a tool box
        if re.search(pat, text):
            return 'always_look', reason
    value = re.search(VALUE_WORDS, text)
    for reason, pat in EXCLUDE:
        if re.search(pat, text) and not value:
            return 'exclude', reason
    return 'title_pass', ''


# New-price check (Andy, 8 Nov 2026, after lot 1704, a Waratah Thumpa star post driver that costs about $2,700 new,
# was skipped by the photo scan as "modern farm tool"): a lot the scan skips that names a brand or a model of a modern
# manufactured product gets its new retail price looked up, and if that is NEW_PRICE_FLOOR or more it goes to price
# research. The new price only promotes a lot; a maximum still needs a SOLD price.
NEW_PRICE_FLOOR = 500
BRANDS = (r'\b(waratah|stihl|husqvarna|makita|milwaukee|dewalt|bosch|hitachi|hikoki|metabo|festool|hilti|paslode|ryobi|aeg|'
          r'ozito|black ?& ?decker|triton|carbatec|record power|jet|hafco|sherwood|kincrome|sidchrome|snap.on|stanley|irwin|'
          r'itm|lincoln|cigweld|unimig|miller|kemppi|honda|briggs|yamaha|kubota|victa|rover|cox|echo|shindaiwa|tanaka|ego|'
          r'karcher|gerni|atlas copco|mcmillan|peerless|topcon|leica|trimble|sokkia|nikon|canon|sony|panasonic|olympus|'
          r'pentax|fujifilm|hasselblad|bose|sonos|bang ?& ?olufsen|b&o|bowers|marantz|denon|pioneer|technics|nad|rega|'
          r'linn|naim|cambridge audio|klipsch|harman|jbl|roland|fender|gibson|martin|taylor|boss|apple|dyson|breville|'
          r'kitchenaid|thermomix|miele|smeg|delonghi|la marzocco|rancilio|weber|traeger|garmin|lowrance|humminbird|'
          r'shimano|daiwa|penn|abu garcia|trek|specialized|giant|cannondale|bmc|pinarello|polaris|can.am|ditch witch|'
          r'tormek|lie.nielsen|veritas|record|bahco|wera|knipex|fluke|snapon|ingersoll|chicago pneumatic|toku|sumake)\b')
# a model number or product code: letters and digits together (RL-H4C, MS391, K970) or a code of five or more digits
MODEL = r'\b(?=[a-z0-9-]*\d)(?=[a-z0-9-]*[a-z])[a-z0-9]{1,}[a-z0-9-]{2,}\b|\b\d{5,}\b'
SIZE = r'^(h|w|d|l|dia|no|x|c|ca|circa)-?\d+$|^\d+(mm|cm|m|kg|g|ml|l|ct|v|w|hp|cc|in|ft|lb|oz|kw|pc|pcs|piece|x)$'


def looks_branded(text):
    """True when a title or scan note names a brand or a model number, the lots the new-price check looks up."""
    t = (text or '').lower()
    if re.search(BRANDS, t):
        return True
    return any(not re.match(SIZE, m.group(0)) for m in re.finditer(MODEL, t))


if __name__ == '__main__':
    import sys
    for t in sys.argv[1:] or ['2 SEATER LOUNGE', 'HUON PINE CHEST OF DRAWERS', 'BOX OF BOOKS', '5 AXE HEADS INC PLUMB',
                              'CABBAGE LEAF PORTUGUESE BOWL', '2014 TOYOTA COROLLA 85,000 KMS', 'CYCLOPS PEDAL CAR']:
        print(classify(t), '<-', t)

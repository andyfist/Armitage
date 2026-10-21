"""Category rules for the Armitage funnel. Edit these lists; nothing else needs to change.

classify(title, description) returns one of:
  ('exclude', reason)      never scanned: large furniture, whitegoods, motor vehicles (Andy, 21 Oct 2026)
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

# Lots that always get the photo scan. The 21 Oct 2026 sale showed why: four axe lots (a Hytest Racer
# head among them) were passed over until a bidder from Bouvard, WA started on them.
ALWAYS_LOOK = [
    ('books and paper', r'\b(books?|volumes?|vols?\b|atlas|folio|manuscripts?|letters|diary|diaries|journals?|maps?|etchings?|'
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


def classify(title, description=''):
    text = f'{title or ""} {description or ""}'.lower()
    for reason, pat in ALWAYS_LOOK:  # a tool box with a heater in it is still a tool box
        if re.search(pat, text):
            return 'always_look', reason
    value = re.search(VALUE_WORDS, text)
    for reason, pat in EXCLUDE:
        if re.search(pat, text) and not value:
            return 'exclude', reason
    return 'title_pass', ''


if __name__ == '__main__':
    import sys
    for t in sys.argv[1:] or ['2 SEATER LOUNGE', 'HUON PINE CHEST OF DRAWERS', 'BOX OF BOOKS', '5 AXE HEADS INC PLUMB',
                              'CABBAGE LEAF PORTUGUESE BOWL', '2014 TOYOTA COROLLA 85,000 KMS', 'CYCLOPS PEDAL CAR']:
        print(classify(t), '<-', t)

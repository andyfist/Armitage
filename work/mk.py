import json
def o(n,f,c,v,r,s=None,m="none legible",i=None):
    d={"photos_viewed":n,"findings":f,"condition":c,"verdict":v,"reason":r,"marks_read":m}
    if s:d["strength"]=s
    if i:d["interest"]=i
    return d
S="SKIP";C="CANDIDATE"
d={
"440276":o(1,"Two costume cameos in gold-tone frames, one orange resin, one blue/white moulded. No marks visible.","Light wear","SKIP","Plastic costume cameos, low value"),
"440277":o(1,"Miniature St Edward's style crown ornament in red presentation case, coloured paste stones, velvet cap. No marks seen.","Good","SKIP","Costume souvenir crown, low value"),
"440278":o(1,"Gold-tone cat brooch with purple cabochon and green paste eyes. No marks visible.","Some tarnish","SKIP","Costume brooch"),
"440279":o(1,"Seiko ladies watch on steel bracelet, dial reads SEIKO, 17 jewels, date window, bracelet short/damaged. Second watch gold-tone digital-style ladies bracelet watch, no name read.","Bracelet incomplete on Seiko, gold-tone worn","SKIP","Common ladies watches, low value",None,"SEIKO 17 JEWELS dial",{"kind":"watch","note":"Seiko ladies 17 jewel mechanical with date, steel, bracelet short; plus unnamed gold-tone ladies watch. Low value."}),
"440280":o(1,"Pair of baroque cultured-looking pearls on silver-coloured hook wires with small gilt collars. No hallmarks visible.","Good","CANDIDATE","Baroque pearl drops, possibly real, modest value",3),
"440281":o(1,"Gold-tone square case watch, dial reads BENUS (not Benrus) CRYSTAL, day-date window, grey lizard-print strap. Title claims Benrus; dial looks like Benus, an inexpensive brand.","Good","SKIP","Dial reads Benus, plated watch, low value",None,"dial BENUS CRYSTAL",{"kind":"watch","note":"Gold-tone day-date quartz-style watch, dial BENUS not Benrus. Low value."}),
"440282":o(1,"Letter opener with embossed silver handle in navy case lined with cream; case stamped in gold for a George St jeweller (55 George St). Blade has gold printed text, likely maker/retailer. Handle has what looks like a hallmark near the bolster but too blurry to read. Sterling claim plausible but unverified.","Good, light wear","CANDIDATE","Probably sterling handled opener in retailer case, small value",3,"possible hallmark near bolster, illegible; case 55 George St jeweller"),
"440283":o(1,"Ladies gold-tone stretch bracelet watch, black dial with crystal markers, logo ck and QUARTZ. Likely imitation Calvin Klein.","Worn plating","SKIP","Fashion quartz watch",None,"ck QUARTZ dial",{"kind":"watch","note":"Gold-tone ck quartz ladies watch, fashion, low value."}),
"440284":o(1,"Silver-tone key pendant with paste on ball chain, charm bracelet with pearls, glass beads and spacer charms in pink brocade pouch. No marks visible.","Fine","SKIP","Costume jewellery"),
"440285":o(1,"Bose true wireless earbuds (QuietComfort style) with charging case and USB-C cable, BOSE logo on buds. Model not readable.","Some wear on case","CANDIDATE","Branded noise-cancelling earbuds with case, resale value reasonable if working",5,"BOSE logo"),
"440286":o(1,"Seven small brass and white-metal figures: naga, Ganesha, Buddhas and a Welsh lady bell. No marks seen.","Normal wear","SKIP","Common small brass items"),
"440287":o(2,"Chinese soapstone seal with carved foo lion top and gilt script, blue and white porcelain ink paste pot with red paste. Seal face reads LORRAINE in reversed English with Chinese characters, a modern tourist seal.","Chip/crack to pot rim possible","SKIP","Modern souvenir seal",None,"seal face LORRAINE plus characters"),
"440288":o(1,"Gold-tone open-faced skeleton-back mechanical pocket watch with snake chain and clip, number 109 on movement. Plated, modern Chinese-style movement.","Brushed finish good","SKIP","Modern plated mechanical pocket watch, low value",None,"109 on movement",{"kind":"watch","note":"Modern gold-plated skeleton mechanical pocket watch with chain, low value."}),
"441701":o(2,"White glazed woven basket dish with applied pink roses, impressed circular mark reading CAPODIMONTE ITALY with crown over fleur-de-lis. Supports title.","Glaze crazing, small chip near rim possible","SKIP","Common Capodimonte dish",None,"impressed Capodimonte Italy crowned N mark"),
"440289":o(2,"Gold-tone enamel clown brooch with pink enamel; reverse shows pin catch with no maker mark or hallmark.","Good","SKIP","Unmarked costume brooch",None,"none on reverse"),
}
json.dump(d,open('obs_g3_440276.json','w'),indent=1)

#!/usr/bin/env python3
"""Usage: python3 -I flip_rule.py [commission]
Flip maximum after selling costs. The old flip max (comp / 2.44) is kept in flip_max_gross; the resale comp is
flip_max_gross x 2.44. Most verified flips already took selling fees off before dividing by 2.44, so their
comp x 2.44 is already net. Only the flips set gross (GROSS below, and maximums added by window_adjust.py) get the commission taken off. Net resale = comp x (1 - commission). Bid the higher of: net >= 2 x all-in cost, or net >= all-in + $500.
All-in = hammer x 1.22. Rounded down to $5. Idempotent."""
import json, sys, os
W = os.path.dirname(os.path.abspath(__file__))
S = float(sys.argv[1]) if len(sys.argv) > 1 else 0.15
GROSS = {('28838', 39), ('28838', 89), ('28839', 883)}
for c in ['28838', '28839', '28840', '28841', '28842']:
    F = f'{W}/armitage{c}_result.json'; R = json.load(open(F)); n = 0
    for p in R['lots']:
        done = 'flip_rule_out' in p and p['flip_rule_out'] == p.get('flip_max_hammer')   # already converted; else an earlier pass reset it
        g = p['flip_max_gross'] if done else p.get('flip_max_hammer')
        if not g: continue
        p['flip_max_gross'] = g
        gross = (c, p['lot']) in GROSS or ('-YEAR WINDOW' in (p.get('working') or '') and not p.get('keep_max_24m'))
        net = g * 2.44 * ((1 - S) if gross else 1)
        allin = max(net / 2, net - 500)
        new = int(round(allin / 1.22, 6)) // 5 * 5
        if new != p.get('flip_max_hammer'): n += 1
        p['flip_max_hammer'] = p['flip_rule_out'] = new
        p['flip_rule'] = (f'Resale ${g * 2.44:,.0f} less {S:.0%} selling commission = net ${net:,.0f}; ' if gross else f'Net resale after selling fees ${net:,.0f} (from the working); ') + f'higher of double your money or $500 profit gives all-in ${allin:,.0f}, hammer ${new:,}.'
    json.dump(R, open(F, 'w'), indent=1); print(c, 'flip changed', n)

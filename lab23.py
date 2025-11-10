#!/usr/bin/env python3
"""
lab_generator.py
- Sposta i comandi di debug BGP globali sotto 'log file /var/log/frr/frr.log'
  invece che dentro la sezione 'router bgp ...'
"""
import os
import shutil
import ipaddress
import subprocess
import argparse
import json
import sys

# -------------------------
# Utility input / validazioni
# -------------------------
def input_non_vuoto(prompt):
    while True:
        v = input(prompt).strip()
        if v:
            return v

def input_int(prompt, min_val=0):
    while True:
        s = input(prompt).strip()
        try:
            n = int(s)
            if n >= min_val:
                return n
            print(f"❌ Inserisci un intero ≥ {min_val}")
        except ValueError:
            print("❌ Inserisci un numero intero valido")
 
def valida_ip_cidr(prompt):
    """Valida e ritorna un indirizzo con CIDR (es. 10.0.0.1/24)."""
    while True:
        s = input(prompt).strip()
        try:
            ipaddress.ip_interface(s)
            return s
        except Exception:
            print("❌ Formato non valido. Usa x.x.x.x/yy (es. 192.168.1.1/24)")

def valida_ip_senza_cidr(prompt):
    while True:
        s = input(prompt).strip()
        try:
            ipaddress.ip_address(s)
            return s
        except Exception:
            print("❌ IP non valido. Inserisci un IPv4 (es. 10.0.0.2)")

def valida_protocols(prompt):
    allowed = {"bgp", "ospf", "rip"}
    while True:
        s = input(prompt).strip().lower().replace(",", " ")
        toks = [t for t in s.split() if t]
        if toks and all(t in allowed for t in toks):
            return list(dict.fromkeys(toks))
        print("❌ Usa solo: bgp ospf rip")

# -------------------------
# Templates
# -------------------------
DAEMONS_TMPL = """zebra={zebra} 
ripd={ripd}
ospfd={ospfd}
bgpd={bgpd}

ospf6d=no
ripngd=no
isisd=no
pimd=no
ldpd=no
nhrpd=no
eigrpd=no
babeld=no
sharpd=no
staticd=no
pbrd=no
bfdd=no
fabricd=no

######

vtysh_enable=yes
zebra_options=" -s 90000000 --daemon -A 127.0.0.1"
bgpd_options="   --daemon -A 127.0.0.1"
ospfd_options="  --daemon -A 127.0.0.1"
ospf6d_options=" --daemon -A ::1"
ripd_options="   --daemon -A 127.0.0.1"
ripngd_options=" --daemon -A ::1"
isisd_options="  --daemon -A 127.0.0.1"
pimd_options="  --daemon -A 127.0.0.1"
ldpd_options="  --daemon -A 127.0.0.1"
nhrpd_options="  --daemon -A 127.0.0.1"
eigrpd_options="  --daemon -A 127.0.0.1"
babeld_options="  --daemon -A 127.0.0.1"
sharpd_options="  --daemon -A 127.0.0.1"
staticd_options="  --daemon -A 127.0.0.1"
pbrd_options="  --daemon -A 127.0.0.1"
bfdd_options="  --daemon -A 127.0.0.1"
fabricd_options="  --daemon -A 127.0.0.1"
"""

VTYSH_TMPL = """service integrated-vtysh-config
hostname {hostname}
"""

FRR_HEADER = """password zebra
enable password zebra

log file /var/log/frr/frr.log
"""
STARTUP_ROUTER_TMPL = """{ip_config}

systemctl start frr
"""

STARTUP_HOST_TMPL = """{ip_config}
ip route add default via {gateway} dev eth0
"""

STARTUP_WWW_TMPL = """ip address add {ip} dev eth0
ip route add default via {gateway} dev eth0
systemctl start apache2 
"""

WWW_INDEX = """<html><head><title>www</title></head><body><h1>Server WWW</h1></body></html>"""

LAB_CONF_HEADER = ""

# -------------------------
# Helpers FRR: aggregazione reti
# -------------------------
def aggregate_to_supernet_for_router(interface_ips, agg_prefix=16):
    """
    Aggrega le reti collegate di un router.

    - Prima collassa gli indirizzi adiacenti (come prima).
    - Poi, per IPv4, se ci sono più reti che ricadono nello stesso supernet
      di lunghezza `agg_prefix` (es. /16), queste saranno aggregate in quel
      supernet. Se invece c'è una sola rete nel supernet, viene mantenuta
      la rete originale.

    Questo evita di permettere modifiche manuali ai singoli `frr.conf` per
    gestire l'aggregazione: viene calcolata automaticamente qui.

    Note/assunzioni:
    - L'aggregazione automatica opera per default su /16 per IPv4. Se vuoi
      un comportamento diverso puoi cambiare `agg_prefix`.
    - IPv6 viene semplicemente collassato ma non verrà ulteriormente
      supernettato dal comportamento di gruppo qui (per evitare scelte
      ambigue sui prefissi IPv6).
    """
    networks = []
    for ip_cidr in interface_ips:
        try:
            iface = ipaddress.ip_interface(ip_cidr)
            networks.append(iface.network)
        except ValueError:
            continue
    if not networks:
        return []

    # Collassa reti contigue come prima
    collapsed = list(ipaddress.collapse_addresses(networks))

    ipv4_nets = [n for n in collapsed if isinstance(n, ipaddress.IPv4Network)]
    ipv6_nets = [n for n in collapsed if isinstance(n, ipaddress.IPv6Network)]

    # Raggruppa IPv4 per supernet di lunghezza agg_prefix
    super_map = {}
    for n in ipv4_nets:
        if n.prefixlen <= agg_prefix:
            # la rete è già più ampia o uguale del target: la manteniamo così
            super_map.setdefault(n, []).append(n)
        else:
            s = n.supernet(new_prefix=agg_prefix)
            super_map.setdefault(s, []).append(n)

    result_nets = []
    for supern, members in super_map.items():
        if isinstance(supern, ipaddress.IPv4Network):
            # se ci sono più reti nel supernet, allora usiamo il supernet
            if len(members) > 1:
                result_nets.append(supern)
            else:
                # una sola rete -> mantieni la rete originale
                result_nets.append(members[0])
        else:
            # safety fallback
            for m in members:
                result_nets.append(m)

    # aggiungi IPv6 così come è stato collassato
    result_nets.extend(ipv6_nets)

    # Riricollassa per sicurezza e ritorna come stringhe
    final = list(ipaddress.collapse_addresses(result_nets))
    return [str(n) for n in final]


def collapse_interface_networks(interface_ips):
    """
    Collassa le reti derivate dalle interfacce evitando di forzare
    supernet di lunghezza fissa. Restituisce la lista di reti collassate
    (es. ['1.2.0.0/24','1.3.0.0/24'] -> ['1.2.0.0/24','1.3.0.0/24'] o
    se contigue vengono unite secondo ipaddress.collapse_addresses).

    Questa funzione è il punto centrale che useremo per passare le reti
    ai generatori di stanza (BGP/OSPF/RIP). I generatori possono poi
    scegliere di prendere un supernet più ampio se lo ritengono opportuno.
    """
    networks = []
    for ip_cidr in interface_ips:
        try:
            iface = ipaddress.ip_interface(ip_cidr)
            networks.append(iface.network)
        except Exception:
            continue
    if not networks:
        return []
    collapsed = list(ipaddress.collapse_addresses(networks))
    return [str(n) for n in collapsed]

# -------------------------
# FRR stanza builders
# -------------------------
def mk_bgp_stanza(asn, redistribute=None, networks=None):
    lines = [
        f"router bgp {asn}",
        "    no bgp ebgp-requires-policy",
        "    no bgp network import-check",
    ]
    # networks handled below; redistribute directives will be appended
    # at the end of the 'router bgp' block (after networks) to keep
    # stanza visually grouped.
    # I comandi debug BGP sono stati rimossi da qui
    # compatta le network BGP: se più network possono essere rappresentate
    # da un supernet comune, viene usato il supernet più specifico che
    # copre l'intero insieme (es. reti 1.2.0.0/24 e 1.3.0.0/24 -> 1.0.0.0/8
    # secondo la policy di copertura richiesta dall'utente)
    if networks:
        try:
            from ipaddress import ip_network, IPv4Network, IPv6Network
            nets = [ip_network(n) for n in networks]
            ipv4_nets = [n for n in nets if isinstance(n, IPv4Network)]
            ipv6_nets = [n for n in nets if isinstance(n, IPv6Network)]

            # Gestione IPv4: valutiamo se usare un byte-aligned supernet (/24,/16,/8)
            # basandoci sulle reti originali (non solo sul risultato del collapse)
            if ipv4_nets:
                collapsed = list(ipaddress.collapse_addresses(ipv4_nets))
                # Calcola range (min/max) sulle reti originali per permettere
                # di scegliere un supernet più ampio anche quando il collapse
                # ha prodotto un singolo network (es. due /24 adiacenti -> /23)
                min_addr = min(n.network_address for n in ipv4_nets)
                max_addr = max(n.broadcast_address for n in ipv4_nets)

                # cerca candidati allineati /24, /16, /8 (preferiamo la più specifica tra queste)
                chosen = None
                for cand in (24, 16, 8):
                    mask = ((0xFFFFFFFF << (32 - cand)) & 0xFFFFFFFF)
                    aligned_int = int(min_addr) & mask
                    cand_net = IPv4Network((aligned_int, cand))
                    if int(cand_net.network_address) <= int(min_addr) and int(cand_net.broadcast_address) >= int(max_addr):
                        chosen = cand_net
                        break

                # calcola il prefix minimo che copre l'intervallo
                xor = int(min_addr) ^ int(max_addr)
                if xor == 0:
                    # tutte le reti sono identiche
                    prefixlen = ipv4_nets[0].prefixlen
                else:
                    prefixlen = 32 - xor.bit_length()

                min_orig = min(n.prefixlen for n in ipv4_nets)

                # preferiamo un candidato byte-aligned se copre l'intervallo e
                # non è troppo ampio (soglia minima /8)
                if chosen is not None and chosen.prefixlen < min_orig and chosen.prefixlen >= 8:
                    lines.append(f"    network {str(chosen)}")
                else:
                    # se il supernet calcolato è più ampio delle reti originali ed è >= /8, usalo
                    if prefixlen < min_orig and prefixlen >= 8:
                        net_addr_int = int(min_addr) & (((0xFFFFFFFF << (32 - prefixlen)) & 0xFFFFFFFF))
                        supern = IPv4Network((net_addr_int, prefixlen))
                        lines.append(f"    network {str(supern)}")
                    else:
                        # fallback: scrivi le network collassate (più conservativo)
                        for n in collapsed:
                            lines.append(f"    network {str(n)}")

            # IPv6: mantieni le reti così come sono (no supernetting automatico qui)
            for n in ipv6_nets:
                lines.append(f"    network {n}")
        except Exception:
            # fallback semplice: stampa le stringhe originali dedupate
            nets_seen = set()
            for net in networks:
                if net not in nets_seen:
                    lines.append(f"    network {net}")
                    nets_seen.add(net)
    # NOTE: non aggiungiamo più automaticamente comandi `redistribute`.
    # L'amministratore preferisce gestirli manualmente nel file `frr.conf`.
    # Questo evita policy non desiderate inserite automaticamente.

    return "\n".join(lines) + "\n\n"

def mk_ospf_stanza(networks, redistribute=None):
    lines = ["router ospf"]
    if networks:
        try:
            nets = [ipaddress.ip_network(n) for n in networks]
            ipv4_nets = [n for n in nets if isinstance(n, ipaddress.IPv4Network)]
            ipv6_nets = [n for n in nets if isinstance(n, ipaddress.IPv6Network)]
            if ipv4_nets:
                # collapse contiguous/prefix-overlapping networks first
                collapsed = list(ipaddress.collapse_addresses(ipv4_nets))
                # compute minimal covering supernet (use original ipv4_nets for range)
                min_addr = min(n.network_address for n in ipv4_nets)
                max_addr = max(n.broadcast_address for n in ipv4_nets)
                xor = int(min_addr) ^ int(max_addr)
                if xor == 0:
                    prefixlen = ipv4_nets[0].prefixlen
                else:
                    prefixlen = 32 - xor.bit_length()
                min_orig = min(n.prefixlen for n in ipv4_nets)

                # Considera il supernet solo se non è troppo ampio (evitiamo /0..../7)
                # e solo se effettivamente più ampio delle reti originali.
                if prefixlen < min_orig and prefixlen >= 8:
                    # build supernet aligned to prefixlen
                    net_addr_int = int(min_addr) & (~((1 << (32 - prefixlen)) - 1))
                    supern = ipaddress.IPv4Network((net_addr_int, prefixlen))
                    # prefer byte-aligned (/24,/16,/8) if they still cover the range
                    chosen = None
                    for cand in (24, 16, 8):
                        mask = (~((1 << (32 - cand)) - 1)) & ((1 << 32) - 1)
                        aligned_int = int(min_addr) & mask
                        cand_net = ipaddress.IPv4Network((aligned_int, cand))
                        if int(cand_net.network_address) <= int(min_addr) and int(cand_net.broadcast_address) >= int(max_addr):
                            chosen = cand_net
                            break
                    if chosen is not None:
                        lines.append(f"    network {chosen} area 0.0.0.0")
                    else:
                        lines.append(f"    network {supern} area 0.0.0.0")
                else:
                    # fallback al comportamento più conservativo: scrivi le reti collassate
                    for n in collapsed:
                        lines.append(f"    network {n} area 0.0.0.0")
            # append IPv6 networks without further aggregation
            for n in ipv6_nets:
                lines.append(f"    network {n} area 0.0.0.0")
        except Exception:
            # fallback: print original strings
            for net in networks:
                lines.append(f"    network {net} area 0.0.0.0")
    # Non aggiungiamo automaticamente `redistribute`.
    return "\n".join(lines) + "\n\n"

def mk_rip_stanza(networks, redistribute=None):
    lines = ["router rip"]
    for net in networks:
        lines.append(f"    network {net}")
    # Non aggiungiamo automaticamente `redistribute`.
    return "\n".join(lines) + "\n\n"

# -------------------------
# Creazione file router
# -------------------------
def crea_router_files(base_path, rname, data):
    etc_frr = os.path.join(base_path, rname, "etc", "frr")
    os.makedirs(etc_frr, exist_ok=True)

    # Forza sempre zebra=yes come richiesto
    zebra_flag = "yes"
    daemons = DAEMONS_TMPL.format(
        zebra=zebra_flag,
        ripd="yes" if "rip" in data["protocols"] else "no",
        ospfd="yes" if "ospf" in data["protocols"] else "no",
        bgpd="yes" if "bgp" in data["protocols"] else "no"
    )
    with open(os.path.join(etc_frr, "daemons"), "w") as f:
        f.write(daemons)

    hostname_line = f"{rname}-frr"
    with open(os.path.join(etc_frr, "vtysh.conf"), "w") as f:
        f.write(VTYSH_TMPL.format(hostname=hostname_line))

    parts = [FRR_HEADER]

    # Se il router usa BGP, aggiungi debug subito dopo l'intestazione
    if "bgp" in data["protocols"]:
        parts.append(
            "debug bgp keepalives\n"
            "debug bgp updates in\n"
            "debug bgp updates out\n"
        )

    iface_ips = [iface["ip"] for iface in data["interfaces"]]
    # collapse minimale delle reti collegate; i singoli stanza-builder
    # (mk_bgp_stanza, mk_ospf_stanza) possono ulteriormente scegliere
    # di usare un supernet più ampio se rilevano che conviene.
    aggregated_nets = collapse_interface_networks(iface_ips)

    # Non creiamo più automaticamente direttive `redistribute`:
    # l'amministratore preferisce aggiungerle manualmente nel file frr.conf.
    if "bgp" in data["protocols"]:
        parts.append(mk_bgp_stanza(data.get("asn", ""), networks=aggregated_nets))
    if "ospf" in data["protocols"]:
        parts.append(mk_ospf_stanza(aggregated_nets))
    if "rip" in data["protocols"]:
        parts.append(mk_rip_stanza(aggregated_nets))

    with open(os.path.join(etc_frr, "frr.conf"), "w") as f:
        f.write("\n".join(parts))

    ip_cfg_lines = [f"ip address add {iface['ip']} dev {iface['name']}" for iface in data["interfaces"]]
    startup_path = os.path.join(base_path, f"{rname}.startup")
    with open(startup_path, "w") as f:
        f.write(STARTUP_ROUTER_TMPL.format(ip_config="\n".join(ip_cfg_lines)))
    try:
        os.chmod(startup_path, 0o755)
    except Exception:
        pass



# -------------------------
# Host e WWW
# -------------------------
def crea_host_file(base_path, hname, ip_cidr, gateway_cidr, lan):
    os.makedirs(base_path, exist_ok=True)
    # gateway_cidr può contenere /prefisso; rimuoviamo la maschera per la route
    gateway = gateway_cidr.split('/')[0] if '/' in gateway_cidr else gateway_cidr
    startup = STARTUP_HOST_TMPL.format(ip_config=f"ip address add {ip_cidr} dev eth0", gateway=gateway)
    path = os.path.join(base_path, f"{hname}.startup")
    with open(path, "w") as f:
        f.write(startup)
    try:
        os.chmod(path, 0o755)
    except Exception:
        pass

def crea_www_file(base_path, name, ip_cidr, gateway_cidr, lan):
    www_dir = os.path.join(base_path, name, "var", "www", "html")
    os.makedirs(www_dir, exist_ok=True)
    index_path = os.path.join(www_dir, "index.html")
    with open(index_path, "w") as f:
        f.write(WWW_INDEX)
    startup_path = os.path.join(base_path, f"{name}.startup")
    # rimuovi la maschera dal gateway per la route (mantieni la maschera sull'IP dell'interfaccia)
    gateway = gateway_cidr.split('/')[0] if '/' in gateway_cidr else gateway_cidr
    with open(startup_path, "w") as f:
        f.write(STARTUP_WWW_TMPL.format(ip=ip_cidr, gateway=gateway))
    try:
        os.chmod(startup_path, 0o755)
    except Exception:
        pass

# -------------------------
# BGP relations: manual menu
# -------------------------
def aggiungi_relazioni_bgp_menu(base_path, routers):
    print("\n=== Aggiungi relazioni BGP (manuale) ===")
    if not routers:
        print("Nessun router disponibile.")
        return
    while True:
        print("\nRouter disponibili:")
        for rn, r in routers.items():
            print(f" - {rn} (ASN: {r.get('asn','-')})")
        src = input("Router sorgente (vuoto per uscire): ").strip()
        if not src:
            break
        if src not in routers:
            print("Router sorgente non valido.")
            continue
        dst = input("Router destinazione: ").strip()
        if dst not in routers:
            print("Router destinazione non valido.")
            continue
        if "bgp" not in routers[src]["protocols"] or "bgp" not in routers[dst]["protocols"]:
            print("Entrambi i router devono avere BGP abilitato.")
            continue
        rel = input("Tipo relazione (peer/provider/customer): ").strip().lower()
        if rel not in ("peer", "provider", "customer"):
            print("Tipo relazione non valido.")
            continue
        neigh_ip = valida_ip_senza_cidr("IP neighbor verso dst (es. 10.0.0.2): ")
        aggiungi_policy = input("Aggiungere prefix-list / route-map (s/N)? ").strip().lower().startswith("s")
        lp_map = {"peer": 100, "provider": 80, "customer": 120}
        local_pref = lp_map[rel]
        fpath = os.path.join(base_path, src, "etc", "frr", "frr.conf")
        # crea le righe neighbor da inserire dentro il blocco router bgp
        neighbor_lines = [f"neighbor {neigh_ip} remote-as {routers[dst]['asn']}",
                          f"neighbor {neigh_ip} description {rel}_{dst}"]
        insert_lines_into_protocol_block(fpath, proto='bgp', asn=None, lines=neighbor_lines)

        # se richiesto, aggiungi le policy (prefix-list / route-map) al fondo del file
        if aggiungi_policy:
            policy = []
            policy.append(f"neighbor {neigh_ip} prefix-list {rel}_{dst}_in in")
            policy.append(f"neighbor {neigh_ip} prefix-list {rel}_{dst}_out out")
            policy.append("")
            policy.append(f"ip prefix-list {rel}_{dst}_in permit any")
            policy.append(f"ip prefix-list {rel}_{dst}_out permit any")
            policy.append("")
            policy.append(f"route-map pref_{dst}_in permit 10")
            policy.append(f"    set local-preference {local_pref}")
            policy.append("")
            policy.append(f"neighbor {neigh_ip} route-map pref_{dst}_in in")
            with open(fpath, "a") as f:
                for line in policy:
                    f.write(line + "\n")
        print(f"Relazione BGP ({rel}) aggiunta su {src} verso {dst} (neighbor {neigh_ip}).")

# -------------------------
# Auto-generate BGP neighbors for routers sharing same LAN
# -------------------------
def auto_generate_bgp_neighbors(base_path, routers):
    """
    Per ogni coppia di router che condividono la stessa LAN (campo 'lan' su interfacce),
    aggiunge neighbor reciproci usando l'IP dell'interfaccia del peer collegata a quella LAN.
    """
    lan_map = {}
    for rname, rdata in routers.items():
        for iface in rdata["interfaces"]:
            lan = iface.get("lan")
            if not lan:
                continue
            lan_map.setdefault(lan, []).append((rname, iface["ip"], rdata.get("asn")))

    for lan, members in lan_map.items():
        if len(members) < 2:
            continue
        for i in range(len(members)):
            for j in range(i+1, len(members)):
                r1, ip1, asn1 = members[i]
                r2, ip2, asn2 = members[j]
                if "bgp" not in routers[r1]["protocols"] or "bgp" not in routers[r2]["protocols"]:
                    continue
                add_neighbor_if_missing(base_path, r1, ip2, routers[r2]['asn'], desc=f"Router AS{routers[r2]['asn']}{r2}")
                add_neighbor_if_missing(base_path, r2, ip1, routers[r1]['asn'], desc=f"Router AS{routers[r1]['asn']}{r1}")

def add_neighbor_if_missing(base_path, src_router, neigh_ip, neigh_asn, desc=None):
    fpath = os.path.join(base_path, src_router, "etc", "frr", "frr.conf")
    if not os.path.exists(fpath):
        return
    with open(fpath, "r") as f:
        content = f.read()
    # strip CIDR if present
    neigh_ip_stripped = neigh_ip.split('/')[0] if '/' in neigh_ip else neigh_ip
    if f"neighbor {neigh_ip_stripped} remote-as" in content:
        return
    # Costruiamo le righe neighbor (senza newline finali)
    lines = [f"neighbor {neigh_ip_stripped} remote-as {neigh_asn}"]
    if desc:
        lines.append(f"neighbor {neigh_ip_stripped} description {desc}")
    # Inseriamo le righe dentro il blocco 'router bgp' se presente,
    # altrimenti appendiamo a fine file
    insert_lines_into_protocol_block(fpath, proto='bgp', asn=None, lines=lines)

# -------------------------
# Modifica frr.conf con editor
# -------------------------
def modifica_router_menu(base_path, routers):
    print("\n=== Modifica frr.conf router ===")
    keys = list(routers.keys())
    for i, k in enumerate(keys, 1):
        print(f"{i}. {k}")
    idx = input_int("Seleziona router (numero, 0 per annullare): ", 0)
    if idx == 0 or idx > len(keys):
        return
    sel = keys[idx - 1]
    fpath = os.path.join(base_path, sel, "etc", "frr", "frr.conf")
    if not os.path.exists(fpath):
        print("frr.conf non trovato per", sel)
        return
    editor = os.environ.get("EDITOR", "nano")
    try:
        subprocess.call([editor, fpath])
    except Exception as e:
        print("Errore aprendo editor:", e)


# -------------------------
# Menu post-creazione: implementazione richieste (in italiano)
# -------------------------
def append_frr_stanza(base_path, router, stanza):
    fpath = os.path.join(base_path, router, "etc", "frr", "frr.conf")
    if not os.path.exists(fpath):
        print(f"⚠️ frr.conf non trovato per {router}: {fpath}")
        return False
    with open(fpath, "a") as f:
        f.write("\n" + stanza + "\n")
    return True

def insert_lines_into_protocol_block(fpath, proto='bgp', asn=None, lines=None):
    """Inserisce `lines` (lista di stringhe, senza newline) dentro la sezione 'router <proto>' di fpath.
    - proto: 'bgp', 'ospf', 'rip', etc.
    - asn: opzionale, quando fornito cerca la stanza che contiene anche l'ASN (utile per 'router bgp <asn>').
    Se non trova una sezione valida, appende le righe alla fine del file.
    Le righe saranno indentate con 4 spazi quando inserite dentro il blocco.
    """
    if lines is None:
        return False
    try:
        with open(fpath, 'r') as f:
            content = f.readlines()
    except Exception:
        return False

    # trova la prima occorrenza di 'router <proto>' (linea che comincia con 'router proto')
    idx = None
    for i, L in enumerate(content):
        s = L.strip()
        if s.startswith('router ' + proto):
            # se viene passato un asn, verifichiamo che la linea lo contenga
            if asn and str(asn) not in s:
                continue
            idx = i
            break

    if idx is None:
        # non trovato: append a fine file
        with open(fpath, 'a') as f:
            f.write('\n')
            for l in lines:
                f.write(l + '\n')
        return True

    # trova il punto di inserimento: il primo indice dopo il blocco indentato
    j = idx + 1
    while j < len(content):
        line = content[j]
        # considera appartenenti al blocco le linee vuote o indentate
        if line.startswith(' ') or line.startswith('\t') or line.strip() == '':
            j += 1
            continue
        # se incontriamo un commento di sezione (es. '!') trattiamolo come parte del blocco
        if line.lstrip().startswith('!'):
            j += 1
            continue
        break

    # prepara le righe indentate
    ind_lines = [('    ' + l) for l in lines]
    # inserisci prima dell'indice j
    new_content = content[:j] + [l + '\n' for l in ind_lines] + content[j:]
    with open(fpath, 'w') as f:
        f.writelines(new_content)
    return True

def select_router(routers, prompt="Seleziona router:"):
    keys = list(routers.keys())
    if not keys:
        print("Nessun router disponibile.")
        return None
    print(prompt)
    for i, k in enumerate(keys, 1):
        asn = routers[k].get('asn','-')
        print(f"{i}) {k} (ASN: {asn})")
    while True:
        sel = input("Numero router (o nome, vuoto per annullare): ").strip()
        if not sel:
            return None
        if sel.isdigit():
            idx = int(sel)
            if 1 <= idx <= len(keys):
                return keys[idx-1]
            print("Indice non valido.")
        else:
            if sel in routers:
                return sel
            print("Nome router non valido.")

def select_interface(router_data):
    if not router_data or not router_data.get('interfaces'):
        print('Nessuna interfaccia disponibile per questo router.')
        return None
    ifaces = router_data['interfaces']
    for i, it in enumerate(ifaces, 1):
        print(f"{i}) {it.get('name')} - {it.get('ip')}")
    while True:
        sel = input('Seleziona interfaccia (numero o nome, vuoto per annullare): ').strip()
        if not sel:
            return None
        if sel.isdigit():
            idx = int(sel)
            if 1 <= idx <= len(ifaces):
                return ifaces[idx-1]['name']
            print('Indice non valido.')
        else:
            for it in ifaces:
                if it.get('name') == sel:
                    return sel
            print('Nome interfaccia non valido.')

def get_first_iface_ip(ifaces):
    # ritorna l'IP (senza /prefisso) della prima interfaccia fornita
    if not ifaces:
        return None
    ip_cidr = ifaces[0].get("ip")
    if not ip_cidr:
        return None
    return ip_cidr.split("/")[0]


def _strip_cidr(ip_cidr):
    if not ip_cidr:
        return None
    return str(ip_cidr).split('/')[0]


def collect_lab_ips(lab_path, routers=None):
    """Raccoglie gli endpoint del lab: tutte le IP associate a interfacce.

    Restituisce una lista di dict con chiavi: 'ip', 'name', 'iface'.
    - Se `routers` è fornito (dict), prende gli IP dalle interfacce dei router
      e imposta 'name' al nome del router e 'iface' al nome dell'interfaccia.
    - Scansiona i file `*.startup` nella directory del lab per trovare tutte le
      occorrenze di `ip address add <ip>` e aggiunge record con 'name' = nome
      del file (senza .startup) e 'iface' se presente nella riga.
    Mantiene l'ordine di scoperta e rimuove duplicati identici (stesso IP, name, iface).
    """
    endpoints = []
    seen = set()
    # dai router
    if routers:
        for rname, rdata in routers.items():
            for iface in rdata.get('interfaces', []):
                ip = _strip_cidr(iface.get('ip'))
                if ip:
                    key = (ip, rname, iface.get('name'))
                    if key not in seen:
                        seen.add(key)
                        endpoints.append({'ip': ip, 'name': rname, 'iface': iface.get('name')})

    # dai file .startup (tutte le occorrenze)
    try:
        for fname in os.listdir(lab_path):
            if not fname.endswith('.startup'):
                continue
            node_name = fname[:-8]
            fpath = os.path.join(lab_path, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    for L in f:
                        if 'ip address add' in L:
                            parts = L.strip().split()
                            # ip address add <ip> [dev <iface>]
                            if len(parts) >= 4:
                                ip = _strip_cidr(parts[3])
                                iface = None
                                if 'dev' in parts:
                                    try:
                                        dev_idx = parts.index('dev')
                                        if dev_idx + 1 < len(parts):
                                            iface = parts[dev_idx + 1]
                                    except Exception:
                                        iface = None
                                key = (ip, node_name, iface)
                                if ip and key not in seen:
                                    seen.add(key)
                                    endpoints.append({'ip': ip, 'name': node_name, 'iface': iface})
            except Exception:
                continue
    except Exception:
        pass

    return endpoints


def generate_ping_oneliner(endpoints):
    """Genera una one-liner bash che esegue `ping -c 1` su ogni endpoint.

    `endpoints` è una lista di dict con chiavi: 'ip', 'name', 'iface'. La one-liner
    esegue un singolo ping per IP e stampa per ogni record: "<ip> (<name> <iface>): <loss> packet loss"
    o "no reply" se l'output non è parsabile.
    """
    if not endpoints:
        return ''
    toks = []
    for e in endpoints:
        ip = e.get('ip')
        name = e.get('name') or ''
        iface = e.get('iface') or ''
        # escape any double quotes by removing them (names shouldn't contain quotes normally)
        token = f"{ip}|{name}|{iface}"
        toks.append(f'"{token}"')
    recs = ' '.join(toks)
    # single probe, print packet loss percentage extracted from ping summary
    cmd = (
        "for rec in " + recs + "; do IFS='|' read -r ip name iface <<< \"$rec\"; "
        "out=$(ping -c 1 \"$ip\" 2>&1); "
        "loss=$(echo \"$out\" | awk -F',' '/packet loss/ {print $3}' | awk '{print $1}'); "
        "if [ -z \"$loss\" ]; then echo -e \"❌ $ip ($name $iface): no reply\"; else "
        "loss_num=$(echo \"$loss\" | tr -d '%'); "
        "if [ \"$loss_num\" = \"0\" ]; then echo -e \"✅ $ip ($name $iface): $loss packet loss\"; else echo -e \"❌ $ip ($name $iface): $loss packet loss\"; fi; fi; done"
    )
    return cmd

def find_routers_by_asn(routers, asn):
    return [name for name, r in routers.items() if str(r.get("asn","")) == str(asn)]

def assegna_costo_interfaccia(base_path, routers):
    print('\n--- Assegna costo OSPF su una interfaccia di un router ---')
    target = select_router(routers, prompt='Seleziona il router su cui impostare il costo OSPF:')
    if not target:
        print('Operazione annullata.')
        return
    # Validation: il router deve avere OSPF abilitato
    prot = routers.get(target, {}).get('protocols', [])
    if 'ospf' not in prot:
        print(f"⚠️ Il router {target} non ha OSPF abilitato (protocols: {prot}). Abilita OSPF prima di impostare il costo.")
        return
    iface = select_interface(routers[target])
    if not iface:
        print('Interfaccia non selezionata. Annullato.')
        return
    costo = input_int(f'Inserisci il costo OSPF desiderato per {iface} (intero ≥ 1): ', 1)
    stanza = f"interface {iface}\n    ip ospf cost {costo}\n"
    if append_frr_stanza(base_path, target, stanza):
        print(f"✅ Costo impostato su {target} {iface} = {costo} (append su frr.conf).")

# implementa_relazioni_as: rimosso — usare la creazione manuale di neighbor o riabilitare se necessario

# asboh_lookup_option: rimosso — l'operazione richiede consultazione esterna

# filter_as10_from_as60: rimosso — puoi riattivare la versione interattiva se ti serve

def preferenza_as50r1(base_path, routers):
    print('\n--- Imposta preferenza su un router per privilegiar annunci da un neighbor ---')
    src = select_router(routers, prompt='Seleziona il router sorgente che deve preferire gli annunci:')
    if not src:
        print('Operazione annullata.')
        return
    print('Seleziona il router preferito (neighbor) dalla lista, o premi invio per inserire IP/ASN manualmente:')
    neigh = select_router(routers, prompt='Seleziona il router preferito (neighbor):')
    if neigh:
        neigh_asn = routers[neigh].get('asn')
        neigh_ip = get_first_iface_ip(routers[neigh]['interfaces'])
    else:
        neigh_asn = input_non_vuoto('ASN del router preferito (es. 70): ')
        neigh_ip = input_non_vuoto('IP del neighbor (es. 10.0.0.2): ')
    if not neigh_ip or not neigh_asn:
        print('Informazioni incomplete; annullato.')
        return
    # strip CIDR if user or source provided it accidentally
    neigh_ip = neigh_ip.split('/')[0] if '/' in neigh_ip else neigh_ip
    # route-map (globale)
    policy_lines = [f"route-map PREF_FROM_{neigh_ip.replace('.', '_')} permit 10",
                    f"    match ip address prefix-list any",
                    f"    set local-preference 200",
                    ""]
    # neighbor lines (da inserire sotto router bgp)
    neighbor_lines = [f"neighbor {neigh_ip} remote-as {neigh_asn}",
                      f"neighbor {neigh_ip} route-map PREF_FROM_{neigh_ip.replace('.', '_')} in"]
    # append policy globalmente
    with open(os.path.join(base_path, src, 'etc', 'frr', 'frr.conf'), 'a') as f:
        for L in policy_lines:
            f.write(L + "\n")
    # inserisci neighbor nel blocco router bgp
    insert_lines_into_protocol_block(os.path.join(base_path, src, 'etc', 'frr', 'frr.conf'), proto='bgp', asn=None, lines=neighbor_lines)
    print(f"✅ Aggiunta preferenza su {src} per annunci provenienti da {neigh_ip} (ASN {neigh_asn}).")
    print(f"✅ Aggiunta preferenza su {src} per annunci provenienti da {neigh_ip} (ASN {neigh_asn}).")

def menu_post_creazione(base_path, routers):
    while True:
        print('\n=== Menu post-creazione (scegli un\'opzione) ===')
        print('1) Imposta costo OSPF su una interfaccia di un router')
        print('2) Imposta preferenza su un router per dare priorità agli annunci da un neighbor')
        print('3) Rigenera file XML del laboratorio (da file modificati)')
        print('4) Genera comando ping per tutti gli indirizzi del lab (copia/incolla)')
        print('0) Esci dal menu')
        choice = input('Seleziona (numero): ').strip()
        if choice == '0':
            break
        if choice == '1':
            assegna_costo_interfaccia(base_path, routers)
        elif choice == '2':
            preferenza_as50r1(base_path, routers)
        elif choice == '3':
            # rigenera XML leggendo lab.conf / startup / etc per ricostruire lo stato corrente
            try:
                xmlpath = rebuild_lab_metadata_and_export(base_path)
                if xmlpath:
                    print(f"✅ XML rigenerato: {xmlpath}")
                else:
                    print("❌ Rigenerazione XML non riuscita.")
            except Exception as e:
                print('Errore durante la rigenerazione XML:', e)
        elif choice == '4':
            try:
                ips = collect_lab_ips(base_path, routers)
                if not ips:
                    print('Nessun IP trovato nel lab. Controlla i file .startup o le interfacce dei router.')
                else:
                    cmd = generate_ping_oneliner(ips)
                    print('\n=== Comando ping generato (copia/incolla sulle macchine del lab) ===\n\n')
                    print(cmd)
                    print('\n\n=== Fine comando ===\n')
            except Exception as e:
                print('Errore generando il comando ping:', e)
        else:
            print('Scelta non valida, riprova.')


def export_lab_to_xml(lab_name, lab_path, routers, hosts, wwws):
    """Esporta una rappresentazione XML del laboratorio in `lab_path/<lab_name>.xml`.
    Struttura semplice: <lab><routers>...<hosts>...<www>...<lab_conf>...</lab>
    """
    try:
        import xml.etree.ElementTree as ET
        from xml.dom import minidom

        root = ET.Element('lab', attrib={'name': lab_name})

        routers_el = ET.SubElement(root, 'routers')
        for rname, rdata in routers.items():
            r_el = ET.SubElement(routers_el, 'router', attrib={'name': rname})
            prot_el = ET.SubElement(r_el, 'protocols')
            for p in rdata.get('protocols', []):
                p_el = ET.SubElement(prot_el, 'protocol')
                p_el.text = str(p)
            asn = rdata.get('asn', '')
            if asn:
                asn_el = ET.SubElement(r_el, 'asn')
                asn_el.text = str(asn)
            if 'interfaces' in rdata:
                ifs_el = ET.SubElement(r_el, 'interfaces')
                for iface in rdata['interfaces']:
                    attrib = {
                        'name': iface.get('name', ''),
                        'lan': iface.get('lan', ''),
                        'ip': iface.get('ip', '')
                    }
                    ET.SubElement(ifs_el, 'interface', attrib=attrib)

        hosts_el = ET.SubElement(root, 'hosts')
        for h in hosts:
            ET.SubElement(hosts_el, 'host', attrib={'name': h.get('name', ''), 'ip': h.get('ip', ''), 'gateway': h.get('gateway', ''), 'lan': h.get('lan', '')})

        www_el = ET.SubElement(root, 'www')
        for w in wwws:
            ET.SubElement(www_el, 'server', attrib={'name': w.get('name', ''), 'ip': w.get('ip', ''), 'gateway': w.get('gateway', ''), 'lan': w.get('lan', '')})

        # include lab.conf content se presente
        try:
            with open(os.path.join(lab_path, 'lab.conf'), 'r') as f:
                labconf = f.read()
            lc_el = ET.SubElement(root, 'lab_conf')
            lc_el.text = labconf
        except Exception:
            pass

        rough = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough)
        pretty = reparsed.toprettyxml(indent='  ', encoding='utf-8')

        out_path = os.path.join(lab_path, f"{lab_name}.xml")
        with open(out_path, 'wb') as f:
            f.write(pretty)
        print(f"✅ Esportato XML: {out_path}")
    except Exception as e:
        print('Errore esportazione XML:', e)
 
# Funzionalità di caricamento non-interattivo (XML/JSON) e ricreazione lab
def load_lab_from_xml(path):
    """Carica un lab da file XML generato dallo script.
    Ritorna: lab_name, routers(dict), hosts(list), wwws(list), lab_conf_text(str or None)
    """
    import xml.etree.ElementTree as ET
    tree = ET.parse(path)
    root = tree.getroot()
    lab_name = root.attrib.get('name') or os.path.splitext(os.path.basename(path))[0]

    routers = {}
    for r in root.findall('./routers/router'):
        rname = r.attrib.get('name')
        protocols = [p.text for p in r.findall('./protocols/protocol') if p.text]
        asn_el = r.find('asn')
        asn = asn_el.text if asn_el is not None else ''
        interfaces = []
        for it in r.findall('./interfaces/interface'):
            interfaces.append({
                'name': it.attrib.get('name',''),
                'lan': it.attrib.get('lan',''),
                'ip': it.attrib.get('ip','')
            })
        routers[rname] = {'protocols': protocols, 'asn': asn, 'interfaces': interfaces}

    hosts = []
    for h in root.findall('./hosts/host'):
        hosts.append({'name': h.attrib.get('name',''), 'ip': h.attrib.get('ip',''), 'gateway': h.attrib.get('gateway',''), 'lan': h.attrib.get('lan','')})

    wwws = []
    for w in root.findall('./www/server'):
        wwws.append({'name': w.attrib.get('name',''), 'ip': w.attrib.get('ip',''), 'gateway': w.attrib.get('gateway',''), 'lan': w.attrib.get('lan','')})

    lab_conf_text = None
    lc = root.find('lab_conf')
    if lc is not None and lc.text:
        lab_conf_text = lc.text

    return lab_name, routers, hosts, wwws, lab_conf_text


def load_lab_from_json(path):
    """Carica un lab da file JSON. Atteso schema simile all'XML prodotto.
    Ritorna: lab_name, routers(dict), hosts(list), wwws(list), lab_conf_text(str or None)
    """
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    lab_name = data.get('lab', {}).get('name') or data.get('name') or os.path.splitext(os.path.basename(path))[0]
    routers = {}
    for r in data.get('routers', []):
        rname = r.get('name')
        protocols = r.get('protocols', [])
        asn = r.get('asn', '')
        interfaces = r.get('interfaces', [])
        routers[rname] = {'protocols': protocols, 'asn': asn, 'interfaces': interfaces}
    hosts = data.get('hosts', []) or []
    wwws = data.get('www', []) or data.get('wwws', []) or []
    lab_conf_text = data.get('lab_conf') or None
    return lab_name, routers, hosts, wwws, lab_conf_text


def recreate_lab_from_data(lab_name, base, routers, hosts, wwws, lab_conf_text=None):
    """Ricrea il lab sul filesystem usando le funzioni esistenti.
    Restituisce il percorso `lab_path` creato.
    """
    lab_path = os.path.join(base, lab_name)
    if os.path.exists(lab_path):
        # rimuovi esistente per ricreare
        if os.path.isdir(lab_path):
            shutil.rmtree(lab_path)
        else:
            os.remove(lab_path)
    os.makedirs(lab_path, exist_ok=True)

    # crea routers
    for rname, rdata in routers.items():
        crea_router_files(lab_path, rname, rdata)

    # crea hosts
    for h in hosts:
        try:
            crea_host_file(lab_path, h.get('name'), h.get('ip'), h.get('gateway'), h.get('lan'))
        except Exception:
            pass

    # crea webservers
    for w in wwws:
        try:
            crea_www_file(lab_path, w.get('name'), w.get('ip'), w.get('gateway'), w.get('lan'))
        except Exception:
            pass

    # scrivi lab.conf se fornito (altrimenti lo lascio come prima)
    if lab_conf_text:
        try:
            with open(os.path.join(lab_path, 'lab.conf'), 'w', encoding='utf-8') as f:
                f.write(lab_conf_text)
        except Exception:
            pass

    # auto-generate BGP neighbors
    auto_generate_bgp_neighbors(lab_path, routers)

    # esporta XML (aggiorna o crea)
    try:
        export_lab_to_xml(lab_name, lab_path, routers, hosts, wwws)
    except Exception:
        pass

    return lab_path


def parse_lab_conf_for_nodes(lab_path):
    """Parse `lab.conf` per ricavare nodi, mapping interfacce->LAN e immagini.
    Ritorna: nodes dict with keys: name -> {'interfaces': {idx: lan}, 'image': image}
    """
    import re
    nodes = {}
    conf_path = os.path.join(lab_path, 'lab.conf')
    if not os.path.exists(conf_path):
        return nodes, None
    lab_conf_text = None
    try:
        with open(conf_path, 'r', encoding='utf-8') as f:
            lab_conf_text = f.read()
    except Exception:
        return nodes, None

    lines = [L.strip() for L in lab_conf_text.splitlines() if L.strip()]
    # pattern: name[index]=value
    p = re.compile(r"^(?P<name>[^\[]+)\[(?P<idx>[^\]]+)\]=(?:\"(?P<qval>.*)\"|(?P<val>.*))$")
    for L in lines:
        m = p.match(L)
        if not m:
            continue
        name = m.group('name')
        idx = m.group('idx')
        val = m.group('qval') if m.group('qval') is not None else m.group('val')
        val = val.strip()
        node = nodes.setdefault(name, {'interfaces': {}, 'image': ''})
        if idx == 'image':
            node['image'] = val.strip('"')
        else:
            # treat as interface index
            try:
                node['interfaces'][int(idx)] = val
            except Exception:
                node['interfaces'][idx] = val
    return nodes, lab_conf_text


def rebuild_lab_metadata_and_export(lab_path):
    """Ricostruisce routers/hosts/www dal filesystem (lab.conf, startup, etc) e rigenera l'XML.
    Restituisce il percorso del file XML creato o None in caso di errore.
    """
    lab_name = os.path.basename(os.path.normpath(lab_path))
    nodes, lab_conf_text = parse_lab_conf_for_nodes(lab_path)
    routers = {}
    hosts = []
    wwws = []

    for name, meta in nodes.items():
        image = meta.get('image','')
        # collect interfaces: build list of dicts {name, lan, ip}
        ifaces = []
        for idx, lan in sorted(meta.get('interfaces', {}).items(), key=lambda x: int(x[0]) if isinstance(x[0], int) or x[0].isdigit() else 0):
            eth = f"eth{idx}"
            ifaces.append({'name': eth, 'lan': lan, 'ip': ''})

        # read startup file for IPs and gateways
        startup_path = os.path.join(lab_path, f"{name}.startup")
        if os.path.exists(startup_path):
            try:
                with open(startup_path, 'r', encoding='utf-8') as f:
                    for L in f:
                        Ls = L.strip()
                        if not Ls:
                            continue
                        # ip address add <ip> dev <iface>
                        parts = Ls.split()
                        if len(parts) >= 5 and parts[0] == 'ip' and parts[1] == 'address' and parts[2] == 'add':
                            ip = parts[3]
                            dev = parts[5] if len(parts) > 5 and parts[4] == 'dev' else None
                            if dev:
                                for it in ifaces:
                                    if it['name'] == dev:
                                        it['ip'] = ip
                        # gateway extraction for hosts/www: 'ip route add default via <gw> dev eth0'
                        if len(parts) >= 7 and parts[0] == 'ip' and parts[1] == 'route' and parts[2] == 'add' and parts[3] == 'default' and parts[4] == 'via':
                            gw = parts[5]
                            # attach gateway to a host/www entry later
            except Exception:
                pass

        # if it's a FRR router image (heuristic)
        if 'frr' in image.lower() or 'kathara/frr' in image.lower():
            # detect protocols and ASN from etc/frr/frr.conf
            frr_conf = os.path.join(lab_path, name, 'etc', 'frr', 'frr.conf')
            protos = []
            asn = ''
            if os.path.exists(frr_conf):
                try:
                    with open(frr_conf, 'r', encoding='utf-8') as f:
                        txt = f.read()
                    if 'router bgp' in txt:
                        protos.append('bgp')
                        import re
                        m = re.search(r'router bgp\s+(\d+)', txt)
                        if m:
                            asn = m.group(1)
                    if 'router ospf' in txt:
                        protos.append('ospf')
                    if 'router rip' in txt:
                        protos.append('rip')
                except Exception:
                    pass
            routers[name] = {'protocols': protos, 'asn': asn, 'interfaces': ifaces}
        else:
            # decide host vs www by checking for www index file
            www_index = os.path.join(lab_path, name, 'var', 'www', 'html', 'index.html')
            # attempt to read IP/gateway from startup if present
            ip_val = ''
            gw_val = ''
            startup_path = os.path.join(lab_path, f"{name}.startup")
            if os.path.exists(startup_path):
                try:
                    with open(startup_path, 'r', encoding='utf-8') as f:
                        for L in f:
                            if 'ip address add' in L:
                                parts = L.strip().split()
                                if len(parts) >= 4:
                                    ip_val = parts[3]
                            if 'ip route add default via' in L:
                                parts = L.strip().split()
                                if len(parts) >= 6:
                                    gw_val = parts[5]
                except Exception:
                    pass
            if os.path.exists(www_index):
                wwws.append({'name': name, 'ip': ip_val, 'gateway': gw_val, 'lan': meta.get('interfaces', {}).get(0, '')})
            else:
                hosts.append({'name': name, 'ip': ip_val, 'gateway': gw_val, 'lan': meta.get('interfaces', {}).get(0, '')})

    try:
        export_lab_to_xml(lab_name, lab_path, routers, hosts, wwws)
        return os.path.join(lab_path, f"{lab_name}.xml")
    except Exception as e:
        print('Errore rigenerazione XML:', e)
        return None

# -------------------------
# Main
# -------------------------
def main():
    # supporto modalità non-interattiva: --from-xml / --from-json
    parser = argparse.ArgumentParser(description='Generatore Kathará')
    parser.add_argument('--from-xml', help='Percorso file XML da importare per creare il lab')
    parser.add_argument('--from-json', help='Percorso file JSON da importare per creare il lab')
    parser.add_argument('--regen-xml', help='Percorso della directory del lab per rigenerare il file XML')
    args, remaining = parser.parse_known_args()

    base = os.getcwd()

    # Se forniti via CLI, manteniamo il comportamento non-interattivo
    if args.regen_xml:
        out = rebuild_lab_metadata_and_export(args.regen_xml)
        if out:
            print(f"✅ XML rigenerato: {out}")
        else:
            print("❌ Rigenerazione XML fallita.")
        return
    if args.from_xml or args.from_json:
        if args.from_xml:
            lab_name, routers, hosts, wwws, lab_conf_text = load_lab_from_xml(args.from_xml)
        else:
            lab_name, routers, hosts, wwws, lab_conf_text = load_lab_from_json(args.from_json)
        lab_path = recreate_lab_from_data(lab_name, base, routers, hosts, wwws, lab_conf_text)
        print(f"✅ Lab '{lab_name}' creato (non-interattivo) in: {lab_path}")
        return

    # Modalità interattiva: chiedi all'utente se creare o importare
    print("=== Generatore Kathará ===")
    print("Scegli modalità:")
    print("  C - Crea nuovo laboratorio (interattivo)")
    print("  I - Importa da file (XML/JSON)")
    print("  G - Rigenera XML di un lab esistente")
    print("  P - Genera comando ping per un lab esistente (copia/incolla)")
    print("  Q - Esci")
    while True:
        mode = input_non_vuoto("Seleziona (C/I/G/Q): ").strip().lower()
        if not mode:
            continue
        if mode.startswith('q'):
            print('Uscita.')
            return
        if mode.startswith('c'):
            # procedi con il flusso interattivo classico
            lab_name = input_non_vuoto("Nome del laboratorio: ")
            lab_path = os.path.join(base, lab_name)
            break
        if mode.startswith('i'):
            file_path = input_non_vuoto("Percorso del file XML/JSON da importare: ")
            if not os.path.exists(file_path):
                print(f"File non trovato: {file_path}")
                continue
            ext = os.path.splitext(file_path)[1].lower()
            try:
                if ext == '.xml':
                    lab_name, routers, hosts, wwws, lab_conf_text = load_lab_from_xml(file_path)
                elif ext == '.json':
                    lab_name, routers, hosts, wwws, lab_conf_text = load_lab_from_json(file_path)
                else:
                    # tenta XML prima, poi JSON
                    try:
                        lab_name, routers, hosts, wwws, lab_conf_text = load_lab_from_xml(file_path)
                    except Exception:
                        lab_name, routers, hosts, wwws, lab_conf_text = load_lab_from_json(file_path)
                lab_path = recreate_lab_from_data(lab_name, base, routers, hosts, wwws, lab_conf_text)
                print(f"✅ Lab '{lab_name}' creato da file in: {lab_path}")
                return
            except Exception as e:
                print('Errore importando il file:', e)
                continue
        if mode.startswith('g'):
            target = input_non_vuoto('Percorso della directory del lab da cui rigenerare l\'XML: ')
            if not os.path.isdir(target):
                print(f"Directory non trovata: {target}")
                continue
            out = rebuild_lab_metadata_and_export(target)
            if out:
                print(f"✅ XML rigenerato: {out}")
            else:
                print("❌ Rigenerazione XML fallita.")
            return
        if mode.startswith('p'):
            target = input_non_vuoto('Percorso della directory del lab per generare il comando ping: ')
            if not os.path.isdir(target):
                print(f"Directory non trovata: {target}")
                continue
            # proviamo a leggere routers.xml se presente (semplifica raccolta IP), ma la funzione
            # collect_lab_ips può operare anche senza routers
            routers_meta = None
            try:
                xmlpath = os.path.join(target, os.path.basename(os.path.normpath(target)) + '.xml')
                if os.path.exists(xmlpath):
                    try:
                        _, routers_meta, _, _, _ = load_lab_from_xml(xmlpath)
                    except Exception:
                        routers_meta = None
            except Exception:
                routers_meta = None
            ips = collect_lab_ips(target, routers_meta)
            if not ips:
                print('Nessun IP trovato nella directory del lab. Controlla che ci siano file .startup o i router con interfacce.')
                continue
            cmd = generate_ping_oneliner(ips)
            print('\n=== Comando ping generato (copia/incolla sulle macchine del lab) ===\n\n')
            print(cmd)
            print('\n\n=== Fine comando ===\n')
            return
        print('Scelta non valida, riprova.')

    if os.path.exists(lab_path):
        ans = input("⚠️ Esiste già. Sovrascrivere? (s/n): ").strip().lower()
        if ans != "s":
            print("Annullato.")
            return
        if os.path.isdir(lab_path):
            shutil.rmtree(lab_path)
        else:
            os.remove(lab_path)
        print("Precedente eliminato.")

    os.makedirs(lab_path, exist_ok=True)

    n_router = input_int("Numero di router: ", 0)
    n_host = input_int("Numero di host/PC: ", 0)
    n_www = input_int("Numero di server WWW: ", 0)

    lab_conf_lines = [LAB_CONF_HEADER.strip()]
    routers = {}
    # Collezioni per esportazione XML
    hosts = []
    wwws = []

    # Routers
    for i in range(1, n_router + 1):
        default_name = f"r{i}"
        while True:
            rname_in = input(f"\nNome router (default {default_name}): ").strip()
            rname = rname_in if rname_in else default_name
            # basic validation: unique and no spaces
            if rname in routers:
                print(f"Nome '{rname}' già usato. Scegli un altro.")
                continue
            if ' ' in rname:
                print("Il nome del router non può contenere spazi.")
                continue
            break
        print(f"--- Configurazione router {rname} ---")
        protocols = valida_protocols(f"Protocolli attivi su {rname} (bgp/ospf/rip, separati da spazio/virgola): ")
        asn = ""
        if "bgp" in protocols:
            asn = input_non_vuoto("Numero AS BGP: ")
        n_if = input_int("Numero interfacce: ", 1)
        interfaces = []
        for idx in range(n_if):
            eth = f"eth{idx}"
            lan = input_non_vuoto(f"  LAN associata a {eth} (es. A): ").upper()
            ip_cidr = valida_ip_cidr(f"  IP per {eth} (es. 10.0.{i}.{idx}/24): ")
            interfaces.append({"name": eth, "lan": lan, "ip": ip_cidr})
            lab_conf_lines.append(f"{rname}[{idx}]={lan}")
        # fine ciclo interfacce: aggiungi la riga image e la linea vuota una sola volta
        lab_conf_lines.append(f'{rname}[image]="kathara/frr"')
        lab_conf_lines.append("")  # blank line
        # salva i dati del router e genera i file (frr.conf, startup, ecc.)
        routers[rname] = {"protocols": protocols, "asn": asn, "interfaces": interfaces}
        crea_router_files(lab_path, rname, routers[rname])

    

    # prepara l'insieme dei nomi già usati (router names)
    used_names = set(routers.keys())

    # Hosts
    for h in range(1, n_host + 1):
        default_hname = f"host{h}"
        while True:
            hname_in = input(f"\nNome host (default {default_hname}): ").strip()
            hname = hname_in if hname_in else default_hname
            if ' ' in hname:
                print("Il nome non può contenere spazi.")
                continue
            if hname in used_names:
                print(f"Nome '{hname}' già usato. Scegli un altro.")
                continue
            break
        used_names.add(hname)
        print(f"--- Configurazione host {hname} ---")
        ip = valida_ip_cidr(f"IP per {hname} (es. 192.168.10.{h}/24): ")
        gw = valida_ip_cidr(f"Gateway per {hname} (es. 192.168.10.1/24): ")
        lan = input_non_vuoto("LAN associata (es. A): ").upper()
        crea_host_file(lab_path, hname, ip, gw, lan)
        hosts.append({"name": hname, "ip": ip, "gateway": gw, "lan": lan})
        lab_conf_lines.append(f"{hname}[0]={lan}")
        lab_conf_lines.append(f'{hname}[image]="kathara/base"')
        lab_conf_lines.append("")

    # WWW servers
    for w in range(1, n_www + 1):
        default_wname = f"www{w}"
        while True:
            wname_in = input(f"\nNome webserver (default {default_wname}): ").strip()
            wname = wname_in if wname_in else default_wname
            if ' ' in wname:
                print("Il nome non può contenere spazi.")
                continue
            if wname in used_names:
                print(f"Nome '{wname}' già usato. Scegli un altro.")
                continue
            break
        used_names.add(wname)
        print(f"--- Configurazione webserver {wname} ---")
        ip = valida_ip_cidr(f"IP per {wname} (es. 10.10.{w}.1/24): ")
        gw = valida_ip_cidr(f"Gateway per {wname} (es. 10.10.{w}.254/24): ")
        lan = input_non_vuoto("LAN associata (es. Z): ").upper()
        crea_www_file(lab_path, wname, ip, gw, lan)
        wwws.append({"name": wname, "ip": ip, "gateway": gw, "lan": lan})
        lab_conf_lines.append(f"{wname}[0]={lan}")
        lab_conf_lines.append(f'{wname}[image]="kathara/base"')
        lab_conf_lines.append("")

    # write lab.conf
    with open(os.path.join(lab_path, "lab.conf"), "w") as f:
        f.write("\n".join(lab_conf_lines).strip() + "\n")

    # Auto-generate BGP neighbors for routers sharing LANs
    auto_generate_bgp_neighbors(lab_path, routers)

    # Esporta il laboratorio in formato XML per poterlo riusare come input
    try:
        export_lab_to_xml(lab_name, lab_path, routers, hosts, wwws)
    except Exception as e:
        print('Attenzione: esportazione XML fallita:', e)

    print(f"\n✅ Lab '{lab_name}' creato in: {lab_path}")
    print("Nota: sono stati generati neighbor BGP automatici per router che condividono la stessa LAN.")
    # Menu in italiano per implementare richieste aggiuntive
    try:
        menu_post_creazione(lab_path, routers)
    except Exception as e:
        print('Errore durante il menu post-creazione:', e)

if __name__ == "__main__":
    main()


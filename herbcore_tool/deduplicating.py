import argparse
import pandas as pd
from rapidfuzz import fuzz
from collections import Counter # count frequency
import re

def clean_name(name): # remove null, extra space etc
    if pd.isna(name):
        return None # None if null
    name = name.strip()
    name = re.sub(r"\s+", " ", name)  # remove multiple blank spaces
    return name if name else None

def extract_individual_names(name):
    if not name:
        return []
    return [n.strip() for n in re.split(r"[;&]", name)] # segregates and cleans names separated by ; or &

def group_names(names, similar): # grouping names by their fuzzy similarities
    groups = [] # author groups

    for name in names:
        if not name:
            continue

        individual_names = extract_individual_names(name) # segregates names separated by ; or &
        group_ids = set() # if a name belongs on a group this gets marked

        for name_ind in individual_names: # for each name piece
            for i, group in enumerate(groups): # for each name in group i
                if any(fuzz.token_sort_ratio(name_ind, member_id) >= similar
                       for member in group # for each member, agregated names or single
                       for member_id in extract_individual_names(member)): # for each member on aggregated name
                    group_ids.add(i) # compatible group

        if group_ids: # if compatible groups
            new_group = set([name])
            for gid in sorted(group_ids, reverse=True): # for each compatible group
                new_group.update(groups[gid]) # aggregate names
                del groups[gid] 
            groups.append(list(new_group)) 
        else:
            groups.append([name])

    return groups

def save_groups_txt(groups, all_names, txt): # save groups in a txt
    counter_names = Counter(all_names) # all original occurences

    with open(txt, 'w', encoding='utf-8') as f:
        for group in groups:
            total = sum(counter_names[n] for n in group) # occurences per group
            f.write(f"{group[0]} : {total} occurence(s)\n") # group header
            for name in sorted(group, key=lambda n: -counter_names[n]): # by order
                oc = counter_names[name]
                f.write(f"  - {name} ({oc})\n")
                for _ in range(oc):
                    f.write(f"     - {name}\n")
            f.write("\n") 

def processing(csv_path, ranking, similar, txt):
    df = pd.read_csv(csv_path) 
    all_names = df['identifiedby'].dropna().map(clean_name).dropna().tolist() # remove space and nulls, turn into a list

    simples = []
    composed = []

    for n in all_names:
        if re.search(r"[;&]", n):
            # if composed name
            composed.append(n)
        else:
            # if simple name
            simples.append(n)

    # duplicate list
    composed_unique = list(dict.fromkeys(composed)) 

    # fuzzy with simple names
    simple_groups = group_names(simples, similar)

    groups = []
    for group in simple_groups: 
        members = set(group)

        composed_group = [ 
            comp for comp in composed_unique 
            if any(
                m in extract_individual_names(comp) 
                for m in members
            )
        ]
        groups.append(group + composed_group)

    counter_names = Counter(all_names)
    groups_in_order = sorted(
        groups,
        key=lambda g: sum(counter_names[n] for n in g), 
        reverse=True
    )

    save_groups_txt(groups_in_order, all_names, txt)

    most_frequent = [
        (grp[0], sum(counter_names[n] for n in grp))
        for grp in groups_in_order
    ]
    print(f"\n\ntop {ranking} most frequent taxonomists:\n")
    for i, (nome, count) in enumerate(most_frequent[:ranking], 1):
        print(f"{i}. {nome} -> {count} occurence(s)")

def main():
    parser = argparse.ArgumentParser(description="fuzzy grouping of taxonomic identifier names")
    parser.add_argument('--csv', type=str, required=True, help='CSV path with authors')
    parser.add_argument('--ranking', type=int, default=10, help='number of most frequent taxonomists')
    parser.add_argument('--similar', type=int, default=60, help='fuzzy similarity (0-100)')
    parser.add_argument('--txt', type=str, default='groups_taxonomists.txt', help='output file for the grouping')

    args = parser.parse_args()
    processing(args.csv, args.ranking, args.similar, args.txt)

if __name__ == "__main__":
    main()

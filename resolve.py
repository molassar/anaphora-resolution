from collections import Counter
from os.path import join
from os.path import splitext
from os import listdir
import xml.etree.ElementTree as ET

PATH = './resources'
OUTPUT = './output'

MENTIONS_DIR = 'Mentions'
CHAINS_DIR = 'Chains'
NS = {'Aux': 'http://www.abbyy.com/ns/Aux#',
      'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}


def init():
    mentions_path = join(PATH, MENTIONS_DIR)
    chains_path = join(PATH, CHAINS_DIR)
    for filename in listdir(mentions_path):
        with open(join(mentions_path, filename)) as f:
            mentions_content = f.read()
        with open(join(chains_path, filename)) as f:
            chains_content = f.read()
        mentions = parse_xml(mentions_content)
        chains = parse_xml(chains_content)
        merged = {**chains, **mentions}
        merged_sorted_keys = sorted(merged.keys(), key=lambda mention: mention[0])
        output_filename = splitext(filename)[0] + '.txt'
        with open(join(OUTPUT, MENTIONS_DIR, output_filename), 'w+') as f:
            count = 1
            for (start, length) in merged_sorted_keys:
                merged[(start, length)]['id'] = count
                f.write('{} {} {}\n'.format(count, start, length))
                count += 1
        chains_counter = Counter(list(map(lambda d: d['node_id'], chains.values())))
        chains_sorted_keys = sorted(chains.keys(), key=lambda chain: chain[0])
        with open(join(OUTPUT, CHAINS_DIR, output_filename), 'w+') as f:
            chain_seq_index = {}
            count = 1
            for (start, length) in chains_sorted_keys:
                chain_id = chains[(start, length)]['node_id']
                chain_len = chains_counter[chain_id]
                if chain_len <= 1:
                    continue
                if chain_id in chain_seq_index:
                    chain_seq_num = chain_seq_index[chain_id]
                else:
                    chain_seq_num = count
                    chain_seq_index[chain_id] = chain_seq_num
                    count += 1
                f.write('{} {} {} {}\n'.format(merged[(start, length)]['id'], start, length, chain_seq_num))


# parse xml content into dict {(start, length): {'node_id': <id>}}
# each entry corresponds to InstanceAnnotation elem
def parse_xml(xml_content):
    entries = {}
    for ann in get_annotations(xml_content):
        instance_ann = ann.find('Aux:InstanceAnnotation', NS)
        start, length, node_id = prepare_entry_elems(instance_ann)
        entries[(start, length)] = {'node_id': node_id}
    return entries


def get_annotations(xml_content):
    root = ET.fromstring(xml_content)
    text_ann = root.find('Aux:TextAnnotations', NS)
    return text_ann.findall('Aux:annotation', NS)


def prepare_entry_elems(instance_ann):
    start = int(instance_ann.find('Aux:annotation_start', NS).text)
    end = int(instance_ann.find('Aux:annotation_end', NS).text)
    instance = instance_ann.find('Aux:instance', NS)
    instance_id = instance.attrib['{{{}}}nodeID'.format(NS['rdf'])]
    return start, end - start, instance_id


init()

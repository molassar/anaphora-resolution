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
    # process mentions
    mentions_path = join(PATH, MENTIONS_DIR)
    for filename in listdir(mentions_path):
        with open(join(mentions_path, filename)) as f:
            xml_content = f.read()
        mentions = process_mentions(xml_content)
        output_filename = splitext(filename)[0] + '.txt'
        with open(join(OUTPUT, MENTIONS_DIR, output_filename), 'w+') as f:
            f.write(mentions)
    # process chains
    chains_path = join(PATH, CHAINS_DIR)
    for filename in listdir(chains_path):
        with open(join(chains_path, filename)) as f:
            xml_content = f.read()
        chains = process_chains(xml_content)
        output_filename = splitext(filename)[0] + '.txt'
        with open(join(OUTPUT, CHAINS_DIR, output_filename), 'w+') as f:
            f.write(chains)


def process_mentions(xml_content):
    entry_list = list()
    entry_id = 1
    for ann in get_annotations(xml_content):
        instance_ann = ann.find('Aux:InstanceAnnotation', NS)
        entry_elems = prepare_entry_elems(instance_ann)
        entry = '{} {} {}'.format(entry_id, *entry_elems)
        entry_list.append(entry)
        entry_id += 1
    return '\n'.join(entry_list)


def process_chains(xml_content):
    chains_dict = dict()
    new_chain_id = 1
    raw_entry_list = list()
    entry_id = 1
    for ann in get_annotations(xml_content):
        instance_ann = ann.find('Aux:InstanceAnnotation', NS)
        entry_elems = prepare_entry_elems(instance_ann)
        raw_entry = dict(zip(['start', 'length', 'inst_id'], entry_elems))
        raw_entry['id'] = entry_id
        inst_id = raw_entry['inst_id']
        if inst_id not in chains_dict:
            chains_dict[inst_id] = {'id': new_chain_id, 'count': 1}
            raw_entry['chain_id'] = new_chain_id
            new_chain_id += 1
        else:
            raw_entry['chain_id'] = chains_dict[inst_id]['id']
            chains_dict[inst_id]['count'] += 1
        raw_entry_list.append(raw_entry)
        entry_id += 1
    return '\n'.join(postprocess_chain_entries(raw_entry_list, chains_dict))


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


def postprocess_chain_entries(entry_list, chains_dict):
    filtered_entries = [entry for entry in entry_list if chains_dict[entry['inst_id']]['count'] > 1]
    return list(map(lambda entry: '{} {} {} {}'.format(entry['id'], entry['start'], entry['length'], entry['chain_id']),
                    filtered_entries))


init()

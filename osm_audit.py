#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
import datetime


lower = re.compile(r'^([a-z]|_)*$')
number = re.compile(r'^([0-9])*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
POS = ["lat","lon"]

expected = ["St", "St.", "Ave", "Rd","Rd.","Dr","Dr.","Pkwy"]

# Abbreviated street name to corrected street name
mapping = { "St": "Street",
            "St.": "Street",
            "Ave":"Avenue",
            "Rd.":"Road",
            "Rd":"Road",
            "Dr":"Drive",
            "Dr.":"Drive",
            "Pkwy":"Parkway"
            }

#zip code changes for Santa Ana city
zipmapping = {"Goetz Avenue":"92707",
                "South Oak Street": "92707",
                "Orange Avenue":"92707",
                "Rousselle Street":"92707",
                "Halladay Street":"92701",
                "South Hickory Street":"92707",
                "East Dyer Street":"92707"}




def update_name(name, mapping):

    streetName = name.split(' ')
    size =  len(streetName)
    actual = streetName[size-1]
    if actual  in expected:
        newValue = mapping[actual]
        streetName[size-1] = newValue
        name = ' '.join(streetName)
        #print name

    # YOUR CODE HERE

    return name
def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :
        node['created'] = {}
        geo = {}
        node['pos']=[]
        node['address']={}
        node['node_refs']=[]

        for tag in element.iter(element.tag):
            node['type'] = element.tag
            for name in tag.attrib:
                if name in CREATED:
                    node['created'][name] = tag.attrib[name]
                elif name in POS:
                    geo[name] = float(tag.attrib[name])
                else:
                    node[name] = tag.attrib[name]
            if 'lat' in geo:
               node['pos'].append(geo['lat'])
               node['pos'].append(geo['lon'])


        for tag in list(element):

            if tag.tag == "tag":


                key = tag.attrib['k']
                match = re.search(problemchars, key)
                if  match:
                    continue
                elif key.startswith('addr'):
                   value = key.split(':')
                   if len(value) > 2:
                        continue
                   else:
                      name = tag.attrib['v']
                      #clean  street names
                      if value[1] == 'street':
                          #fix abbreviated street name
                          name = update_name(tag.attrib['v'],mapping)

                          #skip lines that have just number
                          match = re.search(number,name)
                          if match:
                              print name
                              continue


                      if value[1]== 'postcode':
                          #Fix post code
                          post = tag.attrib['v'].split(' ')
                          if len(post) > 1:
                             name = post[1]
                          match = re.search(number, name)
                          if not match:
                              print name
                              continue
                      node['address'][value[1]] = name
                else:
                   node[tag.attrib['k']]=tag.attrib['v']
            elif tag.tag == "nd":
                node['node_refs'].append(tag.attrib['ref'])

    else:
        return None

    if node['address']=={}:
        node.pop('address')
    if node['node_refs']==[]:
        node.pop('node_refs')

    # Fix incorrect post code
    if 'address' in node:
       dict = node['address']
       if 'street' in dict:
          if node['address']['street'] in zipmapping:
              street = node['address']['street']
              node['address']['postcode'] = zipmapping[street]
              print node['address']['postcode']


    return node

def process_map(file_in, pretty = False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    db = get_db()
    data = []
    count = 0
    print datetime.datetime.now()
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)

            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:

                    #print el['id']
                    fo.write(json.dumps(el) + "\n")
                    db.osmclean.insert(el)
                    count = count + 1
                    #check if correctly inserting into mongodb by peridically checking from the db
                    if (count % 10000) == 0:
                        print count
                        print db.osmclean.find_one({"id": el['id']})
                        print datetime.datetime.now()


    print datetime.datetime.now()

    return data

def get_db():
    from pymongo import MongoClient
    client = MongoClient('127.0.0.1:27017')
    db = client.osm
    return db

def test():
    data = process_map('orange.osm', False)


if __name__ == "__main__":
    test()

#!/usr/bin/env python

import datetime
import json
import pprint

from lxml import etree
from pymongo import MongoClient
import requests
import xmltodict


class QBPInterface:

    def __init__(self):

        self.api_key = u''
        self.base_url = u'http://api.qbp.com/api/1/'

        self.headers = {
                u'X-QBPAPI-KEY': self.api_key,
                u'content-type': u'application/xhtml+xml'
                }

    def get(self, url):
        res = requests.get(url, headers=self.headers)
        return etree.fromstring(res.content)

    def post(self, url, xml_content):
        res = requests.post(url, headers=self.headers, data=xml_content)
        return etree.fromstring(res.content)

    def getSkuList(self):
        url = self.base_url + u'/product/skulist'
        xml = self.get(url)

        skus = [sku.text for sku in xml[0]]
        return skus

    def getProductsBySkuList(self, sku_list):
        url = self.base_url + u'/product/sku?stocklevels=yes&barcodes=yes&freightdata=yes&images=yes&substitues=yes&bulletpoints=yes'
        req_xml = self.qbpXMLRequest(u'productRequest', u'ids', u'id', sku_list)
        xml = self.post(url, etree.tostring(req_xml))

        return xml

    def qbpXMLRequest(self, parent, child, item_tag, item_list):
        xml_request = etree.Element(parent)
        id_list = etree.SubElement(xml_request, child)
        for item in item_list:
            element = etree.SubElement(id_list, item_tag)
            element.text = item

        return xml_request


qbp = QBPInterface()

client = MongoClient()
db = client.radiantretail
collection = db.product

skus = qbp.getSkuList()
for i in range(10):

    low = i*100
    high = (i+1)*100
    #product_list_xml = etree.parse('test.xml').getroot()

    #print json.dumps(product_list_dict['productResponse']['products']['product'], indent=2)
    product_list_xml = qbp.getProductsBySkuList(skus[low:high])
    #product_list_dict = xmltodict.parse(etree.tostring(product_list_xml))
    #pprint.pprint(product_list_dict['products'])
    #print json.dumps(product_list_dict['productResponse']['products']['product'], indent=2)

    products = []
    for product in product_list_xml.findall('products/product'):
        print product.findtext('sku')
        product_dict = {
            'sku': product.findtext('sku'),
            'name': product.findtext('name'),
            'manufacturerPartNumber': product.findtext('manufacturerPartNumber'),
            'cost': float(product.findtext('basePrice/value')),
            'price': float(product.findtext('msrp/value')),
            'freight': {
                'length': {
                    'value': float(product.findtext('freightData/Length/value')),
                    'unit': product.findtext('freightData/Length/unit')
                    },
                'width': {
                    'value': float(product.findtext('freightData/Width/value')),
                    'unit': product.findtext('freightData/Width/unit')
                    },
                'height': {
                    'value': float(product.findtext('freightData/Height/value')),
                    'unit': product.findtext('freightData/Height/unit')
                    },
                'weight': {
                    'value': float(product.findtext('freightData/Weight/value')),
                    'unit': product.findtext('freightData/Weight/unit')
                    },
                },
            'images': [],
            'barcode': {
                'type': product.findtext('barcodes/Barcode/type'),
                'value': product.findtext('barcodes/Barcode/value'),
                'checksum': product.findtext('barcodes/Barcode/chksum')
                },
            'stockLevels': []
            }

        for image in product.findall('images/image'):
            product_dict['images'].append(image.findtext('fileName'))

        for stockLevel in product.findall('stockLevels/stockLevel'):
            d = xmltodict.parse(etree.tostring(stockLevel))['stockLevel']
            w = d['warehouse']
            product_dict['stockLevels'].append({
                'warehouse': {
                    'name': w['name'],
                    'city': w['description'],
                    'state': w['abbreviation'],
                    'code': w['code']
                    },
                'quantity': int(d['quantityAvailable']),
                'status': d['stockLevelStatus'],
                'estimatedArrivalDate': datetime.datetime.fromtimestamp(int(d['estimatedArrivalDate']['iMillis'][:-3]))
                })

        products.append(product_dict)


    #pprint.pprint(products)
    collection.insert(products)

#if __name__ == '__main__':
#    getProducts()
